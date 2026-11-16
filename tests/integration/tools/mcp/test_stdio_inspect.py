"""Discover native MCP tools over real stdio without enabling their execution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from guillotine.core.mcp_configuration import ServerSpec
from guillotine.interfaces.mcp_commands import inspect_server


@pytest.mark.asyncio
async def test_inspect_real_local_stdio_server() -> None:
    server_file = Path(__file__).with_name("stdio_server.py")
    server = ServerSpec(
        id="fixture",
        transport="stdio",
        command=sys.executable,
        args=(str(server_file),),
    )
    names = await inspect_server(server)
    assert "write_marker" in names
    assert "ignored_tool" in names
