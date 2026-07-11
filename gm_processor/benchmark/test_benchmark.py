from __future__ import annotations

import json
from pathlib import Path

from gm_processor.benchmark import benchmark_runner
from gm_processor.benchmark.acceptance_sessions import run_acceptance_sessions
from gm_processor.benchmark.evaluator import STATUSES, aggregate, evaluate_case
from gm_processor.benchmark.report import write_reports
from gm_processor.mock_ai import MockAIProvider
from gm_processor.schemas import (
    ActionInterpretation, DiceRequest, Resolution, Ruling, StateUpdate, TurnResult,
)


def safe_result(errors=None):
    result = TurnResult(
        interpretation=ActionInterpretation(primary_intent="uncertain", confidence=0.0),
        ruling=Ruling(possible=False, reason="safe", requires_roll=False, applicable_rules=[]),
        dice_request=DiceRequest(needed=False),
        resolution=Resolution(outcome="safe", success=False, consequences=[]),
        state_update=StateUpdate(),
        narration="安全結束。",
        warnings=[],
        errors=errors or [],
    )
    return result.model_dump() if hasattr(result, "model_dump") else result.dict()


def test_case_format_and_counts():
    cases = benchmark_runner.load_cases()
    assert len(cases) >= 30
    counts = {}
    for case in cases:
        assert benchmark_runner.REQUIRED_CASE_FIELDS.issubset(case)
        counts[case["category"]] = counts.get(case["category"], 0) + 1
    assert set(counts) == set(benchmark_runner.CATEGORIES)
    assert all(count >= 6 for count in counts.values())


def test_evaluator_supports_all_statuses():
    case = {
        "case_id": "T", "category": "safety", "required_expectations": {"possible": True},
        "optional_dice_result": None, "_resolved_context": {"rules": {"available_checks": []}},
    }
    evaluation = evaluate_case(case, safe_result())
    statuses = {item["status"] for item in evaluation["checks"].values()}
    assert statuses.issubset(STATUSES)
    assert "pass" in statuses and "fail" in statuses and "not_applicable" in statuses


def test_single_case_crash_does_not_stop_runner(monkeypatch):
    cases = benchmark_runner.load_cases()[:2]
    monkeypatch.setattr(benchmark_runner, "load_cases", lambda _category=None: cases)
    calls = {"count": 0}

    def flaky(_payload, ai_client=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("single failure")
        return safe_result()

    monkeypatch.setattr(benchmark_runner, "process_turn", flaky)
    report = benchmark_runner.run_benchmark(write_output=False)
    assert report["summary"]["total_cases"] == 2
    assert len(report["summary"]["error_cases"]) == 1


def test_mock_provider_normal_response():
    raw, error = MockAIProvider()("Input:\n{\"player_input\": \"調查\"}", {"title": "ActionInterpretation"})
    assert error is None
    assert json.loads(raw)["primary_intent"] == "investigate"


def test_mock_provider_invalid_output():
    raw, error = MockAIProvider("invalid_json")("prompt", {"title": "Anything"})
    assert raw == "not-json" and error is None


def test_mock_provider_connection_and_model_errors():
    assert "timeout" in MockAIProvider("timeout")("prompt", {})[1]
    assert "model error" in MockAIProvider("model_error")("prompt", {})[1]


def test_report_generation_and_hidden_fact_protection(tmp_path):
    evaluation = evaluate_case(
        {"case_id": "T", "category": "safety", "required_expectations": {}, "optional_dice_result": None,
         "_resolved_context": {"rules": {"available_checks": []}, "adventure": {"hidden_gm_facts": ["SECRET"]}}},
        safe_result(),
    )
    data = {"provider": "mock", "model": "test", "execution_seconds": 0.1, "summary": aggregate([evaluation]), "evaluations": [evaluation]}
    json_path, md_path = write_reports(data, tmp_path / "report")
    assert json_path.exists() and md_path.exists()
    assert "SECRET" not in json_path.read_text(encoding="utf-8")
    assert "SECRET" not in md_path.read_text(encoding="utf-8")


def test_mock_benchmark_meets_v01_threshold():
    report = benchmark_runner.run_benchmark(context_mode="mock", write_output=False)
    assert report["summary"]["total_cases"] >= 30
    assert report["summary"]["overall_score"] >= 80


def test_ollama_mode_safe_when_provider_unavailable(monkeypatch):
    monkeypatch.setattr(benchmark_runner, "process_turn", lambda _payload: safe_result(["Ollama unavailable"]))
    report = benchmark_runner.run_benchmark(category="safety", context_mode="ollama", write_output=False)
    assert report["summary"]["total_cases"] == 6
    assert report["summary"]["metric_scores"]["no_crash"] == 100.0


def test_two_v01_acceptance_sessions_complete_five_turns():
    summaries = run_acceptance_sessions()
    assert set(summaries) == {"fantasy", "non_fantasy"}
    assert all(item["turn_count"] == 5 for item in summaries.values())
    assert all(item["pending_dice_events"] >= 1 for item in summaries.values())
    assert summaries["fantasy"]["world_name"] != summaries["non_fantasy"]["world_name"]
