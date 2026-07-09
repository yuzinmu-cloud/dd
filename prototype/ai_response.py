from __future__ import annotations

import json
from typing import Any


NARRATION_MARKER = "===NARRATION==="
STATE_UPDATE_MARKER = "===STATE_UPDATE_JSON==="

STRING_LIST_FIELDS = {
    "clues_added",
    "flags_added",
    "inventory_added",
    "inventory_removed",
    "objectives_completed",
    "objectives_failed",
    "notes_added",
}
ALLOWED_FIELDS = STRING_LIST_FIELDS | {"npc_memories_added", "hp_delta", "ending"}
ALLOWED_ENDINGS = {None, "rescue_focused", "truth_revealing", "confrontation_focused", "failure"}

DEFAULT_STRUCTURED_UPDATE = {
    "clues_added": [],
    "flags_added": [],
    "npc_memories_added": [],
    "inventory_added": [],
    "inventory_removed": [],
    "hp_delta": 0,
    "objectives_completed": [],
    "objectives_failed": [],
    "ending": None,
    "notes_added": [],
}


def parse_ai_response(raw_response: str) -> dict[str, Any]:
    narration, json_text, parse_errors = split_ai_response(raw_response)
    validation = validate_structured_update_json(json_text) if json_text is not None else _invalid_result(parse_errors)

    return {
        "raw_response": raw_response,
        "narration": narration,
        "structured_update": validation["structured_update"],
        "is_valid": validation["is_valid"],
        "errors": parse_errors + validation["errors"],
    }


def split_ai_response(raw_response: str) -> tuple[str, str | None, list[str]]:
    if STATE_UPDATE_MARKER not in raw_response:
        narration = raw_response.replace(NARRATION_MARKER, "").strip()
        return narration, None, ["missing_state_update_marker"]

    before_json, after_json = raw_response.split(STATE_UPDATE_MARKER, 1)
    narration = before_json.replace(NARRATION_MARKER, "").strip()
    json_text = _strip_markdown_fence(after_json.strip())

    errors: list[str] = []
    if not narration:
        errors.append("empty_narration")
    if not json_text:
        errors.append("empty_state_update_json")

    return narration, json_text or None, errors


def validate_structured_update_json(json_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as error:
        return _invalid_result([f"invalid_json:{error.msg}"])

    return validate_structured_update(payload)


def validate_structured_update(payload: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return _invalid_result(["structured_update_must_be_object"])

    unknown_fields = sorted(set(payload) - ALLOWED_FIELDS)
    if unknown_fields:
        errors.append(f"unknown_fields:{','.join(unknown_fields)}")

    normalized = _default_update()
    for field in STRING_LIST_FIELDS:
        value = payload.get(field, [])
        if not _is_string_list(value):
            errors.append(f"{field}_must_be_string_list")
        else:
            normalized[field] = list(value)

    npc_memories = payload.get("npc_memories_added", [])
    if not _is_npc_memory_list(npc_memories):
        errors.append("npc_memories_added_must_be_npc_memory_list")
    else:
        normalized["npc_memories_added"] = [dict(item) for item in npc_memories]

    hp_delta = payload.get("hp_delta", 0)
    if not _is_plain_int(hp_delta):
        errors.append("hp_delta_must_be_integer")
    else:
        normalized["hp_delta"] = hp_delta

    ending = payload.get("ending", None)
    if ending not in ALLOWED_ENDINGS:
        errors.append("ending_is_not_allowed")
    else:
        normalized["ending"] = ending

    return {
        "structured_update": normalized,
        "is_valid": not errors,
        "errors": errors,
    }


def _default_update() -> dict[str, Any]:
    return {
        key: list(value) if isinstance(value, list) else value
        for key, value in DEFAULT_STRUCTURED_UPDATE.items()
    }


def _invalid_result(errors: list[str]) -> dict[str, Any]:
    return {
        "structured_update": _default_update(),
        "is_valid": False,
        "errors": errors,
    }


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_npc_memory_list(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    for item in value:
        if not isinstance(item, dict):
            return False
        if set(item) != {"npc", "memory"}:
            return False
        if not isinstance(item["npc"], str) or not isinstance(item["memory"], str):
            return False
    return True


def _is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _strip_markdown_fence(text: str) -> str:
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text
