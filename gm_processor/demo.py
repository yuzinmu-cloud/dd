from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .schemas import GMContext, validate_model
    from .session_log import write_turn_log
    from .session_runner import run_session
except ImportError:
    from schemas import GMContext, validate_model
    from session_log import write_turn_log
    from session_runner import run_session


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_data"


def main() -> None:
    args = parse_args()
    context = validate_model(GMContext, read_context(args.context))

    print("GM Processor Multi-Turn Demo")
    print("============================")
    print(f"世界名稱：{context.world.world_name}")
    print(f"冒險名稱：{context.adventure.title}")
    print(f"目前地點：{context.world.current_location}")
    print(f"當前情境：{context.adventure.current_situation}")
    print(f"玩家角色：{context.character.name}")
    print("輸入『離開』、quit 或 exit 結束 Session。")
    print()
    logger_warnings: list[str] = []

    def input_provider(request: dict) -> str:
        if request["type"] == "dice_result":
            dice = request.get("dice_request") or {}
            print(f"需要檢定：{dice.get('dice') or '未指定'}，難度：{dice.get('difficulty') or '未指定'}")
            return input("請輸入 roll <結果> > ").strip()
        return input("你要怎麼做？ > ").strip()

    def output_handler(event: dict) -> None:
        event_type = event["type"]
        if event_type == "warning":
            print(event["message"])
        elif event_type == "turn_result":
            result = event["result"]
            print("\nInterpretation")
            print(json.dumps(result["interpretation"], ensure_ascii=False, indent=2))
            print("\nRuling")
            print(json.dumps(result["ruling"], ensure_ascii=False, indent=2))
            print("\nDice Request")
            print(json.dumps(result["dice_request"], ensure_ascii=False, indent=2))
            print("\nResolution")
            print(json.dumps(result["resolution"], ensure_ascii=False, indent=2))
            print("\nState Update")
            print(json.dumps(result["state_update"], ensure_ascii=False, indent=2))
            print("\nNarration")
            print(result["narration"])
            if event.get("pending"):
                print("\nWarnings")
                print(json.dumps(result["warnings"], ensure_ascii=False, indent=2))
                print("\nErrors")
                print(json.dumps(result["errors"], ensure_ascii=False, indent=2))
            if args.log:
                error = write_turn_log(BASE_DIR / "logs", event)
                if error:
                    logger_warnings.append(error)
        elif event_type == "context_updated":
            updated = event["context"]
            print("\n更新後狀態")
            print(f"回合數：{updated['session']['turn_number']}")
            print(f"地點：{updated['world']['current_location']}")
            print(f"HP：{updated['character']['current_hp']}/{updated['character']['max_hp']}")
            print("本回合新增線索：", event["applied_diff"]["added_clues"])
            print("活躍事件：", updated["adventure"]["active_events"])
            if event["apply_errors"]:
                print("State Update Errors:", event["apply_errors"])
            result = event["turn_result"]
            print("\nWarnings")
            print(json.dumps(result["warnings"], ensure_ascii=False, indent=2))
            print("\nErrors")
            print(json.dumps(result["errors"], ensure_ascii=False, indent=2))

    result = run_session(context, input_provider, output_handler)
    print("\nSession 摘要")
    print(f"狀態：{result.session_status}")
    print(f"完成回合：{result.turn_count}")
    print(f"最終地點：{result.final_context.world.current_location}")
    if logger_warnings:
        print("Logging Warnings:", logger_warnings)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a multi-turn GM Processor session.")
    parser.add_argument("--context", default="gm_context.json", help="Context filename in sample_data/.")
    parser.add_argument("--log", action="store_true", help="Write sanitized playtest logs to gm_processor/logs/.")
    return parser.parse_args()


def read_context(filename: str) -> dict:
    path = (SAMPLE_DIR / filename).resolve()
    if path.parent != SAMPLE_DIR.resolve():
        raise ValueError("Context 必須位於 gm_processor/sample_data/。")
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
