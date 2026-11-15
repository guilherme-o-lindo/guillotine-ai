"""CLI selection must keep URL expansion tokens scoped and unapproved."""

from __future__ import annotations

from pathlib import Path

import pytest

from guillotine.interfaces import mcp_commands


def test_select_expand_link_ref_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "mcp.json"
    monkeypatch.setattr(mcp_commands, "config_path", lambda: path)
    mcp_commands.run_mcp_command(["init"])
    mcp_commands.run_mcp_command(["add-stdio", "duckduckgo", "uvx"])
    mcp_commands.run_mcp_command(
        [
            "select",
            "duckduckgo",
            "expand_link",
            "--effect",
            "read",
            "--ref-argument",
            "token",
        ]
    )
    config = mcp_commands.read_config(path)
    scope = config.servers[0].tools[0].resource
    assert scope.kind == "reference_token"
    assert scope.argument == "token"


def test_ref_scope_cannot_be_mixed_with_query_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "mcp.json"
    monkeypatch.setattr(mcp_commands, "config_path", lambda: path)
    mcp_commands.run_mcp_command(["init"])
    mcp_commands.run_mcp_command(["add-stdio", "duckduckgo", "uvx"])
    with pytest.raises(SystemExit):
        mcp_commands.run_mcp_command(
            [
                "select",
                "duckduckgo",
                "expand_link",
                "--effect",
                "read",
                "--ref-argument",
                "token",
                "--query-argument",
                "query",
            ]
        )
