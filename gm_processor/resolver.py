from __future__ import annotations

from typing import Any

try:
    from .ai_provider import AIProvider
    from .schemas import ActionInterpretation, DiceResult, GMContext, Resolution, Ruling, model_to_dict
    from .validator import Validator
except ImportError:
    from ai_provider import AIProvider
    from schemas import ActionInterpretation, DiceResult, GMContext, Resolution, Ruling, model_to_dict
    from validator import Validator


class Resolver:
    def __init__(self, provider: AIProvider, validator: Validator) -> None:
        self.provider = provider
        self.validator = validator

    def resolve(
        self,
        interpretation: ActionInterpretation,
        ruling: Ruling,
        dice_result: DiceResult,
        context: GMContext,
    ) -> tuple[Resolution | None, list[str], list[str]]:
        if dice_result.status == "pending":
            return Resolution(
                outcome="等待外部骰子結果。",
                success=None,
                consequences=[],
                proposed_updates={},
            ), [], []
        payload, error = self.provider.generate(
            "嚴格根據 Action Interpretation、Ruling 與 Dice Result 推導 Resolution。Resolution 必須維持原始行動類型與目標；攻擊不得改成調查、移動、聊天或結案。不得修改 Context 或產生玩家可見敘事。",
            {
                "interpretation": model_to_dict(interpretation),
                "ruling": model_to_dict(ruling),
                "dice_result": model_to_dict(dice_result),
                "gm_context": model_to_dict(context),
            },
            Resolution,
        )
        if error:
            return None, [], [f"Resolver：{error}"]
        result, warnings, errors = self.validator.validate(Resolution, payload, "Resolution")
        if result is not None and _resolution_conflicts(interpretation, result):
            return None, warnings, ["Resolution 與 Action Interpretation 衝突：敵意/攻擊行動被解析成無關行動。"]
        return result, warnings, errors


def _resolution_conflicts(interpretation: ActionInterpretation, resolution: Resolution) -> bool:
    hostile = interpretation.hostility or interpretation.primary_intent.lower() in {"attack", "hostile", "hostile_action", "violence"}
    if not hostile:
        return False
    outcome = resolution.outcome.lower()
    unrelated = ("調查", "腳印", "聊天", "移動", "暫告一段落", "investigat", "move", "chat")
    return any(word in outcome for word in unrelated)
