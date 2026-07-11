from __future__ import annotations

from typing import Any

try:
    from .ai_provider import AIProvider
    from .schemas import ActionInterpretation, GMContext, model_to_dict
    from .validator import Validator
except ImportError:
    from ai_provider import AIProvider
    from schemas import ActionInterpretation, GMContext, model_to_dict
    from validator import Validator


class Interpreter:
    def __init__(self, provider: AIProvider, validator: Validator) -> None:
        self.provider = provider
        self.validator = validator

    def interpret(self, player_input: str, context: GMContext) -> tuple[ActionInterpretation | None, list[str], list[str]]:
        payload, error = self.provider.generate(
            "理解玩家想做的行動，只輸出 Action Interpretation；不要裁定、更新狀態或敘事。",
            {"player_input": player_input, "gm_context": model_to_dict(context)},
            ActionInterpretation,
        )
        if error:
            return None, [], [f"Interpreter：{error}"]
        result, warnings, errors = self.validator.validate(ActionInterpretation, payload, "Action Interpretation")
        if result is not None and result.ambiguity:
            warnings.append(f"玩家行動存在歧義：{result.ambiguity}")
        return result, warnings, errors
