from __future__ import annotations

from game_state import GameState


IMPOSSIBLE_REASON = "目前角色沒有能力直接完成這個行動。"


def evaluate_action(state: GameState, action: str) -> dict:
    text = action.strip().lower()

    if _contains_any(text, ["飛起來", "瞬間移動", "變成神", "直接殺死所有人"]):
        return _result(
            action_type="impossible",
            target=_guess_target(action),
            requires_roll=False,
            check_type=None,
            dc=None,
            is_possible=False,
            reason=IMPOSSIBLE_REASON,
            state_hints=["不要讓玩家直接成功。請溫和說明限制，並提供仍符合場景的可行方向。"],
        )

    if _contains_any(text, ["說服", "騙", "假裝", "威脅", "恐嚇"]):
        return _result(
            action_type="social_check",
            target=_guess_target(action),
            requires_roll=True,
            check_type="charisma",
            dc=13,
            is_possible=True,
            reason="這是有風險的社交行動，結果不應由 AI DM 直接決定。",
            state_hints=["根據擲骰結果描述 NPC 的反應。"],
        )

    if _contains_any(text, ["搜索", "調查", "查看", "觀察", "檢查", "尋找"]):
        return _result(
            action_type="investigation",
            target=_guess_target(action),
            requires_roll=True,
            check_type="wisdom",
            dc=10,
            is_possible=True,
            reason="這是搜索或觀察行動，可能發現線索，也可能只得到有限資訊。",
            state_hints=["若成功，可以揭露一個符合目前場景的小線索；若失敗，提供氣氛或模糊跡象。"],
        )

    if _contains_any(text, ["攻擊", "打", "砍", "丟", "砸", "射"]):
        return _result(
            action_type="attack",
            target=_guess_target(action),
            requires_roll=True,
            check_type="attack",
            dc=13,
            is_possible=True,
            reason="這是攻擊或暴力行動，必須用擲骰結果決定成敗。",
            state_hints=["不要擴充完整戰鬥系統，只描述單次行動造成的局部後果。"],
        )

    if _contains_any(text, ["問", "詢問", "聊天", "說", "告訴", "談"]):
        return _result(
            action_type="social",
            target=_guess_target(action),
            requires_roll=False,
            check_type=None,
            dc=None,
            is_possible=True,
            reason="這是普通對話，不需要擲骰。",
            state_hints=["根據 NPC 已知資訊與隱瞞內容回應，不要一次揭露所有秘密。"],
        )

    return _result(
        action_type="general",
        target=_guess_target(action),
        requires_roll=False,
        check_type=None,
        dc=None,
        is_possible=True,
        reason="一般行動，不需要擲骰。",
        state_hints=["保持場景脈絡，接住玩家創意，但不要讓結果超出目前原型範圍。"],
    )


def _result(
    action_type: str,
    target: str,
    requires_roll: bool,
    check_type: str | None,
    dc: int | None,
    is_possible: bool,
    reason: str,
    state_hints: list[str],
) -> dict:
    return {
        "action_type": action_type,
        "target": target,
        "requires_roll": requires_roll,
        "check_type": check_type,
        "dc": dc,
        "is_possible": is_possible,
        "reason": reason,
        "state_hints": state_hints,
    }


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _guess_target(action: str) -> str:
    return action.strip()[:40] or "未指定"
