"""Load user-owned MCP configuration into the real guarded stdio transport."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from guillotine.core.mcp_configuration import (
    FileResource,
    MCPConfiguration,
    SelectedTool,
    ServerSpec,
    connect_configured_servers,
    read_config,
    write_config,
)
from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionProfile,
    PermissionRule,
)
from guillotine.tools.core.contracts import ToolEffect
from guillotine.tools.core.executor import ToolExecutionDenied, ToolExecutor
from guillotine.tools.core.registry import ToolRegistry
from guillotine.tools.mcp.manager import MCPManager

SERVER_FILE = Path(__file__).with_name("stdio_server.py")
TOOL_ID = "mcp:fixture:write_marker"


@pytest.mark.asyncio
async def test_configured_tools_still_require_exact_permission(tmp_path: Path) -> None:
    """Configuration enables one tool, not an implicit grant to execute it."""
    marker = tmp_path / "marker.txt"
    configuration = MCPConfiguration(
        servers=(
            ServerSpec(
                id="fixture",
                transport="stdio",
                command=sys.executable,
                args=(str(SERVER_FILE),),
                tools=(
                    SelectedTool(
                        name="write_marker",
                        effects=(ToolEffect.WRITE,),
                        resource=FileResource(
                            kind="file",
                            argument="path",
                            root=tmp_path,
                        ),
                    ),
                ),
            ),
        ),
    )
    config_file = tmp_path / "mcp.json"
    write_config(config_file, configuration)
    loaded = read_config(config_file)
    registry = ToolRegistry()
    policy = PermissionDecision.DENY

    async def current_permissions() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(PermissionRule(TOOL_ID, marker.resolve().as_uri(), policy),),
        )

    executor = ToolExecutor(registry, current_permissions)
    manager = MCPManager(registry, executor)
    try:
        await connect_configured_servers(manager, loaded)
        assert {entry.identifier for entry in registry.list_tools()} == {TOOL_ID}
        with pytest.raises(ToolExecutionDenied):
            await executor.execute(
                TOOL_ID,
                arguments={"path": str(marker), "content": "blocked"},
            )
        assert not marker.exists()
        policy = PermissionDecision.ALLOW
        await executor.execute(
            TOOL_ID,
            arguments={"path": str(marker), "content": "authorized"},
        )
        assert marker.read_text(encoding="utf-8") == "authorized"
    finally:
        await manager.close()
    assert registry.list_tools() == ()
