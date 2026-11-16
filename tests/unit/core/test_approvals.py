"""Approval decisions cannot be confused with durable policy grants."""

from collections.abc import Awaitable, Callable

import pytest

from guillotine.core.approvals import (
    ApprovalChoice,
    ApprovalManager,
    ApprovalRequest,
    JsonValue,
)
from guillotine.core.permissions import PermissionDecision, PermissionResult


def decision(
    outcome: PermissionDecision = PermissionDecision.REQUIRE_APPROVAL,
    *,
    resource: str | None = "file:/safe.txt",
) -> PermissionResult:
    return PermissionResult(outcome, "test", "local:write", resource)


def responder(
    choice: ApprovalChoice, calls: list[ApprovalRequest]
) -> Callable[[ApprovalRequest], Awaitable[ApprovalChoice]]:
    async def prompt(request: ApprovalRequest) -> ApprovalChoice:
        calls.append(request)
        return choice

    return prompt


@pytest.mark.asyncio
async def test_approve_once_bound_to_exact_call() -> None:
    calls: list[ApprovalRequest] = []
    manager = ApprovalManager(responder(ApprovalChoice.APPROVE_ONCE, calls))
    arguments: dict[str, JsonValue] = {"path": "safe.txt", "lines": [1, 2]}
    ticket = await manager.request(decision(), arguments=arguments)
    assert ticket is not None
    assert len(calls) == 1
    assert calls[0].tool_id == "local:write"
    assert calls[0].arguments == arguments
    assert manager.consume(ticket, decision(), arguments=arguments)
    assert not manager.consume(ticket, decision(), arguments=arguments)


@pytest.mark.asyncio
async def test_denial_never_issues_ticket() -> None:
    manager = ApprovalManager(responder(ApprovalChoice.DENY, []))
    assert await manager.request(decision(), arguments={}) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", [PermissionDecision.ALLOW, PermissionDecision.DENY])
async def test_nonapproval_policy_cannot_be_approved(
    outcome: PermissionDecision,
) -> None:
    calls: list[ApprovalRequest] = []
    manager = ApprovalManager(responder(ApprovalChoice.APPROVE_ONCE, calls))
    with pytest.raises(ValueError):
        await manager.request(decision(outcome), arguments={})
    assert not calls


@pytest.mark.asyncio
async def test_changed_arguments_burns_ticket() -> None:
    manager = ApprovalManager(responder(ApprovalChoice.APPROVE_ONCE, []))
    ticket = await manager.request(decision(), arguments={"path": "safe.txt"})
    assert ticket is not None
    assert not manager.consume(ticket, decision(), arguments={"path": "secret.txt"})
    assert not manager.consume(ticket, decision(), arguments={"path": "safe.txt"})


@pytest.mark.asyncio
async def test_changed_resource_is_rejected() -> None:
    manager = ApprovalManager(responder(ApprovalChoice.APPROVE_ONCE, []))
    ticket = await manager.request(decision(), arguments={})
    assert ticket is not None
    assert not manager.consume(
        ticket, decision(resource="file:/different"), arguments={}
    )


@pytest.mark.asyncio
async def test_changed_tool_is_rejected() -> None:
    manager = ApprovalManager(responder(ApprovalChoice.APPROVE_ONCE, []))
    ticket = await manager.request(decision(), arguments={})
    assert ticket is not None
    different = PermissionResult(
        PermissionDecision.REQUIRE_APPROVAL, "test", "local:delete", "file:/safe.txt"
    )
    assert not manager.consume(ticket, different, arguments={})


@pytest.mark.asyncio
async def test_revoke_disables_ticket() -> None:
    manager = ApprovalManager(responder(ApprovalChoice.APPROVE_ONCE, []))
    ticket = await manager.request(decision(), arguments={})
    assert ticket is not None
    manager.revoke(ticket)
    assert not manager.consume(ticket, decision(), arguments={})


@pytest.mark.asyncio
async def test_argument_snapshot_cannot_be_mutated_by_prompt() -> None:
    async def mutate(request: ApprovalRequest) -> ApprovalChoice:
        request.arguments["path"] = "secret.txt"
        return ApprovalChoice.APPROVE_ONCE

    manager = ApprovalManager(mutate)
    args = {"path": "safe.txt"}
    ticket = await manager.request(decision(), arguments=args)
    assert ticket is not None
    assert manager.consume(ticket, decision(), arguments=args)


@pytest.mark.asyncio
async def test_unknown_prompt_value_fails_closed() -> None:
    async def unknown(_request: ApprovalRequest) -> ApprovalChoice:
        return "yes"  # type: ignore[return-value]

    manager = ApprovalManager(unknown)
    assert await manager.request(decision(), arguments={}) is None


@pytest.mark.asyncio
async def test_invalid_non_json_arguments_rejected() -> None:
    manager = ApprovalManager(responder(ApprovalChoice.APPROVE_ONCE, []))
    with pytest.raises((TypeError, ValueError)):
        await manager.request(decision(), arguments={"value": float("nan")})


@pytest.mark.asyncio
async def test_missing_ui_does_not_approve() -> None:
    async def eof(_request: ApprovalRequest) -> ApprovalChoice:
        raise EOFError

    manager = ApprovalManager(eof)
    assert await manager.request(decision(), arguments={}) is None
