from __future__ import annotations

from typing import Any

try:
    from .ai_provider import AIProvider
    from .schemas import ActionInterpretation, DiceRequest, Ruling, StrictModel, model_to_dict
    from .validator import Validator
except ImportError:
    from ai_provider import AIProvider
    from schemas import ActionInterpretation, DiceRequest, Ruling, StrictModel, model_to_dict
    from validator import Validator


class JudgeOutput(StrictModel):
    ruling: Ruling
    dice_request: DiceRequest


class Judge:
    def __init__(self, provider: AIProvider, validator: Validator) -> None:
        self.provider = provider
        self.validator = validator

    def judge(self, interpretation: ActionInterpretation, context: dict[str, Any]) -> tuple[Ruling | None, DiceRequest | None, list[str], list[str]]:
        warnings: list[str] = []
        rule_context = context.get("rule_context") or context.get("rule_system")
        if not rule_context:
            warnings.append("Rule Context 資訊不足；Judge 不會自行發明規則。")
        payload, error = self.provider.generate(
            "依 Rule Context 裁定行動，輸出 ruling 與 dice_request；不要擲骰、更新狀態或敘事。資訊不足時不得發明規則。",
            {"interpretation": model_to_dict(interpretation), "gm_context": context},
            JudgeOutput,
        )
        if error:
            return None, None, warnings, [f"Judge：{error}"]
        result, validation_warnings, errors = self.validator.validate(JudgeOutput, payload, "Ruling 與 Dice Request")
        warnings.extend(validation_warnings)
        if result is None:
            return None, None, warnings, errors
        return result.ruling, result.dice_request, warnings, errors
