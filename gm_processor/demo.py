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
    print("玩家可見敘事")
    print("------------")
    print(result["narration"])
    print()
    print("裁定結果")
    print("--------")
    print(json.dumps(result["ruling"], ensure_ascii=False, indent=2))
    print()
    print("狀態更新")
    print("--------")
    print(json.dumps(result["state_update"], ensure_ascii=False, indent=2))
    if result["warnings"]:
        print()
        print("Warnings")
        print(json.dumps(result["warnings"], ensure_ascii=False, indent=2))
    if result["errors"]:
        print()
        print("Errors")
        print(json.dumps(result["errors"], ensure_ascii=False, indent=2))


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
