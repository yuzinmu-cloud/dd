from __future__ import annotations
from .dice import apply_advantage, apply_disadvantage, calculate_modifier, roll_d20
from .schemas import RuleRequest, RuleResult


def resolve(request: RuleRequest) -> RuleResult:
    values = request.provided_values
    missing = [name for name in ("ability_score", "target_ac") if values.get(name) is None]
    if missing:
        return RuleResult(rule_module="attack", status="pending_rule_data", pending_input=True, missing_fields=missing)
    if request.fixed_roll is None and request.external_roll_required:
        return RuleResult(rule_module="attack", status="pending_roll", pending_dice=True)
    natural = roll_d20(request.fixed_roll)
    advantage_state = values.get("advantage_state", "normal")
    if advantage_state in {"advantage", "disadvantage"}:
        second = roll_d20(values.get("fixed_secondary_roll"))
        natural = apply_advantage(natural, second) if advantage_state == "advantage" else apply_disadvantage(natural, second)
    ability = calculate_modifier(int(values["ability_score"]))
    proficiency = int(values.get("proficiency_bonus", 0)) if values.get("proficient") else 0
    situational = int(values.get("situational_modifier", 0))
    modifier = ability + proficiency + situational
    total = natural + modifier
    ac = int(values["target_ac"])
    critical_hit = natural == 20
    critical_miss = natural == 1
    hit = critical_hit or (not critical_miss and total >= ac)
    damage_request = None
    if hit:
        damage_request = {
            "rule_system_id": request.rule_system_id, "rule_module": "damage", "actor_id": request.actor_id,
            "target_id": request.target_id, "provided_values": values.get("damage", {}),
            "metadata": {"critical_hit": critical_hit},
        }
    return RuleResult(rule_module="attack", status="resolved", success=hit, values={
        "natural_roll": natural, "attack_modifier": modifier, "total": total, "target_ac": ac,
        "hit": hit, "critical_hit": critical_hit, "critical_miss": critical_miss,
        "damage_request": damage_request, "advantage_state": advantage_state,
    })
