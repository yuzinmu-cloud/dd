from __future__ import annotations

import json
from pathlib import Path

from adventure import HELP_TEXT, OPENING_NARRATION, describe_current_scene, handle_action, status_text
from ai_gm import ask_ai_gm
from ai_response import parse_ai_response
from dice import format_check_result, resolve_check
from game_state import GameState
from judge import evaluate_action
from playtest import log_turn
from state_update import apply_structured_update


SAVE_FILE = Path(__file__).with_name("save_game.json")

HELP_COMMANDS = {"help", "幫助"}
STATUS_COMMANDS = {"status", "狀態"}
SAVE_COMMANDS = {"save", "存檔"}
LOAD_COMMANDS = {"load", "讀檔"}
QUIT_COMMANDS = {"quit", "exit", "離開"}
YES_COMMANDS = {"y", "yes", "是", "好", "讀取"}
FALLBACK_MOVEMENT_WORDS = {
    "酒館", "inn", "廣場", "square", "礦坑", "礦坑入口", "入口", "entrance",
    "礦坑深處", "坑道", "interior", "最深處", "final chamber", "前往", "進入", "離開",
}
FALLBACK_ENDING_WORDS = {
    "救援", "救出", "拯救", "真相", "揭露", "決戰", "對抗", "攻擊", "阻止",
}


def main() -> None:
    print("AIGMOS Demo v0.6")
    print("輸入「幫助」查看可用指令。輸入「離開」結束冒險。")
    print()

    state = choose_start_state()

    if state.turn_count == 0 and not state.ended:
        print(OPENING_NARRATION)
        print()
        print(describe_current_scene(state))
    else:
        print("已成功讀取存檔。")
        print(describe_current_scene(state) if not state.ended else "這段冒險已經抵達結局。")

    while True:
        print()
        action = input("你要怎麼做？ > ").strip()

        if not action:
            print("遊戲主持人靜靜等待你說出下一步行動。")
            continue

        command = action.lower()

        if command in QUIT_COMMANDS:
            print("冒險結束，期待再次見到你。")
            break

        if command in HELP_COMMANDS:
            print(HELP_TEXT)
            continue

        if command in STATUS_COMMANDS:
            print(status_text(state))
            continue

        if command in SAVE_COMMANDS:
            save_game(state)
            print(f"已儲存目前進度：{SAVE_FILE.name}")
            continue

        if command in LOAD_COMMANDS:
            state = load_game()
            print("已成功讀取存檔。")
            print(describe_current_scene(state) if not state.ended else "這段冒險已經抵達結局。")
            continue

        judge_result = evaluate_action(state, action)
        dice_result = None
        if judge_result["is_possible"] and judge_result["requires_roll"]:
            dice_result = resolve_check(judge_result["dc"])
            print(format_check_result(dice_result))

        state.record_action(action)
        raw_response = ask_ai_gm(state, action, judge_result, dice_result)
        parsed_response = parse_ai_response(raw_response)
        narration = parsed_response["narration"] or raw_response
        state_update = parsed_response["structured_update"]

        if parsed_response["is_valid"]:
            state_update = apply_structured_update(state, state_update)
        elif should_use_legacy_fallback(action, state_update, judge_result):
            handle_action(state, action, record=False)

        print(narration)
        log_turn(state, action, judge_result, dice_result, narration, state_update)

        if state.ended:
            print()
            print("冒險已完成。你可以輸入「狀態」、「存檔」或「離開」。")


def should_use_legacy_fallback(action: str, state_update: dict, judge_result: dict) -> bool:
    if judge_result.get("is_possible") is False:
        return False
    if state_update.get("clues_added") or state_update.get("npc_memories_added"):
        return False
    if state_update.get("ending") or state_update.get("hp_delta"):
        return False
    return any(word in action for word in FALLBACK_MOVEMENT_WORDS | FALLBACK_ENDING_WORDS)


def choose_start_state() -> GameState:
    if SAVE_FILE.exists():
        answer = input("發現既有存檔，要讀取嗎？[是/否] > ").strip().lower()
        if answer in YES_COMMANDS:
            return load_game()

    return GameState()


def save_game(state: GameState) -> None:
    SAVE_FILE.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def load_game() -> GameState:
    if not SAVE_FILE.exists():
        print("找不到存檔，將開始新的冒險。")
        return GameState()

    data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    return GameState.from_dict(data)


if __name__ == "__main__":
    main()
