"""Disposable stdio MCP search fixture; never accesses the public internet."""

from mcp.server.mcpserver import MCPServer

server = MCPServer("guillotine-web-search-test")


@server.tool()
def search(query: str) -> str:
    """Return a deterministic search hit for the end-to-end test."""
    if query != "documentação MCP":
        return "No matching results"
    return "MCP test docs | https://example.org/docs/mcp | Sample documentation"


if __name__ == "__main__":
    server.run(transport="stdio")
