from __future__ import annotations

from action_resolution.schemas import ActionResolutionResult

try:
    from .schemas import ActionInterpretation, GMContext, Resolution, Ruling
except ImportError:
    from schemas import ActionInterpretation, GMContext, Resolution, Ruling


class Resolver:
    """Converts deterministic ActionResolutionResult into the GM Resolution contract."""

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def resolve(
        self,
        interpretation: ActionInterpretation,
        ruling: Ruling,
        action_resolution: ActionResolutionResult,
        context: GMContext,
    ) -> tuple[Resolution, list[str], list[str]]:
        if action_resolution.status.startswith("pending_"):
            return Resolution(
                outcome=f"等待必要輸入：{action_resolution.status}", success=None,
                consequences=[], proposed_updates={},
            ), list(action_resolution.warnings), list(action_resolution.errors)
        if action_resolution.status in {"unsupported", "failed_validation"}:
            return Resolution(
                outcome=action_resolution.outcome, success=False, consequences=[], proposed_updates={}
            ), list(action_resolution.warnings), list(action_resolution.errors)
        return Resolution(
            outcome=action_resolution.outcome,
            success=action_resolution.success,
            consequences=[],
            proposed_updates=action_resolution.state_change_proposal,
        ), list(action_resolution.warnings), list(action_resolution.errors)
