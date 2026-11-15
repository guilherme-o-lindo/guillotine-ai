"""Native MCP schema discovery does not register or authorize tools."""

from pathlib import Path

import pytest
from mcp.types import Tool as MCPTool

from guillotine.interfaces import mcp_commands
from guillotine.interfaces.mcp_commands import run_mcp_command


def test_inspect_details_shows_native_schema(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(mcp_commands, "config_path", lambda: tmp_path / "mcp.json")
    run_mcp_command(["init"])
    run_mcp_command(["add-stdio", "duckduckgo", "python"])

    async def fake_details(_server: object) -> tuple[MCPTool, ...]:
        return (
            MCPTool(
                name="search",
                description="Search the web",
                input_schema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            ),
        )

    monkeypatch.setattr(mcp_commands, "inspect_server_details", fake_details)
    capsys.readouterr()
    run_mcp_command(["inspect", "duckduckgo", "--details"])
    output = capsys.readouterr().out
    assert '"search"' in output
    assert "Search the web" in output
    assert '"query"' in output
    assert '"required"' in output
    assert "[selected]" not in output


def test_inspect_details_preserves_tool_selection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(mcp_commands, "config_path", lambda: tmp_path / "mcp.json")
    run_mcp_command(["init"])
    run_mcp_command(["add-stdio", "duckduckgo", "python"])
    run_mcp_command(
        [
            "select",
            "duckduckgo",
            "search",
            "--effect",
            "network",
            "--query-argument",
            "query",
        ]
    )

    async def fake_details(_server: object) -> tuple[MCPTool, ...]:
        return (MCPTool(name="search", input_schema={"type": "object"}),)

    monkeypatch.setattr(mcp_commands, "inspect_server_details", fake_details)
    capsys.readouterr()
    run_mcp_command(["inspect", "duckduckgo", "--details"])
    assert '"search" [selected]' in capsys.readouterr().out
