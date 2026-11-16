"""Minimal, append-only audit trail for tool authorization and execution.

No arguments, resource identifiers, remote responses, or exception messages are
persisted: they can contain credentials or personal information.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import StrEnum

from guillotine.core.permissions import PermissionDecision
from guillotine.memory.storage.database import get_connection


class AuditOutcome(StrEnum):
    BLOCKED = "blocked"
    AUTHORIZED = "authorized"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


# Injected callback for the executor; no transport/storage dependencies there.
type ToolAuditWriter = Callable[
    [str, PermissionDecision | None, AuditOutcome], Awaitable[None]
]


class ToolAuditStore:
    """Store minimum necessary facts using the existing SQLite connection."""

    async def initialize(self) -> None:
        async with get_connection() as database:
            await database.execute(
                """CREATE TABLE IF NOT EXISTS tool_audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    tool_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    outcome TEXT NOT NULL
                )"""
            )
            await database.commit()

    async def record(
        self, tool_id: str, decision: PermissionDecision | None, outcome: AuditOutcome
    ) -> None:
        """Record one event. Database failures propagate; never bypass auditing."""
        async with get_connection() as database:
            await database.execute(
                """INSERT INTO tool_audit_events (tool_id, decision, outcome)
                   VALUES (?, ?, ?)""",
                (
                    tool_id,
                    decision.value if decision is not None else "undetermined",
                    outcome.value,
                ),
            )
            await database.commit()
