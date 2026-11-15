"""The executor must never dispatch a call without matching authorization."""

from collections.abc import Mapping
from types import SimpleNamespace
from typing import cast

import pytest
from pydantic_ai.tools import Tool as PydanticTool

from guillotine.core.approvals import (
    ApprovalChoice,
    ApprovalManager,
    ApprovalRequest,
    JsonValue,
)
from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionProfile,
    PermissionRule,
)
from guillotine.tools.contracts import ToolEffect, ToolSecurity
from guillotine.tools.executor import (
    ToolAdapterMissing,
    ToolExecutionDenied,
    ToolExecutor,
)
from guillotine.tools.registry import ToolRegistry


def local(name: str = "write") -> PydanticTool[object]:
    return cast("PydanticTool[object]", SimpleNamespace(name=name))


def registry() -> ToolRegistry:
    tools = ToolRegistry()
    tools.register_local(
        local(), security=ToolSecurity(effects=frozenset({ToolEffect.WRITE}))
    )
    return tools


def policy(
    tools: ToolRegistry,
    outcome: PermissionDecision,
    resource: str | None = "file:/safe.txt",
) -> PermissionManager:
    return PermissionManager(
        tools,
        profile=PermissionProfile.CUSTOM,
        rules=(PermissionRule("local:write", resource, outcome),),
    )


def executor(
    tools: ToolRegistry,
    decision: PermissionDecision,
    *,
    approvals: ApprovalManager | None = None,
    resource: str | None = "file:/safe.txt",
) -> ToolExecutor:
    async def current() -> PermissionManager:
        return policy(tools, decision, resource)

    return ToolExecutor(tools, current, approvals=approvals)


def bind(exe: ToolExecutor, calls: list[dict[str, JsonValue]]) -> None:
    async def invoke(args: dict[str, JsonValue]) -> object:
        calls.append(args)
        return {"success": True}

    def resource(args: Mapping[str, JsonValue]) -> str | None:
        value = args.get("path")
        if not isinstance(value, str):
            raise ValueError("Missing file path")
        return f"file:/{value}"

    exe.bind("local:write", invoke=invoke, resource=resource)


@pytest.mark.asyncio
async def test_explicit_allow_executes_once() -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []
    exe = executor(tools, PermissionDecision.ALLOW)
    bind(exe, calls)
    assert await exe.execute("local:write", arguments={"path": "safe.txt"}) == {
        "success": True
    }
    assert calls == [{"path": "safe.txt"}]


@pytest.mark.asyncio
async def test_explicit_deny_never_invokes() -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []
    exe = executor(tools, PermissionDecision.DENY)
    bind(exe, calls)
    with pytest.raises(ToolExecutionDenied):
        await exe.execute("local:write", arguments={"path": "safe.txt"})
    assert calls == []


@pytest.mark.asyncio
async def test_approval_without_ui_is_denied() -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []
    exe = executor(tools, PermissionDecision.REQUIRE_APPROVAL)
    bind(exe, calls)
    with pytest.raises(ToolExecutionDenied):
        await exe.execute("local:write", arguments={"path": "safe.txt"})
    assert calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("choice", [ApprovalChoice.APPROVE_ONCE, ApprovalChoice.DENY])
async def test_human_choice_controls_dispatch(choice: ApprovalChoice) -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []

    async def prompt(_request: ApprovalRequest) -> ApprovalChoice:
        return choice

    exe = executor(
        tools, PermissionDecision.REQUIRE_APPROVAL, approvals=ApprovalManager(prompt)
    )
    bind(exe, calls)
    if choice is ApprovalChoice.DENY:
        with pytest.raises(ToolExecutionDenied):
            await exe.execute("local:write", arguments={"path": "safe.txt"})
        assert calls == []
    else:
        await exe.execute("local:write", arguments={"path": "safe.txt"})
        assert calls == [{"path": "safe.txt"}]


@pytest.mark.asyncio
async def test_wrong_resource_is_not_authorized() -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []
    exe = executor(tools, PermissionDecision.ALLOW)
    bind(exe, calls)
    with pytest.raises(ToolExecutionDenied):
        await exe.execute("local:write", arguments={"path": "private.txt"})
    assert calls == []


@pytest.mark.asyncio
async def test_missing_adapter_never_executes() -> None:
    tools = registry()
    exe = executor(tools, PermissionDecision.ALLOW)
    with pytest.raises(ToolAdapterMissing):
        await exe.execute("local:write", arguments={"path": "safe.txt"})


@pytest.mark.asyncio
async def test_changed_registry_entry_invalidates_adapter() -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []
    exe = executor(tools, PermissionDecision.ALLOW)
    bind(exe, calls)
    tools.unregister("local:write")
    tools.register_local(
        local(), security=ToolSecurity(effects=frozenset({ToolEffect.WRITE}))
    )
    with pytest.raises(ToolExecutionDenied):
        await exe.execute("local:write", arguments={"path": "safe.txt"})
    assert calls == []


@pytest.mark.asyncio
async def test_arguments_detached_from_caller() -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []
    exe = executor(tools, PermissionDecision.ALLOW)
    bind(exe, calls)
    original: dict[str, JsonValue] = {"path": "safe.txt", "numbers": [1, 2]}
    await exe.execute("local:write", arguments=original)
    original["path"] = "private.txt"
    assert calls[0]["path"] == "safe.txt"


@pytest.mark.asyncio
async def test_policy_change_during_prompt_denies() -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []
    current_decision = PermissionDecision.REQUIRE_APPROVAL

    async def prompt(_request: ApprovalRequest) -> ApprovalChoice:
        nonlocal current_decision
        current_decision = PermissionDecision.DENY
        return ApprovalChoice.APPROVE_ONCE

    async def current() -> PermissionManager:
        return policy(tools, current_decision)

    exe = ToolExecutor(tools, current, approvals=ApprovalManager(prompt))
    bind(exe, calls)
    with pytest.raises(ToolExecutionDenied):
        await exe.execute("local:write", arguments={"path": "safe.txt"})
    assert calls == []


@pytest.mark.asyncio
async def test_registry_change_during_prompt_denies() -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []

    async def prompt(_request: ApprovalRequest) -> ApprovalChoice:
        tools.unregister("local:write")
        return ApprovalChoice.APPROVE_ONCE

    exe = executor(
        tools, PermissionDecision.REQUIRE_APPROVAL, approvals=ApprovalManager(prompt)
    )
    bind(exe, calls)
    with pytest.raises((ToolExecutionDenied, LookupError)):
        await exe.execute("local:write", arguments={"path": "safe.txt"})
    assert calls == []


@pytest.mark.asyncio
async def test_unclassified_tool_is_denied() -> None:
    tools = ToolRegistry()
    tools.register_local(local())
    calls: list[dict[str, JsonValue]] = []
    exe = executor(tools, PermissionDecision.ALLOW)
    bind(exe, calls)
    with pytest.raises(ToolExecutionDenied):
        await exe.execute("local:write", arguments={"path": "safe.txt"})
    assert calls == []


@pytest.mark.asyncio
async def test_resource_resolver_does_not_modify_execution_args() -> None:
    tools = registry()
    calls: list[dict[str, JsonValue]] = []
    exe = executor(tools, PermissionDecision.ALLOW)

    async def invoke(args: dict[str, JsonValue]) -> object:
        calls.append(args)
        return None

    def malicious_resource(args: Mapping[str, JsonValue]) -> str:
        return "file:/safe.txt"

    exe.bind("local:write", invoke=invoke, resource=malicious_resource)
    await exe.execute("local:write", arguments={"path": "safe.txt"})
    assert calls == [{"path": "safe.txt"}]
