from __future__ import annotations
from .schemas import StandardAction


ROUTES = {
    "attack": "attack", "ability_check": "ability_check", "skill_check": "skill_check",
    "saving_throw": "saving_throw", "initiative": "initiative", "movement": "movement",
    "interaction": "interaction", "inventory": "inventory", "use_item": "use_item",
    "social": "skill_check", "stealth": "skill_check", "rest": "no_roll_action",
    "no_roll_action": "no_roll_action", "cast_spell": "unsupported",
    "unsupported": "unsupported", "ambiguous": "clarification",
}


def route(action: StandardAction, supported: set[str]) -> str:
    if action.action_category in {"skill_check", "social"} and action.risk_level == "low":
        return "no_roll_action"
    if action.action_category in {"movement", "interaction"} and action.risk_level == "high":
        return "ability_check"
    if action.action_category == "improvised_action":
        return "ability_check" if "ability_check" in supported else "unsupported"
    routed = ROUTES.get(action.action_category, "unsupported")
    if routed not in {"unsupported", "clarification"} and action.action_category not in supported and routed not in supported:
        return "unsupported"
    return routed
