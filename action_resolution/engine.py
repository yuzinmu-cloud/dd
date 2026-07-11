from __future__ import annotations
from pathlib import Path
from typing import Any
from rule_engine.engine import RuleEngine
from rule_engine.schemas import RuleRequest, RuleResult
from .classifier import classify as classify_action
from .feasibility import analyze, analyze_improvised
from .request_builder import build
from .router import route
from .schemas import ActionResolutionResult, FeasibilityResult, MissingField, StandardAction


class ActionResolutionEngine:
    def __init__(self, rule_pack_path: str | Path | None = None) -> None:
        self.rule_engine = RuleEngine()
        self.rule_pack: dict[str, Any] = {}
        if rule_pack_path:
            self.load_rule_pack(rule_pack_path)

    def load_rule_pack(self, path: str | Path) -> dict[str, Any]:
        self.rule_pack = self.rule_engine.load_rule_pack(path)
        return self.rule_pack

    @property
    def supported_categories(self) -> set[str]:
        return set(self.rule_pack.get("metadata", {}).get("supported_action_categories", []))

    def classify(self, action_interpretation: Any, context: Any) -> StandardAction:
        return classify_action(action_interpretation, context)

    def analyze_feasibility(self, standard_action: StandardAction, context: Any) -> FeasibilityResult:
        result = analyze(standard_action, context, self.supported_categories)
        if standard_action.action_category == "improvised_action":
            improvised = analyze_improvised(standard_action, context, self.supported_categories)
            result.suggested_rule_categories = [improvised["mapped_rule_category"]] if improvised["mapped_rule_category"] else []
            result.missing_fields.extend(MissingField(field=name, reason="GM or Context must provide this value.") for name in improvised["missing_fields"])
        return result

    def build_rule_request(self, standard_action: StandardAction, context: Any) -> RuleRequest:
        routed = route(standard_action, self.supported_categories)
        if standard_action.action_category == "improvised_action":
            mapping = analyze_improvised(standard_action, context, self.supported_categories)
            routed = mapping["mapped_rule_category"] or "unsupported"
        rule_system_id = self.rule_pack.get("metadata", {}).get("rule_system_id", "unknown")
        return build(standard_action, context, routed, rule_system_id)

    def resolve_action(self, request: RuleRequest, context: Any, dice_result: Any = None) -> ActionResolutionResult:
        action = StandardAction.model_validate(request.metadata["standard_action"])
        feasibility = self.analyze_feasibility(action, context)
        routed = request.rule_module
        if action.action_category == "ambiguous":
            return self._pending(action, feasibility, routed, request, "pending_clarification", "Action requires clarification.")
        if feasibility.clarification_required:
            return self._pending(action, feasibility, routed, request, "pending_clarification", "Required action detail is missing.")
        if routed == "unsupported" or action.action_category == "unsupported":
            return self._pending(action, feasibility, routed, request, "unsupported", "Rule Pack does not support this action.")
        if not feasibility.possible and feasibility.missing_fields:
            return self._pending(action, feasibility, routed, request, "pending_rule_data", "Required context data is missing.")
        rule_result = self.rule_engine.resolve(request, dice_result)
        status_map = {
            "pending_rule_data": "pending_rule_data",
            "pending_roll": "pending_attack_roll" if routed == "attack" else "pending_check_roll",
            "unsupported": "unsupported", "failed_validation": "failed_validation", "resolved": "resolved",
        }
        status = status_map[rule_result.status]
        if (
            routed == "attack"
            and rule_result.status == "resolved"
            and rule_result.success is True
            and rule_result.values.get("damage_request")
        ):
            status = "pending_damage_roll"
        return ActionResolutionResult(
            standard_action=action, feasibility=feasibility, routed_rule=routed, rule_request=request,
            rule_result=rule_result, pending_input=rule_result.pending_input,
            pending_dice=rule_result.pending_dice or status == "pending_damage_roll",
            status=status, success=rule_result.success,
            outcome="Rule result resolved." if status == "resolved" else "Damage roll is required." if status == "pending_damage_roll" else "Additional rule input is required.",
            state_change_proposal={} if status == "pending_damage_roll" else rule_result.state_change_proposal,
            warnings=rule_result.warnings, errors=rule_result.errors,
        )

    def process(self, action_interpretation: Any, context: Any, dice_result: Any = None) -> ActionResolutionResult:
        action = self.classify(action_interpretation, context)
        request = self.build_rule_request(action, context)
        return self.resolve_action(request, context, dice_result)

    @staticmethod
    def _pending(action, feasibility, routed, request, status, outcome):
        return ActionResolutionResult(
            standard_action=action, feasibility=feasibility, routed_rule=routed, rule_request=request,
            pending_input=status in {"pending_clarification", "pending_rule_data"}, pending_dice=False,
            status=status, success=None, outcome=outcome,
        )
