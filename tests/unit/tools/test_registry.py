from types import SimpleNamespace
from typing import cast

import pytest
from mcp.types import Tool as MCPTool
from pydantic_ai.tools import Tool as PydanticTool

from guillotine.tools.core.contracts import ToolEffect, ToolRisk, ToolSecurity
from guillotine.tools.core.registry import (
    DuplicateToolError,
    ToolRegistry,
    ToolSource,
    UnknownToolError,
)


def local(name: str | None = "inspect") -> PydanticTool[object]:
    # Native metadata shape, without calling the model/tool at test time.
    return cast("PydanticTool[object]", SimpleNamespace(name=name))


def mcp(name: str = "inspect") -> MCPTool:
    return MCPTool(
        name=name,
        input_schema={"type": "object"},
    )


def test_local_registration_preserves_native_definition() -> None:
    registry = ToolRegistry()
    definition = local()
    entry = registry.register_local(definition)
    assert entry.identifier == "local:inspect"
    assert entry.source is ToolSource.LOCAL
    assert entry.definition is definition
    assert registry.get(entry.identifier) is entry


def test_local_defaults_to_unknown_critical_risk() -> None:
    entry = ToolRegistry().register_local(local())
    assert entry.security.risk_hint is ToolRisk.CRITICAL


def test_explicit_trusted_classification_is_preserved() -> None:
    security = ToolSecurity(effects=frozenset({ToolEffect.READ}))
    entry = ToolRegistry().register_local(local(), security=security)
    assert entry.security is security
    assert entry.security.risk_hint is ToolRisk.MEDIUM


def test_mcp_registration_preserves_sdk_definition() -> None:
    registry = ToolRegistry()
    definition = mcp()
    entry = registry.register_mcp(definition, server_id="files")
    assert entry.identifier == "mcp:files:inspect"
    assert entry.source is ToolSource.MCP
    assert entry.server_id == "files"
    assert entry.definition is definition
    assert entry.security.risk_hint is ToolRisk.CRITICAL


def test_mcp_servers_with_same_tool_name_remain_distinct() -> None:
    registry = ToolRegistry()
    first = registry.register_mcp(mcp(), server_id="files")
    second = registry.register_mcp(mcp(), server_id="other")
    assert first.identifier != second.identifier
    assert len(registry.list_tools()) == 2


def test_local_and_mcp_names_do_not_collide() -> None:
    registry = ToolRegistry()
    registry.register_local(local())
    registry.register_mcp(mcp(), server_id="files")
    assert len(registry.list_tools()) == 2


def test_duplicate_registration_rejected_without_replacement() -> None:
    registry = ToolRegistry()
    first = registry.register_local(local())
    with pytest.raises(DuplicateToolError):
        registry.register_local(local())
    assert registry.get(first.identifier) is first


def test_duplicate_mcp_registration_rejected() -> None:
    registry = ToolRegistry()
    registry.register_mcp(mcp(), server_id="files")
    with pytest.raises(DuplicateToolError):
        registry.register_mcp(mcp(), server_id="files")


@pytest.mark.parametrize("name", ["", " ", " bad", "bad ", "bad:name"])
def test_invalid_local_name_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        ToolRegistry().register_local(local(name))


def test_missing_explicit_local_name_rejected() -> None:
    with pytest.raises(ValueError):
        ToolRegistry().register_local(local(None))


@pytest.mark.parametrize("server_id", ["", " ", " file", "file ", "file:name"])
def test_invalid_mcp_server_id_rejected(server_id: str) -> None:
    with pytest.raises(ValueError):
        ToolRegistry().register_mcp(mcp(), server_id=server_id)


def test_invalid_mcp_tool_name_rejected() -> None:
    with pytest.raises(ValueError):
        ToolRegistry().register_mcp(mcp("bad:name"), server_id="files")


def test_filter_and_snapshot() -> None:
    registry = ToolRegistry()
    first = registry.register_local(local())
    registry.register_mcp(mcp(), server_id="files")
    snapshot = registry.list_tools(source=ToolSource.LOCAL)
    assert snapshot == (first,)
    registry.unregister(first.identifier)
    assert snapshot == (first,)
    assert len(registry.list_tools(source=ToolSource.LOCAL)) == 0


def test_unknown_lookup_and_removal() -> None:
    registry = ToolRegistry()
    with pytest.raises(UnknownToolError):
        registry.get("local:missing")
    with pytest.raises(UnknownToolError):
        registry.unregister("local:missing")


def test_unregister_then_register_again() -> None:
    registry = ToolRegistry()
    old = registry.register_local(local())
    assert registry.unregister(old.identifier) is old
    new = registry.register_local(local())
    assert registry.get(new.identifier) is new
