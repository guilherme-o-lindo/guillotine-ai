"""Configuration selection must never silently authorize tool operations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from guillotine.core.mcp_configuration import (
    FileResource,
    MCPConfiguration,
    NoResource,
    QueryResource,
    RepositoryResource,
    SelectedTool,
    ServerSpec,
    read_config,
    resource_resolver,
    write_config,
)
from guillotine.tools.core.contracts import ToolEffect


def tool(root: Path) -> SelectedTool:
    return SelectedTool(
        name="write_marker",
        effects=(ToolEffect.WRITE,),
        resource=FileResource(kind="file", argument="path", root=root),
    )


def test_round_trip_and_empty_server_remains_inactive(tmp_path: Path) -> None:
    file = tmp_path / "mcp.json"
    config = MCPConfiguration(
        servers=(ServerSpec(id="fixture", transport="stdio", command="python"),)
    )
    write_config(file, config)
    assert read_config(file) == config
    assert file.is_file()


def test_selected_tools_are_explicit(tmp_path: Path) -> None:
    config = MCPConfiguration(
        servers=(
            ServerSpec(
                id="fixture",
                transport="stdio",
                command="python",
                tools=(tool(tmp_path),),
            ),
        )
    )
    file = tmp_path / "mcp.json"
    write_config(file, config)
    restored = read_config(file)
    assert restored.servers[0].tools[0].effects == (ToolEffect.WRITE,)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "version": 1,
            "servers": [
                {
                    "id": "a",
                    "transport": "stdio",
                    "command": "x",
                    "tools": [
                        {
                            "name": "go",
                            "effects": ["unknown"],
                            "resource": {"kind": "none"},
                        },
                    ],
                },
            ],
        },
        {
            "version": 1,
            "servers": [
                {
                    "id": "a",
                    "transport": "streamable-http",
                    "url": "http://example.org/mcp",
                },
            ],
        },
        {
            "version": 1,
            "servers": [
                {"id": "a", "transport": "stdio", "command": "x"},
                {"id": "a", "transport": "stdio", "command": "y"},
            ],
        },
        {"version": 1, "servers": [], "unexpected": "forbidden"},
    ],
)
def test_invalid_or_unsafe_config_fails_closed(payload: object) -> None:
    with pytest.raises(ValidationError):
        MCPConfiguration.model_validate_json(json.dumps(payload))


def test_file_scope_confines_absolute_path_and_symlink(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    root.mkdir()
    resolver = resource_resolver(FileResource(kind="file", argument="path", root=root))
    target = root / "marker.txt"
    assert resolver({"path": str(target)}) == target.resolve().as_uri()
    with pytest.raises(PermissionError):
        resolver({"path": "marker.txt"})
    with pytest.raises(PermissionError):
        resolver({"path": str(tmp_path / "outside.txt")})
    with pytest.raises(ValueError):
        resolver({"wrong_field": str(target)})
    symlink = root / "escape.txt"
    try:
        symlink.symlink_to(tmp_path / "outside.txt")
    except (OSError, NotImplementedError):
        return  # Windows environments may deny symlink creation
    with pytest.raises(PermissionError):
        resolver({"path": str(symlink)})


def test_no_resource_is_not_a_wildcard_grant() -> None:
    resolver = resource_resolver(NoResource(kind="none"))
    assert resolver({"anything": "anything"}) is None


def test_query_scope_uses_private_stable_digest() -> None:
    resolver = resource_resolver(QueryResource(kind="query", argument="query"))
    first = resolver({"query": "private search terms"})
    assert first is not None and first.startswith("query:sha256:")
    assert "private search terms" not in first
    assert first == resolver({"query": "private search terms"})
    assert first != resolver({"query": "different terms"})
    with pytest.raises(ValueError):
        resolver({"query": ""})
    with pytest.raises(ValueError):
        resolver({"wrong": "x"})
    with pytest.raises(ValueError):
        resolver({"query": "x" * 4097})


def test_repository_scope_binds_exact_root(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    other = tmp_path / "other"
    other.mkdir()
    resolver = resource_resolver(
        RepositoryResource(kind="repository", argument="repo_path", root=repo)
    )
    assert resolver({"repo_path": str(repo)}) == repo.resolve().as_uri()
    with pytest.raises(PermissionError):
        resolver({"repo_path": str(other)})
    with pytest.raises(PermissionError):
        resolver({"repo_path": "."})
    with pytest.raises(ValueError):
        resolver({"wrong": str(repo)})


def test_invalid_repository_configuration_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        RepositoryResource(kind="repository", argument="repo_path", root=tmp_path)


def test_query_and_repository_config_json_round_trip(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    config = MCPConfiguration(
        servers=(
            ServerSpec(
                id="search",
                transport="stdio",
                command="python",
                tools=(
                    SelectedTool(
                        name="search",
                        effects=(ToolEffect.NETWORK,),
                        resource=QueryResource(kind="query", argument="query"),
                    ),
                ),
            ),
            ServerSpec(
                id="git",
                transport="stdio",
                command="python",
                tools=(
                    SelectedTool(
                        name="git_status",
                        effects=(ToolEffect.READ,),
                        resource=RepositoryResource(
                            kind="repository", argument="repo_path", root=repo
                        ),
                    ),
                ),
            ),
        ),
    )
    path = tmp_path / "mcp.json"
    write_config(path, config)
    assert read_config(path) == config


def test_query_scope_cannot_be_used_for_writing() -> None:
    with pytest.raises(ValidationError):
        SelectedTool(
            name="dangerous",
            effects=(ToolEffect.WRITE,),
            resource=QueryResource(kind="query", argument="query"),
        )


def test_repository_scope_cannot_be_used_for_git_mutations(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    with pytest.raises(ValidationError):
        SelectedTool(
            name="git_commit",
            effects=(ToolEffect.WRITE,),
            resource=RepositoryResource(
                kind="repository", argument="repo_path", root=repo
            ),
        )
