"""Regression test for closing multiple real MCP stdio sessions on Windows.

The MCP SDK and AnyIO create nested cancellation scopes. Sessions opened
sequentially must be closed in reverse order by MCPManager.close().
"""

import sys
from collections.abc import Mapping
from pathlib import Path

import pytest
from mcp import StdioServerParameters

from guillotine.core.approvals import JsonValue
from guillotine.core.permissions import PermissionManager, PermissionProfile
from guillotine.tools.core.contracts import ToolEffect, ToolSecurity
from guillotine.tools.core.executor import ToolExecutor
from guillotine.tools.core.registry import ToolRegistry
from guillotine.tools.mcp.client import MCPClient, stdio_session_factory
from guillotine.tools.mcp.manager import MCPManager

SERVER_FILE = Path(__file__).with_name("stdio_server.py")
WRITE_SECURITY = ToolSecurity(effects=frozenset({ToolEffect.WRITE}))


def marker_resource(arguments: Mapping[str, JsonValue]) -> str:
    """Resolve the test marker path without granting execution permission."""
    path = arguments.get("path")
    if not isinstance(path, str) or not path:
        raise ValueError("A nonempty path is required")
    return Path(path).resolve().as_uri()


def server_client() -> MCPClient:
    """Spawn a real local MCP server with the project's Python environment."""
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
    )
    return MCPClient(stdio_session_factory(parameters))


@pytest.mark.asyncio
async def test_two_real_stdio_servers_close_without_cancel_scope_errors() -> None:
    """Two independently opened MCP sessions must close without ExceptionGroup."""
    registry = ToolRegistry()

    async def current_permissions() -> PermissionManager:
        return PermissionManager(registry, profile=PermissionProfile.CUSTOM)

    executor = ToolExecutor(registry, current_permissions)
    manager = MCPManager(registry, executor)
    first = server_client()
    second = server_client()

    try:
        for server_id, client in (("first", first), ("second", second)):
            registration = await manager.connect(
                server_id,
                client,
                resolvers={"write_marker": marker_resource},
                security={"write_marker": WRITE_SECURITY},
            )
            assert registration.tool_ids == (f"mcp:{server_id}:write_marker",)
            advertised = await client.list_tools()
            assert "write_marker" in {tool.name for tool in advertised}

        assert len(manager.list_servers()) == 2
        assert {tool.identifier for tool in registry.list_tools()} == {
            "mcp:first:write_marker",
            "mcp:second:write_marker",
        }
    finally:
        # The original Windows/AnyIO bug raised a RuntimeError/ExceptionGroup here.
        await manager.close()

    assert manager.list_servers() == ()
    assert registry.list_tools() == ()
