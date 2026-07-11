from __future__ import annotations

from typing import Any

try:
    from .schemas import DiceRequest, DiceResult
except ImportError:
    from schemas import DiceRequest, DiceResult


class DiceInterface:
    def get_result(self, request: DiceRequest, external_result: Any | None = None) -> tuple[DiceResult, list[str], list[str]]:
        if not request.needed:
            return DiceResult(status="not_required"), [], []
        if external_result is None:
            return DiceResult(status="pending"), ["需要外部骰子結果；Dice Request 目前為 pending。"], []
        if isinstance(external_result, bool):
            return DiceResult(status="pending"), [], ["骰子結果不可為布林值。"]
        if isinstance(external_result, (int, float)):
            return DiceResult(status="provided", total=external_result, raw=external_result), [], []
        if isinstance(external_result, dict):
            total = external_result.get("total")
            if isinstance(total, bool) or not isinstance(total, (int, float)):
                return DiceResult(status="pending"), [], ["外部骰子結果缺少有效的 total。"]
            return DiceResult(status="provided", total=total, raw=external_result), [], []
        return DiceResult(status="pending"), [], ["外部骰子結果格式不合法。"]
