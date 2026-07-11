from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

try:
    from .schemas import validate_model, validation_errors
except ImportError:
    from schemas import validate_model, validation_errors


class Validator:
    """Validates component contracts without changing their decisions."""

    def validate(self, model_type: type[BaseModel], payload: Any, label: str) -> tuple[BaseModel | None, list[str], list[str]]:
        try:
            return validate_model(model_type, payload), [], []
        except ValidationError as error:
            details = validation_errors(error)
            return None, [], [f"{label} 驗證失敗：{detail}" for detail in details]
