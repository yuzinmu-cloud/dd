from __future__ import annotations
from typing import Any, Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field
from rule_engine.schemas import RuleRequest, RuleResult


ACTION_CATEGORIES = (
    "attack", "ability_check", "skill_check", "saving_throw", "movement", "interaction",
    "inventory", "use_item", "social", "stealth", "rest", "initiative", "cast_spell",
    "improvised_action", "no_roll_action", "steal", "unsupported", "ambiguous",
)
ActionCategory = Literal[*ACTION_CATEGORIES]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ActionTarget(StrictModel):
    target_id: str | None = None
    label: str | None = None
    target_type: str | None = None


class ActionObject(StrictModel):
    object_id: str | None = None
    label: str | None = None
    object_type: str | None = None


class ActionClassification(StrictModel):
    category: ActionCategory
    normalized_intent: str
    reason: str
    confidence: float


class StandardAction(StrictModel):
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    raw_player_input: str
    primary_intent: str
    secondary_intents: list[str] = Field(default_factory=list)
    action_category: ActionCategory
    target: ActionTarget | None = None
    object: ActionObject | None = None
    method: str | None = None
    player_goal: str | None = None
    hostility: bool = False
    risk_level: str = "unknown"
    ambiguity: str | None = None
    confidence: float = 0.0
    referenced_abilities: list[str] = Field(default_factory=list)
    referenced_items: list[str] = Field(default_factory=list)
    referenced_spells: list[str] = Field(default_factory=list)
    context_requirements: list[str] = Field(default_factory=list)
    requires_sequence_resolution: bool = False


class MissingField(StrictModel):
    field: str
    reason: str


class ActionWarning(StrictModel):
    code: str
    message: str


class ActionError(StrictModel):
    code: str
    message: str


class FeasibilityResult(StrictModel):
    possible: bool | None
    reason: str
    required_conditions: list[str] = Field(default_factory=list)
    missing_fields: list[MissingField] = Field(default_factory=list)
    clarification_required: bool = False
    suggested_rule_categories: list[str] = Field(default_factory=list)


class ImprovisedActionResult(StrictModel):
    mapped_rule_category: str | None = None
    mapping_reason: str
    required_check: str | None = None
    required_ability: str | None = None
    required_skill: str | None = None
    required_target_value: int | None = None
    missing_fields: list[str] = Field(default_factory=list)
    possible_outcomes: list[str] = Field(default_factory=list)
    requires_sequence_resolution: bool = False


ActionResolutionRequest = RuleRequest


class ActionResolutionResult(StrictModel):
    standard_action: StandardAction
    feasibility: FeasibilityResult
    routed_rule: str
    rule_request: RuleRequest | None = None
    rule_result: RuleResult | None = None
    pending_input: bool = False
    pending_dice: bool = False
    status: Literal["pending_clarification", "pending_rule_data", "pending_attack_roll", "pending_damage_roll", "pending_check_roll", "resolved", "unsupported", "failed_validation"]
    success: bool | None = None
    outcome: str
    state_change_proposal: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
