from __future__ import annotations

import json
from pathlib import Path

from gm_processor.processor import process_turn
from gm_processor.schemas import TurnInput, TurnResult, validate_model


BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLE_DIR = BASE_DIR / "sample_data"


def load_turn_input() -> dict:
    return {
        "player_input": "我調查後門旁的濕泥腳印",
        "rule_system": read_json("rule_system.json"),
        "character": read_json("character.json"),
        "situation": read_json("situation.json"),
        "world_state": read_json("world_state.json"),
        "recent_events": read_json("world_state.json")["recent_events"],
    }


def read_json(filename: str) -> dict:
    return json.loads((SAMPLE_DIR / filename).read_text(encoding="utf-8"))


def valid_ai_payload() -> dict:
    return {
        "interpretation": {
            "primary_intent": "investigate",
            "secondary_intent": None,
            "target": "後門旁的濕泥腳印",
            "object": "腳印",
            "method": "觀察與比對",
            "player_goal": "找出貨箱去向",
            "ambiguity": None,
            "confidence": 0.86,
        },
        "ruling": {
            "possible": True,
            "reason": "角色在現場且具備調查能力。",
            "requires_roll": True,
            "roll_type": "mind",
            "difficulty": "normal",
            "applicable_rules": ["uncertain", "mind"],
        },
        "dice_request": {
            "needed": True,
            "dice": "d20",
            "modifier_source": "character.abilities.mind",
            "difficulty": "normal",
            "reason": "腳印可能被雨水破壞。",
        },
        "resolution": {
            "outcome": "等待檢定結果後描述發現。",
            "success": None,
            "consequences": [],
        },
        "state_update": {
            "player_changes": {},
            "npc_changes": {},
            "world_changes": {},
            "inventory_changes": {},
            "clue_changes": {"pending": ["後門濕泥腳印"]},
            "location_changes": {},
            "event_changes": {"pending_roll": True},
        },
        "narration": "你蹲下查看濕泥腳印。雨水沖淡了邊緣，但仍能看出它通往碼頭方向。這可能需要一次 mind 檢定。",
        "warnings": [],
        "errors": [],
    }


def fake_ai_client(_prompt, _schema):
    return json.dumps(valid_ai_payload(), ensure_ascii=False), None


def test_turn_input_parses():
    parsed = validate_model(TurnInput, load_turn_input())
    assert parsed.player_input == "我調查後門旁的濕泥腳印"


def test_turn_result_matches_schema():
    result = process_turn(load_turn_input(), ai_client=fake_ai_client)
    parsed = validate_model(TurnResult, result)
    assert parsed.ruling.possible is True
    assert parsed.dice_request.needed is True


def test_missing_required_field_returns_safe_error():
    payload = load_turn_input()
    payload.pop("player_input")
    result = process_turn(payload, ai_client=fake_ai_client)
    parsed = validate_model(TurnResult, result)
    assert parsed.errors
    assert parsed.ruling.possible is False


def test_ollama_connection_failure_does_not_crash():
    def failing_ai_client(_prompt, _schema):
        return None, "無法連接本機 AI。請確認 Ollama 已啟動，並已安裝模型。"

    result = process_turn(load_turn_input(), ai_client=failing_ai_client)
    parsed = validate_model(TurnResult, result)
    assert parsed.errors
    assert "無法連接本機 AI" in parsed.errors[0]


def test_schema_extra_fields_are_rejected_safely():
    payload = valid_ai_payload()
    payload["unexpected"] = "not allowed"

    def extra_field_ai_client(_prompt, _schema):
        return json.dumps(payload, ensure_ascii=False), None

    result = process_turn(load_turn_input(), ai_client=extra_field_ai_client)
    parsed = validate_model(TurnResult, result)
    assert parsed.errors
    assert parsed.ruling.possible is False


def test_processor_has_no_specific_adventure_dependency():
    processor_source = (BASE_DIR / "processor.py").read_text(encoding="utf-8")
    prompt_source = (BASE_DIR / "gm_prompt.md").read_text(encoding="utf-8")
    forbidden_names = ["燭芯", "礦坑事件", "Candlewick"]
    combined = processor_source + prompt_source
    assert not any(name in combined for name in forbidden_names)


def test_non_json_ai_output_returns_safe_error():
    def bad_ai_client(_prompt, _schema):
        return "這不是 JSON", None

    result = process_turn(load_turn_input(), ai_client=bad_ai_client)
    parsed = validate_model(TurnResult, result)
    assert parsed.errors
