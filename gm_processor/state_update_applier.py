from __future__ import annotations

from copy import deepcopy
from typing import Any

try:
    from .schemas import GMContext, StateUpdate, model_to_dict, validate_model
    from .validator import Validator
except ImportError:
    from schemas import GMContext, StateUpdate, model_to_dict, validate_model
    from validator import Validator


CHARACTER_FIELDS = {"current_hp", "conditions", "inventory", "equipment", "attributes", "skills"}
NPC_FIELDS = {"attitude", "current_state", "known_facts", "goals"}
WORLD_FIELDS = {"time", "weather", "known_world_facts", "active_world_states"}
SESSION_FIELDS = {"current_phase", "initiative"}


def apply_state_update(context: GMContext, state_update: StateUpdate) -> tuple[GMContext, list[str]]:
    """Apply explicit changes to a copy; on any error return the original context."""
    original = context
    data = deepcopy(model_to_dict(context))
    update = model_to_dict(state_update)
    errors: list[str] = []

    _apply_character(data["character"], update["player_changes"], update["inventory_changes"], errors)
    _apply_npcs(data["adventure"]["relevant_npcs"], update["npc_changes"], errors)
    _apply_world(data["world"], update["world_changes"], update["location_changes"], errors)
    _apply_adventure(data["adventure"], update["clue_changes"], update["event_changes"], errors)
    _apply_session(data["session"], update["session_changes"], errors)

    if errors:
        return original, errors
    try:
        updated = validate_model(GMContext, data)
    except Exception as error:
        return original, [f"State Update 套用後 Context 驗證失敗：{error}"]
    context_errors = Validator._context_errors(updated)
    if context_errors:
        return original, context_errors
    return updated, []


def context_update_diff(before: GMContext, after: GMContext) -> dict[str, Any]:
    before_data = model_to_dict(before)
    after_data = model_to_dict(after)
    before_clues = before_data["adventure"]["known_clues"]
    after_clues = after_data["adventure"]["known_clues"]
    return {
        "added_clues": [clue for clue in after_clues if clue not in before_clues],
        "location_before": before_data["world"]["current_location"],
        "location_after": after_data["world"]["current_location"],
        "hp_before": before_data["character"]["current_hp"],
        "hp_after": after_data["character"]["current_hp"],
        "active_events_before": before_data["adventure"]["active_events"],
        "active_events_after": after_data["adventure"]["active_events"],
    }


def _reject_unknown(changes: dict[str, Any], allowed: set[str], label: str, errors: list[str]) -> None:
    for field in sorted(set(changes) - allowed):
        errors.append(f"{label} 不允許更新欄位：{field}")


def _apply_character(character: dict[str, Any], changes: dict[str, Any], inventory_changes: dict[str, Any], errors: list[str]) -> None:
    _reject_unknown(changes, CHARACTER_FIELDS, "Character", errors)
    for field in CHARACTER_FIELDS.intersection(changes):
        character[field] = deepcopy(changes[field])
    if "current_hp" in changes:
        hp = changes["current_hp"]
        maximum = character.get("max_hp")
        if not isinstance(hp, int) or isinstance(hp, bool) or hp < 0 or (maximum is not None and hp > maximum):
            errors.append("current_hp 必須介於 0 與 max_hp 之間。")
    _apply_list_delta(character["inventory"], inventory_changes, "Inventory", errors)


def _apply_npcs(npcs: list[dict[str, Any]], changes: dict[str, Any], errors: list[str]) -> None:
    by_id = {npc["npc_id"]: npc for npc in npcs}
    for npc_id, npc_changes in changes.items():
        if npc_id not in by_id:
            errors.append(f"不得新增 Adventure 中不存在的 NPC：{npc_id}")
            continue
        if not isinstance(npc_changes, dict):
            errors.append(f"NPC {npc_id} 更新必須是 object。")
            continue
        _reject_unknown(npc_changes, NPC_FIELDS, f"NPC {npc_id}", errors)
        npc = by_id[npc_id]
        for field in NPC_FIELDS.intersection(npc_changes):
            value = npc_changes[field]
            if field in {"known_facts", "goals"} and isinstance(value, dict):
                _apply_list_delta(npc[field], value, f"NPC {npc_id} {field}", errors)
            else:
                npc[field] = deepcopy(value)


def _apply_world(world: dict[str, Any], changes: dict[str, Any], location_changes: dict[str, Any], errors: list[str]) -> None:
    allowed = WORLD_FIELDS | {"invalidated_world_facts"}
    _reject_unknown(changes, allowed, "World", errors)
    for field in WORLD_FIELDS.intersection(changes):
        value = changes[field]
        if field == "known_world_facts":
            if not isinstance(value, dict):
                errors.append("known_world_facts 必須使用 add/remove 明確更新；刪除請使用 invalidated_world_facts。")
            else:
                if value.get("remove"):
                    errors.append("世界事實不可直接移除；請使用 invalidated_world_facts。")
                _apply_list_delta(world[field], {"add": value.get("add", [])}, "World known facts", errors)
        else:
            world[field] = deepcopy(value)
    invalidated = changes.get("invalidated_world_facts", [])
    if not isinstance(invalidated, list):
        errors.append("invalidated_world_facts 必須是 list。")
    else:
        for fact in invalidated:
            if fact not in world["known_world_facts"]:
                errors.append(f"無法失效不存在的世界事實：{fact}")
            else:
                world["known_world_facts"].remove(fact)
    _reject_unknown(location_changes, {"current_location"}, "Location", errors)
    if "current_location" in location_changes:
        world["current_location"] = location_changes["current_location"]


def _apply_adventure(adventure: dict[str, Any], clue_changes: dict[str, Any], event_changes: dict[str, Any], errors: list[str]) -> None:
    _apply_list_delta(adventure["known_clues"], clue_changes, "Known clues", errors)
    allowed = {"add", "remove", "active_objectives", "current_situation"}
    _reject_unknown(event_changes, allowed, "Event", errors)
    _apply_list_delta(adventure["active_events"], {k: v for k, v in event_changes.items() if k in {"add", "remove"}}, "Active events", errors)
    if "active_objectives" in event_changes:
        adventure["active_objectives"] = deepcopy(event_changes["active_objectives"])
    if "current_situation" in event_changes:
        adventure["current_situation"] = event_changes["current_situation"]


def _apply_session(session: dict[str, Any], changes: dict[str, Any], errors: list[str]) -> None:
    _reject_unknown(changes, SESSION_FIELDS, "Session", errors)
    for field in SESSION_FIELDS.intersection(changes):
        session[field] = deepcopy(changes[field])


def _apply_list_delta(target: list[Any], changes: dict[str, Any], label: str, errors: list[str]) -> None:
    if not changes:
        return
    if not isinstance(changes, dict):
        errors.append(f"{label} 更新必須是 object。")
        return
    _reject_unknown(changes, {"add", "remove"}, label, errors)
    additions = changes.get("add", [])
    removals = changes.get("remove", [])
    if not isinstance(additions, list) or not isinstance(removals, list):
        errors.append(f"{label} add/remove 必須是 list。")
        return
    for item in removals:
        if item not in target:
            errors.append(f"{label} 無法移除不存在的項目：{item}")
        else:
            target.remove(item)
    for item in additions:
        if item not in target:
            target.append(deepcopy(item))
