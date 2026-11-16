"""Connect trusted MCP servers to Guillotine's authorized ToolExecutor.

Discovery is not authorization. Only explicitly selected tools with trusted
resource resolvers are bound; all calls still pass through ToolExecutor.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass

from guillotine.core.approvals import JsonValue
from guillotine.tools.core.contracts import ToolSecurity
from guillotine.tools.core.executor import ResourceResolver, ToolExecutor
from guillotine.tools.core.registry import ToolRegistry
from guillotine.tools.mcp.client import MCPClient


class MCPServerAlreadyConnected(ValueError):
    """The given logical server identifier is already in use."""


class MCPToolNotFound(LookupError):
    """A selected tool was not advertised by the server."""


@dataclass(frozen=True, slots=True)
class MCPServerRegistration:
    """The IDs actually registered for this specific server session."""

    server_id: str
    tool_ids: tuple[str, ...]


class MCPManager:
    """Manage trusted MCP sessions and bind selected tools to the executor.

    Call ``close()`` before leaving the task that created the stdio sessions.
    Client instances belong exclusively to one manager and server ID.
    """

    def __init__(self, registry: ToolRegistry, executor: ToolExecutor) -> None:
        self._registry = registry
        self._executor = executor
        self._servers: dict[str, tuple[MCPClient, MCPServerRegistration]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        server_id: str,
        client: MCPClient,
        *,
        resolvers: Mapping[str, ResourceResolver],
        security: Mapping[str, ToolSecurity] | None = None,
    ) -> MCPServerRegistration:
        """Discover then register only tools selected in trusted configuration.

        A resolver is mandatory for every selected tool. Unknown server tools
        remain unregistered. Security metadata defaults to UNKNOWN/CRITICAL.
        No server-supplied annotation is treated as trusted policy.
        """
        if not server_id or not server_id.strip():
            raise ValueError("Server ID must be nonblank")
        if not resolvers:
            raise ValueError("At least one trusted tool resolver is required")
        trusted_security: Mapping[str, ToolSecurity] = (
            security if security is not None else {}
        )
        if set(trusted_security) - set(resolvers):
            raise ValueError("Security metadata refers to an unselected tool")
        async with self._lock:
            if server_id in self._servers:
                raise MCPServerAlreadyConnected(server_id)
            if any(existing is client for existing, _ in self._servers.values()):
                raise ValueError("An MCP client cannot be registered twice")
            registered: list[str] = []
            connected = False
            try:
                await client.connect()
                connected = True
                definitions = await client.list_tools()
                by_name = {definition.name: definition for definition in definitions}
                if len(by_name) != len(definitions):
                    raise ValueError("MCP server advertised duplicate tool names")
                missing = set(resolvers) - set(by_name)
                if missing:
                    raise MCPToolNotFound(
                        f"Selected MCP tools not advertised: {sorted(missing)}"
                    )
                for name, resolver in resolvers.items():
                    entry = self._registry.register_mcp(
                        by_name[name],
                        server_id=server_id,
                        security=trusted_security.get(name),
                    )
                    registered.append(entry.identifier)

                    async def invoke(
                        arguments: dict[str, JsonValue],
                        *,
                        _name: str = name,
                    ) -> object:
                        return await client.call_tool(_name, arguments)

                    self._executor.bind(
                        entry.identifier, invoke=invoke, resource=resolver
                    )
                registration = MCPServerRegistration(server_id, tuple(registered))
                self._servers[server_id] = (client, registration)
                return registration
            except BaseException:
                for tool_id in reversed(registered):
                    self._executor.unbind(tool_id)
                    self._registry.unregister(tool_id)
                if connected:
                    await client.close()
                raise

    async def disconnect(self, server_id: str) -> None:
        """Immediately unbind names before closing the server session."""
        async with self._lock:
            client, registration = self._servers.pop(server_id)
            for tool_id in registration.tool_ids:
                self._executor.unbind(tool_id)
                self._registry.unregister(tool_id)
            await client.close()

    def list_servers(self) -> tuple[MCPServerRegistration, ...]:
        return tuple(registration for _, registration in self._servers.values())

    async def close(self) -> None:
        """Close MCP sessions in reverse connection order."""
        errors: list[Exception] = []

        for server_id in reversed(tuple(self._servers)):
            try:
                await self.disconnect(server_id)
            except Exception as exc:
                errors.append(exc)

        if errors:
            raise ExceptionGroup("Failed to close MCP servers", errors)
