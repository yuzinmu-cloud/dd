from __future__ import annotations

import json
from typing import Any, Callable

from pydantic import BaseModel

try:
    from .local_ai import generate_structured_response
    from .schemas import model_json_schema
except ImportError:
    from local_ai import generate_structured_response
    from schemas import model_json_schema


AIClient = Callable[[str, dict[str, Any]], tuple[str | None, str | None]]


class AIProvider:
    """Stateless boundary around the configured structured-output AI client."""

    def __init__(self, client: AIClient | None = None) -> None:
        self._client = client or generate_structured_response

    def generate(self, instruction: str, payload: dict[str, Any], output_type: type[BaseModel]) -> tuple[Any | None, str | None]:
        request = (
            f"{instruction}\n\n"
            "只根據下列輸入產生結果，不得補充未提供的規則或世界事實。\n"
            f"Input:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )
        raw, error = self._client(request, model_json_schema(output_type))
        if error:
            return None, error
        try:
            decoded = json.loads((raw or "").strip())
        except json.JSONDecodeError:
            return None, "AI 回覆不是合法 JSON。"
        if not isinstance(decoded, dict):
            return None, "AI 回覆必須是 JSON object。"
        return decoded, None
