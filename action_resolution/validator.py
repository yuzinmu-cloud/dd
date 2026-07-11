from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from .schemas import StandardAction


def validate_standard_action(payload: Any) -> tuple[StandardAction | None, list[str]]:
    try:
        return StandardAction.model_validate(payload), []
    except ValidationError as error:
        return None, [str(item) for item in error.errors()]
