"""CLI entry point with explicit user-owned MCP startup configuration."""

from __future__ import annotations

import asyncio
import sys

from guillotine.core.lifecycle import ConfigureTools, lifespan
from guillotine.core.mcp_configuration import (
    config_path,
    connect_configured_servers,
    read_config,
)
from guillotine.interfaces.cli import run_cli
from guillotine.interfaces.mcp_commands import run_mcp_command
from guillotine.tools.mcp.manager import MCPManager


async def run() -> None:
    path = config_path()
    configure: ConfigureTools | None = None
    if path.exists():
        config = read_config(path)  # invalid configuration aborts startup
        if any(server.tools for server in config.servers):

            async def configure_saved_tools(manager: MCPManager) -> None:
                await connect_configured_servers(manager, config)

            configure = configure_saved_tools

    async with lifespan(configure_tools=configure) as conversation_service:
        await run_cli(conversation_service)


def main() -> None:
    if len(sys.argv) > 1:
        if sys.argv[1] != "mcp":
            raise SystemExit("Usage: guillotine [mcp <command>]")
        run_mcp_command(sys.argv[2:])
        return
    asyncio.run(run())


if __name__ == "__main__":
    main()
