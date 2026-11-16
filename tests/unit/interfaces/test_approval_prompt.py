"""Terminal interaction requires an explicit choice and masks secret fields."""

import pytest

from guillotine.core.approvals import ApprovalChoice, ApprovalRequest
from guillotine.interfaces.approval_prompt import terminal_approval_prompt


@pytest.mark.asyncio
async def test_explicit_yes(monkeypatch: pytest.MonkeyPatch) -> None:
    def answer_yes(_prompt: str) -> str:
        return "s"

    monkeypatch.setattr("builtins.input", answer_yes)
    request = ApprovalRequest("local:write", "file:a", "{}", "f" * 64)
    assert await terminal_approval_prompt(request) is ApprovalChoice.APPROVE_ONCE


@pytest.mark.asyncio
async def test_default_deny(monkeypatch: pytest.MonkeyPatch) -> None:
    def answer_empty(_prompt: str) -> str:
        return ""

    monkeypatch.setattr("builtins.input", answer_empty)
    request = ApprovalRequest("local:write", "file:a", "{}", "f" * 64)
    assert await terminal_approval_prompt(request) is ApprovalChoice.DENY


@pytest.mark.asyncio
async def test_masked_secret(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def answer_no(_prompt: str) -> str:
        return "n"

    monkeypatch.setattr("builtins.input", answer_no)
    request = ApprovalRequest(
        "local:write", "file:a", '{"api_key":"hidden-value","path":"a"}', "f" * 64
    )
    await terminal_approval_prompt(request)
    output = capsys.readouterr().out
    assert "hidden-value" not in output
    assert "[REDACTED]" in output
    assert '"path": "a"' in output
