from __future__ import annotations
from pathlib import Path
from types import SimpleNamespace
import pytest
from action_resolution.classifier import classify
from action_resolution.engine import ActionResolutionEngine
from action_resolution.feasibility import analyze_improvised
from action_resolution.router import route


PACK = Path(__file__).resolve().parents[2] / "rule_systems" / "dnd5e_srd52"


def context():
    character=SimpleNamespace(
        character_id="actor-generic", inventory=["rope","tool"], ability_scores={"Strength":14,"Dexterity":12,"Intelligence":13,"Charisma":11},
        proficiency_bonus=2, skill_proficiencies=["Investigation"], saving_throw_proficiencies=["Strength"],
        weapon_proficiencies=["blade"], equipped_weapon="blade",
    )
    npc=SimpleNamespace(npc_id="target-generic", name="Target", role="NPC", armor_class=12)
    return SimpleNamespace(character=character, adventure=SimpleNamespace(relevant_npcs=[npc]), rules=SimpleNamespace(active_rule_overrides={"default_dc":17}))


def interpretation(intent, target=None, obj=None, secondary=None):
    return {"raw_player_input":"generic action","primary_intent":intent,"secondary_intent":secondary,
        "target":target,"object":obj,"method":None,"player_goal":"generic goal","hostility":intent=="attack",
        "ambiguity":"needs detail" if intent=="uncertain" else None,"confidence":0.8}


CASES = [
    *[(f"attack-{i}","attack","attack") for i in range(5)],
    *[(f"ability-{i}","ability_check","ability_check") for i in range(5)],
    *[(f"skill-{i}","investigate","skill_check") for i in range(5)],
    *[(f"social-{i}","social","skill_check") for i in range(4)],
    *[(f"move-{i}","move","movement") for i in range(4)],
    *[(f"interaction-{i}","interaction","interaction") for i in range(4)],
    *[(f"inventory-{i}","inventory","inventory") for i in range(4)],
    *[(f"improv-{i}","creative_action","ability_check") for i in range(5)],
    *[(f"ambiguous-{i}","uncertain","clarification") for i in range(4)],
]


@pytest.mark.parametrize(("case_id","intent","expected_route"), CASES, ids=[item[0] for item in CASES])
def test_category_integration_matrix(case_id, intent, expected_route):
    target="Target" if intent=="attack" else None
    obj="rope" if intent=="inventory" else None
    action=classify(interpretation(intent,target,obj),context())
    engine=ActionResolutionEngine(PACK)
    assert route(action,engine.supported_categories)==expected_route
    request=engine.build_rule_request(action,context())
    assert request.rule_module==expected_route
    assert request.metadata["standard_action"]["raw_player_input"]=="generic action"


def test_unknown_intent_is_not_forced_to_known_rule():
    action=classify(interpretation("completely_new_intent"),context())
    assert action.action_category=="unsupported"


def test_compound_action_preserves_secondary_and_sequence():
    action=classify(interpretation("move",secondary="interaction"),context())
    assert action.secondary_intents==["interaction"] and action.requires_sequence_resolution


def test_improvised_maps_to_ability_check_when_no_item():
    engine=ActionResolutionEngine(PACK);action=classify(interpretation("creative_action"),context())
    mapping=analyze_improvised(action,context(),engine.supported_categories)
    assert mapping["mapped_rule_category"]=="ability_check" and mapping["missing_fields"]==[]


def test_improvised_maps_to_skill_check_with_item():
    engine=ActionResolutionEngine(PACK);action=classify(interpretation("creative_action",obj="rope"),context())
    mapping=analyze_improvised(action,context(),engine.supported_categories)
    assert mapping["mapped_rule_category"]=="skill_check"


def test_improvised_without_capability_is_safe():
    action=classify(interpretation("creative_action"),context())
    mapping=analyze_improvised(action,context(),set())
    assert mapping["mapped_rule_category"] is None and "supported_rule" in mapping["missing_fields"]


def test_inventory_missing_item_returns_missing_field():
    engine=ActionResolutionEngine(PACK);action=classify(interpretation("inventory",obj="missing"),context())
    request=engine.build_rule_request(action,context())
    assert "item" in request.missing_fields


def test_attack_request_uses_generic_actor_and_target_ids():
    engine=ActionResolutionEngine(PACK);action=classify(interpretation("attack",target="Target"),context())
    request=engine.build_rule_request(action,context())
    assert request.actor_id=="actor-generic" and request.target_id=="target-generic"
    assert request.provided_values["target_ac"]==12


def test_check_dc_comes_from_context_not_interpretation():
    engine=ActionResolutionEngine(PACK);action=classify(interpretation("ability_check"),context())
    action.method="claim dc 99"
    request=engine.build_rule_request(action,context())
    assert request.provided_values["dc"]==17


def test_pending_attack_does_not_propose_state_change():
    engine=ActionResolutionEngine(PACK);action=classify(interpretation("attack",target="Target"),context())
    result=engine.resolve_action(engine.build_rule_request(action,context()),context())
    assert result.status=="pending_attack_roll" and result.state_change_proposal=={} and result.success is None


def test_rule_pack_swap_keeps_public_interface(tmp_path):
    pack=tmp_path/"pack";pack.mkdir();(pack/"metadata.json").write_text('{"rule_system_id":"other","supported_action_categories":["movement"]}',encoding="utf-8")
    engine=ActionResolutionEngine(PACK)
    methods={name for name in ("load_rule_pack","classify","analyze_feasibility","build_rule_request","resolve_action") if hasattr(engine,name)}
    engine.load_rule_pack(pack)
    assert len(methods)==5 and engine.supported_categories=={"movement"}


def test_engine_source_contains_no_specific_story_names():
    source="\n".join(path.read_text(encoding="utf-8") for path in Path("action_resolution").glob("*.py"))
    assert not any(name in source for name in ("NPC_SENTINEL_123", "ADVENTURE_SENTINEL_456", "LOCATION_SENTINEL_789"))
