from __future__ import annotations
from pathlib import Path
from typing import Any
from . import ability_check, attack, damage, initiative, interaction
from .loader import load_rule_pack
from .schemas import RuleRequest, RuleResult


class RuleEngine:
    def __init__(self, rule_pack_path: str | Path | None = None) -> None:
        self.rule_pack: dict[str, Any] = {}
        if rule_pack_path:
            self.load_rule_pack(rule_pack_path)

    def load_rule_pack(self, path: str | Path) -> dict[str, Any]:
        self.rule_pack = load_rule_pack(path)
        return self.rule_pack

    def supports(self, action_category: str) -> bool:
        return action_category in self.rule_pack.get("metadata", {}).get("supported_action_categories", [])

    def resolve(self, request: RuleRequest | dict[str, Any], dice_result: Any = None) -> RuleResult:
        request = request if isinstance(request, RuleRequest) else RuleRequest.model_validate(request)
        if dice_result is not None and request.fixed_roll is None:
            total = dice_result.get("total") if isinstance(dice_result, dict) else dice_result
            request = request.model_copy(update={"fixed_roll": int(total)})
        dispatch = {
            "ability_check": self.resolve_ability_check, "skill_check": self.resolve_skill_check,
            "saving_throw": self.resolve_saving_throw, "attack": self.resolve_attack,
            "damage": self.resolve_damage, "initiative": self.resolve_initiative,
            "movement": self.resolve_movement, "interaction": self.resolve_interaction,
            "inventory": self.resolve_interaction, "use_item": self.resolve_interaction,
            "no_roll_action": self.resolve_interaction, "direct_resolution": self.resolve_interaction,
        }
        handler = dispatch.get(request.rule_module)
        if not handler:
            return RuleResult(rule_module=request.rule_module, status="unsupported", errors=["Unsupported rule module."])
        return handler(request)

    def resolve_ability_check(self, request): return ability_check.resolve(request, "ability_check")
    def resolve_skill_check(self, request): return ability_check.resolve(request, "skill_check")
    def resolve_saving_throw(self, request): return ability_check.resolve(request, "saving_throw")
    def resolve_attack(self, request): return attack.resolve(request)
    def resolve_damage(self, request): return damage.resolve(request)
    def resolve_initiative(self, request): return initiative.resolve(request)
    def resolve_movement(self, request): return interaction.resolve(request)
    def resolve_interaction(self, request): return interaction.resolve(request)
