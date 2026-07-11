from __future__ import annotations

import json
import argparse
from pathlib import Path

try:
    from .processor import process_turn
except ImportError:
    from processor import process_turn


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_data"


def main() -> None:
    args = parse_args()
    context = read_context(args.context)

    print("GM Processor Demo")
    print("=================")
    print(f"世界名稱：{context['world']['world_name']}")
    print(f"冒險名稱：{context['adventure']['title']}")
    print(f"目前地點：{context['world']['current_location']}")
    print(f"當前情境：{context['adventure']['current_situation']}")
    print(f"玩家角色：{context['character']['name']}")
    print()

    player_input = input("你要怎麼做？ > ").strip()
    turn_input = {
        "player_input": player_input,
        "context": context,
        "dice_result": None,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one GM Processor turn.")
    parser.add_argument("--context", default="gm_context.json", help="Context filename in sample_data/.")
    return parser.parse_args()


def read_context(filename: str) -> dict:
    path = (SAMPLE_DIR / filename).resolve()
    if path.parent != SAMPLE_DIR.resolve():
        raise ValueError("Context 必須位於 gm_processor/sample_data/。")
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
