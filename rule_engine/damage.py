from __future__ import annotations
from .dice import roll_dice
from .schemas import RuleRequest, RuleResult


def resolve(request: RuleRequest) -> RuleResult:
    values = request.provided_values
    missing = [name for name in ("dice_count", "dice_sides", "target_current_hp") if values.get(name) is None]
    if missing:
        return RuleResult(rule_module="damage", status="pending_rule_data", pending_input=True, missing_fields=missing)
    critical = bool(values.get("critical_hit") or request.metadata.get("critical_hit"))
    count = int(values["dice_count"]) * (2 if critical else 1)
    fixed = values.get("fixed_rolls")
    rolls = roll_dice(count, int(values["dice_sides"]), fixed)
    rolled = sum(rolls)
    modifier = int(values.get("damage_modifier", 0))
    total = max(0, rolled + modifier)
    previous = int(values["target_current_hp"])
    new_hp = max(0, previous - total)
    return RuleResult(rule_module="damage", status="resolved", success=True, values={
        "dice_rolls": rolls, "rolled_damage": rolled, "modifier": modifier, "total_damage": total,
        "previous_hp": previous, "new_hp": new_hp, "target_defeated": new_hp == 0,
        "damage_type": values.get("damage_type"),
    }, state_change_proposal={"npc_changes": {request.target_id: {"current_hp": new_hp}}} if request.target_id else {})
