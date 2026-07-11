from __future__ import annotations

from typing import Any

try:
    from .ai_provider import AIProvider
    from .schemas import ActionInterpretation, GMContext, NarrationResult, Resolution, Ruling, StateUpdate, model_to_dict
    from .validator import Validator
except ImportError:
    from ai_provider import AIProvider
    from schemas import ActionInterpretation, GMContext, NarrationResult, Resolution, Ruling, StateUpdate, model_to_dict
    from validator import Validator


HIDDEN_KEYS = {"hidden_gm_facts", "hidden_facts", "gm_secrets", "secrets"}


def public_context(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: public_context(item)
            for key, item in value.items()
            if key.lower().replace("-", "_").replace(" ", "_") not in HIDDEN_KEYS
        }
    if isinstance(value, list):
        return [public_context(item) for item in value]
    return value


class Narrator:
    def __init__(self, provider: AIProvider, validator: Validator) -> None:
        self.provider = provider
        self.validator = validator

    def narrate(
        self,
        interpretation: ActionInterpretation,
        ruling: Ruling,
        resolution: Resolution,
        state_update: StateUpdate,
        context: GMContext,
    ) -> tuple[NarrationResult | None, list[str], list[str]]:
        payload, error = self.provider.generate(
            "以繁體中文描述已確定結果。不得重新裁定、洩漏隱藏資訊、控制玩家思想情緒或下一步，也不得新增重要事實。",
            {
                "interpretation": model_to_dict(interpretation),
                "ruling": model_to_dict(ruling),
                "resolution": model_to_dict(resolution),
                "state_update": model_to_dict(state_update),
                "public_context": public_context(model_to_dict(context)),
            },
            NarrationResult,
        )
        if error:
            return None, [], [f"Narrator：{error}"]
        result, warnings, errors = self.validator.validate(NarrationResult, payload, "Narration")
        return result, warnings, errors
