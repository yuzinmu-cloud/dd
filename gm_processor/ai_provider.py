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
        context_guide = ""
        context = payload.get("gm_context")
        if isinstance(context, dict):
            context_guide = (
                "\nGM Context 分區用途：\n"
                "- Rule Context (rules)：唯一規則裁定依據。\n"
                "- Character Context (character)：玩家能力與限制。\n"
                "- World Context (world)：客觀世界事實。\n"
                "- Adventure Context (adventure)：當前事件與 NPC；hidden 資料僅供裁定。\n"
                "- History Context (history)：過去行動與未解後果。\n"
                "- Session Context (session)：當前回合與最近對話。\n"
            )
        request = (
            f"{instruction}\n\n"
            "只根據下列輸入產生結果，不得補充未提供的規則或世界事實。\n"
            f"{context_guide}"
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
