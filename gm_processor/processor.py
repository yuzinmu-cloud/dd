from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

try:
    from .local_ai import generate_structured_response
    from .schemas import (
        ActionInterpretation,
        DiceRequest,
        Resolution,
        Ruling,
        StateUpdate,
        TurnInput,
        TurnResult,
        model_json_schema,
        model_to_dict,
        validate_model,
        validation_errors,
    )
except ImportError:
    from local_ai import generate_structured_response
    from schemas import (
        ActionInterpretation,
        DiceRequest,
        Resolution,
        Ruling,
        StateUpdate,
        TurnInput,
        TurnResult,
        model_json_schema,
        model_to_dict,
        validate_model,
        validation_errors,
    )


AIClient = Callable[[str, dict[str, Any]], tuple[str | None, str | None]]
PROMPT_PATH = Path(__file__).with_name("gm_prompt.md")


def process_turn(turn_input: Any, ai_client: AIClient | None = None) -> dict[str, Any]:
    try:
        validated_input = validate_model(TurnInput, turn_input)
    except ValidationError as error:
        return model_to_dict(_safe_error_result(validation_errors(error)))

    prompt = build_prompt(validated_input)
    schema = model_json_schema(TurnResult)
    client = ai_client or generate_structured_response
    raw_response, ai_error = client(prompt, schema)

    if ai_error:
        return model_to_dict(_safe_error_result([ai_error], validated_input))

    parsed_payload, parse_warning = parse_json_payload(raw_response or "")
    if parsed_payload is None:
        return model_to_dict(_safe_error_result(["GM 回覆不是合法 JSON。"], validated_input))

    try:
        result = validate_model(TurnResult, parsed_payload)
    except ValidationError as error:
        return model_to_dict(
            _safe_error_result(["GM 回覆不符合 TurnResult Schema."] + validation_errors(error), validated_input)
        )

    result_dict = model_to_dict(result)
    if parse_warning:
        result_dict["warnings"].append(parse_warning)
    return result_dict


def build_prompt(turn_input: TurnInput) -> str:
    prompt_rules = PROMPT_PATH.read_text(encoding="utf-8")
    return (
        f"{prompt_rules}\n\n"
        "TurnInput JSON:\n"
        f"{json.dumps(model_to_dict(turn_input), ensure_ascii=False, indent=2)}\n\n"
        "TurnResult JSON Schema:\n"
        f"{json.dumps(model_json_schema(TurnResult), ensure_ascii=False, indent=2)}"
    )


def parse_json_payload(raw_response: str) -> tuple[dict[str, Any] | None, str | None]:
    text = raw_response.strip()
    if not text:
        return None, None

    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else None, None
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None, None

    candidate = text[start : end + 1]
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return None, None
    if not isinstance(payload, dict):
        return None, None
    return payload, "GM 回覆包含 JSON 外文字，已嘗試擷取 JSON。"


def _safe_error_result(errors: list[str], turn_input: TurnInput | None = None) -> TurnResult:
    player_input = turn_input.player_input if turn_input is not None else ""
    return TurnResult(
        interpretation=ActionInterpretation(
            primary_intent="unknown",
            secondary_intent=None,
            target=None,
            object=None,
            method=None,
            player_goal=player_input or None,
            ambiguity="無法完成回合處理。",
            confidence=0.0,
        ),
        ruling=Ruling(
            possible=False,
            reason="系統無法安全完成本回合裁定。",
            requires_roll=False,
            roll_type=None,
            difficulty=None,
            applicable_rules=[],
        ),
        dice_request=DiceRequest(
            needed=False,
            dice=None,
            modifier_source=None,
            difficulty=None,
            reason=None,
        ),
        resolution=Resolution(
            outcome="本回合未被套用。",
            success=False,
            consequences=[],
        ),
        state_update=StateUpdate(
            player_changes={},
            npc_changes={},
            world_changes={},
            inventory_changes={},
            clue_changes={},
            location_changes={},
            event_changes={},
        ),
        narration="系統暫時無法安全處理這個回合。請確認輸入資料與本機 AI 狀態後再試一次。",
        warnings=[],
        errors=errors,
    )
