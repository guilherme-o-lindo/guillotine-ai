"""MCP CLI commands modify only tool selection, never the permission database."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from guillotine.core import mcp_configuration
from guillotine.interfaces.mcp_commands import run_mcp_command


def test_configure_stdio_without_starting_server(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    file = tmp_path / "mcp.json"
    monkeypatch.setattr(mcp_configuration, "config_path", lambda: file)
    # mcp_commands uses imported function, so patch its binding too.
    from guillotine.interfaces import mcp_commands

    monkeypatch.setattr(mcp_commands, "config_path", lambda: file)
    run_mcp_command(["init"])
    run_mcp_command(["add-stdio", "fixture", "python", "--arg", "server.py"])
    pending = mcp_configuration.read_config(file)
    assert pending.servers[0].tools == ()
    run_mcp_command(
        [
            "select",
            "fixture",
            "write_marker",
            "--effect",
            "write",
            "--file-argument",
            "path",
            "--root",
            str(tmp_path),
        ]
    )
    chosen = mcp_configuration.read_config(file)
    assert chosen.servers[0].tools[0].name == "write_marker"
    assert chosen.servers[0].args == ("server.py",)


def test_init_does_not_overwrite_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from guillotine.interfaces import mcp_commands

    monkeypatch.setattr(mcp_commands, "config_path", lambda: tmp_path / "mcp.json")
    run_mcp_command(["init"])
    with pytest.raises(SystemExit):
        run_mcp_command(["init"])


def test_select_query_and_repository_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from guillotine.interfaces import mcp_commands

    file = tmp_path / "mcp.json"
    monkeypatch.setattr(mcp_commands, "config_path", lambda: file)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    run_mcp_command(["init"])
    run_mcp_command(["add-stdio", "search", "python"])
    run_mcp_command(["add-stdio", "git", "python"])
    run_mcp_command(
        [
            "select",
            "search",
            "search",
            "--effect",
            "network",
            "--query-argument",
            "query",
        ]
    )
    run_mcp_command(
        [
            "select",
            "git",
            "git_status",
            "--effect",
            "read",
            "--repo-argument",
            "repo_path",
            "--repo-root",
            str(repo),
        ]
    )
    config = mcp_commands.read_config(file)
    assert config.servers[0].tools[0].resource.kind == "query"
    assert config.servers[1].tools[0].resource.kind == "repository"


def test_mixed_scopes_are_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from guillotine.interfaces import mcp_commands

    monkeypatch.setattr(mcp_commands, "config_path", lambda: tmp_path / "mcp.json")
    run_mcp_command(["init"])
    run_mcp_command(["add-stdio", "search", "python"])
    with pytest.raises(SystemExit):
        run_mcp_command(
            [
                "select",
                "search",
                "search",
                "--effect",
                "network",
                "--query-argument",
                "query",
                "--no-resource",
            ]
        )


@pytest.mark.asyncio
async def test_inspect_only_discovers_without_registering(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from guillotine.interfaces import mcp_commands

    path = tmp_path / "mcp.json"
    monkeypatch.setattr(mcp_commands, "config_path", lambda: path)
    run_mcp_command(["init"])
    run_mcp_command(["add-stdio", "test", "python"])

    class FakeClient:
        async def connect(self) -> None:
            events.append("connect")

        async def list_tools(self) -> tuple[object, ...]:
            return (SimpleNamespace(name="beta"), SimpleNamespace(name="alpha"))

        async def close(self) -> None:
            events.append("close")

    events: list[str] = []
    # Exercise the async helper directly. No actual server process is spawned.
    from guillotine.core.mcp_configuration import ServerSpec

    def fake_client_for_server(_server: ServerSpec) -> FakeClient:
        return FakeClient()

    monkeypatch.setattr(mcp_commands, "client_for_server", fake_client_for_server)
    names = await mcp_commands.inspect_server(
        ServerSpec(id="test", transport="stdio", command="python")
    )
    assert names == ("alpha", "beta")
    assert events == ["connect", "close"]


def test_inspect_command_prints_sdk_tool_names(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from guillotine.interfaces import mcp_commands

    monkeypatch.setattr(mcp_commands, "config_path", lambda: tmp_path / "mcp.json")
    run_mcp_command(["init"])
    run_mcp_command(["add-stdio", "test", "python"])

    async def fake_inspect(_server: object) -> tuple[str, ...]:
        return ("inspect", "search")

    monkeypatch.setattr(mcp_commands, "inspect_server", fake_inspect)
    run_mcp_command(["inspect", "test"])
    output = capsys.readouterr().out
    assert "inspect" in output
    assert "search" in output
    assert "[selected]" not in output


def test_inspect_unknown_server_exits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from guillotine.interfaces import mcp_commands

    monkeypatch.setattr(mcp_commands, "config_path", lambda: tmp_path / "mcp.json")
    run_mcp_command(["init"])
    with pytest.raises(SystemExit):
        run_mcp_command(["inspect", "missing"])
