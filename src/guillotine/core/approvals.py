"""One-use human approvals bound to an exact tool invocation.

This module does not execute tools or bypass current permission policies.
The future executor MUST re-evaluate the current policy and verify the
registered tool and canonical resource before consuming an approval ticket.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from guillotine.core.permissions import PermissionDecision, PermissionResult

type JsonValue = (
    str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
)
type ApprovalPrompt = Callable[[ApprovalRequest], Awaitable[ApprovalChoice]]


class ApprovalChoice(StrEnum):
    APPROVE_ONCE = "approve_once"
    DENY = "deny"


def _serialize_call(
    permission: PermissionResult, arguments: Mapping[str, JsonValue]
) -> str:
    """Snapshot a JSON-compatible call; reject invalid or non-finite values."""
    return json.dumps(
        {
            "tool_id": permission.tool_id,
            "resource_id": permission.resource_id,
            "arguments": arguments,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """Immutable request snapshot for a user-visible approval prompt."""

    tool_id: str
    resource_id: str | None
    arguments_json: str
    fingerprint: str

    @property
    def arguments(self) -> dict[str, JsonValue]:
        """Return a fresh copy, not a mutable view of the snapshot."""
        value = cast("dict[str, JsonValue]", json.loads(self.arguments_json))
        return value


@dataclass(frozen=True, slots=True)
class ApprovalTicket:
    """Ephemeral opaque approval; not a persisted policy or reusable grant."""

    token: str
    fingerprint: str


class ApprovalManager:
    """Ask for an explicit approval, issue tickets and consume them once.

    The prompt must be a trusted UI callback, not an LLM tool response.
    Tickets live only in this manager's process memory.
    """

    def __init__(self, prompt: ApprovalPrompt) -> None:
        self._prompt = prompt
        self._issued: dict[str, str] = {}

    async def request(
        self,
        permission: PermissionResult,
        *,
        arguments: Mapping[str, JsonValue],
    ) -> ApprovalTicket | None:
        """Ask only when policy requires it; deny on refusal or missing UI."""
        if permission.decision is not PermissionDecision.REQUIRE_APPROVAL:
            raise ValueError("Only REQUIRE_APPROVAL decisions can be approved")
        snapshot = _serialize_call(permission, arguments)
        parsed = cast("dict[str, JsonValue]", json.loads(snapshot))
        args = parsed["arguments"]
        if not isinstance(args, dict):
            raise ValueError("Tool arguments must be a JSON object")
        arguments_json = json.dumps(
            args, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        fingerprint = hashlib.sha256(snapshot.encode("utf-8")).hexdigest()
        request = ApprovalRequest(
            permission.tool_id, permission.resource_id, arguments_json, fingerprint
        )
        try:
            decision = await self._prompt(request)
        except (EOFError, KeyboardInterrupt):
            return None
        if decision is not ApprovalChoice.APPROVE_ONCE:
            return None
        token = secrets.token_hex(32)
        self._issued[token] = fingerprint
        return ApprovalTicket(token, fingerprint)

    def consume(
        self,
        ticket: ApprovalTicket,
        permission: PermissionResult,
        *,
        arguments: Mapping[str, JsonValue],
    ) -> bool:
        """Atomically burn a ticket; never authorize a different call.

        This is NOT a replacement for rechecking the current policy.
        """
        expected = self._issued.pop(ticket.token, None)
        if (
            expected is None
            or permission.decision is not PermissionDecision.REQUIRE_APPROVAL
        ):
            return False
        actual = hashlib.sha256(
            _serialize_call(permission, arguments).encode("utf-8")
        ).hexdigest()
        return secrets.compare_digest(expected, actual) and secrets.compare_digest(
            expected, ticket.fingerprint
        )

    def revoke(self, ticket: ApprovalTicket) -> None:
        """Discard an unconsumed approval."""
        self._issued.pop(ticket.token, None)
