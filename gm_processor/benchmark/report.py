from __future__ import annotations

import json
from pathlib import Path
from typing import Any


THRESHOLDS = {
    "overall_score": 80.0,
    "schema_valid": 100.0,
    "no_crash": 100.0,
    "player_agency_preserved": 95.0,
    "hidden_fact_protected": 95.0,
    "dice_respected": 95.0,
    "no_rule_invention": 90.0,
}


def acceptance(summary: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if summary["overall_score"] < THRESHOLDS["overall_score"]:
        failures.append("Overall Score < 80")
    for metric, threshold in THRESHOLDS.items():
        if metric == "overall_score":
            continue
        if summary.get("metric_scores", {}).get(metric, 0.0) < threshold:
            failures.append(f"{metric} < {threshold:g}%")
    for category, score in summary.get("category_scores", {}).items():
        if score < 70.0:
            failures.append(f"category {category} < 70%")
    return not failures, failures


def write_reports(report_data: dict[str, Any], output_base: Path) -> tuple[Path, Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_base.with_suffix(".json")
    markdown_path = output_base.with_suffix(".md")
    json_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = report_data["summary"]
    passed, failures = acceptance(summary)
    lines = [
        "# GM Benchmark Report",
        "",
        f"- Provider: {report_data['provider']}",
        f"- Model: {report_data['model']}",
        f"- Execution time: {report_data['execution_seconds']} seconds",
        f"- Total cases: {summary['total_cases']}",
        f"- Overall score: {summary['overall_score']}",
        f"- v0.1 threshold: {'PASS' if passed else 'FAIL'}",
        "",
        "## Category Scores",
        "",
    ]
    lines.extend(f"- {name}: {score}" for name, score in summary["category_scores"].items())
    lines.extend(["", "## Metric Scores", ""])
    lines.extend(f"- {name}: {score}" for name, score in summary["metric_scores"].items())
    if failures:
        lines.extend(["", "## Failed Thresholds", ""])
        lines.extend(f"- {failure}" for failure in failures)
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path
