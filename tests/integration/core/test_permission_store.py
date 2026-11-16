from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite
import pytest

from guillotine.core.permission_store import PermissionPolicy, PermissionStore
from guillotine.core.permissions import (
    PermissionDecision,
    PermissionProfile,
    PermissionRule,
)


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PermissionStore:
    database_file = tmp_path / "permissions.db"

    @asynccontextmanager
    async def isolated_connection() -> AsyncGenerator[aiosqlite.Connection]:
        async with aiosqlite.connect(database_file) as connection:
            connection.row_factory = aiosqlite.Row
            yield connection

    monkeypatch.setattr(
        "guillotine.core.permission_store.get_connection", isolated_connection
    )
    return PermissionStore()


@pytest.mark.asyncio
async def test_fresh_database_defaults_to_no_grants(store: PermissionStore) -> None:
    await store.initialize()
    assert await store.load() == PermissionPolicy()


@pytest.mark.asyncio
async def test_round_trip_exact_scopes_and_profile(store: PermissionStore) -> None:
    await store.initialize()
    policy = PermissionPolicy(
        profile=PermissionProfile.CUSTOM,
        rules=(
            PermissionRule("local:read", None, PermissionDecision.DENY),
            PermissionRule(
                "mcp:files:read", "file:/report.txt", PermissionDecision.ALLOW
            ),
            PermissionRule(
                "mcp:files:read", "file:/private.txt", PermissionDecision.DENY
            ),
        ),
    )
    await store.replace(policy)
    loaded = await store.load()
    assert loaded.profile is policy.profile
    assert set(loaded.rules) == set(policy.rules)

    reloaded = await PermissionStore().load()
    assert reloaded == loaded


@pytest.mark.asyncio
async def test_replacing_policy_removes_previous_grants(store: PermissionStore) -> None:
    await store.initialize()
    await store.replace(
        PermissionPolicy(
            rules=(PermissionRule("local:read", None, PermissionDecision.ALLOW),)
        )
    )
    await store.replace(PermissionPolicy(profile=PermissionProfile.RESTRICTED))
    assert await store.load() == PermissionPolicy(profile=PermissionProfile.RESTRICTED)


@pytest.mark.asyncio
async def test_duplicate_keys_rejected_without_mutation(store: PermissionStore) -> None:
    await store.initialize()
    existing = PermissionPolicy(
        rules=(PermissionRule("local:read", None, PermissionDecision.DENY),)
    )
    await store.replace(existing)
    with pytest.raises(ValueError, match="Duplicate"):
        await store.replace(
            PermissionPolicy(
                rules=(
                    PermissionRule("local:read", None, PermissionDecision.ALLOW),
                    PermissionRule("local:read", None, PermissionDecision.DENY),
                )
            )
        )
    assert await store.load() == existing


@pytest.mark.asyncio
async def test_initialize_is_idempotent(store: PermissionStore) -> None:
    await store.initialize()
    policy = PermissionPolicy(profile=PermissionProfile.SUPERVISED)
    await store.replace(policy)
    await store.initialize()
    assert await store.load() == policy


@pytest.mark.asyncio
async def test_invalid_stored_decision_does_not_silently_allow(
    store: PermissionStore,
) -> None:
    await store.initialize()
    # Directly simulate an invalid on-disk value to verify fail-closed loading.
    from guillotine.core import permission_store  # noqa: PLC0415

    async with permission_store.get_connection() as database:
        await database.execute(
            """INSERT INTO permission_rules (tool_id, resource_id, decision)
               VALUES (?, ?, ?)""",
            ("local:x", "", "invalid"),
        )
        await database.commit()
    with pytest.raises(ValueError):
        await store.load()
