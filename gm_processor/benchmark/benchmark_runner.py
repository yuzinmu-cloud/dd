from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from gm_processor.local_ai import get_local_model
from gm_processor.mock_ai import MockAIProvider
from gm_processor.processor import process_turn
from gm_processor.schemas import GMContext, TurnResult, model_to_dict, validate_model

from .evaluator import aggregate, evaluate_case
from .report import acceptance, write_reports


BASE_DIR = Path(__file__).resolve().parent
CASES_DIR = BASE_DIR / "cases"
REPORTS_DIR = BASE_DIR / "reports"
CATEGORIES = ("interpretation", "rule_judgment", "creative_actions", "consistency", "safety")
REQUIRED_CASE_FIELDS = {
    "case_id", "category", "gm_context", "player_input", "optional_dice_result",
    "required_expectations", "forbidden_results", "notes",
}


def load_cases(category: str | None = None) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(CASES_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"{path.name} 必須是案例陣列。")
        for case in payload:
            missing = REQUIRED_CASE_FIELDS - set(case)
            if missing:
                raise ValueError(f"{case.get('case_id', path.name)} 缺少欄位：{sorted(missing)}")
            if case["category"] not in CATEGORIES:
                raise ValueError(f"未知分類：{case['category']}")
            if category is None or case["category"] == category:
                cases.append(case)
    return cases


def run_benchmark(category: str | None = None, context_mode: str = "mock", write_output: bool = True) -> dict[str, Any]:
    started = time.perf_counter()
    evaluations: list[dict[str, Any]] = []
    for source_case in load_cases(category):
        case = dict(source_case)
        crashed = False
        result: dict[str, Any] | None = None
        try:
            context_path = Path("gm_processor/sample_data") / case["gm_context"]
            context = validate_model(GMContext, json.loads(context_path.read_text(encoding="utf-8")))
            case["_resolved_context"] = model_to_dict(context)
            turn_input = {
                "player_input": case["player_input"],
                "context": model_to_dict(context),
                "dice_result": case["optional_dice_result"],
            }
            if context_mode == "mock":
                failure_mode = _failure_mode(case.get("notes", ""))
                result = process_turn(turn_input, ai_client=MockAIProvider(failure_mode))
            else:
                result = process_turn(turn_input)
            result = model_to_dict(validate_model(TurnResult, result))
        except Exception:
            crashed = True
        evaluations.append(evaluate_case(case, result, crashed))

    summary = aggregate(evaluations)
    provider = "MockAIProvider" if context_mode == "mock" else "Ollama"
    model = "deterministic-v1" if context_mode == "mock" else get_local_model()
    report_data = {
        "provider": provider,
        "model": model,
        "python_version": platform.python_version(),
        "execution_seconds": round(time.perf_counter() - started, 3),
        "summary": summary,
        "evaluations": evaluations,
    }
    if write_output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path, md_path = write_reports(report_data, REPORTS_DIR / f"benchmark_{context_mode}_{timestamp}")
        report_data["report_files"] = [str(json_path), str(md_path)]
    return report_data


def _failure_mode(notes: str) -> str | None:
    for mode in ("invalid_json", "timeout", "model_error"):
        if f"simulate:{mode}" in notes:
            return mode
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AIGMOS GM benchmark.")
    parser.add_argument("--category", choices=CATEGORIES)
    parser.add_argument("--context-mode", choices=("mock", "ollama"), default="mock")
    args = parser.parse_args()
    report_data = run_benchmark(args.category, args.context_mode)
    passed, failures = acceptance(report_data["summary"])
    print(json.dumps(report_data["summary"], ensure_ascii=False, indent=2))
    print(f"Provider: {report_data['provider']} / {report_data['model']}")
    print(f"v0.1 threshold: {'PASS' if passed else 'FAIL'}")
    if args.context_mode == "ollama" and report_data["summary"]["metric_scores"].get("schema_valid", 0) == 100:
        error_cases = len(report_data["summary"]["failed_cases"])
        if error_cases:
            print("Ollama 可能未啟動或輸出未達預期；Benchmark 已安全完成，請查看報告。")
    if failures:
        print("Failed thresholds:", "; ".join(failures))


if __name__ == "__main__":
    main()
