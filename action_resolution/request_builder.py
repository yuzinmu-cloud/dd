from __future__ import annotations
from typing import Any
from rule_engine.schemas import RuleRequest
from .schemas import StandardAction


def build(action: StandardAction, context: Any, routed_rule: str, rule_system_id: str) -> RuleRequest:
    character = context.character
    actor_id = character.character_id
    target_id = action.target.target_id if action.target and action.target.target_id else _target_id(action, context)
    values: dict[str, Any] = {}
    missing: list[str] = []
    external_roll = routed_rule in {"attack", "ability_check", "skill_check", "saving_throw", "initiative"}
    if routed_rule == "attack":
        ability = _ability_score(character, "Strength")
        target = _target_context(target_id, context)
        values = {
            "attack_type": "weapon", "weapon_id": getattr(character, "equipped_weapon", None),
            "ability_score": ability, "proficiency_bonus": getattr(character, "proficiency_bonus", 0),
            "proficient": bool(getattr(character, "equipped_weapon", None) in getattr(character, "weapon_proficiencies", [])),
            "situational_modifier": 0, "advantage_state": "normal",
            "target_ac": getattr(target, "armor_class", None) if target else None,
        }
        missing = [key for key in ("ability_score", "target_ac") if values.get(key) is None]
    elif routed_rule in {"ability_check", "skill_check", "saving_throw"}:
        ability_name = action.referenced_abilities[0] if action.referenced_abilities else _default_ability(action, routed_rule)
        values = {
            "ability": ability_name, "ability_score": _ability_score(character, ability_name),
            "proficiency_bonus": getattr(character, "proficiency_bonus", 0),
            "proficient": _is_proficient(character, action, routed_rule), "situational_modifier": 0,
            "dc": context.rules.active_rule_overrides.get("default_dc") if hasattr(context, "rules") else None,
        }
        missing = [key for key in ("ability_score", "dc") if values.get(key) is None]
    elif routed_rule == "initiative":
        values = {"dexterity_score": _ability_score(character, "Dexterity")}
        missing = ["dexterity_score"] if values["dexterity_score"] is None else []
    elif routed_rule in {"movement", "interaction", "inventory", "use_item", "no_roll_action"}:
        movement_blocked = bool(getattr(context.world, "active_world_states", {}).get("movement_blocked", False)) if hasattr(context, "world") else False
        values = {"possible": not movement_blocked if routed_rule == "movement" else True, "destination": action.target.label if action.target else None, "item": action.object.label if action.object else None}
        if routed_rule in {"inventory", "use_item"} and action.object and action.object.label not in character.inventory:
            missing.append("item")
    return RuleRequest(
        rule_system_id=rule_system_id, rule_module=routed_rule, actor_id=actor_id, target_id=target_id,
        required_values=list(values), provided_values=values, missing_fields=missing,
        external_roll_required=external_roll, metadata={"action_id": action.action_id, "standard_action": action.model_dump()},
    )


def _target_id(action: StandardAction, context: Any) -> str | None:
    if not action.target or not action.target.label:
        return None
    label = action.target.label
    for npc in context.adventure.relevant_npcs:
        if label in {npc.npc_id, npc.name, npc.role} or label in (npc.role or ""):
            return npc.npc_id
    return None


def _target_context(target_id: str | None, context: Any) -> Any:
    return next((npc for npc in context.adventure.relevant_npcs if npc.npc_id == target_id), None)


def _ability_score(character: Any, name: str) -> int | None:
    scores = getattr(character, "ability_scores", {}) or {}
    for key in (name, name.lower(), name[:3].lower()):
        if key in scores:
            return int(scores[key])
    return None


def _default_ability(action: StandardAction, routed: str) -> str:
    if action.action_category in {"social"}: return "Charisma"
    if action.action_category in {"stealth", "skill_check"}: return "Dexterity" if action.action_category == "stealth" else "Intelligence"
    return "Strength"


def _is_proficient(character: Any, action: StandardAction, routed: str) -> bool:
    if routed == "saving_throw":
        return any(item.lower() in {value.lower() for value in character.saving_throw_proficiencies} for item in action.referenced_abilities)
    return bool(character.skill_proficiencies)
