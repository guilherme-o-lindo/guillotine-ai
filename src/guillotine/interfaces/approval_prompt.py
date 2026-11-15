"""Terminal approval UI for Guillotine tool requests.

Keep this separate from conversation commands until the tool executor exists.
"""

from __future__ import annotations

import asyncio
import json

from guillotine.core.approvals import ApprovalChoice, ApprovalRequest, JsonValue

_SECRET_WORDS = (
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "credential",
)


def _redact(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return {
            key: (
                "[REDACTED]"
                if any(word in key.lower() for word in _SECRET_WORDS)
                else _redact(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


async def terminal_approval_prompt(request: ApprovalRequest) -> ApprovalChoice:
    """Present an explicit, one-time yes/no decision (default: deny)."""
    print("\nGuillotine solicita aprovação para uma ferramenta:")
    print(f"  Ferramenta: {request.tool_id}")
    print(f"  Recurso: {request.resource_id or '(não identificado)'}")
    print("  Argumentos (campos sensíveis ocultados):")
    print(json.dumps(_redact(request.arguments), ensure_ascii=False, indent=2))
    print(f"  Identificador da chamada: {request.fingerprint[:16]}")
    print("  Aprovar somente esta execução? [s/N]", flush=True)
    try:
        answer = await asyncio.to_thread(input, "> ")
    except (EOFError, KeyboardInterrupt):
        return ApprovalChoice.DENY
    return (
        ApprovalChoice.APPROVE_ONCE
        if answer.strip().casefold() == "s"
        else ApprovalChoice.DENY
    )
