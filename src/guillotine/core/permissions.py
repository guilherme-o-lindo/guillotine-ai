from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from guillotine.tools.core.contracts import ToolEffect
from guillotine.tools.core.registry import ToolRegistry


class PermissionDecision(StrEnum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


class PermissionProfile(StrEnum):
    RESTRICTED = "restricted"
    BALANCED = "balanced"
    SUPERVISED = "supervised"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class PermissionRule:
    """Trusted policy for one precise tool and optional exact resource ID.

    ``resource_id=None`` matches ONLY requests with no resource ID. It is not
    a wildcard. This avoids accidentally broad grants to filesystem paths,
    hosts, repositories, or other resources.
    """

    tool_id: str
    resource_id: str | None
    decision: PermissionDecision

    def __post_init__(self) -> None:
        if not self.tool_id or not self.tool_id.strip():
            raise ValueError("tool_id must be nonblank")
        if self.resource_id is not None and not self.resource_id.strip():
            raise ValueError("resource_id must be nonblank or None")


@dataclass(frozen=True, slots=True)
class PermissionResult:
    decision: PermissionDecision
    reason: str
    tool_id: str
    resource_id: str | None

    @property
    def granted(self) -> bool:
        """Only ALLOW grants execution; approval requests are not grants."""
        return self.decision is PermissionDecision.ALLOW


class PermissionManager:
    """Evaluate explicit trusted policies against current registry metadata.

    Rules are passed by the application, never derived from model responses,
    MCP tool annotations, or user-supplied tool arguments. This evaluator is
    intentionally synchronous and side-effect free.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        profile: PermissionProfile = PermissionProfile.BALANCED,
        rules: tuple[PermissionRule, ...] = (),
    ) -> None:
        self._registry = registry
        self._profile = profile
        self._rules = rules

    def evaluate(
        self,
        tool_id: str,
        *,
        resource_id: str | None = None,
    ) -> PermissionResult:
        """Determine if a tool call is allowed, denied or needs approval.

        A resource ID is an exact opaque identifier, NOT a validated path or
        URL. Before execution the caller must derive it from the actual tool
        arguments using tool-specific canonicalization and scope checks.
        """
        entry = self._registry.get(tool_id)
        effects = entry.security.effects

        def result(decision: PermissionDecision, reason: str) -> PermissionResult:
            return PermissionResult(decision, reason, tool_id, resource_id)

        if ToolEffect.UNKNOWN in effects:
            return result(
                PermissionDecision.DENY,
                "Unclassified effects are denied until explicitly classified",
            )

        if self._profile is PermissionProfile.RESTRICTED and effects != frozenset(
            {ToolEffect.READ}
        ):
            return result(
                PermissionDecision.DENY,
                "Restricted profile blocks non-read operations",
            )

        matching = (
            rule.decision
            for rule in self._rules
            if rule.tool_id == tool_id and rule.resource_id == resource_id
        )
        matches = frozenset(matching)
        if PermissionDecision.DENY in matches:
            return result(PermissionDecision.DENY, "Explicit policy denies this call")

        if PermissionDecision.REQUIRE_APPROVAL in matches:
            return result(
                PermissionDecision.REQUIRE_APPROVAL,
                "Explicit policy requires approval",
            )

        if PermissionDecision.ALLOW in matches:
            return result(PermissionDecision.ALLOW, "Explicit policy allows this call")

        if self._profile is PermissionProfile.CUSTOM:
            return result(PermissionDecision.DENY, "No matching custom policy")

        return result(
            PermissionDecision.REQUIRE_APPROVAL,
            "No explicit permission: human approval required",
        )
