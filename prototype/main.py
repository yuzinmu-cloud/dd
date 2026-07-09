from __future__ import annotations

import json
from pathlib import Path

from adventure import HELP_TEXT, OPENING_NARRATION, describe_current_scene, handle_action, status_text
from game_state import GameState


SAVE_FILE = Path(__file__).with_name("save_game.json")


def main() -> None:
    print("AIGMOS Text Prototype")
    print("Type 'help' for commands. Type 'quit' to exit.")
    print()

    state = choose_start_state()

    if state.turn_count == 0 and not state.ended:
        print(OPENING_NARRATION)
        print()
        print(describe_current_scene(state))
    else:
        print("Loaded session.")
        print(describe_current_scene(state) if not state.ended else "This session has already reached an ending.")

    while True:
        print()
        action = input("What do you do? > ").strip()

        if not action:
            print("The AI GM waits for a clear action.")
            continue

        command = action.lower()

        if command in {"quit", "exit"}:
            print("Session closed.")
            break

        if command == "help":
            print(HELP_TEXT)
            continue

        if command == "status":
            print(status_text(state))
            continue

        if command == "save":
            save_game(state)
            print(f"Game saved to {SAVE_FILE.name}.")
            continue

        if command == "load":
            state = load_game()
            print("Game loaded.")
            print(describe_current_scene(state) if not state.ended else "This session has already reached an ending.")
            continue

        response = handle_action(state, action)
        print(response)

        if state.ended:
            print()
            print("The adventure is complete. You can type 'status', 'save', or 'quit'.")


def choose_start_state() -> GameState:
    if SAVE_FILE.exists():
        answer = input("Load existing save? [y/N] > ").strip().lower()
        if answer in {"y", "yes"}:
            return load_game()

    return GameState()


def save_game(state: GameState) -> None:
    SAVE_FILE.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def load_game() -> GameState:
    if not SAVE_FILE.exists():
        print("No save file found. Starting a new game.")
        return GameState()

    data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    return GameState.from_dict(data)


if __name__ == "__main__":
    main()
