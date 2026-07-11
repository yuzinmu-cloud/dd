from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gm_processor.session_runner as session_runner
from gm_processor.mock_ai import MockAIProvider
from gm_processor.processor import process_turn
from gm_processor.schemas import GMContext, validate_model


SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data"


SCENARIOS = {
    "fantasy": {
        "context": "gm_context.json",
        "inputs": [
            "我檢查後門旁的腳印",
            "我嘗試跳過危險的濕滑木板",
            "roll 14",
            "我利用油燈斜光創意地尋找痕跡",
            "資訊不足，我詢問未知的船班規則",
            "我詢問阿岑最後看見貨箱的時間",
            "exit",
        ],
    },
    "non_fantasy": {
        "context": "gm_context_alt.json",
        "inputs": [
            "我診斷外環感測器",
            "我嘗試破解危險的備援匯流排",
            "roll 15",
            "我利用診斷平板創意地比較時間差",
            "資訊不足，我檢查未知協定",
            "我詢問伊沃能量峰值的時間",
            "exit",
        ],
    },
}


def run_acceptance_sessions() -> dict[str, Any]:
    original_process_turn = session_runner.process_turn
    session_runner.process_turn = lambda payload: process_turn(payload, ai_client=MockAIProvider())
    summaries: dict[str, Any] = {}
    try:
        for name, scenario in SCENARIOS.items():
            context = validate_model(
                GMContext,
                json.loads((SAMPLE_DIR / scenario["context"]).read_text(encoding="utf-8")),
            )
            values = iter(scenario["inputs"])
            events: list[dict[str, Any]] = []
            result = session_runner.run_session(context, lambda _request: next(values), events.append)
            summaries[name] = {
                "world_name": result.final_context.world.world_name,
                "character_name": result.final_context.character.name,
                "adventure_title": result.final_context.adventure.title,
                "turn_count": result.turn_count,
                "final_turn_number": result.final_context.session.turn_number,
                "session_status": result.session_status,
                "pending_dice_events": sum(
                    event.get("type") == "turn_result" and event.get("pending", False) for event in events
                ),
                "errors": result.errors,
            }
    finally:
        session_runner.process_turn = original_process_turn
    return summaries


def main() -> None:
    print(json.dumps(run_acceptance_sessions(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
