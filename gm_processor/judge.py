from __future__ import annotations

from pathlib import Path
from typing import Any

from action_resolution.engine import ActionResolutionEngine
from action_resolution.schemas import ActionResolutionResult

try:
    from .schemas import ActionInterpretation, DiceRequest, DiceResult, GMContext, Ruling
except ImportError:
    from schemas import ActionInterpretation, DiceRequest, DiceResult, GMContext, Ruling


DEFAULT_RULE_PACK = Path(__file__).resolve().parents[1] / "rule_systems" / "dnd5e_srd52"


class Judge:
    """Confirms classification and delegates all deterministic rules to the Action Resolution Engine."""

    def __init__(self, *_args: Any, action_engine: ActionResolutionEngine | None = None, **_kwargs: Any) -> None:
        self.action_engine = action_engine or ActionResolutionEngine(DEFAULT_RULE_PACK)

    def judge(
        self,
        interpretation: ActionInterpretation,
        context: GMContext,
        dice_result: DiceResult | None = None,
    ) -> tuple[Ruling, DiceRequest, ActionResolutionResult, list[str], list[str]]:
        reference = context.rules.rule_pack_reference
        if reference:
            path = Path(reference)
            if not path.is_absolute():
                path = Path(__file__).resolve().parents[1] / path
            if str(path) != self.action_engine.rule_pack.get("path") and path.exists():
                self.action_engine.load_rule_pack(path)
        standard_action = self.action_engine.classify(interpretation, context)
        feasibility = self.action_engine.analyze_feasibility(standard_action, context)
        request = self.action_engine.build_rule_request(standard_action, context)
        fixed = dice_result.model_dump() if dice_result is not None else None
        action_result = self.action_engine.resolve_action(request, context, fixed)
        warnings = list(action_result.warnings)
        errors = list(action_result.errors)
        if action_result.status == "pending_rule_data":
            warnings.append(f"規則資料不足：{', '.join(action_result.rule_result.missing_fields if action_result.rule_result else [])}")
        possible = feasibility.possible is not False and action_result.status not in {"unsupported", "failed_validation"}
        requires_roll = bool(request.external_roll_required)
        ruling = Ruling(
            possible=possible,
            reason=feasibility.reason,
            requires_roll=requires_roll,
            roll_type=(context.rules.available_checks[0] if requires_roll and context.rules.available_checks else request.rule_module if requires_roll else None),
            difficulty=str(request.provided_values.get("dc")) if request.provided_values.get("dc") is not None else None,
            applicable_rules=[],
        )
        dice_request = DiceRequest(
            needed=action_result.pending_dice,
            dice="d20" if action_result.pending_dice else None,
            modifier_source=request.rule_module if action_result.pending_dice else None,
            difficulty=ruling.difficulty,
            reason="Deterministic Rule Engine requires an external roll." if action_result.pending_dice else None,
        )
        return ruling, dice_request, action_result, warnings, errors
