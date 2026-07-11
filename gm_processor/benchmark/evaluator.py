from __future__ import annotations

from typing import Any


STATUSES = {"pass", "fail", "not_applicable"}


def evaluate_case(case: dict[str, Any], result: dict[str, Any] | None, crashed: bool = False) -> dict[str, Any]:
    expectations = case.get("required_expectations", {})
    checks: dict[str, dict[str, str]] = {}

    def check(name: str, applicable: bool, passed: bool, reason: str) -> None:
        checks[name] = {
            "status": "not_applicable" if not applicable else ("pass" if passed else "fail"),
            "reason": reason,
        }

    schema_valid = isinstance(result, dict) and not crashed
    check("schema_valid", True, schema_valid, "TurnResult Schema 可驗證。" if schema_valid else "沒有合法 TurnResult。")
    interpretation = (result or {}).get("interpretation", {})
    expected_intent = expectations.get("expected_primary_intent")
    check("interpretation_correct", expected_intent is not None, interpretation.get("primary_intent") == expected_intent, "比較 primary intent。")
    ruling = (result or {}).get("ruling", {})
    ruling_expected = "possible" in expectations or "requires_roll" in expectations
    ruling_ok = (
        ("possible" not in expectations or ruling.get("possible") == expectations["possible"])
        and ("requires_roll" not in expectations or ruling.get("requires_roll") == expectations["requires_roll"])
        and ("expected_roll_type" not in expectations or ruling.get("roll_type") == expectations["expected_roll_type"])
    )
    check("ruling_correct", ruling_expected, ruling_ok, "比較 possible、requires_roll 與 roll type。")
    supplied_dice = case.get("optional_dice_result")
    resolution = (result or {}).get("resolution", {})
    supplied_total = supplied_dice.get("total") if isinstance(supplied_dice, dict) else None
    rule_values = ((result or {}).get("rule_result") or {}).get("values", {})
    dice_ok = (
        supplied_dice is None
        or resolution.get("success") is not None
        or (supplied_total is not None and rule_values.get("natural_roll") == supplied_total)
    )
    check("dice_respected", supplied_dice is not None, dice_ok, "提供骰子時 Resolution 必須完成。")
    required_fields = expectations.get("required_state_update_fields", [])
    state_update = (result or {}).get("state_update", {})
    check("state_update_valid", bool(required_fields), all(field in state_update for field in required_fields), "檢查必要 State Update 欄位。")
    narration = str((result or {}).get("narration", ""))
    language_required = expectations.get("narration_language")
    narration_ok = bool(narration) and (language_required != "zh-TW" or any("\u4e00" <= ch <= "\u9fff" for ch in narration))
    check("narration_consistent", language_required is not None, narration_ok, "Narration 存在且符合語言需求。")
    hidden = _hidden_facts(case.get("_resolved_context", {}))
    check("hidden_fact_protected", True, all(fact not in narration for fact in hidden), "Narration 不得包含 hidden facts。")
    agency_phrases = ("你決定", "你感到", "你必須", "你接著會")
    check("player_agency_preserved", True, not any(phrase in narration for phrase in agency_phrases), "Narration 不控制玩家思想或下一步。")
    available = set(case.get("_resolved_context", {}).get("rules", {}).get("available_checks", []))
    applied = set(ruling.get("applicable_rules", []))
    check("no_rule_invention", True, applied.issubset(available), "裁定規則必須來自 Rule Context。")
    expects_signal = "expected_warning" in expectations or "expected_error" in expectations
    signal_ok = (
        (not expectations.get("expected_warning") or bool((result or {}).get("warnings")))
        and (not expectations.get("expected_error") or bool((result or {}).get("errors")))
    )
    check("expected_signal", expects_signal, signal_ok, "資訊不足或 provider failure 必須產生預期 warning/error。")
    check("no_crash", True, not crashed, "單一案例不得崩潰。")

    applicable = [item for item in checks.values() if item["status"] != "not_applicable"]
    score = 100.0 * sum(item["status"] == "pass" for item in applicable) / len(applicable) if applicable else 0.0
    return {"case_id": case["case_id"], "category": case["category"], "score": round(score, 2), "checks": checks}


def aggregate(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    categories: dict[str, list[float]] = {}
    metric_values: dict[str, list[bool]] = {}
    for evaluation in evaluations:
        categories.setdefault(evaluation["category"], []).append(evaluation["score"])
        for name, item in evaluation["checks"].items():
            if item["status"] != "not_applicable":
                metric_values.setdefault(name, []).append(item["status"] == "pass")
    overall = sum(item["score"] for item in evaluations) / len(evaluations) if evaluations else 0.0
    passed = [item["case_id"] for item in evaluations if item["score"] == 100.0]
    failed = [item["case_id"] for item in evaluations if item["score"] < 100.0]
    return {
        "overall_score": round(overall, 2),
        "category_scores": {name: round(sum(scores) / len(scores), 2) for name, scores in categories.items()},
        "metric_scores": {name: round(100.0 * sum(values) / len(values), 2) for name, values in metric_values.items()},
        "passed_cases": passed,
        "failed_cases": failed,
        "error_cases": [item["case_id"] for item in evaluations if item["checks"]["no_crash"]["status"] == "fail"],
        "total_cases": len(evaluations),
    }


def _hidden_facts(context: dict[str, Any]) -> list[str]:
    adventure = context.get("adventure", {})
    facts = list(adventure.get("hidden_gm_facts", []))
    for npc in adventure.get("relevant_npcs", []):
        facts.extend(npc.get("hidden_facts", []))
    return facts
