from __future__ import annotations

from typing import Any

try:
    from .ai_provider import AIProvider
    from .schemas import ActionInterpretation, DiceRequest, GMContext, Ruling, StrictModel, model_to_dict
    from .validator import Validator
except ImportError:
    from ai_provider import AIProvider
    from schemas import ActionInterpretation, DiceRequest, GMContext, Ruling, StrictModel, model_to_dict
    from validator import Validator


class JudgeOutput(StrictModel):
    ruling: Ruling
    dice_request: DiceRequest


class Judge:
    def __init__(self, provider: AIProvider, validator: Validator) -> None:
        self.provider = provider
        self.validator = validator

    def judge(self, interpretation: ActionInterpretation, context: GMContext) -> tuple[Ruling | None, DiceRequest | None, list[str], list[str]]:
        warnings: list[str] = []
        if not context.rules.available_checks or not context.rules.difficulty_rules:
            warnings.append("Rule Context 資訊不足；Judge 不會自行發明規則。")
        hostile = interpretation.hostility or interpretation.primary_intent.lower() in {"attack", "hostile", "hostile_action", "violence"}
        attack_rules = [rule for rule in context.rules.available_checks + context.rules.special_rules if any(word in rule.lower() for word in ("attack", "combat", "攻擊", "戰鬥"))]
        if hostile and not attack_rules:
            warnings.append("Rule Context 缺少明確攻擊規則；Judge 不得將攻擊改判為其他行動或自行發明規則。")
        payload, error = self.provider.generate(
            "只依既有 Action Interpretation、Rule Context 與目前 Context 裁定，禁止重新解讀 player_input 或改寫 primary_intent。hostile/attack 行動若目標存在且可行，必須依 Rule Context 判斷是否檢定；規則不足時保持攻擊語意並回報限制，不得改判為調查。輸出 ruling 與 dice_request；不要擲骰、更新狀態或敘事，不得發明規則。",
            {"interpretation": model_to_dict(interpretation), "gm_context": model_to_dict(context)},
            JudgeOutput,
        )
        if error:
            return None, None, warnings, [f"Judge：{error}"]
        result, validation_warnings, errors = self.validator.validate(JudgeOutput, payload, "Ruling 與 Dice Request")
        warnings.extend(validation_warnings)
        if result is None:
            return None, None, warnings, errors
        if hostile and result.ruling.possible and interpretation.target and not result.ruling.requires_roll:
            warnings.append("敵意行動被裁定為不需擲骰；請確認 Rule Context 是否明確允許此裁定。")
        return result.ruling, result.dice_request, warnings, errors
