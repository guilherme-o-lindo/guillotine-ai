from types import SimpleNamespace
from typing import cast

import pytest
from pydantic_ai.tools import Tool as PydanticTool

from guillotine.core.permissions import (
    PermissionDecision,
    PermissionManager,
    PermissionProfile,
    PermissionRule,
)
from guillotine.tools.contracts import ToolEffect, ToolSecurity
from guillotine.tools.registry import ToolRegistry, UnknownToolError


def register(registry: ToolRegistry, name: str, *effects: ToolEffect) -> str:
    definition = cast("PydanticTool[object]", SimpleNamespace(name=name))
    return registry.register_local(
        definition, security=ToolSecurity(effects=frozenset(effects))
    ).identifier


def test_unclassified_tool_is_denied_by_default() -> None:
    registry = ToolRegistry()
    definition = cast("PydanticTool[object]", SimpleNamespace(name="unknown"))
    tool_id = registry.register_local(definition).identifier
    decision = PermissionManager(registry).evaluate(tool_id)
    assert decision.decision is PermissionDecision.DENY
    assert not decision.granted


@pytest.mark.parametrize(
    "effects",
    [
        (ToolEffect.READ,),
        (ToolEffect.WRITE,),
        (ToolEffect.READ, ToolEffect.NETWORK),
    ],
)
def test_balanced_requires_approval_without_explicit_rule(
    effects: tuple[ToolEffect, ...],
) -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "tool", *effects)
    decision = PermissionManager(registry).evaluate(tool_id)
    assert decision.decision is PermissionDecision.REQUIRE_APPROVAL
    assert not decision.granted


def test_explicit_scoped_allow() -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "inspect", ToolEffect.READ)
    manager = PermissionManager(
        registry,
        rules=(
            PermissionRule(tool_id, "file:/safe/report.txt", PermissionDecision.ALLOW),
        ),
    )
    allowed = manager.evaluate(tool_id, resource_id="file:/safe/report.txt")
    assert allowed.granted
    assert not manager.evaluate(tool_id, resource_id="file:/other.txt").granted
    assert not manager.evaluate(tool_id).granted


def test_resource_none_does_not_grant_other_resources() -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "inspect", ToolEffect.READ)
    manager = PermissionManager(
        registry,
        rules=(PermissionRule(tool_id, None, PermissionDecision.ALLOW),),
    )
    assert manager.evaluate(tool_id).granted
    assert not manager.evaluate(tool_id, resource_id="file:secret").granted


def test_deny_overrides_allow_irrespective_of_order() -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "inspect", ToolEffect.READ)
    rules = (
        PermissionRule(tool_id, "file:a", PermissionDecision.ALLOW),
        PermissionRule(tool_id, "file:a", PermissionDecision.DENY),
    )
    for order in (rules, rules[::-1]):
        manager = PermissionManager(registry, rules=order)
        assert (
            manager.evaluate(tool_id, resource_id="file:a").decision
            is PermissionDecision.DENY
        )


def test_approval_overrides_allow() -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "inspect", ToolEffect.READ)
    manager = PermissionManager(
        registry,
        rules=(
            PermissionRule(tool_id, None, PermissionDecision.ALLOW),
            PermissionRule(tool_id, None, PermissionDecision.REQUIRE_APPROVAL),
        ),
    )
    assert not manager.evaluate(tool_id).granted


def test_restricted_blocks_writes_even_when_explicitly_allowed() -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "write", ToolEffect.WRITE)
    manager = PermissionManager(
        registry,
        profile=PermissionProfile.RESTRICTED,
        rules=(PermissionRule(tool_id, "file:a", PermissionDecision.ALLOW),),
    )
    assert (
        manager.evaluate(tool_id, resource_id="file:a").decision
        is PermissionDecision.DENY
    )


def test_restricted_read_requires_approval() -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "read", ToolEffect.READ)
    manager = PermissionManager(registry, profile=PermissionProfile.RESTRICTED)
    assert manager.evaluate(tool_id).decision is PermissionDecision.REQUIRE_APPROVAL


def test_supervised_defaults_to_approval() -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "delete", ToolEffect.DELETE)
    manager = PermissionManager(registry, profile=PermissionProfile.SUPERVISED)
    assert manager.evaluate(tool_id).decision is PermissionDecision.REQUIRE_APPROVAL


def test_custom_denies_without_match() -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "read", ToolEffect.READ)
    manager = PermissionManager(registry, profile=PermissionProfile.CUSTOM)
    assert manager.evaluate(tool_id).decision is PermissionDecision.DENY


def test_unknown_effect_dominates_explicit_allow() -> None:
    registry = ToolRegistry()
    tool_id = register(registry, "tool", ToolEffect.READ, ToolEffect.UNKNOWN)
    manager = PermissionManager(
        registry,
        rules=(PermissionRule(tool_id, None, PermissionDecision.ALLOW),),
    )
    assert manager.evaluate(tool_id).decision is PermissionDecision.DENY


def test_policy_is_bound_to_exact_tool_identifier() -> None:
    registry = ToolRegistry()
    first = register(registry, "first", ToolEffect.READ)
    second = register(registry, "second", ToolEffect.READ)
    manager = PermissionManager(
        registry, rules=(PermissionRule(first, None, PermissionDecision.ALLOW),)
    )
    assert manager.evaluate(first).granted
    assert not manager.evaluate(second).granted


def test_unregistered_tool_rejected() -> None:
    with pytest.raises(UnknownToolError):
        PermissionManager(ToolRegistry()).evaluate("local:missing")


@pytest.mark.parametrize("value", ["", " ", "\t"])
def test_rule_rejects_blank_tool_id(value: str) -> None:
    with pytest.raises(ValueError):
        PermissionRule(value, None, PermissionDecision.ALLOW)


@pytest.mark.parametrize("value", ["", " ", "\t"])
def test_rule_rejects_blank_resource_id(value: str) -> None:
    with pytest.raises(ValueError):
        PermissionRule("local:tool", value, PermissionDecision.ALLOW)
