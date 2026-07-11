from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from gm_processor.ai_provider import AIProvider
from gm_processor.dice_interface import DiceInterface
from gm_processor.narrator import Narrator
from gm_processor.processor import process_turn
from gm_processor.schemas import (
    ActionInterpretation,
    DiceRequest,
    Resolution,
    Ruling,
    StateUpdate,
    TurnInput,
    TurnResult,
    validate_model,
)
from gm_processor.state_update_builder import StateUpdateBuilder
from gm_processor.validator import Validator


BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLE_DIR = BASE_DIR / "sample_data"


def read_json(filename: str) -> dict:
    return json.loads((SAMPLE_DIR / filename).read_text(encoding="utf-8"))


def load_turn_input() -> dict:
    world_state = read_json("world_state.json")
    return {
        "player_input": "我調查後門旁的濕泥腳印",
        "rule_system": read_json("rule_system.json"),
        "character": read_json("character.json"),
        "situation": read_json("situation.json"),
        "world_state": world_state,
        "recent_events": world_state["recent_events"],
    }


def component_ai_client(_prompt: str, schema: dict) -> tuple[str, None]:
    title = schema.get("title")
    payloads = {
        "ActionInterpretation": {
            "primary_intent": "investigate",
            "secondary_intent": None,
            "target": "後門旁的濕泥腳印",
            "object": "腳印",
            "method": "觀察",
            "player_goal": "找出線索",
            "ambiguity": None,
            "confidence": 0.9,
        },
        "JudgeOutput": {
            "ruling": {
                "possible": True,
                "reason": "目前資訊允許調查。",
                "requires_roll": False,
                "roll_type": None,
                "difficulty": None,
                "applicable_rules": ["investigation"],
            },
            "dice_request": {
                "needed": False,
                "dice": None,
                "modifier_source": None,
                "difficulty": None,
                "reason": None,
            },
        },
        "Resolution": {
            "outcome": "角色確認腳印朝碼頭方向延伸。",
            "success": True,
            "consequences": ["取得腳印方向"],
            "proposed_updates": {"clue_changes": {"add": ["腳印通往碼頭"]}},
        },
        "NarrationResult": {"narration": "你仔細查看泥地，確認腳印一路朝碼頭方向延伸。"},
    }
    return json.dumps(payloads[title], ensure_ascii=False), None


def test_process_turn_only_delegates_to_orchestrator(monkeypatch):
    import gm_processor.processor as processor

    calls = []
    orchestrated_result = validate_model(TurnResult, process_turn(load_turn_input(), ai_client=component_ai_client))

    class FakeOrchestrator:
        def __init__(self, ai_client=None):
            calls.append(("init", ai_client))

        def process(self, payload):
            calls.append(("process", payload))
            return orchestrated_result

    expected = {"input": "value"}
    monkeypatch.setattr(processor, "TurnOrchestrator", FakeOrchestrator)
    result = processor.process_turn(expected)
    assert calls[1] == ("process", expected)
    assert validate_model(TurnResult, result)


@pytest.mark.parametrize(
    "module",
    [
        "orchestrator",
        "interpreter",
        "judge",
        "dice_interface",
        "resolver",
        "state_update_builder",
        "narrator",
        "validator",
        "ai_provider",
    ],
)
def test_each_component_imports(module):
    assert importlib.import_module(f"gm_processor.{module}")


def test_turn_input_and_result_match_schemas():
    assert validate_model(TurnInput, load_turn_input())
    result = process_turn(load_turn_input(), ai_client=component_ai_client)
    parsed = validate_model(TurnResult, result)
    assert parsed.ruling.possible is True
    assert parsed.state_update.clue_changes == {"add": ["腳印通往碼頭"]}
    assert not parsed.errors


def test_missing_required_input_returns_safe_error():
    payload = load_turn_input()
    payload.pop("player_input")
    parsed = validate_model(TurnResult, process_turn(payload, ai_client=component_ai_client))
    assert parsed.errors
    assert parsed.ruling.possible is False


def test_ollama_connection_failure_does_not_crash():
    def failing_client(_prompt, _schema):
        return None, "無法連接本機 AI。"

    parsed = validate_model(TurnResult, process_turn(load_turn_input(), ai_client=failing_client))
    assert any("無法連接本機 AI" in error for error in parsed.errors)


def test_dice_interface_never_rolls_automatically():
    request = DiceRequest(needed=True, dice="d20")
    result, warnings, errors = DiceInterface().get_result(request)
    assert result.status == "pending"
    assert warnings
    assert not errors


def test_narrator_does_not_receive_hidden_gm_facts():
    captured = {}

    def client(prompt, _schema):
        captured["prompt"] = prompt
        return json.dumps({"narration": "你看見門邊留下新的腳印。"}, ensure_ascii=False), None

    narrator = Narrator(AIProvider(client), Validator())
    result, _, errors = narrator.narrate(
        ActionInterpretation(primary_intent="investigate", confidence=1.0),
        Ruling(possible=True, reason="可調查", requires_roll=False, applicable_rules=[]),
        Resolution(outcome="看見腳印", success=True, consequences=[]),
        StateUpdate(),
        {"adventure_context": {"visible": "門", "Hidden GM Facts": ["兇手是管家"]}},
    )
    assert result is not None
    assert not errors
    assert "兇手是管家" not in captured["prompt"]
    assert "Hidden GM Facts" not in captured["prompt"]


def test_state_update_builder_only_uses_resolution_updates():
    resolution = Resolution(
        outcome="發現線索",
        success=True,
        consequences=[],
        proposed_updates={"clue_changes": {"add": ["泥腳印"]}},
    )
    update, warnings, errors = StateUpdateBuilder().build(
        resolution, {"world_context": {"unrelated": "不可複製"}}
    )
    assert update.clue_changes == {"add": ["泥腳印"]}
    assert update.world_changes == {}
    assert not warnings
    assert not errors


def test_processor_has_no_specific_adventure_name():
    source = (BASE_DIR / "processor.py").read_text(encoding="utf-8")
    assert not any(name in source for name in ["燭芯", "礦坑事件", "Candlewick"])


def test_gm_processor_does_not_depend_on_prototype():
    sources = "\n".join(path.read_text(encoding="utf-8") for path in BASE_DIR.glob("*.py"))
    assert "prototype" not in sources.lower()
