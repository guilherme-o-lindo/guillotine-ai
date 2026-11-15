import pytest
from pydantic import ValidationError

from guillotine.tools.core.contracts import ToolEffect, ToolRisk, ToolSecurity


def test_unknown_by_default_is_critical() -> None:
    assert ToolSecurity().risk_hint == ToolRisk.CRITICAL


@pytest.mark.parametrize(
    ("effect", "risk"),
    [
        (ToolEffect.READ, ToolRisk.MEDIUM),
        (ToolEffect.NETWORK, ToolRisk.MEDIUM),
        (ToolEffect.WRITE, ToolRisk.HIGH),
        (ToolEffect.DELETE, ToolRisk.HIGH),
        (ToolEffect.EXECUTE, ToolRisk.HIGH),
        (ToolEffect.EXTERNAL_ACTION, ToolRisk.HIGH),
        (ToolEffect.UNKNOWN, ToolRisk.CRITICAL),
    ],
)
def test_effect_risk_hint(effect: ToolEffect, risk: ToolRisk) -> None:
    assert ToolSecurity(effects=frozenset({effect})).risk_hint == risk


def test_highest_effect_risk_wins() -> None:
    security = ToolSecurity(effects=frozenset({ToolEffect.READ, ToolEffect.DELETE}))
    assert security.risk_hint == ToolRisk.HIGH


def test_unknown_cannot_be_hidden_by_other_effects() -> None:
    security = ToolSecurity(effects=frozenset({ToolEffect.READ, ToolEffect.UNKNOWN}))
    assert security.risk_hint == ToolRisk.CRITICAL


def test_empty_effects_rejected() -> None:
    with pytest.raises(ValidationError):
        ToolSecurity(effects=frozenset())


def test_undeclared_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        ToolSecurity.model_validate({"name": "read_file"})


def test_security_metadata_is_frozen() -> None:
    security = ToolSecurity()
    with pytest.raises(ValidationError):
        security.effects = frozenset({ToolEffect.READ})


def test_invalid_effect_rejected() -> None:
    with pytest.raises(ValidationError):
        ToolSecurity.model_validate({"effects": ["do_anything"]})
