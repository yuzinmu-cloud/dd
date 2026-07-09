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
    state_update: dict[str, Any],
    raw_ai_response: str | None = None,
    parsed_response: dict[str, Any] | None = None,
    fallback_used: bool | None = None,
) -> None:
    parsed_response = parsed_response or {}
    raw_ai_response = raw_ai_response if raw_ai_response is not None else ai_response
    fallback_used = bool(fallback_used)

    entry = [
        "=" * 40,
        f"turn: {state.turn_count}",
        f"scene: {state.current_scene}",
        f"location: {state.current_location}",
        f"current_hp: {state.hp}/{state.max_hp}",
        f"player_action: {action}",
        f"fallback_used: {json.dumps(fallback_used, ensure_ascii=False)}",
        "judge_result:",
        json.dumps(judge_result, ensure_ascii=False, indent=2),
        "dice_result:",
        json.dumps(dice_result or {}, ensure_ascii=False, indent=2),
        "ai_raw_response:",
        raw_ai_response,
        "parsed_narration:",
        str(parsed_response.get("narration", ai_response)),
        "parsed_structured_update:",
        json.dumps(parsed_response.get("structured_update", {}), ensure_ascii=False, indent=2),
        "parsed_errors:",
        json.dumps(parsed_response.get("errors", []), ensure_ascii=False, indent=2),
        "state_update:",
        json.dumps(state_update, ensure_ascii=False, indent=2),
        "final_game_state_summary:",
        json.dumps(_game_state_summary(state), ensure_ascii=False, indent=2),
        "known_clues_after_update:",
        json.dumps(state.known_clues, ensure_ascii=False, indent=2),
        "world_flags_after_update:",
        json.dumps(state.world_flags, ensure_ascii=False, indent=2),
        "ai_response_visible:",
        ai_response,
        "",
    ]
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write("\n".join(entry))


def _game_state_summary(state: GameState) -> dict[str, Any]:
    return {
        "player_name": state.player_name,
        "hp": state.hp,
        "max_hp": state.max_hp,
        "scene": state.current_scene,
        "location": state.current_location,
        "turn_count": state.turn_count,
        "ended": state.ended,
        "ending": state.ending,
        "inventory": list(state.inventory),
        "known_clues": list(state.known_clues),
        "npc_memory": dict(state.npc_memory),
        "world_flags": dict(state.world_flags),
        "completed_objectives": list(state.completed_objectives),
        "failed_objectives": list(state.failed_objectives),
        "recent_actions": state.action_log[-5:],
    }
