from __future__ import annotations

from typing import Any

try:
    from .schemas import GMContext, Resolution, StateUpdate, validate_model
except ImportError:
    from schemas import GMContext, Resolution, StateUpdate, validate_model


class StateUpdateBuilder:
    def build(self, resolution: Resolution, _context: GMContext) -> tuple[StateUpdate, list[str], list[str]]:
        allowed = set(StateUpdate.model_fields if hasattr(StateUpdate, "model_fields") else StateUpdate.__fields__)
        proposed = resolution.proposed_updates
        unknown = sorted(set(proposed) - allowed)
        warnings = [f"Resolution 包含不支援的更新類別：{name}" for name in unknown]
        filtered = {name: value for name, value in proposed.items() if name in allowed}
        try:
            return validate_model(StateUpdate, filtered), warnings, []
        except Exception as error:
            return StateUpdate(), warnings, [f"State Update 驗證失敗：{error}"]
