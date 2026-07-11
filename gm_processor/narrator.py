from __future__ import annotations

from typing import Any
from action_resolution.schemas import ActionResolutionResult

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
        action_resolution: ActionResolutionResult | None = None,
    ) -> tuple[NarrationResult | None, list[str], list[str]]:
        if action_resolution and action_resolution.status == "pending_clarification":
            target = (
                action_resolution.standard_action.target.label
                if action_resolution.standard_action.target
                else "目標"
            )
            missing = {item.field for item in action_resolution.feasibility.missing_fields}
            if "object" in missing:
                return NarrationResult(narration=f"你想從{target}身上偷走什麼？"), [], []
            return NarrationResult(narration="請補充這個行動所缺少的必要資訊。"), [], []
        if ruling.requires_roll and resolution.success is None:
            target = interpretation.target or "目標"
            action = interpretation.raw_player_input or interpretation.player_goal or interpretation.primary_intent
            action_start = (
                f"你開始對{target}發動攻擊（{action}）"
                if interpretation.hostility
                else f"你開始執行「{action}」，動作指向{target}"
            )
            return NarrationResult(
                narration=f"{action_start}；結果仍取決於尚未提供的骰子檢定。"
            ), [], []
        payload, error = self.provider.generate(
            "玩家原始輸入是本回合敘事中心。只能描述 Resolution 已決定的內容，並維持 Interpretation 的行動類型與目標；不得改寫成無關行動。不得替玩家決定後續行動、內心想法、情緒或自主行動，不得自行推進下一事件。禁止使用『玩家決定』、『下一回合將』或『事件暫告一段落』，除非 Resolution 明確包含該結果。不得重新裁定、洩漏 hidden facts 或新增重要事實。以繁體中文輸出。",
            {
                "interpretation": model_to_dict(interpretation),
                "ruling": model_to_dict(ruling),
                "resolution": model_to_dict(resolution),
                "state_update": model_to_dict(state_update),
                "public_context": public_context(model_to_dict(context)),
                "standard_action": action_resolution.standard_action.model_dump() if action_resolution else None,
                "feasibility": action_resolution.feasibility.model_dump() if action_resolution else None,
                "rule_result": action_resolution.rule_result.model_dump() if action_resolution and action_resolution.rule_result else None,
            },
            NarrationResult,
        )
        if error:
            return None, [], [f"Narrator：{error}"]
        result, warnings, errors = self.validator.validate(NarrationResult, payload, "Narration")
        if result is not None:
            forbidden = ("玩家決定", "下一回合將", "事件暫告一段落")
            if any(phrase in result.narration for phrase in forbidden):
                return None, warnings, ["Narration 違反玩家自主性：包含禁止的後續行動或結案描述。"]
            if _narration_conflicts(interpretation, result.narration):
                return None, warnings, ["Narration 與玩家原始輸入衝突：描述了無關行動。"]
        return result, warnings, errors


def _narration_conflicts(interpretation: ActionInterpretation, narration: str) -> bool:
    hostile = interpretation.hostility or interpretation.primary_intent.lower() in {"attack", "hostile", "hostile_action", "violence"}
    if not hostile:
        return False
    return any(word in narration.lower() for word in ("調查腳印", "查看腳印", "investigate footprints"))
