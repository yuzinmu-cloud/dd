from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

try:
    from .processor import process_turn
    from .schemas import DiceResult, GMContext, SessionResult, TurnResult, model_to_dict, validate_model
    from .state_update_applier import apply_state_update, context_update_diff
    from .validator import Validator
except ImportError:
    from processor import process_turn
    from schemas import DiceResult, GMContext, SessionResult, TurnResult, model_to_dict, validate_model
    from state_update_applier import apply_state_update, context_update_diff
    from validator import Validator


InputProvider = Callable[[dict[str, Any]], str | None]
OutputHandler = Callable[[dict[str, Any]], None]
EXIT_COMMANDS = {"離開", "quit", "exit"}
RECENT_EVENTS_LIMIT = 20
RECENT_CONVERSATION_LIMIT = 12
PLAYER_DECISIONS_LIMIT = 30
UNRESOLVED_CONSEQUENCES_LIMIT = 20


def run_session(initial_context: Any, input_provider: InputProvider, output_handler: OutputHandler) -> SessionResult:
    context = validate_model(GMContext, deepcopy(model_to_dict(initial_context) if isinstance(initial_context, GMContext) else initial_context))
    context_errors = Validator._context_errors(context)
    if context_errors:
        raise ValueError("; ".join(context_errors))

    turns: list[TurnResult] = []
    warnings: list[str] = []
    errors: list[str] = []
    status = "active"
    pending_input: str | None = None
    pending_request: dict[str, Any] | None = None

    while status == "active":
        request_type = "dice_result" if pending_input is not None else "player_input"
        request = {
            "type": request_type,
            "context": model_to_dict(context),
            "dice_request": pending_request,
            "player_input": pending_input,
        }
        try:
            raw_input = input_provider(request)
        except Exception as error:
            errors.append(f"Input Provider 失敗：{error}")
            status = "aborted"
            break
        if raw_input is None:
            status = "aborted"
            break
        command = raw_input.strip()
        if command.lower() in EXIT_COMMANDS or command == "離開":
            status = "completed"
            break

        dice_result: DiceResult | None = None
        if pending_input is not None:
            dice_result = _parse_roll(command)
            if dice_result is None:
                message = "骰子格式錯誤，請輸入 roll <數字>，例如 roll 14。"
                warnings.append(message)
                _emit(output_handler, {"type": "warning", "message": message}, warnings)
                continue
            player_input = pending_input
        else:
            if not command:
                message = "玩家輸入不可為空。"
                warnings.append(message)
                _emit(output_handler, {"type": "warning", "message": message}, warnings)
                continue
            player_input = command

        result_payload = process_turn(
            {"player_input": player_input, "context": model_to_dict(context), "dice_result": model_to_dict(dice_result) if dice_result else None}
        )
        result = validate_model(TurnResult, result_payload)
        is_pending = _is_pending(result, dice_result)
        _emit(
            output_handler,
            {
                "type": "turn_result",
                "result": model_to_dict(result),
                "context": model_to_dict(context),
                "player_input": player_input,
                "dice_result": model_to_dict(dice_result) if dice_result else None,
                "pending": is_pending,
            },
            warnings,
        )
        if is_pending:
            if result.dice_request.needed:
                pending_input = player_input
                pending_request = model_to_dict(result.dice_request)
            else:
                warnings.append(f"回合等待必要資料：{result.resolution_status}")
                pending_input = None
                pending_request = None
            continue

        pending_input = None
        pending_request = None
        before_update = context
        updated_context, apply_errors = apply_state_update(context, result.state_update)
        applied_diff = context_update_diff(before_update, updated_context)
        errors.extend(apply_errors)
        context = _update_history_and_session(
            updated_context,
            player_input,
            result,
            state_update_applied=not apply_errors,
        )
        turns.append(result)
        warnings.extend(result.warnings)
        errors.extend(result.errors)
        status = result.session_status
        _emit(
            output_handler,
            {
                "type": "context_updated",
                "context": model_to_dict(context),
                "apply_errors": apply_errors,
                "applied_diff": applied_diff,
                "turn_result": model_to_dict(result),
            },
            warnings,
        )

    final = SessionResult(
        final_context=context,
        turns=turns,
        turn_count=len(turns),
        session_status=status,
        warnings=warnings,
        errors=errors,
    )
    _emit(output_handler, {"type": "session_end", "result": model_to_dict(final)}, warnings)
    return final


def _parse_roll(text: str) -> DiceResult | None:
    parts = text.split()
    if len(parts) != 2 or parts[0].lower() != "roll":
        return None
    try:
        total = int(parts[1])
    except ValueError:
        return None
    return DiceResult(status="provided", total=total, raw={"total": total})


def _is_pending(result: TurnResult, supplied_dice: DiceResult | None) -> bool:
    explicit_pending = bool(result.resolution_status and result.resolution_status.startswith("pending_"))
    legacy_dice_pending = result.dice_request.needed and supplied_dice is None
    return (explicit_pending or legacy_dice_pending) and result.resolution.success is None


def _update_history_and_session(
    context: GMContext,
    player_input: str,
    result: TurnResult,
    state_update_applied: bool,
) -> GMContext:
    data = deepcopy(model_to_dict(context))
    history = data["history"]
    session = data["session"]
    history["player_decisions"].append(player_input)
    history["recent_events"].append(result.resolution.outcome)
    for consequence in result.resolution.consequences:
        if consequence not in history["unresolved_consequences"]:
            history["unresolved_consequences"].append(consequence)
    if state_update_applied:
        world_summary = _change_summary(result.state_update.world_changes, result.state_update.location_changes)
        if world_summary:
            history["world_changes"].append(world_summary)
        for npc_id, changes in result.state_update.npc_changes.items():
            history["npc_memories"].setdefault(npc_id, []).append(_change_summary(changes))
    history["recent_events"] = history["recent_events"][-RECENT_EVENTS_LIMIT:]
    history["player_decisions"] = history["player_decisions"][-PLAYER_DECISIONS_LIMIT:]
    history["unresolved_consequences"] = history["unresolved_consequences"][-UNRESOLVED_CONSEQUENCES_LIMIT:]

    session["turn_number"] += 1
    session["recent_conversation"].extend(
        [{"speaker": "player", "text": player_input}, {"speaker": "gm", "text": result.narration}]
    )
    session["recent_conversation"] = session["recent_conversation"][-RECENT_CONVERSATION_LIMIT:]
    return validate_model(GMContext, data)


def _change_summary(*changes: dict[str, Any]) -> str:
    parts: list[str] = []
    for change in changes:
        for key, value in change.items():
            parts.append(f"{key}={value}")
    return "; ".join(parts)


def _emit(handler: OutputHandler, event: dict[str, Any], warnings: list[str]) -> None:
    try:
        handler(event)
    except Exception as error:
        warnings.append(f"Output Handler 失敗：{error}")
