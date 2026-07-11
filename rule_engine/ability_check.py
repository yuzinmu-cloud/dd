from __future__ import annotations
from .dice import calculate_modifier, roll_d20
from .schemas import RuleRequest, RuleResult


def resolve(request: RuleRequest, module: str = "ability_check") -> RuleResult:
    values = request.provided_values
    missing = [name for name in ("ability_score", "dc") if values.get(name) is None]
    if missing:
        return RuleResult(rule_module=module, status="pending_rule_data", pending_input=True, missing_fields=missing)
    if request.fixed_roll is None and request.external_roll_required:
        return RuleResult(rule_module=module, status="pending_roll", pending_dice=True)
    natural = roll_d20(request.fixed_roll)
    ability_modifier = calculate_modifier(int(values["ability_score"]))
    proficiency = int(values.get("proficiency_bonus", 0)) if values.get("proficient") else 0
    situational = int(values.get("situational_modifier", 0))
    total = natural + ability_modifier + proficiency + situational
    return RuleResult(rule_module=module, status="resolved", success=total >= int(values["dc"]), values={
        "natural_roll": natural, "ability_modifier": ability_modifier, "proficiency_modifier": proficiency,
        "situational_modifier": situational, "total": total, "dc": int(values["dc"]),
    })
