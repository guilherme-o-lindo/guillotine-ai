"""Disposable real MCP stdio server for integration tests only.

Run only as a child of the test suite. Stdout is reserved for the MCP protocol.
This fixture is not a sandbox and must not be exposed to untrusted callers.
"""

from pathlib import Path

from mcp.server.mcpserver import MCPServer

server = MCPServer("guillotine-test-stdio")


@server.tool()
def write_marker(path: str, content: str) -> str:
    """Write a test marker to the supplied path."""
    Path(path).write_text(content, encoding="utf-8")
    return "marker written"


@server.tool()
def ignored_tool() -> str:
    """A tool that should never be registered by the Guillotine test."""
    return "should stay unavailable"


if __name__ == "__main__":
    server.run(transport="stdio")
