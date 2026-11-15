from __future__ import annotations

from dataclasses import dataclass

from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionProfile,
    PermissionRule,
)
from guillotine.memory.storage.database import get_connection
from guillotine.tools.registry import ToolRegistry


@dataclass(frozen=True, slots=True)
class PermissionPolicy:
    """Immutable policy snapshot; a resource of None matches only None."""

    profile: PermissionProfile = PermissionProfile.BALANCED
    rules: tuple[PermissionRule, ...] = ()

    def manager(self, registry: ToolRegistry) -> PermissionManager:
        """Create an evaluator from a trusted snapshot, not from tool output."""
        return PermissionManager(registry, profile=self.profile, rules=self.rules)


class PermissionStore:
    """Transactional policy storage in the existing Guillotine SQLite database.

    One local policy is supported; user/workspace-specific identities are not
    introduced prematurely. The active manager must be refreshed after changes.
    """

    async def initialize(self) -> None:
        """Create tables without changing existing conversation tables."""
        async with get_connection() as database:
            await database.executescript(
                """
                CREATE TABLE IF NOT EXISTS permission_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    profile TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS permission_rules (
                    tool_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    PRIMARY KEY (tool_id, resource_id)
                );
                """
            )
            await database.commit()

    async def load(self) -> PermissionPolicy:
        """Return the stored policy, or balanced with no grants initially.

        Invalid persisted enum values fail closed: do not silently ignore a
        corrupt DENY or reinterpret invalid policy contents as authorization.
        """
        async with get_connection() as database:
            async with database.execute(
                "SELECT profile FROM permission_settings WHERE id = 1"
            ) as cursor:
                setting = await cursor.fetchone()
            async with database.execute(
                """SELECT tool_id, resource_id, decision
                   FROM permission_rules ORDER BY tool_id, resource_id"""
            ) as cursor:
                rows = await cursor.fetchall()

        if setting is None and rows:
            raise ValueError("Permission rules exist without a valid profile")

        profile = (
            PermissionProfile(str(setting["profile"]))
            if setting is not None
            else PermissionProfile.BALANCED
        )
        rules = tuple(
            PermissionRule(
                tool_id=str(row["tool_id"]),
                resource_id=(
                    str(row["resource_id"]) if row["resource_id"] != "" else None
                ),
                decision=PermissionDecision(str(row["decision"])),
            )
            for row in rows
        )
        return PermissionPolicy(profile=profile, rules=rules)

    async def replace(self, policy: PermissionPolicy) -> None:
        """Atomically replace the policy; rollback preserves the old policy.

        At most one explicit decision is persisted per exact tool/resource key.
        Duplicate keys are refused instead of relying on insertion order.
        """
        if type(policy.profile) is not PermissionProfile:
            raise ValueError("Invalid permission profile")
        seen: set[tuple[str, str | None]] = set()
        for rule in policy.rules:
            if type(rule.decision) is not PermissionDecision:
                raise ValueError("Invalid permission decision")
            key = (rule.tool_id, rule.resource_id)
            if key in seen:
                raise ValueError(f"Duplicate permission rule: {key!r}")
            seen.add(key)

        async with get_connection() as database:
            try:
                await database.execute("BEGIN IMMEDIATE")
                await database.execute("DELETE FROM permission_rules")
                await database.execute(
                    """INSERT INTO permission_settings (id, profile)
                       VALUES (1, ?)
                       ON CONFLICT(id) DO UPDATE SET profile = excluded.profile""",
                    (policy.profile.value,),
                )
                await database.executemany(
                    """INSERT INTO permission_rules
                       (tool_id, resource_id, decision) VALUES (?, ?, ?)""",
                    [
                        (rule.tool_id, rule.resource_id or "", rule.decision.value)
                        for rule in policy.rules
                    ],
                )
                await database.commit()
            except BaseException:
                await database.rollback()
                raise
