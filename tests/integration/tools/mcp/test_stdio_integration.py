"""End-to-end MCP stdio transport through Guillotine's authorization boundary.

Unlike unit tests, these spawn a real local MCP server process. No model,
network service, API key or Docker installation is required.
"""

import sys
from collections.abc import Mapping
from pathlib import Path

import pytest
from mcp import StdioServerParameters

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
from guillotine.tools.core.contracts import ToolEffect, ToolSecurity
from guillotine.tools.core.executor import (
    ToolAdapterMissing,
    ToolExecutionDenied,
    ToolExecutor,
)
from guillotine.tools.core.registry import ToolRegistry
from guillotine.tools.mcp.client import MCPClient, stdio_session_factory
from guillotine.tools.mcp.manager import MCPManager

TOOL_ID = "mcp:fixture:write_marker"
WRITE_SECURITY = ToolSecurity(effects=frozenset({ToolEffect.WRITE}))
SERVER_FILE = Path(__file__).with_name("stdio_server.py")


def marker_resource(arguments: Mapping[str, JsonValue]) -> str:
    """Derive a canonical ID from actual call arguments, not the model's claim."""
    path = arguments.get("path")
    if not isinstance(path, str) or not path:
        raise ValueError("A nonempty path is required")
    return Path(path).resolve().as_uri()


def server_client() -> MCPClient:
    """Use the current venv Python, ensuring the subprocess sees its MCP SDK."""
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
    )
    return MCPClient(stdio_session_factory(parameters))


@pytest.mark.asyncio
async def test_real_stdio_discovery_allow_deny_and_disconnect(
    tmp_path: Path,
) -> None:
    allowed_path = tmp_path / "allowed.txt"
    denied_path = tmp_path / "denied.txt"
    registry = ToolRegistry()

    async def current_permissions() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(
                PermissionRule(
                    TOOL_ID,
                    allowed_path.resolve().as_uri(),
                    PermissionDecision.ALLOW,
                ),
            ),
        )

    executor = ToolExecutor(registry, current_permissions)
    manager = MCPManager(registry, executor)
    try:
        registered = await manager.connect(
            "fixture",
            server_client(),
            resolvers={"write_marker": marker_resource},
            security={"write_marker": WRITE_SECURITY},
        )
        assert registered.tool_ids == (TOOL_ID,)
        assert tuple(item.identifier for item in registry.list_tools()) == (TOOL_ID,)

        with pytest.raises(ToolExecutionDenied):
            await executor.execute(
                TOOL_ID,
                arguments={"path": str(denied_path), "content": "NOT ALLOWED"},
            )
        assert not denied_path.exists()

        await executor.execute(
            TOOL_ID,
            arguments={"path": str(allowed_path), "content": "AUTHORIZED"},
        )
        assert allowed_path.read_text(encoding="utf-8") == "AUTHORIZED"
    finally:
        await manager.close()

    assert registry.list_tools() == ()
    assert manager.list_servers() == ()
    with pytest.raises(ToolAdapterMissing, match="adapter"):
        await executor.execute(
            TOOL_ID,
            arguments={"path": str(allowed_path), "content": "AFTER CLOSE"},
        )
    assert allowed_path.read_text(encoding="utf-8") == "AUTHORIZED"


@pytest.mark.asyncio
async def test_real_stdio_requires_approval_and_respects_refusal(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "needs-approval.txt"
    registry = ToolRegistry()
    prompts: list[ApprovalRequest] = []
    choices = iter((ApprovalChoice.DENY, ApprovalChoice.APPROVE_ONCE))

    async def prompt(request: ApprovalRequest) -> ApprovalChoice:
        prompts.append(request)
        return next(choices)

    async def current_permissions() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(
                PermissionRule(
                    TOOL_ID,
                    marker.resolve().as_uri(),
                    PermissionDecision.REQUIRE_APPROVAL,
                ),
            ),
        )

    executor = ToolExecutor(
        registry,
        current_permissions,
        approvals=ApprovalManager(prompt),
    )
    manager = MCPManager(registry, executor)
    try:
        await manager.connect(
            "fixture",
            server_client(),
            resolvers={"write_marker": marker_resource},
            security={"write_marker": WRITE_SECURITY},
        )
        arguments: dict[str, JsonValue] = {
            "path": str(marker),
            "content": "APPROVED ONCE",
        }
        with pytest.raises(ToolExecutionDenied):
            await executor.execute(TOOL_ID, arguments=arguments)
        assert not marker.exists()

        await executor.execute(TOOL_ID, arguments=arguments)
        assert marker.read_text(encoding="utf-8") == "APPROVED ONCE"
        assert len(prompts) == 2
        assert all(request.tool_id == TOOL_ID for request in prompts)
    finally:
        await manager.close()
