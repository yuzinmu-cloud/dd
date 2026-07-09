from __future__ import annotations

from typing import Any

from game_state import GameState


DEFAULT_UPDATE = {
    "location_changed": False,
    "new_location": None,
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


def apply_structured_update(state: GameState, structured_update: dict[str, Any]) -> dict[str, Any]:
    update = _new_update()
    for key in update:
        if key in structured_update:
            update[key] = structured_update[key]

    _apply_update(state, update)
    return update


def apply_supplemental_state_update(
    state: GameState,
    action: str,
    judge_result: dict[str, Any],
    ai_response: str,
) -> dict[str, Any]:
    update = _new_update()
    combined_text = f"{action}\n{ai_response}"

    _collect_location_update(update, action)
    _collect_npc_updates(update, combined_text, action)
    _collect_clue_updates(update, combined_text)
    _collect_flag_updates(update, judge_result)
    _collect_ending_update(update, action, state.current_scene)

    _apply_update(state, update)
    return update


def merge_updates(primary: dict[str, Any], supplemental: dict[str, Any]) -> dict[str, Any]:
    merged = _new_update()
    for key in merged:
        primary_value = primary.get(key, merged[key])
        supplemental_value = supplemental.get(key, merged[key])
        if isinstance(merged[key], list):
            merged[key] = _merge_lists(primary_value, supplemental_value)
        elif key == "hp_delta":
            merged[key] = primary_value
        elif key == "ending":
            merged[key] = primary_value or supplemental_value
        else:
            merged[key] = primary_value if primary_value not in (None, False) else supplemental_value
    return merged


def apply_state_update(
    state: GameState,
    action: str,
    judge_result: dict[str, Any],
    dice_result: dict[str, Any] | None,
    ai_response: str,
) -> dict[str, Any]:
    update = _new_update()
    combined_text = f"{action}\n{ai_response}"

    _collect_location_update(update, action)
    _collect_npc_updates(update, combined_text, action)
    _collect_clue_updates(update, combined_text)
    _collect_flag_updates(update, judge_result)
    _collect_hp_update(update, judge_result, dice_result)
    _collect_ending_update(update, action, state.current_scene)
    _collect_notes(update, judge_result, dice_result)

    _apply_update(state, update)
    return update


def _new_update() -> dict[str, Any]:
    return {
        key: list(value) if isinstance(value, list) else value
        for key, value in DEFAULT_UPDATE.items()
    }


def _collect_location_update(update: dict[str, Any], action: str) -> None:
    scene_id = _scene_from_action(action)
    if scene_id:
        update["location_changed"] = True
        update["new_location"] = scene_id
        _add_flag(update, f"visited_{scene_id}")


def _scene_from_action(action: str) -> str | None:
    text = action.strip().lower()
    movement_words = ["前往", "到", "去", "進入", "走向", "移動", "返回", "回到", "離開", "探索", "抵達", "move", "go", "enter", "return"]
    if not _mentions_any(text, movement_words):
        return None

    if _mentions_any(text, ["最深處", "最深", "最後房間", "final chamber"]):
        return "final_chamber"
    if _mentions_any(text, ["礦坑入口", "坑口", "入口", "mine entrance"]):
        return "mine_entrance"
    if _mentions_any(text, ["礦坑深處", "坑道", "礦坑內", "更深", "mine interior"]):
        return "mine_interior"
    if _mentions_any(text, ["村莊廣場", "村子廣場", "廣場", "village square"]):
        return "village_square"
    if _mentions_any(text, ["酒館", "旅店", "inn"]):
        return "village_inn"
    return None


def _collect_npc_updates(update: dict[str, Any], text: str, action: str) -> None:
    if _mentions_any(text, ["瑪拉", "老闆娘", "酒館老闆"]):
        _add_memory(update, "瑪拉", f"玩家行動與瑪拉相關：{action}")
        if _mentions_any(text, ["問", "詢問", "調查", "檢查", "查看", "舊礦燈", "礦燈"]):
            _add_clue(update, "酒館線索：瑪拉曾把一盞舊礦燈交給失蹤礦工。")
            _add_flag(update, "mara_lantern_clue")

    if _mentions_any(text, ["奧倫", "村長"]):
        _add_memory(update, "奧倫", f"玩家行動與奧倫相關：{action}")
        _add_flag(update, "oren_contacted")

    if _mentions_any(text, ["莉娜", "妹妹", "失蹤礦工家屬", "家屬"]):
        _add_memory(update, "莉娜", f"玩家行動與莉娜相關：{action}")
        _add_flag(update, "lina_contacted")


def _collect_clue_updates(update: dict[str, Any], text: str) -> None:
    if _mentions_any(text, ["腳印", "靴印"]):
        _add_clue(update, "礦坑線索：新鮮腳印進入礦坑，卻沒有返回痕跡。")
        _add_flag(update, "footprint_clue")

    if _mentions_any(text, ["燭光", "奇異光", "微光"]):
        _add_clue(update, "礦坑線索：燭色微光似乎在引導闖入者。")
        _add_flag(update, "candlelight_clue")

    if _mentions_any(text, ["舊礦燈", "礦燈"]):
        _add_clue(update, "酒館線索：瑪拉曾把一盞舊礦燈交給失蹤礦工。")
        _add_flag(update, "mara_lantern_clue")


def _collect_flag_updates(update: dict[str, Any], judge_result: dict[str, Any]) -> None:
    action_type = judge_result.get("action_type")
    if action_type:
        _add_flag(update, f"last_action_{action_type}")
    if judge_result.get("is_possible") is False:
        _add_flag(update, "last_action_impossible")


def _collect_hp_update(
    update: dict[str, Any],
    judge_result: dict[str, Any],
    dice_result: dict[str, Any] | None,
) -> None:
    if not dice_result or dice_result.get("success") is not False:
        return

    action_type = judge_result.get("action_type")
    reason = str(judge_result.get("reason", ""))
    if action_type == "attack":
        update["hp_delta"] = -1
    elif action_type == "general" and _mentions_any(reason, ["危險", "風險"]):
        update["hp_delta"] = -1


def _collect_ending_update(update: dict[str, Any], action: str, current_scene: str) -> None:
    can_end = current_scene == "final_chamber" or _mentions_any(action, ["最深處", "最終", "最後房間", "final chamber"])
    if not can_end:
        return

    if _mentions_any(action, ["救援", "救出", "拯救", "放出失蹤", "救出失蹤", "救出礦工"]):
        update["ending"] = "rescue_focused"
        _add_objective(update, "objectives_completed", "救出失蹤礦工")
        _add_flag(update, "prioritized_rescue")

    if _mentions_any(action, ["揭露真相", "真相大白", "說出真相", "公開真相", "揭露"]):
        update["ending"] = "truth_revealing"
        _add_objective(update, "objectives_completed", "揭露燭芯礦坑真相")
        _add_flag(update, "prioritized_truth")

    if _mentions_any(action, ["決戰", "正面對抗", "擊退", "擊敗", "阻止威脅"]):
        update["ending"] = "confrontation_focused"
        _add_objective(update, "objectives_completed", "阻止礦坑威脅")
        _add_flag(update, "prioritized_confrontation")


def _collect_notes(
    update: dict[str, Any],
    judge_result: dict[str, Any],
    dice_result: dict[str, Any] | None,
) -> None:
    if judge_result.get("is_possible") is False:
        _add_note(update, str(judge_result.get("reason", "這個行動目前不可行。")))
    if dice_result and dice_result.get("success") is False:
        _add_note(update, "一次有風險的行動失敗了。")


def _apply_update(state: GameState, update: dict[str, Any]) -> None:
    if update["location_changed"] and update["new_location"]:
        state.move_to_scene(update["new_location"])

    for clue in update["clues_added"]:
        state.add_clue(clue)

    for flag in update["flags_added"]:
        state.set_flag(flag)

    for memory in update["npc_memories_added"]:
        state.remember_npc(memory["npc"], memory["memory"])

    for item in update["inventory_added"]:
        if item not in state.inventory:
            state.inventory.append(item)

    for item in update["inventory_removed"]:
        if item in state.inventory:
            state.inventory.remove(item)

    if update["hp_delta"]:
        state.hp = max(0, min(state.max_hp, state.hp + update["hp_delta"]))

    for objective in update["objectives_completed"]:
        state.complete_objective(objective)

    for objective in update["objectives_failed"]:
        state.fail_objective(objective)

    for note in update["notes_added"]:
        state.add_note(note)

    if state.hp <= 0:
        update["ending"] = "failure"
        _add_objective(update, "objectives_failed", "冒險者倒下，未能完成燭芯礦坑事件。")
        state.fail_objective("冒險者倒下，未能完成燭芯礦坑事件。")

    if update["ending"]:
        state.ending = update["ending"]
        state.ended = True


def _mentions_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _add_clue(update: dict[str, Any], clue: str) -> None:
    if clue not in update["clues_added"]:
        update["clues_added"].append(clue)


def _add_flag(update: dict[str, Any], flag: str) -> None:
    if flag not in update["flags_added"]:
        update["flags_added"].append(flag)


def _add_memory(update: dict[str, Any], npc: str, memory: str) -> None:
    item = {"npc": npc, "memory": memory}
    if item not in update["npc_memories_added"]:
        update["npc_memories_added"].append(item)


def _add_note(update: dict[str, Any], note: str) -> None:
    if note not in update["notes_added"]:
        update["notes_added"].append(note)


def _add_objective(update: dict[str, Any], key: str, objective: str) -> None:
    if objective not in update[key]:
        update[key].append(objective)


def _merge_lists(primary: list[Any], supplemental: list[Any]) -> list[Any]:
    merged: list[Any] = []
    for item in list(primary) + list(supplemental):
        if item not in merged:
            merged.append(item)
    return merged
