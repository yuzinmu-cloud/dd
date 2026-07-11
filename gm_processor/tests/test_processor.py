from __future__ import annotations

import importlib
import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from gm_processor.ai_provider import AIProvider
from gm_processor.dice_interface import DiceInterface
from gm_processor.interpreter import Interpreter
from gm_processor.judge import Judge
from gm_processor.narrator import Narrator
from gm_processor.processor import process_turn
from gm_processor.resolver import Resolver
from gm_processor.schemas import (
    ActionInterpretation,
    DiceRequest,
    DiceResult,
    GMContext,
    Resolution,
    Ruling,
    StateUpdate,
    TurnInput,
    TurnResult,
    model_to_dict,
    validate_model,
)
from gm_processor.state_update_builder import StateUpdateBuilder
from gm_processor.validator import Validator


BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLE_DIR = BASE_DIR / "sample_data"


def read_json(filename: str) -> dict:
    return json.loads((SAMPLE_DIR / filename).read_text(encoding="utf-8"))


def load_context(filename: str = "gm_context.json") -> dict:
    return read_json(filename)


def load_turn_input(filename: str = "gm_context.json") -> dict:
    return {"player_input": "我調查目前的異常。", "context": load_context(filename), "dice_result": None}


def component_ai_client(_prompt: str, schema: dict) -> tuple[str, None]:
    payloads = {
        "ActionInterpretation": {
            "primary_intent": "investigate",
            "secondary_intent": None,
            "target": "目前異常",
            "object": None,
            "method": "觀察與診斷",
            "player_goal": "找出原因",
            "ambiguity": None,
            "confidence": 0.9,
        },
        "JudgeOutput": {
            "ruling": {
                "possible": True,
                "reason": "Context 提供足夠資訊。",
                "requires_roll": False,
                "roll_type": None,
                "difficulty": None,
                "applicable_rules": ["routine investigation"],
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
            "outcome": "角色確認一項可見線索。",
            "success": True,
            "consequences": ["取得公開線索"],
            "proposed_updates": {"clue_changes": {"add": ["公開線索"]}},
        },
        "NarrationResult": {"narration": "你仔細檢查現場，確認了一項可見線索。"},
    }
    return json.dumps(payloads[schema["title"]], ensure_ascii=False), None


def test_complete_gm_context_validates():
    context = validate_model(GMContext, load_context())
    assert context.context_version == "1.0"
    assert context.world.world_name == "霧河諸境"


@pytest.mark.parametrize("missing", ["rules", "character", "adventure"])
def test_missing_required_context_fails(missing):
    payload = load_context()
    payload.pop(missing)
    with pytest.raises(ValidationError):
        validate_model(GMContext, payload)
    result = validate_model(
        TurnResult,
        process_turn({"player_input": "測試", "context": payload, "dice_result": None}, ai_client=component_ai_client),
    )
    assert result.errors


def test_current_hp_cannot_exceed_max_hp():
    payload = load_turn_input()
    payload["context"]["character"]["current_hp"] = 11
    payload["context"]["character"]["max_hp"] = 10
    result = validate_model(TurnResult, process_turn(payload, ai_client=component_ai_client))
    assert any("current_hp" in error for error in result.errors)


def test_turn_number_cannot_be_negative():
    payload = load_turn_input()
    payload["context"]["session"]["turn_number"] = -1
    result = validate_model(TurnResult, process_turn(payload, ai_client=component_ai_client))
    assert any("turn_number" in error for error in result.errors)


def test_hidden_facts_cannot_also_be_player_known():
    payload = load_turn_input()
    secret = payload["context"]["adventure"]["hidden_gm_facts"][0]
    payload["context"]["adventure"]["known_clues"].append(secret)
    result = validate_model(TurnResult, process_turn(payload, ai_client=component_ai_client))
    assert any("hidden_gm_facts" in error for error in result.errors)


def test_turn_input_only_accepts_unified_context_format():
    fields = set(TurnInput.model_fields if hasattr(TurnInput, "model_fields") else TurnInput.__fields__)
    assert fields == {"player_input", "context", "dice_result"}
    legacy = {
        "player_input": "測試",
        "rule_system": {},
        "character": {},
        "situation": {},
        "world_state": {},
        "recent_events": [],
    }
    with pytest.raises(ValidationError):
        validate_model(TurnInput, legacy)


@pytest.mark.parametrize(
    ("component", "method"),
    [(Interpreter, "interpret"), (Judge, "judge"), (Resolver, "resolve"), (StateUpdateBuilder, "build"), (Narrator, "narrate")],
)
def test_context_consuming_components_require_gm_context(component, method):
    annotation = inspect.signature(getattr(component, method)).parameters["context" if component is not StateUpdateBuilder else "_context"].annotation
    assert "GMContext" in str(annotation)


def test_components_do_not_read_sample_data_directly():
    component_files = [
        "orchestrator.py", "interpreter.py", "judge.py", "dice_interface.py", "resolver.py",
        "state_update_builder.py", "narrator.py", "validator.py", "ai_provider.py", "processor.py",
    ]
    combined = "\n".join((BASE_DIR / name).read_text(encoding="utf-8") for name in component_files)
    assert "sample_data" not in combined
    assert "prototype" not in combined.lower()


def test_hidden_facts_are_not_available_to_narration():
    captured = {}

    def client(prompt, _schema):
        captured["prompt"] = prompt
        return json.dumps({"narration": "你只看見公開可觀察的線索。"}, ensure_ascii=False), None

    context = validate_model(GMContext, load_context())
    hidden_values = list(context.adventure.hidden_gm_facts)
    hidden_values.extend(fact for npc in context.adventure.relevant_npcs for fact in npc.hidden_facts)
    result, _, errors = Narrator(AIProvider(client), Validator()).narrate(
        ActionInterpretation(primary_intent="investigate", confidence=1.0),
        Ruling(possible=True, reason="可以觀察", requires_roll=False, applicable_rules=[]),
        Resolution(outcome="看見公開線索", success=True, consequences=[]),
        StateUpdate(),
        context,
    )
    assert result is not None and not errors
    assert all(secret not in captured["prompt"] for secret in hidden_values)
    assert all(secret not in result.narration for secret in hidden_values)


def test_alternate_context_validates_and_processes():
    context = validate_model(GMContext, load_context("gm_context_alt.json"))
    assert context.world.world_name == "赫利俄斯航域"
    result = validate_model(TurnResult, process_turn(load_turn_input("gm_context_alt.json"), ai_client=component_ai_client))
    assert not result.errors


def test_changing_context_does_not_require_processor_changes():
    primary = validate_model(TurnResult, process_turn(load_turn_input(), ai_client=component_ai_client))
    alternate = validate_model(TurnResult, process_turn(load_turn_input("gm_context_alt.json"), ai_client=component_ai_client))
    assert primary.narration == alternate.narration
    processor_source = (BASE_DIR / "processor.py").read_text(encoding="utf-8")
    assert "霧河諸境" not in processor_source
    assert "赫利俄斯航域" not in processor_source


def test_process_turn_does_not_mutate_context():
    payload = load_turn_input()
    original = deepcopy(payload["context"])
    process_turn(payload, ai_client=component_ai_client)
    assert payload["context"] == original


def test_ollama_failure_returns_legal_turn_result():
    def failing_client(_prompt, _schema):
        return None, "無法連接本機 AI。"

    result = validate_model(TurnResult, process_turn(load_turn_input(), ai_client=failing_client))
    assert result.errors
    assert result.narration


def test_dice_interface_requires_validated_external_result():
    request = DiceRequest(needed=True, dice="d20")
    pending, warnings, errors = DiceInterface().get_result(request)
    assert pending.status == "pending" and warnings and not errors
    provided = DiceResult(status="provided", total=14, raw={"total": 14})
    result, warnings, errors = DiceInterface().get_result(request, provided)
    assert result.total == 14 and not warnings and not errors


def test_state_update_builder_only_uses_resolution_updates():
    context = validate_model(GMContext, load_context())
    resolution = Resolution(
        outcome="發現線索", success=True, consequences=[],
        proposed_updates={"clue_changes": {"add": ["泥腳印"]}},
    )
    update, warnings, errors = StateUpdateBuilder().build(resolution, context)
    assert update.clue_changes == {"add": ["泥腳印"]}
    assert update.world_changes == {}
    assert not warnings and not errors


@pytest.mark.parametrize(
    "module",
    ["orchestrator", "interpreter", "judge", "dice_interface", "resolver", "state_update_builder", "narrator", "validator", "ai_provider"],
)
def test_each_component_imports(module):
    assert importlib.import_module(f"gm_processor.{module}")


def test_process_turn_only_delegates_to_orchestrator(monkeypatch):
    import gm_processor.processor as processor

    expected = validate_model(TurnResult, process_turn(load_turn_input(), ai_client=component_ai_client))
    calls = []

    class FakeOrchestrator:
        def __init__(self, ai_client=None):
            calls.append("init")

        def process(self, payload):
            calls.append(payload)
            return expected

    monkeypatch.setattr(processor, "TurnOrchestrator", FakeOrchestrator)
    payload = load_turn_input()
    assert validate_model(TurnResult, processor.process_turn(payload))
    assert calls == ["init", payload]


def test_gm_processor_does_not_depend_on_prototype():
    sources = "\n".join(path.read_text(encoding="utf-8") for path in BASE_DIR.glob("*.py"))
    assert "prototype" not in sources.lower()
