from __future__ import annotations

import json
from typing import Any


class MockAIProvider:
    """Deterministic AIClient-compatible provider for repeatable structural tests."""

    def __init__(self, failure_mode: str | None = None) -> None:
        self.failure_mode = failure_mode

    def __call__(self, prompt: str, schema: dict[str, Any]) -> tuple[str | None, str | None]:
        if self.failure_mode == "invalid_json":
            return "not-json", None
        if self.failure_mode == "timeout":
            return None, "Mock provider timeout."
        if self.failure_mode == "model_error":
            return None, "Mock provider model error."

        data = _input_payload(prompt)
        title = schema.get("title")
        if title == "ActionInterpretation":
            player_input = str(data.get("player_input", ""))
            return _json({
                "primary_intent": _intent(player_input),
                "secondary_intent": None,
                "target": None,
                "object": None,
                "method": "依玩家描述行動",
                "player_goal": player_input,
                "ambiguity": "資訊不足" if any(word in player_input for word in ("不知道", "隨便", "資訊不足")) else None,
                "confidence": 0.85,
            }), None
        if title == "JudgeOutput":
            interpretation = data.get("interpretation", {})
            context = data.get("gm_context", {})
            text = str(interpretation.get("player_goal", ""))
            possible = not any(word in text for word in ("不可能", "徒手飛", "瞬間移動"))
            needs_roll = possible and any(word in text for word in ("嘗試", "危險", "說服", "破解", "跳", "攻擊"))
            checks = context.get("rules", {}).get("available_checks", [])
            roll_type = checks[0] if needs_roll and checks else None
            ruling = {
                "possible": possible,
                "reason": "依目前 Context 可裁定。" if context.get("rules") else "規則資訊不足。",
                "requires_roll": needs_roll,
                "roll_type": roll_type,
                "difficulty": "normal" if needs_roll else None,
                "applicable_rules": [roll_type] if roll_type else [],
            }
            request = {
                "needed": needs_roll,
                "dice": "d20" if needs_roll else None,
                "modifier_source": None,
                "difficulty": "normal" if needs_roll else None,
                "reason": "行動結果具有不確定性。" if needs_roll else None,
            }
            return _json({"ruling": ruling, "dice_request": request}), None
        if title == "Resolution":
            dice = data.get("dice_result", {})
            total = dice.get("total")
            success = True if total is None else total >= 10
            return _json({
                "outcome": "行動依既有 Context 得到結果。",
                "success": success,
                "consequences": [],
                "proposed_updates": {},
            }), None
        if title == "NarrationResult":
            return _json({"narration": "你依照目前可見資訊採取行動，結果已依裁定呈現。"}), None
        return None, f"Mock provider 不支援 Schema：{title}"


def _input_payload(prompt: str) -> dict[str, Any]:
    marker = "Input:\n"
    if marker not in prompt:
        return {}
    try:
        return json.loads(prompt.split(marker, 1)[1])
    except json.JSONDecodeError:
        return {}


def _intent(text: str) -> str:
    mapping = (
        (("製作", "利用", "組合", "創意"), "creative_action"),
        (("調查", "檢查", "尋找", "觀察", "診斷"), "investigate"),
        (("說服", "交涉", "詢問"), "social"),
        (("前往", "移動", "離開"), "move"),
        (("攻擊", "射擊"), "attack"),
    )
    for words, intent in mapping:
        if any(word in text for word in words):
            return intent
    return "uncertain"


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)
