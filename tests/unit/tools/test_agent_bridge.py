"""The model-to-tool bridge enforces registry and permission boundaries."""

from collections.abc import Mapping
from types import SimpleNamespace
from typing import cast

import pytest
from pydantic_ai.models.test import TestModel
from pydantic_ai.tools import Tool as PydanticTool

from guillotine.core.agent import create_agent
from guillotine.core.approvals import JsonValue
from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionProfile,
    PermissionRule,
)
from guillotine.tools.bridges.pydantic_ai import (
    decode_tool_arguments,
    execute_model_call,
    tool_catalog,
    visible_tools,
)
from guillotine.tools.core.contracts import ToolEffect, ToolSecurity
from guillotine.tools.core.executor import ToolExecutor
from guillotine.tools.core.registry import RegisteredTool, ToolRegistry


def setup_tool(
    decision: PermissionDecision,
) -> tuple[ToolRegistry, ToolExecutor, list[dict[str, JsonValue]]]:
    registry = ToolRegistry()
    native = cast("PydanticTool[object]", SimpleNamespace(name="write"))
    registry.register_local(
        native, security=ToolSecurity(effects=frozenset({ToolEffect.WRITE}))
    )

    async def current() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(PermissionRule("local:write", "file:/safe", decision),),
        )

    executor = ToolExecutor(registry, current)
    calls: list[dict[str, JsonValue]] = []

    async def invoke(arguments: dict[str, JsonValue]) -> object:
        calls.append(arguments)
        return "executado"

    def resolve(arguments: Mapping[str, JsonValue]) -> str | None:
        path = arguments.get("path")
        return f"file:/{path}" if isinstance(path, str) else None

    executor.bind("local:write", invoke=invoke, resource=resolve)
    return registry, executor, calls


def snapshot(registry: ToolRegistry) -> dict[str, RegisteredTool]:
    return {entry.identifier: entry for entry in visible_tools(registry)}


@pytest.mark.asyncio
async def test_allow_calls_only_executor() -> None:
    registry, executor, calls = setup_tool(PermissionDecision.ALLOW)
    output = await execute_model_call(
        "local:write",
        '{"path":"safe"}',
        allowed=snapshot(registry),
        registry=registry,
        executor=executor,
    )
    assert output == "executado"
    assert calls == [{"path": "safe"}]


@pytest.mark.asyncio
async def test_explicit_deny_does_not_execute() -> None:
    registry, executor, calls = setup_tool(PermissionDecision.DENY)
    output = await execute_model_call(
        "local:write",
        '{"path":"safe"}',
        allowed=snapshot(registry),
        registry=registry,
        executor=executor,
    )
    assert "não autorizada" in output
    assert calls == []


@pytest.mark.asyncio
async def test_approval_required_without_prompt_is_denied() -> None:
    registry, executor, calls = setup_tool(PermissionDecision.REQUIRE_APPROVAL)
    output = await execute_model_call(
        "local:write",
        '{"path":"safe"}',
        allowed=snapshot(registry),
        registry=registry,
        executor=executor,
    )
    assert "não autorizada" in output
    assert not calls


@pytest.mark.asyncio
async def test_unknown_tool_never_dispatches() -> None:
    registry, executor, calls = setup_tool(PermissionDecision.ALLOW)
    output = await execute_model_call(
        "mcp:unknown:write",
        '{"path":"safe"}',
        allowed=snapshot(registry),
        registry=registry,
        executor=executor,
    )
    assert "não disponibilizada" in output
    assert not calls


@pytest.mark.asyncio
async def test_unregister_and_reregister_cannot_reuse_snapshot() -> None:
    registry, executor, calls = setup_tool(PermissionDecision.ALLOW)
    allowed = snapshot(registry)
    registry.unregister("local:write")
    registry.register_local(
        cast("PydanticTool[object]", SimpleNamespace(name="write")),
        security=ToolSecurity(effects=frozenset({ToolEffect.WRITE})),
    )
    output = await execute_model_call(
        "local:write",
        '{"path":"safe"}',
        allowed=allowed,
        registry=registry,
        executor=executor,
    )
    assert "alterada" in output
    assert not calls


@pytest.mark.asyncio
async def test_invalid_arguments_do_not_execute() -> None:
    registry, executor, calls = setup_tool(PermissionDecision.ALLOW)
    for raw in ("not json", '["safe"]', "null"):
        result = await execute_model_call(
            "local:write",
            raw,
            allowed=snapshot(registry),
            registry=registry,
            executor=executor,
        )
        assert "inválidos" in result
    assert calls == []


def test_arguments_must_be_json_object() -> None:
    assert decode_tool_arguments('{"path":"safe"}') == {"path": "safe"}
    with pytest.raises(ValueError):
        decode_tool_arguments("[]")


def test_catalog_contains_only_ids_not_server_descriptions() -> None:
    registry, _, _ = setup_tool(PermissionDecision.ALLOW)
    result = tool_catalog(visible_tools(registry))
    assert "local:write" in result
    assert "instruções do servidor" not in result


def test_agent_registers_gateway_only_when_registry_has_tools() -> None:
    registry, executor, _ = setup_tool(PermissionDecision.ALLOW)
    assert create_agent(TestModel(), registry=registry, executor=executor) is not None
    assert (
        create_agent(TestModel(), registry=ToolRegistry(), executor=executor)
        is not None
    )


def test_agent_rejects_half_configured_tool_stack() -> None:
    with pytest.raises(ValueError):
        create_agent(TestModel(), registry=ToolRegistry())
