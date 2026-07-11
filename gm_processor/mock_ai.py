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
            intent = _intent(player_input)
            return _json({
                "raw_player_input": player_input,
                "primary_intent": intent,
                "secondary_intent": None,
                "target": _target(player_input, data.get("gm_context", {})),
                "object": "鑰匙" if "鑰匙" in player_input else None,
                "method": "依玩家描述行動",
                "player_goal": player_input,
                "hostility": intent in {"attack", "hostile_action"},
                "risk_level": "impossible" if any(word in player_input for word in ("徒手飛", "瞬間移動", "不可能")) else "high" if any(word in player_input for word in ("嘗試", "危險", "說服", "破解", "跳", "攻擊", "殺", "砍", "刺", "揍", "射", "偷")) else "low",
                "ambiguity": "資訊不足" if any(word in player_input for word in ("不知道", "隨便", "資訊不足")) else None,
                "confidence": 0.85,
            }), None
        if title == "JudgeOutput":
            interpretation = data.get("interpretation", {})
            context = data.get("gm_context", {})
            text = str(interpretation.get("player_goal", ""))
            possible = not any(word in text for word in ("不可能", "徒手飛", "瞬間移動"))
            needs_roll = possible and any(word in text for word in ("嘗試", "危險", "說服", "破解", "跳", "攻擊", "殺", "砍", "刺", "揍", "射", "偷"))
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
            interpretation = data.get("interpretation", {})
            if interpretation.get("hostility"):
                target = interpretation.get("target") or "目標"
                narration = f"你對{target}發動攻擊，結果依照裁定與骰子呈現。"
            else:
                narration = "你依照目前可見資訊採取行動，結果已依裁定呈現。"
            return _json({"narration": narration}), None
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
        (("殺死", "殺", "砍", "刺", "攻擊", "揍", "射"), "attack"),
        (("偷偷", "潛行", "隱藏"), "stealth"),
        (("偷走", "偷", "竊取"), "steal"),
        (("製作", "利用", "組合", "創意"), "creative_action"),
        (("調查", "檢查", "尋找", "觀察", "診斷"), "investigate"),
        (("說服", "交涉", "詢問"), "social"),
        (("前往", "移動", "離開"), "move"),
        (("拿起", "取得", "撿起", "裝備", "放下"), "inventory"),
        (("跳",), "move"),
        (("飛",), "move"),
        (("破解",), "investigate"),
        (("攻擊", "射擊"), "attack"),
    )
    for words, intent in mapping:
        if any(word in text for word in words):
            return intent
    return "uncertain"


def _target(text: str, context: dict[str, Any]) -> str | None:
    for npc in context.get("adventure", {}).get("relevant_npcs", []):
        name = npc.get("name")
        role = npc.get("role")
        if name and name in text:
            return name
        if role:
            for alias in (role, role[-2:], role[-3:]):
                if alias in text:
                    return alias
        for alias in npc.get("aliases", []):
            if alias in text:
                return alias
    return None


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)
