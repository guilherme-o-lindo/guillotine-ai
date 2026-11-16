"""Small lifecycle wrapper around the official MCP Python client SDK.

Transport configuration comes exclusively from trusted Guillotine configuration.
Do not accept arbitrary connection settings or URLs suggested by the model.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable, Mapping
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from typing import TYPE_CHECKING

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

if TYPE_CHECKING:
    from mcp.types import CallToolResult, Tool


type SessionFactory = Callable[[], AbstractAsyncContextManager[ClientSession]]


class MCPNotConnectedError(RuntimeError):
    """A server session has not been initialized or is already closed."""


class MCPRemoteToolError(RuntimeError):
    """The MCP server reported that a tool call failed."""


@asynccontextmanager
async def _stdio_session(
    parameters: StdioServerParameters,
) -> AsyncGenerator[ClientSession]:
    async with (
        stdio_client(parameters) as (reader, writer),
        ClientSession(reader, writer) as session,
    ):
        yield session


@asynccontextmanager
async def _http_session(url: str) -> AsyncGenerator[ClientSession]:
    async with (
        streamable_http_client(url) as (reader, writer),
        ClientSession(reader, writer) as session,
    ):
        yield session


def stdio_session_factory(parameters: StdioServerParameters) -> SessionFactory:
    """Build a trusted stdio factory, never from model-provided commands."""

    def factory() -> AbstractAsyncContextManager[ClientSession]:
        return _stdio_session(parameters)

    return factory


def http_session_factory(url: str) -> SessionFactory:
    """Create a Streamable HTTP factory for an explicitly trusted endpoint."""
    if not url.startswith(("https://", "http://")):
        raise ValueError("MCP HTTP endpoint must use http:// or https://")

    def factory() -> AbstractAsyncContextManager[ClientSession]:
        return _http_session(url)

    return factory


class MCPClient:
    """Own one MCP session and initialize it exactly once per connection.

    Public operations are serialized with close, so a session cannot be closed
    halfway through an SDK request. Open and close in the same async task when
    using transports backed by AnyIO task groups (including stdio).
    """

    def __init__(self, factory: SessionFactory) -> None:
        self._factory = factory
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            if self._session is not None:
                raise RuntimeError("MCP client is already connected")
            stack = AsyncExitStack()
            try:
                session = await stack.enter_async_context(self._factory())
                await session.initialize()
            except BaseException:
                await stack.aclose()
                raise
            self._stack = stack
            self._session = session

    async def list_tools(self) -> tuple[Tool, ...]:
        async with self._lock:
            if self._session is None:
                raise MCPNotConnectedError("MCP client is not connected")
            response = await self._session.list_tools()
            return tuple(response.tools)

    async def call_tool(
        self, name: str, arguments: Mapping[str, object]
    ) -> CallToolResult:
        async with self._lock:
            if self._session is None:
                raise MCPNotConnectedError("MCP client is not connected")
            # Permission approval and argument snapshots belong to ToolExecutor.
            result = await self._session.call_tool(name, arguments=dict(arguments))
            if result.is_error:
                raise MCPRemoteToolError(f"MCP tool reported an error: {name}")
            return result

    async def close(self) -> None:
        async with self._lock:
            stack = self._stack
            self._stack = None
            self._session = None
            if stack is not None:
                await stack.aclose()
