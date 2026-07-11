from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError


class StrictModel(BaseModel):
    class Config:
        extra = "forbid"


class TurnInput(StrictModel):
    player_input: str = Field(min_length=1)
    rule_system: dict[str, Any]
    character: dict[str, Any]
    situation: dict[str, Any]
    world_state: dict[str, Any]
    recent_events: list[Any]


class ActionInterpretation(StrictModel):
    primary_intent: str
    secondary_intent: str | None = None
    target: str | None = None
    object: str | None = None
    method: str | None = None
    player_goal: str | None = None
    ambiguity: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class Ruling(StrictModel):
    possible: bool
    reason: str
    requires_roll: bool
    roll_type: str | None = None
    difficulty: str | None = None
    applicable_rules: list[str]


class DiceRequest(StrictModel):
    needed: bool
    dice: str | None = None
    modifier_source: str | None = None
    difficulty: str | None = None
    reason: str | None = None


class Resolution(StrictModel):
    outcome: str
    success: bool | None = None
    consequences: list[str]


class StateUpdate(StrictModel):
    player_changes: dict[str, Any]
    npc_changes: dict[str, Any]
    world_changes: dict[str, Any]
    inventory_changes: dict[str, Any]
    clue_changes: dict[str, Any]
    location_changes: dict[str, Any]
    event_changes: dict[str, Any]


class TurnResult(StrictModel):
    interpretation: ActionInterpretation
    ruling: Ruling
    dice_request: DiceRequest
    resolution: Resolution
    state_update: StateUpdate
    narration: str
    warnings: list[str]
    errors: list[str]


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def model_json_schema(model_class: type[BaseModel]) -> dict[str, Any]:
    if hasattr(model_class, "model_json_schema"):
        return model_class.model_json_schema()
    return model_class.schema()


def validate_model(model_class: type[BaseModel], payload: Any) -> BaseModel:
    if hasattr(model_class, "model_validate"):
        return model_class.model_validate(payload)
    return model_class.parse_obj(payload)


def validation_errors(error: ValidationError) -> list[str]:
    return [str(item) for item in error.errors()]
