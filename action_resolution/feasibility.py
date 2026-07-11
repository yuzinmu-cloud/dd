from __future__ import annotations
from typing import Any
from .schemas import FeasibilityResult, MissingField, StandardAction


def analyze(action: StandardAction, context: Any, capabilities: set[str]) -> FeasibilityResult:
    if action.risk_level == "impossible":
        return FeasibilityResult(possible=False, reason="Context marks the action as impossible under current conditions.")
    if action.action_category == "ambiguous" or action.ambiguity:
        return FeasibilityResult(possible=None, reason="Action requires clarification.", clarification_required=True,
            missing_fields=[MissingField(field="clarification", reason="Primary action is ambiguous.")])
    if action.action_category == "unsupported":
        return FeasibilityResult(possible=None, reason="No supported category matches this action.",
            missing_fields=[MissingField(field="supported_rule", reason="Rule Pack has no mapping.")])
    missing: list[MissingField] = []
    if action.action_category == "attack" and not action.target:
        missing.append(MissingField(field="target", reason="Attack requires a target."))
    if action.action_category in {"inventory", "use_item"} and not action.object:
        missing.append(MissingField(field="object", reason="Inventory action requires an item."))
    if action.referenced_items and action.action_category in {"inventory", "use_item"}:
        inventory = set(getattr(getattr(context, "character", None), "inventory", []))
        for item in action.referenced_items:
            if item not in inventory:
                missing.append(MissingField(field=f"item:{item}", reason="Referenced item is unavailable."))
    return FeasibilityResult(
        possible=False if missing else True,
        reason="Required action data is missing." if missing else "Action is feasible enough to route.",
        required_conditions=[], missing_fields=missing,
        clarification_required=False, suggested_rule_categories=[action.action_category],
    )


def analyze_improvised(action: StandardAction, context: Any, capabilities: set[str]) -> dict[str, Any]:
    mapped = "skill_check" if action.referenced_items and "skill_check" in capabilities else "ability_check" if "ability_check" in capabilities else None
    missing = [] if mapped else ["supported_rule"]
    default_dc = getattr(getattr(getattr(context, "rules", None), "active_rule_overrides", {}), "get", lambda _key: None)("default_dc")
    if mapped and default_dc is None:
        missing.append("dc")
    return {
        "mapped_rule_category": mapped, "mapping_reason": "Map method and available resources to a generic check." if mapped else "No safe mapping available.",
        "required_check": mapped, "required_ability": action.referenced_abilities[0] if action.referenced_abilities else None,
        "required_skill": None, "required_target_value": None, "missing_fields": missing,
        "possible_outcomes": ["success", "failure"] if mapped else [],
        "requires_sequence_resolution": action.requires_sequence_resolution,
    }
