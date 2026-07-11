from __future__ import annotations

import json
from pathlib import Path

from gm_processor.ai_provider import AIProvider
from gm_processor.mock_ai import MockAIProvider
from gm_processor.interpreter import Interpreter
from gm_processor.narrator import Narrator
from gm_processor.processor import process_turn
from gm_processor.schemas import (
    ActionInterpretation, GMContext, Resolution, Ruling, StateUpdate, TurnResult, validate_model,
)
from gm_processor.state_update_applier import apply_state_update, context_update_diff
from gm_processor.state_update_builder import StateUpdateBuilder
from gm_processor.validator import Validator


SAMPLE = Path(__file__).resolve().parents[1] / "sample_data" / "gm_context.json"


def context() -> GMContext:
    return validate_model(GMContext, json.loads(SAMPLE.read_text(encoding="utf-8")))


def run(player_input: str) -> TurnResult:
    payload = {"player_input": player_input, "context": json.loads(SAMPLE.read_text(encoding="utf-8")), "dice_result": None}
    return validate_model(TurnResult, process_turn(payload, ai_client=MockAIProvider()))


def test_attack_input_preserves_hostile_action_and_target():
    result = run("試圖殺死看守")
    assert result.interpretation.raw_player_input == "試圖殺死看守"
    assert result.interpretation.primary_intent in {"attack", "hostile_action"}
    assert "看守" in (result.interpretation.target or "")
    assert result.interpretation.hostility is True
    assert result.dice_request.needed is True
    assert result.resolution.success is None
    assert "看守" in result.narration and "攻擊" in result.narration
    assert "調查腳印" not in result.narration


def test_investigation_input_stays_investigation():
    result = run("我調查後門的腳印")
    assert result.interpretation.primary_intent in {"investigation", "investigate"}
    assert "腳印" in result.interpretation.raw_player_input
    assert result.interpretation.hostility is False


def test_ask_input_targets_guard_and_is_not_attack():
    result = run("我詢問看守貨箱的去向")
    assert result.interpretation.primary_intent in {"ask", "social"}
    assert "看守" in (result.interpretation.target or "")
    assert result.interpretation.primary_intent != "attack"


def test_steal_input_preserves_target_and_object():
    result = run("我偷走看守腰間的鑰匙")
    assert result.interpretation.primary_intent == "steal"
    assert "看守" in (result.interpretation.target or "")
    assert result.interpretation.object == "鑰匙"


def test_attack_misclassified_as_investigation_stops_pipeline():
    calls = []

    def wrong_client(_prompt, schema):
        calls.append(schema["title"])
        return json.dumps({
            "raw_player_input": "試圖殺死看守",
            "primary_intent": "investigation",
            "secondary_intent": None,
            "target": "腳印",
            "object": "腳印",
            "method": "觀察",
            "player_goal": "調查腳印",
            "hostility": False,
            "ambiguity": None,
            "confidence": 0.9,
        }, ensure_ascii=False), None

    payload = {"player_input": "試圖殺死看守", "context": json.loads(SAMPLE.read_text(encoding="utf-8")), "dice_result": None}
    result = validate_model(TurnResult, process_turn(payload, ai_client=wrong_client))
    assert calls == ["ActionInterpretation"]
    assert any("Interpretation 與玩家輸入衝突" in error for error in result.errors)
    assert "調查腳印" not in result.narration


def test_attack_intent_alias_is_normalized_without_losing_raw_input():
    def client(_prompt, _schema):
        return json.dumps({
            "raw_player_input": "試圖殺死看守", "primary_intent": "kill", "secondary_intent": None,
            "target": None, "object": None, "method": "攻擊", "player_goal": "殺死看守",
            "hostility": False, "ambiguity": None, "confidence": 0.9,
        }, ensure_ascii=False), None

    result, _, errors = Interpreter(AIProvider(client), Validator()).interpret("試圖殺死看守", context())
    assert not errors
    assert result is not None
    assert result.raw_player_input == "試圖殺死看守"
    assert result.primary_intent == "attack"
    assert result.hostility is True
    assert "看守" in (result.target or "")


def test_narrator_rejects_player_agency_phrases():
    def client(_prompt, _schema):
        return json.dumps({"narration": "玩家決定離開，下一回合將前往碼頭，事件暫告一段落。"}, ensure_ascii=False), None

    result, _, errors = Narrator(AIProvider(client), Validator()).narrate(
        ActionInterpretation(raw_player_input="我查看門", primary_intent="investigation", confidence=1.0),
        Ruling(possible=True, reason="可行", requires_roll=False, applicable_rules=[]),
        Resolution(outcome="看見門", success=True, consequences=[]),
        StateUpdate(),
        context(),
    )
    assert result is None
    assert errors


def test_empty_state_update_has_no_added_clues():
    original = context()
    updated, errors = apply_state_update(original, StateUpdate())
    assert not errors
    assert context_update_diff(original, updated)["added_clues"] == []


def test_clue_diff_contains_only_current_turn_additions():
    original = context()
    updated, errors = apply_state_update(original, StateUpdate(clue_changes={"add": ["本回合新線索"]}))
    assert not errors
    assert context_update_diff(original, updated)["added_clues"] == ["本回合新線索"]


def test_pending_resolution_cannot_create_state_update():
    update, _, errors = StateUpdateBuilder().build(
        Resolution(
            outcome="等待外部骰子結果。", success=None, consequences=[],
            proposed_updates={"clue_changes": {"add": ["不應新增"]}},
        ),
        context(),
    )
    assert update == StateUpdate()
    assert errors
