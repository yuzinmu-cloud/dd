from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

try:
    from .schemas import GMContext, TurnInput, validate_model, validation_errors
except ImportError:
    from schemas import GMContext, TurnInput, validate_model, validation_errors


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
