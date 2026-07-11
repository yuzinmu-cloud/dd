from __future__ import annotations

from typing import Any

try:
    from .ai_provider import AIClient, AIProvider
    from .dice_interface import DiceInterface
    from .interpreter import Interpreter
    from .judge import Judge
    from .narrator import Narrator
    from .resolver import Resolver
    from .schemas import (
        ActionInterpretation,
        DiceRequest,
        Resolution,
        Ruling,
        StateUpdate,
        TurnInput,
        TurnResult,
        model_to_dict,
    )
    from .state_update_builder import StateUpdateBuilder
    from .validator import Validator
except ImportError:
    from ai_provider import AIClient, AIProvider
    from dice_interface import DiceInterface
    from interpreter import Interpreter
    from judge import Judge
    from narrator import Narrator
    from resolver import Resolver
    from schemas import ActionInterpretation, DiceRequest, Resolution, Ruling, StateUpdate, TurnInput, TurnResult, model_to_dict
    from state_update_builder import StateUpdateBuilder
    from validator import Validator


class TurnOrchestrator:
    def __init__(self, ai_client: AIClient | None = None) -> None:
        self.validator = Validator()
        provider = AIProvider(ai_client)
        self.interpreter = Interpreter(provider, self.validator)
        self.judge = Judge(provider, self.validator)
        self.dice_interface = DiceInterface()
        self.resolver = Resolver(provider, self.validator)
        self.state_update_builder = StateUpdateBuilder()
        self.narrator = Narrator(provider, self.validator)

    def process(self, payload: Any) -> TurnResult:
        warnings: list[str] = []
        errors: list[str] = []
        turn_input, new_warnings, new_errors = self.validator.validate(TurnInput, payload, "Turn Input")
        warnings.extend(new_warnings)
        errors.extend(new_errors)
        if turn_input is None:
            return self._safe_result(warnings, errors)

        context = self._build_context(turn_input)
        try:
            interpretation, new_warnings, new_errors = self.interpreter.interpret(turn_input.player_input, context)
            warnings.extend(new_warnings)
            errors.extend(new_errors)
            if interpretation is None:
                return self._safe_result(warnings, errors, player_input=turn_input.player_input)

            ruling, dice_request, new_warnings, new_errors = self.judge.judge(interpretation, context)
            warnings.extend(new_warnings)
            errors.extend(new_errors)
            if ruling is None or dice_request is None:
                return self._safe_result(warnings, errors, interpretation, player_input=turn_input.player_input)

            dice_result, new_warnings, new_errors = self.dice_interface.get_result(dice_request, turn_input.dice_result)
            warnings.extend(new_warnings)
            errors.extend(new_errors)
            if new_errors:
                return self._safe_result(warnings, errors, interpretation, ruling, dice_request, player_input=turn_input.player_input)

            resolution, new_warnings, new_errors = self.resolver.resolve(interpretation, ruling, dice_result, context)
            warnings.extend(new_warnings)
            errors.extend(new_errors)
            if resolution is None:
                return self._safe_result(warnings, errors, interpretation, ruling, dice_request, player_input=turn_input.player_input)

            resolution, new_warnings, new_errors = self.validator.validate(Resolution, model_to_dict(resolution), "Resolution")
            warnings.extend(new_warnings)
            errors.extend(new_errors)
            if resolution is None:
                return self._safe_result(warnings, errors, interpretation, ruling, dice_request, player_input=turn_input.player_input)

            state_update, new_warnings, new_errors = self.state_update_builder.build(resolution, context)
            warnings.extend(new_warnings)
            errors.extend(new_errors)
            state_update, new_warnings, new_errors = self.validator.validate(StateUpdate, model_to_dict(state_update), "State Update")
            warnings.extend(new_warnings)
            errors.extend(new_errors)
            if state_update is None:
                return self._safe_result(warnings, errors, interpretation, ruling, dice_request, resolution, player_input=turn_input.player_input)

            narration, new_warnings, new_errors = self.narrator.narrate(
                interpretation, ruling, resolution, state_update, context
            )
            warnings.extend(new_warnings)
            errors.extend(new_errors)
            if narration is None:
                return self._safe_result(
                    warnings, errors, interpretation, ruling, dice_request, resolution, state_update, turn_input.player_input
                )

            return TurnResult(
                interpretation=interpretation,
                ruling=ruling,
                dice_request=dice_request,
                resolution=resolution,
                state_update=state_update,
                narration=narration.narration,
                warnings=warnings,
                errors=errors,
            )
        except Exception as error:  # Component failures must become a legal TurnResult.
            errors.append(f"GM Processor 發生未預期錯誤：{error}")
            return self._safe_result(warnings, errors, player_input=turn_input.player_input)

    @staticmethod
    def _build_context(turn_input: TurnInput) -> dict[str, Any]:
        return {
            "rule_context": turn_input.rule_system,
            "character_context": turn_input.character,
            "world_context": turn_input.world_state,
            "adventure_context": turn_input.situation,
            "history_context": {"recent_events": turn_input.recent_events},
            "session_context": {},
        }

    @staticmethod
    def _safe_result(
        warnings: list[str],
        errors: list[str],
        interpretation: ActionInterpretation | None = None,
        ruling: Ruling | None = None,
        dice_request: DiceRequest | None = None,
        resolution: Resolution | None = None,
        state_update: StateUpdate | None = None,
        player_input: str = "",
    ) -> TurnResult:
        return TurnResult(
            interpretation=interpretation or ActionInterpretation(
                primary_intent="unknown",
                player_goal=player_input or None,
                ambiguity="無法完成行動解讀。",
                confidence=0.0,
            ),
            ruling=ruling or Ruling(
                possible=False,
                reason="系統無法安全完成本回合裁定。",
                requires_roll=False,
                applicable_rules=[],
            ),
            dice_request=dice_request or DiceRequest(needed=False),
            resolution=resolution or Resolution(
                outcome="本回合未被套用。",
                success=False,
                consequences=[],
            ),
            state_update=state_update or StateUpdate(),
            narration="系統暫時無法安全處理這個回合。請確認輸入資料與本機 AI 狀態後再試一次。",
            warnings=warnings,
            errors=errors or ["未知錯誤。"],
        )
