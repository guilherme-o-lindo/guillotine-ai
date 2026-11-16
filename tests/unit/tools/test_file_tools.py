"""Local file tools are opt-in and use the same permission/audit boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionProfile,
    PermissionRule,
)
from guillotine.tools.core.contracts import ToolEffect
from guillotine.tools.core.executor import ToolExecutionDenied, ToolExecutor
from guillotine.tools.core.registry import ToolRegistry
from guillotine.tools.local.file_tools import (
    LIST_ID,
    READ_ID,
    SEARCH_ID,
    register_file_tools,
)


@pytest.mark.asyncio
async def test_registration_read_only_and_denied_by_default(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("bonjour", encoding="utf-8")
    registry = ToolRegistry()

    async def current() -> PermissionManager:
        return PermissionManager(registry, profile=PermissionProfile.CUSTOM, rules=())

    executor = ToolExecutor(registry, current)
    assert register_file_tools(registry, executor, root=tmp_path) == (
        LIST_ID,
        READ_ID,
        SEARCH_ID,
    )
    for entry in registry.list_tools():
        assert entry.security.effects == frozenset({ToolEffect.READ})
    with pytest.raises(ToolExecutionDenied):
        await executor.execute(READ_ID, arguments={"path": "note.txt"})


@pytest.mark.asyncio
async def test_explicit_permission_allows_only_matching_file(tmp_path: Path) -> None:
    (tmp_path / "allowed.txt").write_text("bonjour", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")
    registry = ToolRegistry()
    resource = (tmp_path / "allowed.txt").resolve().as_uri()

    async def current() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(PermissionRule(READ_ID, resource, PermissionDecision.ALLOW),),
        )

    executor = ToolExecutor(registry, current)
    register_file_tools(registry, executor, root=tmp_path)
    assert await executor.execute(READ_ID, arguments={"path": "allowed.txt"}) == {
        "path": "allowed.txt",
        "content": "bonjour",
        "truncated": False,
    }
    with pytest.raises(ToolExecutionDenied):
        await executor.execute(READ_ID, arguments={"path": "secret.txt"})


@pytest.mark.asyncio
async def test_list_and_search_via_executor(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("bonjour\nhello", encoding="utf-8")
    registry = ToolRegistry()
    resource = tmp_path.resolve().as_uri()

    async def current() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(
                PermissionRule(LIST_ID, resource, PermissionDecision.ALLOW),
                PermissionRule(SEARCH_ID, resource, PermissionDecision.ALLOW),
            ),
        )

    executor = ToolExecutor(registry, current)
    register_file_tools(registry, executor, root=tmp_path)
    listing = await executor.execute(LIST_ID, arguments={"path": "."})
    assert isinstance(listing, dict)
    assert listing["entries"] == [{"name": "note.txt", "type": "file"}]
    results = await executor.execute(
        SEARCH_ID, arguments={"query": "bonjour", "path": "."}
    )
    assert isinstance(results, dict)
    assert results["matches"] == [{"path": "note.txt", "line": 1, "text": "bonjour"}]


@pytest.mark.asyncio
async def test_escape_and_unknown_arguments_never_dispatch(tmp_path: Path) -> None:
    registry = ToolRegistry()

    async def current() -> PermissionManager:
        return PermissionManager(registry, profile=PermissionProfile.CUSTOM, rules=())

    executor = ToolExecutor(registry, current)
    register_file_tools(registry, executor, root=tmp_path)
    for path in ("../secret", "/etc/passwd", "C:/Windows"):
        with pytest.raises(PermissionError):
            await executor.execute(READ_ID, arguments={"path": path})
    with pytest.raises(ValueError):
        await executor.execute(LIST_ID, arguments={"path": ".", "extra": True})


def test_requires_existing_authorized_root(tmp_path: Path) -> None:
    registry = ToolRegistry()

    async def current() -> PermissionManager:
        return PermissionManager(registry, profile=PermissionProfile.CUSTOM, rules=())

    executor = ToolExecutor(registry, current)
    with pytest.raises(ValueError, match="Authorized root"):
        register_file_tools(registry, executor, root=tmp_path / "missing")
    assert registry.list_tools() == ()
