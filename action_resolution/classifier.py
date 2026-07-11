from __future__ import annotations
from typing import Any
from .schemas import ACTION_CATEGORIES, ActionObject, ActionTarget, StandardAction
from .intents import normalize_intent


INTENT_MAP = {
    "attack": "attack", "hostile_action": "attack", "kill": "attack", "violence": "attack",
    "ability_check": "ability_check", "check": "ability_check", "investigate": "skill_check",
    "investigation": "skill_check", "observe": "skill_check", "search": "skill_check",
    "stealth": "stealth", "hide": "stealth", "sneak": "stealth", "steal": "steal",
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
    intent, _warning = normalize_intent(str(data.get("primary_intent", "unknown")), data.get("raw_player_input", ""))
    category = INTENT_MAP.get(intent, "unsupported")
    secondary = data.get("secondary_intent")
    secondary_intents = [secondary] if secondary else []
    target_label = data.get("target")
    object_label = data.get("object")
    target_id = _resolve_target_id(target_label, context)
    return StandardAction(
        raw_player_input=data.get("raw_player_input", ""), primary_intent=intent,
        secondary_intents=secondary_intents, action_category=category,
        target=ActionTarget(target_id=target_id, label=target_label, target_type="npc" if target_id else None) if target_label else None,
        object=ActionObject(label=object_label) if object_label else None,
        method=data.get("method"), player_goal=data.get("player_goal"), hostility=bool(data.get("hostility")),
        risk_level=data.get("risk_level") or ("high" if category in {"attack", "saving_throw"} else "unknown"),
        ambiguity=data.get("ambiguity"), confidence=float(data.get("confidence", 0.0)),
        referenced_items=[object_label] if object_label else [],
        requires_sequence_resolution=bool(secondary_intents),
    )


def _resolve_target_id(label: str | None, context: Any) -> str | None:
    if not label or context is None:
        return None
    for npc in getattr(getattr(context, "adventure", None), "relevant_npcs", []):
        candidates = [npc.npc_id, npc.name, npc.role, *getattr(npc, "aliases", [])]
        if any(candidate and (label == candidate or label in candidate or candidate in label) for candidate in candidates):
            return npc.npc_id
    return None
