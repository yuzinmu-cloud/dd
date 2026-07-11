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
        intent_aliases = {
            "kill": "attack",
            "violent_action": "attack",
            "violence": "attack",
            "hostile": "hostile_action",
            "inquiry": "ask",
            "theft": "steal",
        }
        raw_intent = str(payload.get("primary_intent", "")).strip().lower()
        payload["primary_intent"] = intent_aliases.get(raw_intent, payload.get("primary_intent"))
        hostile_input = any(word in player_input for word in ("殺", "砍", "刺", "攻擊", "揍", "射"))
        if hostile_input:
            payload["hostility"] = True
        else:
            payload.setdefault("hostility", False)
        if not payload.get("target"):
            payload["target"] = _explicit_target(player_input, context)
        result, warnings, errors = self.validator.validate_interpretation(player_input, context, payload)
        if result is not None and result.ambiguity:
            warnings.append(f"玩家行動存在歧義：{result.ambiguity}")
        return result, warnings, errors


def _explicit_target(player_input: str, context: GMContext) -> str | None:
    for npc in context.adventure.relevant_npcs:
        if npc.name in player_input:
            return npc.name
        if npc.role:
            for alias in (npc.role, npc.role[-2:], npc.role[-3:]):
                if alias in player_input:
                    return alias
    return None
