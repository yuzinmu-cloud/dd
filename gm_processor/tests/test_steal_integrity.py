from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import gm_processor.session_runner as session_runner
from gm_processor.mock_ai import MockAIProvider
from gm_processor.processor import process_turn
from gm_processor.schemas import (
    ActionInterpretation, DiceRequest, Resolution, Ruling, StateUpdate, TurnResult, validate_model,
)


SAMPLE = Path(__file__).resolve().parents[1] / "sample_data" / "gm_context.json"


def context_payload():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def run(text: str, client=None):
    return validate_model(TurnResult, process_turn(
        {"player_input": text, "context": context_payload(), "dice_result": None},
        ai_client=client or MockAIProvider(),
    ))


def test_steal_holder_without_object_requests_clarification():
    result = run("偷竊驛站看守")
    assert result.interpretation.raw_player_input == "偷竊驛站看守"
    assert result.interpretation.primary_intent == "steal"
    assert result.standard_action["action_category"] == "steal"
    assert result.standard_action["target"]["target_id"] == "npc-a-cen"
    assert result.standard_action["object"] is None
    assert result.resolution_status == "pending_clarification"
    assert "object" in [item["field"] for item in result.feasibility["missing_fields"]]
    assert result.state_update == StateUpdate()
    assert "偷走什麼" in result.narration


def test_sneaking_toward_npc_remains_stealth():
    result = run("我偷偷靠近驛站看守")
    assert result.interpretation.primary_intent == "stealth"
    assert result.standard_action["action_category"] == "stealth"


def test_steal_with_object_can_reach_check_flow():
    result = run("我偷走驛站看守腰間的鑰匙")
    assert result.interpretation.primary_intent == "steal"
    assert result.interpretation.target == "驛站看守"
    assert result.interpretation.object == "鑰匙"
    assert result.routed_rule == "skill_check"
    assert result.resolution_status == "pending_check_roll"


def test_take_own_item_is_not_steal():
    result = run("我從桌上拿起自己的水壺")
    assert result.interpretation.primary_intent == "inventory"
    assert result.standard_action["action_category"] == "inventory"


def test_model_stealth_is_normalized_for_explicit_theft():
    mock = MockAIProvider()

    def client(prompt, schema):
        if schema.get("title") == "ActionInterpretation":
            return json.dumps({
                "raw_player_input": "偷竊驛站看守", "primary_intent": "stealth", "secondary_intent": None,
                "target": None, "object": None, "method": "秘密接近", "player_goal": "取得物品",
                "hostility": False, "risk_level": "high", "ambiguity": None, "confidence": 0.8,
            }, ensure_ascii=False), None
        return mock(prompt, schema)

    result = run("偷竊驛站看守", client)
    assert result.interpretation.primary_intent == "steal"
    assert any("正規化為 steal" in warning for warning in result.warnings)
    assert not result.errors


def test_target_resolves_from_role_and_alias():
    role_result = run("偷竊驛站看守")
    alias_result = run("偷竊看守")
    assert role_result.standard_action["target"]["target_id"] == "npc-a-cen"
    assert alias_result.standard_action["target"]["target_id"] == "npc-a-cen"


def test_pending_clarification_does_not_increment_or_apply_state(monkeypatch):
    monkeypatch.setattr(session_runner, "process_turn", lambda payload: process_turn(payload, ai_client=MockAIProvider()))
    values = iter(["偷竊驛站看守", "exit"])
    original = context_payload()
    result = session_runner.run_session(deepcopy(original), lambda _request: next(values), lambda _event: None)
    assert result.turn_count == 0
    assert result.final_context.session.turn_number == original["session"]["turn_number"]
    assert result.final_context.character.current_hp == original["character"]["current_hp"]


def test_clarification_continues_same_action_and_preserves_target(monkeypatch):
    monkeypatch.setattr(session_runner, "process_turn", lambda payload: process_turn(payload, ai_client=MockAIProvider()))
    values = iter(["偷竊驛站看守", "偷走他腰間的鑰匙", "roll 14", "exit"])
    events = []
    result = session_runner.run_session(context_payload(), lambda _request: next(values), events.append)
    assert result.turn_count == 1
    assert result.final_context.session.turn_number == 1
    completed = result.turns[0]
    assert completed.interpretation.primary_intent == "steal"
    assert "看守" in (completed.interpretation.target or "")
    assert completed.interpretation.object == "鑰匙"
    assert result.final_context.history.player_decisions == [completed.interpretation.raw_player_input]


def test_failed_validation_does_not_increment_turn(monkeypatch):
    failed = TurnResult(
        interpretation=ActionInterpretation(primary_intent="unknown", confidence=0.0),
        ruling=Ruling(possible=False, reason="invalid", requires_roll=False, applicable_rules=[]),
        dice_request=DiceRequest(needed=False), resolution=Resolution(outcome="invalid", success=False, consequences=[]),
        state_update=StateUpdate(), narration="invalid", warnings=[], errors=["validation failed"],
        resolution_status="failed_validation",
    )
    monkeypatch.setattr(session_runner, "process_turn", lambda _payload: failed.model_dump())
    values = iter(["bad input", "exit"])
    result = session_runner.run_session(context_payload(), lambda _request: next(values), lambda _event: None)
    assert result.turn_count == 0 and result.final_context.session.turn_number == 0


def test_only_resolved_turn_increments(monkeypatch):
    resolved = TurnResult(
        interpretation=ActionInterpretation(raw_player_input="resolved", primary_intent="move", confidence=1.0),
        ruling=Ruling(possible=True, reason="ok", requires_roll=False, applicable_rules=[]),
        dice_request=DiceRequest(needed=False), resolution=Resolution(outcome="done", success=True, consequences=[]),
        state_update=StateUpdate(), narration="完成。", warnings=[], errors=[], resolution_status="resolved",
    )
    monkeypatch.setattr(session_runner, "process_turn", lambda _payload: resolved.model_dump())
    values = iter(["resolved", "exit"])
    result = session_runner.run_session(context_payload(), lambda _request: next(values), lambda _event: None)
    assert result.turn_count == 1 and result.final_context.session.turn_number == 1
