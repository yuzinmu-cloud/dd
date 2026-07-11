from __future__ import annotations

from typing import Any
from action_resolution.intents import STEAL_MARKERS, normalize_intent

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
            "第一任務是忠實解析 player_input。raw_player_input 必須逐字原樣回傳；primary_intent 必須對應玩家主要動詞，target 必須對應玩家明確指定對象。current_situation 與既有線索只提供背景，絕不可取代 player_input 或被當成本回合行動。只輸出 Action Interpretation；不要裁定、更新狀態或敘事。",
            {"player_input": player_input, "gm_context": model_to_dict(context)},
            ActionInterpretation,
        )
        if error:
            return None, [], [f"Interpreter：{error}"]
        if not isinstance(payload, dict):
            return None, [], ["Interpreter：Action Interpretation 必須是 object。"]
        payload = dict(payload)
        if not payload.get("raw_player_input"):
            payload["raw_player_input"] = player_input
        normalized_intent, normalization_warning = normalize_intent(
            str(payload.get("primary_intent", "")), player_input
        )
        payload["primary_intent"] = normalized_intent
        confidence = payload.get("confidence")
        if isinstance(confidence, (int, float)) and 1 < confidence <= 100:
            payload["confidence"] = confidence / 100
        hostile_input = any(word in player_input for word in ("殺", "砍", "刺", "攻擊", "揍", "射"))
        if hostile_input:
            payload["hostility"] = True
            payload["risk_level"] = "high"
        else:
            payload.setdefault("hostility", False)
            payload.setdefault("risk_level", "unknown")
        explicit_target = _explicit_target(player_input, context)
        model_target = payload.get("target")
        if explicit_target and (
            not model_target or explicit_target in str(model_target) or str(model_target) in explicit_target
        ):
            payload["target"] = explicit_target
        if normalized_intent == "steal" and not payload.get("object"):
            payload["object"] = _explicit_object(player_input)
        if normalized_intent == "steal" and not payload.get("object"):
            payload["ambiguity"] = payload.get("ambiguity") or "偷竊行動缺少要取得的物品。"
        result, warnings, errors = self.validator.validate_interpretation(player_input, context, payload)
        if normalization_warning:
            warnings.append(normalization_warning)
        if result is not None and result.ambiguity:
            warnings.append(f"玩家行動存在歧義：{result.ambiguity}")
        return result, warnings, errors


def _explicit_target(player_input: str, context: GMContext) -> str | None:
    for npc in context.adventure.relevant_npcs:
        candidates = [npc.name, npc.role, *npc.aliases]
        for candidate in candidates:
            if candidate and candidate in player_input:
                return candidate
        if npc.role:
            for suffix in (npc.role[-2:], npc.role[-3:]):
                if suffix in player_input:
                    return suffix
    return None


def _explicit_object(player_input: str) -> str | None:
    if not any(marker in player_input for marker in STEAL_MARKERS):
        return None
    if "的" in player_input:
        candidate = player_input.rsplit("的", 1)[1].strip(" 。！？!?，,")
        return candidate or None
    return None
