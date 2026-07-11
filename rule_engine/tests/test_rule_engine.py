from __future__ import annotations
import inspect
from pathlib import Path
import pytest
from rule_engine.dice import calculate_modifier, roll_dice
from rule_engine.engine import RuleEngine
from rule_engine.schemas import RuleRequest


PACK = Path(__file__).resolve().parents[2] / "rule_systems" / "dnd5e_srd52"


def request(module, values, fixed=10, **kwargs):
    return RuleRequest(rule_system_id="test", rule_module=module, actor_id="actor", target_id="target",
        provided_values=values, fixed_roll=fixed, **kwargs)


@pytest.mark.parametrize(("score","expected"), [(1,-5),(8,-1),(10,0),(12,1),(20,5)])
def test_ability_modifier(score, expected): assert calculate_modifier(score) == expected


def test_ability_check_success_and_proficiency():
    result = RuleEngine(PACK).resolve(request("ability_check", {"ability_score":14,"dc":14,"proficiency_bonus":2,"proficient":True,"situational_modifier":0}, fixed=10))
    assert result.success and result.values["total"] == 14


def test_ability_check_missing_dc():
    result = RuleEngine(PACK).resolve(request("ability_check", {"ability_score":14,"dc":None}))
    assert result.status == "pending_rule_data" and "dc" in result.missing_fields


def test_skill_check_uses_proficiency():
    result = RuleEngine(PACK).resolve(request("skill_check", {"ability_score":12,"dc":13,"proficiency_bonus":2,"proficient":True}, fixed=10))
    assert result.values["proficiency_modifier"] == 2 and result.success


def test_saving_throw():
    assert RuleEngine(PACK).resolve(request("saving_throw", {"ability_score":16,"dc":13}, fixed=10)).success


@pytest.mark.parametrize(("roll","ac","hit"), [(15,15,True),(8,15,False)])
def test_attack_hit_and_miss(roll, ac, hit):
    result=RuleEngine(PACK).resolve(request("attack", {"ability_score":10,"target_ac":ac,"proficient":False}, fixed=roll))
    assert result.values["hit"] is hit


def test_attack_natural_20():
    result=RuleEngine(PACK).resolve(request("attack", {"ability_score":1,"target_ac":99}, fixed=20))
    assert result.values["critical_hit"] and result.values["hit"]


def test_attack_natural_1():
    result=RuleEngine(PACK).resolve(request("attack", {"ability_score":30,"target_ac":1}, fixed=1))
    assert result.values["critical_miss"] and not result.values["hit"]


def test_attack_missing_ac():
    result=RuleEngine(PACK).resolve(request("attack", {"ability_score":12,"target_ac":None}))
    assert "target_ac" in result.missing_fields


def test_damage_and_hp_floor():
    result=RuleEngine(PACK).resolve(request("damage", {"dice_count":1,"dice_sides":6,"fixed_rolls":[6],"damage_modifier":3,"target_current_hp":5,"damage_type":"piercing"}, fixed=None))
    assert result.values["total_damage"] == 9 and result.values["new_hp"] == 0


def test_critical_damage_doubles_dice():
    result=RuleEngine(PACK).resolve(request("damage", {"dice_count":1,"dice_sides":6,"fixed_rolls":[4,5],"damage_modifier":1,"target_current_hp":20,"critical_hit":True}, fixed=None))
    assert result.values["dice_rolls"] == [4,5] and result.values["total_damage"] == 10


def test_damage_ignores_untrusted_metadata_total():
    req=request("damage", {"dice_count":1,"dice_sides":6,"fixed_rolls":[3],"damage_modifier":2,"target_current_hp":10}, fixed=None)
    req=req.model_copy(update={"metadata":{"claimed_total_damage":999}})
    result=RuleEngine(PACK).resolve(req)
    assert result.values["total_damage"]==5 and result.values["new_hp"]==5


def test_initiative():
    result=RuleEngine(PACK).resolve(request("initiative", {"dexterity_score":14}, fixed=12))
    assert result.values["total"] == 14


def test_fixed_roll_cannot_be_overridden_by_external_value():
    req=request("attack", {"ability_score":10,"target_ac":15}, fixed=5)
    result=RuleEngine(PACK).resolve(req, {"total":20})
    assert result.values["natural_roll"] == 5


def test_rule_engine_has_no_gm_processor_dependency():
    source="\n".join(path.read_text(encoding="utf-8") for path in Path("rule_engine").glob("*.py"))
    assert "gm_processor" not in source and "ollama" not in source.lower()


def test_rule_pack_supports_and_loads():
    engine=RuleEngine(PACK)
    assert engine.supports("attack") and not engine.supports("cast_spell")


def test_roll_dice_fixed_values(): assert roll_dice(2,6,[2,5]) == [2,5]
