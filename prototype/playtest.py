from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from game_state import GameState


LOG_FILE = Path(__file__).with_name("playtest_log.txt")


def log_turn(
    state: GameState,
    action: str,
    judge_result: dict[str, Any],
    dice_result: dict[str, Any] | None,
    ai_response: str,
) -> None:
    entry = [
        "=" * 40,
        f"turn: {state.turn_count}",
        f"scene: {state.current_scene}",
        f"location: {state.current_location}",
        f"player_action: {action}",
        "judge_result:",
        json.dumps(judge_result, ensure_ascii=False, indent=2),
        "dice_result:",
        json.dumps(dice_result or {}, ensure_ascii=False, indent=2),
        "ai_response:",
        ai_response,
        "",
    ]
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write("\n".join(entry))
