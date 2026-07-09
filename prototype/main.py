from __future__ import annotations

import json
from pathlib import Path

from adventure import HELP_TEXT, OPENING_NARRATION, describe_current_scene, handle_action, status_text
from game_state import GameState


SAVE_FILE = Path(__file__).with_name("save_game.json")

HELP_COMMANDS = {"help", "幫助"}
STATUS_COMMANDS = {"status", "狀態"}
SAVE_COMMANDS = {"save", "存檔"}
LOAD_COMMANDS = {"load", "讀檔"}
QUIT_COMMANDS = {"quit", "exit", "離開"}
YES_COMMANDS = {"y", "yes", "是", "好", "讀取"}


def main() -> None:
    print("AIGMOS Demo v0.2")
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
            print("AI GM 靜靜等待你說出下一步行動。")
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

        response = handle_action(state, action)
        print(response)

        if state.ended:
            print()
            print("冒險已完成。你可以輸入「狀態」、「存檔」或「離開」。")


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
