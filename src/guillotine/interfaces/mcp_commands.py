"""Explicit commands for user-owned MCP configuration, never model-accessible."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence

from mcp.types import Tool as MCPTool

from guillotine.core.mcp_configuration import (
    FileResource,
    MCPConfiguration,
    NoResource,
    QueryResource,
    ReferenceTokenResource,
    RepositoryResource,
    SelectedTool,
    ServerSpec,
    URLResource,
    client_for_server,
    config_path,
    read_config,
    write_config,
)
from guillotine.tools.core.contracts import ToolEffect


async def inspect_server(server: ServerSpec) -> tuple[str, ...]:
    """Read a server's tool catalog without registering or executing tools."""
    client = client_for_server(server)
    try:
        await client.connect()
        tools = await client.list_tools()
        return tuple(sorted(tool.name for tool in tools))
    finally:
        await client.close()


async def inspect_server_details(server: ServerSpec) -> tuple[MCPTool, ...]:
    """Return SDK tool definitions without registering or executing them."""
    client = client_for_server(server)
    try:
        await client.connect()
        tools = await client.list_tools()
        return tuple(sorted(tools, key=lambda tool: tool.name))
    finally:
        await client.close()


def run_mcp_command(arguments: Sequence[str]) -> None:
    """Manage server selection without granting permission to execute tools."""
    parser = argparse.ArgumentParser(prog="guillotine mcp")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("init", help="Create an empty MCP configuration")
    commands.add_parser("list", help="List configured servers and selected tools")
    inspect = commands.add_parser(
        "inspect", help="Discover tools on a configured server"
    )
    inspect.add_argument("server_id")
    inspect.add_argument(
        "--details",
        action="store_true",
        help="Show tool description and native MCP input JSON Schema",
    )

    add = commands.add_parser("add-stdio", help="Add a local stdio server")
    add.add_argument("server_id")
    add.add_argument("command")
    add.add_argument("--arg", action="append", default=[])

    http = commands.add_parser("add-http", help="Add a Streamable HTTP server")
    http.add_argument("server_id")
    http.add_argument("url")

    select = commands.add_parser("select", help="Select an existing server's tool")
    select.add_argument("server_id")
    select.add_argument("tool_name")
    select.add_argument(
        "--effect",
        action="append",
        required=True,
        choices=[
            effect.value for effect in ToolEffect if effect is not ToolEffect.UNKNOWN
        ],
    )
    select.add_argument("--file-argument")
    select.add_argument("--root")
    select.add_argument("--no-resource", action="store_true")
    select.add_argument("--query-argument")
    select.add_argument("--ref-argument")
    select.add_argument("--url-argument")
    select.add_argument("--repo-argument")
    select.add_argument("--repo-root")

    parsed = parser.parse_args(list(arguments))
    path = config_path()
    if parsed.action == "init":
        if path.exists():
            parser.error(f"Configuration already exists: {path}")
        write_config(path, MCPConfiguration())
        print(f"Created: {path}")
        return

    if not path.is_file():
        parser.error(f"Missing configuration: {path}; run 'guillotine mcp init'")
    configuration = read_config(path)

    if parsed.action == "list":
        print(f"Configuration: {path}")
        for server in configuration.servers:
            print(f"  {server.id} ({server.transport})")
            for tool in server.tools:
                effects = ", ".join(effect.value for effect in tool.effects)
                print(f"    - {tool.name}: {effects}")
        return

    if parsed.action == "inspect":
        server = next(
            (item for item in configuration.servers if item.id == parsed.server_id),
            None,
        )
        if server is None:
            parser.error("Unknown server ID")
        # Explicitly user-invoked: runs the server process or contacts its URL.
        selected = {tool.name for tool in server.tools}
        if parsed.details:
            definitions = asyncio.run(inspect_server_details(server))
            for tool in definitions:
                suffix = " [selected]" if tool.name in selected else ""
                print(f"  {json.dumps(tool.name, ensure_ascii=True)}{suffix}")
                if tool.description:
                    print(f"    Description: {tool.description}")
                print("    Input schema:")
                schema = json.dumps(tool.input_schema, indent=2, ensure_ascii=False)
                for line in schema.splitlines():
                    print(f"      {line}")
        else:
            names = asyncio.run(inspect_server(server))
            for name in names:
                suffix = " [selected]" if name in selected else ""
                print(f"  {json.dumps(name, ensure_ascii=True)}{suffix}")
        return

    if parsed.action in ("add-stdio", "add-http"):
        if any(server.id == parsed.server_id for server in configuration.servers):
            parser.error("This server ID already exists")
        if parsed.action == "add-stdio":
            server = ServerSpec(
                id=parsed.server_id,
                transport="stdio",
                command=parsed.command,
                args=tuple(parsed.arg),
            )
        else:
            server = ServerSpec(
                id=parsed.server_id,
                transport="streamable-http",
                url=parsed.url,
            )
        write_config(
            path,
            MCPConfiguration(servers=(*configuration.servers, server)),
        )
        print(f"Server {server.id} configured but inactive (select a tool to enable)")
        return

    if parsed.action == "select":
        requested = sum(
            (
                bool(parsed.no_resource),
                bool(parsed.query_argument),
                bool(parsed.ref_argument),
                bool(parsed.url_argument),
                bool(parsed.repo_argument or parsed.repo_root),
                bool(parsed.file_argument or parsed.root),
            )
        )
        if requested != 1:
            parser.error("Choose exactly one resource scope")
        if parsed.no_resource:
            resource = NoResource(kind="none")
        elif parsed.query_argument:
            resource = QueryResource(kind="query", argument=parsed.query_argument)
        elif parsed.ref_argument:
            resource = ReferenceTokenResource(
                kind="reference_token", argument=parsed.ref_argument
            )
        elif parsed.url_argument:
            resource = URLResource(kind="url", argument=parsed.url_argument)
        elif parsed.repo_argument or parsed.repo_root:
            if not parsed.repo_argument or not parsed.repo_root:
                parser.error("--repo-argument and --repo-root must be paired")
            resource = RepositoryResource(
                kind="repository",
                argument=parsed.repo_argument,
                root=parsed.repo_root,
            )
        else:
            if not parsed.file_argument or not parsed.root:
                parser.error("--file-argument and --root must be paired")
            resource = FileResource(
                kind="file",
                argument=parsed.file_argument,
                root=parsed.root,
            )
        selected = SelectedTool(
            name=parsed.tool_name,
            effects=tuple(ToolEffect(effect) for effect in parsed.effect),
            resource=resource,
        )
        updated: list[ServerSpec] = []
        found = False
        for server in configuration.servers:
            if server.id != parsed.server_id:
                updated.append(server)
                continue
            found = True
            if any(tool.name == selected.name for tool in server.tools):
                parser.error("Tool is already selected")
            updated.append(
                server.model_copy(update={"tools": (*server.tools, selected)})
            )
        if not found:
            parser.error("Unknown server ID")
        write_config(path, MCPConfiguration(servers=tuple(updated)))
        print(f"Selected {parsed.server_id}:{selected.name}; permissions unchanged")
