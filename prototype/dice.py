from __future__ import annotations

import random


def roll_d20() -> int:
    return random.randint(1, 20)


def resolve_check(dc: int, modifier: int = 0) -> dict:
    roll = roll_d20()
    total = roll + modifier
    return {
        "roll": roll,
        "modifier": modifier,
        "total": total,
        "dc": dc,
        "success": total >= dc,
    }


def format_check_result(dice_result: dict) -> str:
    outcome = "成功" if dice_result["success"] else "失敗"
    modifier = dice_result.get("modifier", 0)
    modifier_text = f"，修正值 {modifier:+d}" if modifier else ""
    return f"檢定：d20 = {dice_result['roll']}{modifier_text}，DC {dice_result['dc']}，{outcome}。"
