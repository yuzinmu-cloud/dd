from __future__ import annotations
from .dice import calculate_modifier, roll_d20
from .schemas import RuleRequest, RuleResult


def resolve(request: RuleRequest) -> RuleResult:
    score = request.provided_values.get("dexterity_score")
    if score is None:
        return RuleResult(rule_module="initiative", status="pending_rule_data", pending_input=True, missing_fields=["dexterity_score"])
    if request.fixed_roll is None and request.external_roll_required:
        return RuleResult(rule_module="initiative", status="pending_roll", pending_dice=True)
    natural = roll_d20(request.fixed_roll)
    modifier = calculate_modifier(int(score))
    return RuleResult(rule_module="initiative", status="resolved", success=True, values={"natural_roll": natural, "modifier": modifier, "total": natural + modifier})
