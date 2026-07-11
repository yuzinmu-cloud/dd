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
            "根據 Interpretation、Ruling 與 Dice Result 推導 Resolution；不得修改 Context 或產生玩家可見敘事。",
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
        return result, warnings, errors
