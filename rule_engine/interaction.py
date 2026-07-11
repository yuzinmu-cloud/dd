from __future__ import annotations
from .schemas import RuleRequest, RuleResult


def resolve(request: RuleRequest) -> RuleResult:
    if request.missing_fields:
        return RuleResult(rule_module=request.rule_module, status="pending_rule_data", pending_input=True, missing_fields=request.missing_fields)
    possible = request.provided_values.get("possible", True)
    return RuleResult(rule_module=request.rule_module, status="resolved", success=bool(possible), values=request.provided_values)
