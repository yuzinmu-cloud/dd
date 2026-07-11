from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REDACTED_KEYS = {
    "hidden_gm_facts",
    "hidden_facts",
    "api_key",
    "apikey",
    "authorization",
    "password",
    "secret",
    "token",
}


def write_turn_log(log_directory: Path, event: dict[str, Any]) -> str | None:
    """Append a public turn summary. Logging errors are returned, never raised."""
    try:
        result = event.get("result", {})
        context = event.get("context", {})
        session = context.get("session", {})
        world = context.get("world", {})
        adventure = context.get("adventure", {})
        character = context.get("character", {})
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session.get("session_id"),
            "turn_number": session.get("turn_number"),
            "player_input": _redact(event.get("player_input")),
            "interpretation": _redact(result.get("interpretation")),
            "ruling": _redact(result.get("ruling")),
            "dice_result": _redact(event.get("dice_result")),
            "resolution": _redact(result.get("resolution")),
            "state_update": _redact(result.get("state_update")),
            "narration": _redact(result.get("narration")),
            "warnings": _redact(result.get("warnings", [])),
            "errors": _redact(result.get("errors", [])),
            "context_summary": {
                "world_name": world.get("world_name"),
                "current_location": world.get("current_location"),
                "adventure_title": adventure.get("title"),
                "character_name": character.get("name"),
            },
        }
        log_directory.mkdir(parents=True, exist_ok=True)
        safe_session_id = "".join(ch for ch in str(session.get("session_id") or "session") if ch.isalnum() or ch in "-_")
        path = log_directory / f"{safe_session_id}.jsonl"
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return None
    except Exception as error:
        return f"Session logging 失敗：{error}"


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _redact(item)
            for key, item in value.items()
            if key.lower().replace("-", "_").replace(" ", "_") not in REDACTED_KEYS
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value
