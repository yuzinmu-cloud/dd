from __future__ import annotations
from typing import Any
from .schemas import ACTION_CATEGORIES, ActionObject, ActionTarget, StandardAction


INTENT_MAP = {
    "attack": "attack", "hostile_action": "attack", "kill": "attack", "violence": "attack",
    "ability_check": "ability_check", "check": "ability_check", "investigate": "skill_check",
    "investigation": "skill_check", "observe": "skill_check", "search": "skill_check",
    "stealth": "stealth", "hide": "stealth", "sneak": "stealth", "steal": "skill_check",
    "ask": "social", "social": "social", "persuade": "social", "deceive": "social",
    "move": "movement", "movement": "movement", "travel": "movement",
    "interact": "interaction", "interaction": "interaction",
    "inventory": "inventory", "use_item": "use_item", "equip": "inventory",
    "rest": "rest", "initiative": "initiative", "cast_spell": "cast_spell",
    "creative_action": "improvised_action", "improvise": "improvised_action",
    "no_roll_action": "no_roll_action", "uncertain": "ambiguous", "unknown": "ambiguous",
}


def classify(action_interpretation: Any, context: Any = None) -> StandardAction:
    data = action_interpretation.model_dump() if hasattr(action_interpretation, "model_dump") else dict(action_interpretation)
    intent = str(data.get("primary_intent", "unknown")).strip().lower()
    category = INTENT_MAP.get(intent, "unsupported")
    secondary = data.get("secondary_intent")
    secondary_intents = [secondary] if secondary else []
    target_label = data.get("target")
    object_label = data.get("object")
    return StandardAction(
        raw_player_input=data.get("raw_player_input", ""), primary_intent=intent,
        secondary_intents=secondary_intents, action_category=category,
        target=ActionTarget(label=target_label) if target_label else None,
        object=ActionObject(label=object_label) if object_label else None,
        method=data.get("method"), player_goal=data.get("player_goal"), hostility=bool(data.get("hostility")),
        risk_level=data.get("risk_level") or ("high" if category in {"attack", "saving_throw"} else "unknown"),
        ambiguity=data.get("ambiguity"), confidence=float(data.get("confidence", 0.0)),
        referenced_items=[object_label] if object_label else [],
        requires_sequence_resolution=bool(secondary_intents),
    )
