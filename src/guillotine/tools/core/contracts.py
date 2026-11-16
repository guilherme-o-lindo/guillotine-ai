from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolEffect(StrEnum):
    """Potential side effects used to classify a tool conservatively."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    NETWORK = "network"
    EXTERNAL_ACTION = "external_action"
    UNKNOWN = "unknown"


class ToolRisk(StrEnum):
    """Preliminary severity hint; never an authorization decision."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_RISK_RANK: dict[ToolRisk, int] = {
    ToolRisk.LOW: 0,
    ToolRisk.MEDIUM: 1,
    ToolRisk.HIGH: 2,
    ToolRisk.CRITICAL: 3,
}

_EFFECT_RISK: dict[ToolEffect, ToolRisk] = {
    ToolEffect.READ: ToolRisk.MEDIUM,
    ToolEffect.WRITE: ToolRisk.HIGH,
    ToolEffect.DELETE: ToolRisk.HIGH,
    ToolEffect.EXECUTE: ToolRisk.HIGH,
    ToolEffect.NETWORK: ToolRisk.MEDIUM,
    ToolEffect.EXTERNAL_ACTION: ToolRisk.HIGH,
    ToolEffect.UNKNOWN: ToolRisk.CRITICAL,
}


class ToolSecurity(BaseModel):
    """Trusted, declarative security classification for a tool.

    Only the Guillotine's own trusted configuration may populate this model.
    Never derive or downgrade security from untrusted MCP tool annotations.
    Effects are hints, not permissions; runtime arguments and resources must
    still be checked by the future permission manager.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    effects: frozenset[ToolEffect] = Field(
        default_factory=lambda: frozenset({ToolEffect.UNKNOWN})
    )

    @field_validator("effects")
    @classmethod
    def effects_cannot_be_empty(
        cls, effects: frozenset[ToolEffect]
    ) -> frozenset[ToolEffect]:
        if not effects:
            raise ValueError("effects cannot be empty")
        return effects

    @property
    def risk_hint(self) -> ToolRisk:
        """Conservative classification only; does not approve execution."""
        return max(
            (_EFFECT_RISK[effect] for effect in self.effects),
            key=_RISK_RANK.__getitem__,
        )
