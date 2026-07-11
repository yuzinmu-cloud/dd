from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

try:
    from pydantic import ConfigDict
except ImportError:  # Pydantic v1 compatibility
    ConfigDict = None


class StrictModel(BaseModel):
    if ConfigDict is not None:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


class RuleContext(StrictModel):
    system_name: str
    system_version: str | None
    available_checks: list[str]
    difficulty_rules: dict[str, int | str]
    special_rules: list[str]
    house_rules: list[str]


class CharacterContext(StrictModel):
    character_id: str
    name: str
    race: str | None
    character_class: str | None
    level: int | None
    attributes: dict[str, int | str]
    skills: dict[str, int | str]
    inventory: list[str]
    equipment: list[str]
    conditions: list[str]
    current_hp: int | None
    max_hp: int | None


class WorldContext(StrictModel):
    world_name: str
    current_region: str | None
    current_location: str
    time: str | None
    weather: str | None
    known_world_facts: list[str]
    active_world_states: dict[str, object]


class NPCContext(StrictModel):
    npc_id: str
    name: str
    role: str | None
    description: str
    known_facts: list[str]
    hidden_facts: list[str]
    goals: list[str]
    attitude: str | int | None
    current_state: dict[str, object]


class AdventureContext(StrictModel):
    adventure_id: str
    title: str
    premise: str
    current_situation: str
    relevant_npcs: list[NPCContext]
    known_clues: list[str]
    active_objectives: list[str]
    hidden_gm_facts: list[str]
    active_events: list[str]


class HistoryContext(StrictModel):
    recent_events: list[str]
    player_decisions: list[str]
    unresolved_consequences: list[str]
    world_changes: list[str]
    npc_memories: dict[str, list[str]]


class SessionContext(StrictModel):
    session_id: str
    turn_number: int
    recent_conversation: list[dict[str, str]]
    initiative: list[str] | None
    current_phase: str | None


class GMContext(StrictModel):
    context_version: str
    rules: RuleContext
    character: CharacterContext
    world: WorldContext
    adventure: AdventureContext
    history: HistoryContext
    session: SessionContext


class ActionInterpretation(StrictModel):
    raw_player_input: str = ""
    primary_intent: str
    secondary_intent: str | None = None
    target: str | None = None
    object: str | None = None
    method: str | None = None
    player_goal: str | None = None
    hostility: bool = False
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


class DiceResult(StrictModel):
    status: Literal["not_required", "pending", "provided"]
    total: int | float | None = None
    raw: Any | None = None


class TurnInput(StrictModel):
    player_input: str = Field(min_length=1)
    context: GMContext
    dice_result: DiceResult | None = None


class Resolution(StrictModel):
    outcome: str
    success: bool | None = None
    consequences: list[str]
    proposed_updates: dict[str, Any] = Field(default_factory=dict)


class StateUpdate(StrictModel):
    player_changes: dict[str, Any] = Field(default_factory=dict)
    npc_changes: dict[str, Any] = Field(default_factory=dict)
    world_changes: dict[str, Any] = Field(default_factory=dict)
    inventory_changes: dict[str, Any] = Field(default_factory=dict)
    clue_changes: dict[str, Any] = Field(default_factory=dict)
    location_changes: dict[str, Any] = Field(default_factory=dict)
    event_changes: dict[str, Any] = Field(default_factory=dict)
    session_changes: dict[str, Any] = Field(default_factory=dict)


class NarrationResult(StrictModel):
    narration: str


SessionStatus = Literal["active", "completed", "failed", "aborted"]


class TurnResult(StrictModel):
    interpretation: ActionInterpretation
    ruling: Ruling
    dice_request: DiceRequest
    resolution: Resolution
    state_update: StateUpdate
    narration: str
    warnings: list[str]
    errors: list[str]
    session_status: SessionStatus = "active"


class SessionResult(StrictModel):
    final_context: GMContext
    turns: list[TurnResult]
    turn_count: int
    session_status: SessionStatus
    warnings: list[str]
    errors: list[str]


def empty_state_update() -> StateUpdate:
    return StateUpdate()


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
