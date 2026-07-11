from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

import gm_processor.session_runner as session_runner
from gm_processor.schemas import (
    ActionInterpretation,
    DiceRequest,
    Resolution,
    Ruling,
    StateUpdate,
    TurnResult,
    validate_model,
    GMContext,
)
from gm_processor.session_log import write_turn_log
from gm_processor.state_update_applier import apply_state_update


BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLE_DIR = BASE_DIR / "sample_data"


def load_context(name: str = "gm_context.json") -> GMContext:
    return validate_model(GMContext, json.loads((SAMPLE_DIR / name).read_text(encoding="utf-8")))


def input_provider(*values: str):
    items = iter(values)
    return lambda _request: next(items)


def turn_result(
    *,
    outcome: str = "完成行動",
    state_update: StateUpdate | None = None,
    pending: bool = False,
    errors: list[str] | None = None,
    consequences: list[str] | None = None,
) -> dict:
    result = TurnResult(
        interpretation=ActionInterpretation(primary_intent="act", confidence=1.0),
        ruling=Ruling(
            possible=True,
            reason="測試裁定",
            requires_roll=pending,
            roll_type="mind" if pending else None,
            difficulty="normal" if pending else None,
            applicable_rules=[],
        ),
        dice_request=DiceRequest(
            needed=pending,
            dice="d20" if pending else None,
            difficulty="normal" if pending else None,
        ),
        resolution=Resolution(
            outcome="等待外部骰子結果。" if pending else outcome,
            success=None if pending else True,
            consequences=consequences or [],
        ),
        state_update=state_update or StateUpdate(),
        narration="等待骰子。" if pending else "行動完成。",
        warnings=[],
        errors=errors or [],
    )
    return result.model_dump() if hasattr(result, "model_dump") else result.dict()


def test_session_processes_ten_continuous_turns(monkeypatch):
    monkeypatch.setattr(session_runner, "process_turn", lambda _payload: turn_result())
    context = load_context()
    result = session_runner.run_session(
        context,
        input_provider(*[f"行動 {number}" for number in range(10)], "exit"),
        lambda _event: None,
    )
    assert result.turn_count == 10
    assert result.final_context.session.turn_number == context.session.turn_number + 10
    assert result.session_status == "completed"


def test_pending_dice_does_not_advance_until_roll(monkeypatch):
    calls: list[dict] = []

    def fake_process(payload):
        calls.append(deepcopy(payload))
        return turn_result(pending=payload["dice_result"] is None)

    events: list[dict] = []
    monkeypatch.setattr(session_runner, "process_turn", fake_process)
    context = load_context()
    result = session_runner.run_session(
        context,
        input_provider("我冒險跳過裂縫", "wrong", "roll 14", "exit"),
        events.append,
    )
    assert len(calls) == 2
    assert calls[0]["dice_result"] is None
    assert calls[1]["dice_result"]["total"] == 14
    assert result.turn_count == 1
    assert result.final_context.session.turn_number == context.session.turn_number + 1
    assert result.final_context.history.player_decisions.count("我冒險跳過裂縫") == 1
    assert any(event["type"] == "warning" for event in events)


def test_state_update_is_visible_to_next_turn(monkeypatch):
    seen_locations: list[str] = []

    def fake_process(payload):
        seen_locations.append(payload["context"]["world"]["current_location"])
        update = StateUpdate(location_changes={"current_location": "碼頭"}) if len(seen_locations) == 1 else StateUpdate()
        return turn_result(state_update=update)

    monkeypatch.setattr(session_runner, "process_turn", fake_process)
    result = session_runner.run_session(load_context(), input_provider("前往碼頭", "觀察四周", "exit"), lambda _event: None)
    assert seen_locations == ["河岸驛站", "碼頭"]
    assert result.final_context.world.current_location == "碼頭"


@pytest.mark.parametrize("hp", [-1, 11])
def test_hp_update_outside_bounds_rolls_back(hp):
    context = load_context()
    updated, errors = apply_state_update(context, StateUpdate(player_changes={"current_hp": hp}))
    assert errors
    assert updated == context


def test_missing_inventory_item_cannot_be_removed():
    context = load_context()
    updated, errors = apply_state_update(context, StateUpdate(inventory_changes={"remove": ["不存在物品"]}))
    assert errors
    assert updated.character.inventory == context.character.inventory


def test_npc_attitude_can_be_updated_without_mutating_original():
    context = load_context()
    npc_id = context.adventure.relevant_npcs[0].npc_id
    updated, errors = apply_state_update(context, StateUpdate(npc_changes={npc_id: {"attitude": "信任"}}))
    assert not errors
    assert updated.adventure.relevant_npcs[0].attitude == "信任"
    assert context.adventure.relevant_npcs[0].attitude != "信任"


def test_location_changes_update_current_location():
    updated, errors = apply_state_update(load_context(), StateUpdate(location_changes={"current_location": "河邊碼頭"}))
    assert not errors
    assert updated.world.current_location == "河邊碼頭"


def test_known_clues_add_without_duplicates():
    context = load_context()
    clue = "後門旁有濕泥腳印。"
    updated, errors = apply_state_update(context, StateUpdate(clue_changes={"add": [clue, "藍漆碎片"]}))
    assert not errors
    assert updated.adventure.known_clues.count(clue) == 1
    assert updated.adventure.known_clues.count("藍漆碎片") == 1


def test_history_and_conversation_limits(monkeypatch):
    context = load_context()
    data = context.model_dump() if hasattr(context, "model_dump") else context.dict()
    data["history"]["recent_events"] = [f"事件 {n}" for n in range(20)]
    data["history"]["player_decisions"] = [f"決定 {n}" for n in range(30)]
    data["history"]["unresolved_consequences"] = [f"後果 {n}" for n in range(20)]
    data["session"]["recent_conversation"] = [{"speaker": "x", "text": str(n)} for n in range(12)]
    context = validate_model(GMContext, data)
    monkeypatch.setattr(
        session_runner,
        "process_turn",
        lambda _payload: turn_result(outcome="最新事件", consequences=["最新未解後果"]),
    )
    result = session_runner.run_session(context, input_provider("最新決定", "exit"), lambda _event: None)
    assert len(result.final_context.history.recent_events) == 20
    assert result.final_context.history.recent_events[-1] == "最新事件"
    assert len(result.final_context.history.player_decisions) == 30
    assert len(result.final_context.history.unresolved_consequences) == 20
    assert result.final_context.history.unresolved_consequences[-1] == "最新未解後果"
    assert len(result.final_context.session.recent_conversation) == 12
    assert result.final_context.session.recent_conversation[-1]["speaker"] == "gm"


def test_process_turn_stub_is_stateless_across_sessions(monkeypatch):
    monkeypatch.setattr(session_runner, "process_turn", lambda _payload: turn_result())
    context = load_context()
    first = session_runner.run_session(context, input_provider("行動一", "exit"), lambda _event: None)
    second = session_runner.run_session(context, input_provider("行動二", "exit"), lambda _event: None)
    assert first.final_context.session.turn_number == second.final_context.session.turn_number
    assert context.session.turn_number == 0


def test_original_context_file_is_not_modified(monkeypatch):
    path = SAMPLE_DIR / "gm_context.json"
    before = path.read_bytes()
    monkeypatch.setattr(session_runner, "process_turn", lambda _payload: turn_result())
    session_runner.run_session(load_context(), input_provider("行動", "exit"), lambda _event: None)
    assert path.read_bytes() == before


def test_two_contexts_start_independent_sessions(monkeypatch):
    monkeypatch.setattr(session_runner, "process_turn", lambda _payload: turn_result())
    first = session_runner.run_session(load_context(), input_provider("行動", "exit"), lambda _event: None)
    second = session_runner.run_session(load_context("gm_context_alt.json"), input_provider("行動", "exit"), lambda _event: None)
    assert first.final_context.world.world_name == "霧河諸境"
    assert second.final_context.world.world_name == "赫利俄斯航域"
    assert first.final_context.session.session_id != second.final_context.session.session_id


def test_ollama_error_does_not_crash_session(monkeypatch):
    monkeypatch.setattr(session_runner, "process_turn", lambda _payload: turn_result(errors=["無法連接本機 AI。"] ))
    result = session_runner.run_session(load_context(), input_provider("行動", "exit"), lambda _event: None)
    assert result.turn_count == 1
    assert any("無法連接本機 AI" in error for error in result.errors)


def test_exit_command_ends_session_without_turn(monkeypatch):
    monkeypatch.setattr(session_runner, "process_turn", lambda _payload: pytest.fail("不應呼叫 process_turn"))
    result = session_runner.run_session(load_context(), input_provider("離開"), lambda _event: None)
    assert result.turn_count == 0
    assert result.session_status == "completed"


def test_log_does_not_contain_hidden_facts(tmp_path):
    context = load_context()
    hidden = context.adventure.hidden_gm_facts[0]
    event = {
        "context": context.model_dump() if hasattr(context, "model_dump") else context.dict(),
        "player_input": "調查",
        "dice_result": None,
        "result": turn_result(),
    }
    event["result"]["state_update"]["world_changes"] = {
        "hidden_gm_facts": [hidden],
        "api_key": "do-not-log-this",
    }
    assert write_turn_log(tmp_path, event) is None
    content = next(tmp_path.glob("*.jsonl")).read_text(encoding="utf-8")
    assert "hidden_gm_facts" not in content
    assert hidden not in content
    assert "hidden_gm_facts" not in content
    assert "api_key" not in content
    assert "do-not-log-this" not in content


def test_gm_processor_still_does_not_depend_on_prototype():
    sources = "\n".join(path.read_text(encoding="utf-8") for path in BASE_DIR.glob("*.py"))
    assert "prototype" not in sources.lower()
