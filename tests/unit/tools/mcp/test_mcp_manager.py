"""MCP discovery is never a bypass around Guillotine authorization."""

from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import cast

import pytest
from mcp import ClientSession
from mcp.types import CallToolResult
from mcp.types import Tool as MCPTool

from guillotine.core.approvals import JsonValue
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
from guillotine.tools.core.registry import ToolRegistry, UnknownToolError
from guillotine.tools.mcp.client import (
    MCPClient,
    MCPNotConnectedError,
    MCPRemoteToolError,
)
from guillotine.tools.mcp.manager import (
    MCPManager,
    MCPServerAlreadyConnected,
    MCPToolNotFound,
)


class FakeSession:
    def __init__(self, *, names: tuple[str, ...] = ("read", "write")) -> None:
        self.names = names
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.initializations = 0
        self.closed = False
        self.error = False

    async def initialize(self) -> object:
        self.initializations += 1
        return None

    async def list_tools(self) -> object:
        return SimpleNamespace(
            tools=tuple(
                MCPTool(name=name, input_schema={"type": "object"})
                for name in self.names
            )
        )

    async def call_tool(
        self, name: str, arguments: dict[str, object]
    ) -> CallToolResult:
        self.calls.append((name, arguments))
        return cast("CallToolResult", SimpleNamespace(is_error=self.error, content=[]))


def client(session: FakeSession) -> MCPClient:
    @asynccontextmanager
    async def factory() -> AsyncGenerator[ClientSession]:
        try:
            yield cast("ClientSession", session)
        finally:
            session.closed = True

    return MCPClient(factory)


def resolver(args: Mapping[str, JsonValue]) -> str | None:
    path = args.get("path")
    if not isinstance(path, str):
        raise ValueError("path required")
    return f"file:/{path}"


def setup(
    outcome: PermissionDecision = PermissionDecision.ALLOW,
) -> tuple[ToolRegistry, ToolExecutor, MCPManager]:
    registry = ToolRegistry()

    async def current() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(PermissionRule("mcp:files:read", "file:/safe.txt", outcome),),
        )

    executor = ToolExecutor(registry, current)
    return registry, executor, MCPManager(registry, executor)


READ = ToolSecurity(effects=frozenset({ToolEffect.READ}))


@pytest.mark.asyncio
async def test_client_lifecycle_and_native_result() -> None:
    session = FakeSession()
    c = client(session)
    with pytest.raises(MCPNotConnectedError):
        await c.list_tools()
    await c.connect()
    assert session.initializations == 1
    assert len(await c.list_tools()) == 2
    await c.call_tool("read", {"path": "safe.txt"})
    assert session.calls == [("read", {"path": "safe.txt"})]
    await c.close()
    assert session.closed
    with pytest.raises(MCPNotConnectedError):
        await c.call_tool("read", {})


@pytest.mark.asyncio
async def test_server_error_not_mistaken_for_success() -> None:
    session = FakeSession()
    session.error = True
    c = client(session)
    await c.connect()
    with pytest.raises(MCPRemoteToolError):
        await c.call_tool("read", {})
    await c.close()


@pytest.mark.asyncio
async def test_selected_tool_calls_only_through_authorized_executor() -> None:
    registry, executor, manager = setup()
    session = FakeSession()
    registration = await manager.connect(
        "files", client(session), resolvers={"read": resolver}, security={"read": READ}
    )
    assert registration.tool_ids == ("mcp:files:read",)
    assert len(registry.list_tools()) == 1  # write is not implicitly exposed
    await executor.execute("mcp:files:read", arguments={"path": "safe.txt"})
    assert session.calls == [("read", {"path": "safe.txt"})]
    await manager.close()
    assert session.closed


@pytest.mark.asyncio
async def test_denied_resource_never_reaches_server() -> None:
    _, executor, manager = setup()
    session = FakeSession()
    await manager.connect(
        "files", client(session), resolvers={"read": resolver}, security={"read": READ}
    )
    with pytest.raises(ToolExecutionDenied):
        await executor.execute("mcp:files:read", arguments={"path": "private.txt"})
    assert session.calls == []
    await manager.close()


@pytest.mark.asyncio
async def test_unknown_security_stays_denied_even_with_allow_rule() -> None:
    _, executor, manager = setup()
    session = FakeSession()
    await manager.connect("files", client(session), resolvers={"read": resolver})
    with pytest.raises(ToolExecutionDenied):
        await executor.execute("mcp:files:read", arguments={"path": "safe.txt"})
    assert not session.calls
    await manager.close()


@pytest.mark.asyncio
async def test_missing_selected_tool_rolls_back_and_closes() -> None:
    registry, _, manager = setup()
    session = FakeSession()
    with pytest.raises(MCPToolNotFound):
        await manager.connect("files", client(session), resolvers={"absent": resolver})
    assert registry.list_tools() == ()
    assert manager.list_servers() == ()
    assert session.closed


@pytest.mark.asyncio
async def test_duplicate_remote_names_roll_back() -> None:
    registry, _, manager = setup()
    session = FakeSession(names=("read", "read"))
    with pytest.raises(ValueError, match="duplicate"):
        await manager.connect("files", client(session), resolvers={"read": resolver})
    assert registry.list_tools() == ()
    assert session.closed


@pytest.mark.asyncio
async def test_bad_tool_name_after_partial_registration_rolls_back() -> None:
    registry, executor, manager = setup()
    session = FakeSession(names=("read", "bad:name"))
    with pytest.raises(ValueError):
        await manager.connect(
            "files",
            client(session),
            resolvers={"read": resolver, "bad:name": resolver},
        )
    assert registry.list_tools() == ()
    with pytest.raises((ToolAdapterMissing, UnknownToolError)):
        await executor.execute("mcp:files:read", arguments={"path": "safe.txt"})
    assert session.closed


@pytest.mark.asyncio
async def test_duplicate_server_does_not_connect_second_session() -> None:
    _, _, manager = setup()
    first = FakeSession()
    second = FakeSession()
    await manager.connect("files", client(first), resolvers={"read": resolver})
    with pytest.raises(MCPServerAlreadyConnected):
        await manager.connect("files", client(second), resolvers={"read": resolver})
    assert second.initializations == 0
    await manager.close()


@pytest.mark.asyncio
async def test_disconnect_unbinds_and_unregisters() -> None:
    registry, executor, manager = setup()
    session = FakeSession()
    await manager.connect("files", client(session), resolvers={"read": resolver})
    await manager.disconnect("files")
    assert registry.list_tools() == ()
    assert session.closed
    with pytest.raises((ToolAdapterMissing, UnknownToolError)):
        await executor.execute("mcp:files:read", arguments={"path": "safe.txt"})


@pytest.mark.asyncio
async def test_security_cannot_be_declared_for_unselected_tool() -> None:
    _, _, manager = setup()
    session = FakeSession()
    with pytest.raises(ValueError):
        await manager.connect(
            "files",
            client(session),
            resolvers={"read": resolver},
            security={"write": READ},
        )
    assert session.initializations == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "server_ids",
    [
        (),
        ("server_a",),
        ("server_a", "server_b"),
        ("server_a", "server_b", "server_c"),
        ("server_a", "server_b", "server_c", "server_d"),
    ],
)
async def test_close_disconnects_servers_in_reverse_order(
    monkeypatch: pytest.MonkeyPatch,
    server_ids: tuple[str, ...],
) -> None:
    manager = MCPManager.__new__(MCPManager)

    monkeypatch.setattr(
        manager,
        "_servers",
        dict.fromkeys(server_ids),
        raising=False,
    )

    disconnected: list[str] = []

    async def fake_disconnect(server_id: str) -> None:
        disconnected.append(server_id)

    monkeypatch.setattr(manager, "disconnect", fake_disconnect)

    await manager.close()

    assert disconnected == list(reversed(server_ids))
