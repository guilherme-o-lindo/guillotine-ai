"""Tool execution audit trail: no arguments or resource identifiers on disk."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import aiosqlite
import pytest
from pydantic_ai.tools import Tool as PydanticTool

from guillotine.core.approvals import (
    ApprovalChoice,
    ApprovalManager,
    ApprovalRequest,
    JsonValue,
)
from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionProfile,
    PermissionRule,
)
from guillotine.core.tool_audit import AuditOutcome, ToolAuditStore
from guillotine.tools.core.contracts import ToolEffect, ToolSecurity
from guillotine.tools.core.executor import ToolExecutionDenied, ToolExecutor
from guillotine.tools.core.registry import ToolRegistry


@pytest.fixture
def audit_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ToolAuditStore:
    database_file = tmp_path / "guillotine-audit.db"

    @asynccontextmanager
    async def connection() -> AsyncGenerator[aiosqlite.Connection]:
        async with aiosqlite.connect(database_file) as database:
            database.row_factory = aiosqlite.Row
            yield database

    monkeypatch.setattr("guillotine.core.tool_audit.get_connection", connection)
    return ToolAuditStore()


async def make_executor(
    store: ToolAuditStore,
    decision: PermissionDecision,
    *,
    approvals: ApprovalManager | None = None,
) -> tuple[ToolExecutor, list[dict[str, JsonValue]]]:
    registry = ToolRegistry()
    local = cast("PydanticTool[object]", SimpleNamespace(name="write_marker"))
    registry.register_local(
        local, security=ToolSecurity(effects=frozenset({ToolEffect.WRITE}))
    )

    async def current() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(
                PermissionRule("local:write_marker", "file:/secret-location", decision),
            ),
        )

    calls: list[dict[str, JsonValue]] = []

    async def invoke(arguments: dict[str, JsonValue]) -> object:
        calls.append(arguments)
        if arguments.get("fail") is True:
            raise RuntimeError("SECRET_API_TOKEN must not reach audit")
        return "ok"

    def resource(_args: Mapping[str, JsonValue]) -> str:
        return "file:/secret-location"

    executor = ToolExecutor(registry, current, approvals=approvals, audit=store.record)
    executor.bind("local:write_marker", invoke=invoke, resource=resource)
    return executor, calls


async def read_events() -> list[tuple[str, str]]:
    from guillotine.core import tool_audit  # noqa: PLC0415

    async with (
        tool_audit.get_connection() as connection,
        connection.execute(
            "SELECT decision, outcome FROM tool_audit_events ORDER BY id"
        ) as cursor,
    ):
        rows = await cursor.fetchall()
    return [(str(row[0]), str(row[1])) for row in rows]


@pytest.mark.asyncio
async def test_success_is_audited_without_arguments(
    audit_store: ToolAuditStore,
) -> None:
    await audit_store.initialize()
    executor, calls = await make_executor(audit_store, PermissionDecision.ALLOW)
    await executor.execute(
        "local:write_marker", arguments={"token": "SECRET_API_TOKEN"}
    )
    assert len(calls) == 1
    assert await read_events() == [
        ("allow", AuditOutcome.AUTHORIZED.value),
        ("allow", AuditOutcome.SUCCEEDED.value),
    ]
    from guillotine.core import tool_audit  # noqa: PLC0415

    async with (
        tool_audit.get_connection() as connection,
        connection.execute("SELECT * FROM tool_audit_events") as cursor,
    ):
        row = await cursor.fetchone()
        assert row is not None
        assert set(row.keys()) == {
            "id",
            "occurred_at",
            "tool_id",
            "decision",
            "outcome",
        }
        assert "SECRET_API_TOKEN" not in str(tuple(row))
        assert "secret-location" not in str(tuple(row))


@pytest.mark.asyncio
async def test_denial_is_recorded_and_not_executed(
    audit_store: ToolAuditStore,
) -> None:
    await audit_store.initialize()
    executor, calls = await make_executor(audit_store, PermissionDecision.DENY)
    with pytest.raises(ToolExecutionDenied):
        await executor.execute("local:write_marker", arguments={"token": "secret"})
    assert calls == []
    assert await read_events() == [("deny", "blocked")]


@pytest.mark.asyncio
async def test_native_failure_is_audited_without_exception_details(
    audit_store: ToolAuditStore,
) -> None:
    await audit_store.initialize()
    executor, calls = await make_executor(audit_store, PermissionDecision.ALLOW)
    with pytest.raises(RuntimeError, match="SECRET_API_TOKEN"):
        await executor.execute("local:write_marker", arguments={"fail": True})
    assert len(calls) == 1
    assert await read_events() == [
        ("allow", "authorized"),
        ("allow", "failed"),
    ]


@pytest.mark.asyncio
async def test_broken_audit_fails_closed() -> None:
    registry = ToolRegistry()
    local = cast("PydanticTool[object]", SimpleNamespace(name="write_marker"))
    registry.register_local(
        local, security=ToolSecurity(effects=frozenset({ToolEffect.WRITE}))
    )

    async def current() -> PermissionManager:
        return PermissionManager(
            registry,
            profile=PermissionProfile.CUSTOM,
            rules=(
                PermissionRule("local:write_marker", None, PermissionDecision.ALLOW),
            ),
        )

    async def broken(_tool_id: str, _decision: object, _outcome: object) -> None:
        raise OSError("Audit storage unavailable")

    called = False

    async def invoke(_arguments: dict[str, JsonValue]) -> object:
        nonlocal called
        called = True
        return "ok"

    executor = ToolExecutor(registry, current, audit=broken)
    executor.bind("local:write_marker", invoke=invoke, resource=lambda _: None)
    with pytest.raises(OSError, match="Audit storage unavailable"):
        await executor.execute("local:write_marker", arguments={})
    assert not called


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("choice", "expected_outcomes"),
    [
        (ApprovalChoice.APPROVE_ONCE, ["authorized", "succeeded"]),
        (ApprovalChoice.DENY, ["blocked"]),
    ],
)
async def test_approval_decisions_are_audited(
    audit_store: ToolAuditStore,
    choice: ApprovalChoice,
    expected_outcomes: list[str],
) -> None:
    await audit_store.initialize()

    async def prompt(_request: ApprovalRequest) -> ApprovalChoice:
        return choice

    exe, calls = await make_executor(
        audit_store,
        PermissionDecision.REQUIRE_APPROVAL,
        approvals=ApprovalManager(prompt),
    )
    if choice is ApprovalChoice.DENY:
        with pytest.raises(ToolExecutionDenied):
            await exe.execute("local:write_marker", arguments={})
        assert calls == []
    else:
        await exe.execute("local:write_marker", arguments={})
        assert len(calls) == 1
    assert await read_events() == [
        ("require_approval", outcome) for outcome in expected_outcomes
    ]
