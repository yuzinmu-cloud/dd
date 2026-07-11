from __future__ import annotations

import json
from pathlib import Path

try:
    from .processor import process_turn
except ImportError:
    from processor import process_turn


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_data"


def main() -> None:
    turn_base = load_sample_data()
    situation = turn_base["situation"]

    print("GM Processor Demo")
    print("=================")
    print(f"目前地點：{situation.get('current_location', '未指定')}")
    print(f"當前衝突：{situation.get('current_conflict', '未指定')}")
    print()

    player_input = input("你要怎麼做？ > ").strip()
    turn_input = {
        "player_input": player_input,
        **turn_base,
        "recent_events": turn_base.get("world_state", {}).get("recent_events", []),
    }

    result = process_turn(turn_input)

    print()
    fields = (
        "interpretation",
        "ruling",
        "dice_request",
        "resolution",
        "state_update",
        "narration",
        "warnings",
        "errors",
    )
    for field in fields:
        print()
        print(field)
        print("-" * len(field))
        value = result[field]
        if isinstance(value, str):
            print(value)
        else:
            print(json.dumps(value, ensure_ascii=False, indent=2))


def load_sample_data() -> dict:
    return {
        "rule_system": read_json("rule_system.json"),
        "character": read_json("character.json"),
        "situation": read_json("situation.json"),
        "world_state": read_json("world_state.json"),
    }


def read_json(filename: str) -> dict:
    return json.loads((SAMPLE_DIR / filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
