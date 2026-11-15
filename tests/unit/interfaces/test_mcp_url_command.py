"""The CLI may select URL scopes but never grants permissions by selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from guillotine.interfaces import mcp_commands


def test_select_url_resource_roundtrips(
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
            "fetch_content",
            "--effect",
            "network",
            "--url-argument",
            "url",
        ]
    )
    selected = mcp_commands.read_config(path).servers[0].tools[0]
    assert selected.resource.kind == "url"
    assert selected.resource.argument == "url"


def test_url_and_reference_scopes_are_mutually_exclusive(
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
                "fetch_content",
                "--effect",
                "network",
                "--url-argument",
                "url",
                "--ref-argument",
                "url",
            ]
        )
