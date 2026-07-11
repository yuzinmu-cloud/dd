from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RuleRequest(StrictModel):
    rule_system_id: str
    rule_module: str
    actor_id: str
    target_id: str | None = None
    required_values: list[str] = Field(default_factory=list)
    provided_values: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    external_roll_required: bool = False
    fixed_roll: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AbilityCheckRequest(RuleRequest): pass
class SkillCheckRequest(RuleRequest): pass
class SavingThrowRequest(RuleRequest): pass
class AttackRequest(RuleRequest): pass
class DamageRequest(RuleRequest): pass
class InitiativeRequest(RuleRequest): pass
class MovementRequest(RuleRequest): pass
class InteractionRequest(RuleRequest): pass
class InventoryActionRequest(RuleRequest): pass
class DirectResolutionRequest(RuleRequest): pass


class RuleResult(StrictModel):
    rule_module: str
    status: Literal["resolved", "pending_rule_data", "pending_roll", "unsupported", "failed_validation"]
    success: bool | None = None
    pending_input: bool = False
    pending_dice: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    values: dict[str, Any] = Field(default_factory=dict)
    state_change_proposal: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


CheckResult = RuleResult
SavingThrowResult = RuleResult
AttackResult = RuleResult
DamageResult = RuleResult
InitiativeResult = RuleResult
MovementResult = RuleResult
InteractionResult = RuleResult
