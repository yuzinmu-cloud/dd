from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

try:
    from .schemas import ActionInterpretation, GMContext, TurnInput, validate_model, validation_errors
except ImportError:
    from schemas import ActionInterpretation, GMContext, TurnInput, validate_model, validation_errors


class Validator:
    """Validates component contracts without changing their decisions."""

    def validate(self, model_type: type[BaseModel], payload: Any, label: str) -> tuple[BaseModel | None, list[str], list[str]]:
        try:
            return validate_model(model_type, payload), [], []
        except ValidationError as error:
            details = validation_errors(error)
            return None, [], [f"{label} 驗證失敗：{detail}" for detail in details]

    def validate_turn_input(self, payload: Any) -> tuple[TurnInput | None, list[str], list[str]]:
        result, warnings, errors = self.validate(TurnInput, payload, "Turn Input")
        if result is None:
            return None, warnings, errors
        context_errors = self._context_errors(result.context)
        if context_errors:
            return None, warnings, context_errors
        return result, warnings, errors

    def validate_interpretation(
        self, player_input: str, context: GMContext, payload: Any
    ) -> tuple[ActionInterpretation | None, list[str], list[str]]:
        result, warnings, errors = self.validate(ActionInterpretation, payload, "Action Interpretation")
        if result is None:
            return None, warnings, errors
        conflicts: list[str] = []
        if result.raw_player_input != player_input:
            conflicts.append("raw_player_input 與玩家原始輸入不一致。")
        intent = result.primary_intent.strip().lower()
        families = (
            (("殺死", "殺", "砍", "刺", "攻擊", "揍", "射"), {"attack", "hostile", "hostile_action", "violence"}, "攻擊"),
            (("偷走", "偷", "竊取"), {"steal", "theft", "pickpocket"}, "偷竊"),
            (("詢問", "問", "打聽"), {"ask", "social", "inquiry", "question"}, "詢問"),
            (("利用", "製作", "組合", "創意"), {"creative", "creative_action", "improvise", "craft"}, "創意行動"),
            (("調查", "檢查", "觀察", "尋找"), {"investigation", "investigate", "observe", "search"}, "調查"),
        )
        for keywords, allowed, label in families:
            if any(keyword in player_input for keyword in keywords):
                if intent not in allowed:
                    conflicts.append(f"玩家主要動詞屬於{label}，但 primary_intent 為 {result.primary_intent}。")
                break
        explicit_targets = []
        for npc in context.adventure.relevant_npcs:
            if npc.name in player_input:
                explicit_targets.append(npc.name)
            if npc.role:
                explicit_targets.extend(
                    alias for alias in (npc.role, npc.role[-2:], npc.role[-3:]) if alias in player_input
                )
        if explicit_targets:
            if not result.target:
                conflicts.append(f"玩家明確指定目標 {explicit_targets[0]}，但 target 為空。")
            elif not any(target in result.target or result.target in target for target in explicit_targets):
                conflicts.append(f"玩家指定目標 {explicit_targets[0]}，但 Interpretation target 變成 {result.target}。")
        if conflicts:
            return None, warnings, [f"Interpretation 與玩家輸入衝突：{message}" for message in conflicts]
        return result, warnings, errors

    @staticmethod
    def _context_errors(context: GMContext) -> list[str]:
        errors: list[str] = []
        if not context.context_version.strip():
            errors.append("GM Context 驗證失敗：context_version 不可為空。")
        character = context.character
        if (
            character.current_hp is not None
            and character.max_hp is not None
            and character.current_hp > character.max_hp
        ):
            errors.append("GM Context 驗證失敗：current_hp 不可大於 max_hp。")
        if context.session.turn_number < 0:
            errors.append("GM Context 驗證失敗：turn_number 不可小於 0。")
        adventure_hidden = set(context.adventure.hidden_gm_facts)
        if adventure_hidden.intersection(context.adventure.known_clues):
            errors.append("GM Context 驗證失敗：hidden_gm_facts 不得同時列為 known_clues。")
        for npc in context.adventure.relevant_npcs:
            if set(npc.hidden_facts).intersection(npc.known_facts):
                errors.append(f"GM Context 驗證失敗：NPC {npc.npc_id} 的 hidden_facts 不得同時列為 known_facts。")
        return errors
