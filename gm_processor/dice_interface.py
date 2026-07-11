from __future__ import annotations

try:
    from .schemas import DiceRequest, DiceResult
except ImportError:
    from schemas import DiceRequest, DiceResult


class DiceInterface:
    def get_result(self, request: DiceRequest, external_result: DiceResult | None = None) -> tuple[DiceResult, list[str], list[str]]:
        if not request.needed:
            return DiceResult(status="not_required"), [], []
        if external_result is None:
            return DiceResult(status="pending"), ["需要外部骰子結果；Dice Request 目前為 pending。"], []
        if external_result.status != "provided" or external_result.total is None:
            return DiceResult(status="pending"), [], ["外部骰子結果必須是 provided 且包含 total。"]
        return external_result, [], []
