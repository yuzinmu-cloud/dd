from __future__ import annotations

import json
import os
from typing import Any

from adventure import ADVENTURE_PREMISE, SCENE_DESCRIPTIONS, SCENE_NAMES
from game_state import GameState
from local_ai import generate_local_response


MISSING_API_KEY_MESSAGE = "找不到 OPENAI_API_KEY，請先設定 API 金鑰。"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"

STRUCTURED_UPDATE_SCHEMA = {
    "clues_added": [],
    "flags_added": [],
    "npc_memories_added": [],
    "inventory_added": [],
    "inventory_removed": [],
    "hp_delta": 0,
    "objectives_completed": [],
    "objectives_failed": [],
    "ending": None,
    "notes_added": [],
}

AI_GM_INSTRUCTIONS = """
你是 AIGMOS 的 AI Game Master，負責主持一場 DND 風格的單人文字 TRPG 冒險。

請遵守以下規則：
- 一律使用繁體中文（台灣）。
- 扮演沉浸式、清楚、節制的遊戲主持人。
- 保持目前場景與「燭芯礦坑事件」的脈絡。
- 根據玩家輸入、目前場景、狀態記錄、AI Judge 結果與骰子結果回應。
- 不可控制玩家角色，不替玩家決定下一步行動。
- 不可替玩家移動、說話、思考、感受、承諾、追問或採取任何新行動。
- 只能描述玩家已明確輸入行動造成的世界反應、NPC 反應、線索、限制或後果。
- 如果需要呈現玩家行動，用「你提出這個問題後」或「你這麼做時」概括，不要編寫玩家台詞。
- 不直接宣告玩家成功，除非行動非常簡單、沒有風險。
- 必須尊重 AI Judge 結果。
- 如果 AI Judge 認定行動不可能，要描述限制或失敗，不可硬讓玩家成功。
- 如果有骰子結果，必須根據骰子成功或失敗敘事。
- 遇到危險、對抗、不確定或高風險行動時，要說明「可能需要檢定」。
- 不加入完整規則、戰鬥系統、職業、HP、裝備或法術系統。
- 不假裝有尚未實作的功能。

輸出格式必須分成兩段，並使用完全相同的標記：

===NARRATION===
玩家可見敘事。請用 2 到 5 個短段落。最後要留下玩家下一步可行動空間，並問：「你要怎麼做？」

===STATE_UPDATE_JSON===
一個 JSON object。只能包含指定 schema 欄位。不要使用 markdown code block。不要在 JSON 後面補文字。

STATE_UPDATE_JSON 規則：
- 如果沒有要更新的內容，使用空陣列、0 或 null。
- clues_added、flags_added、inventory_added、inventory_removed、objectives_completed、objectives_failed、notes_added 必須是字串陣列。
- npc_memories_added 必須是物件陣列，每個物件格式為 {"npc": "名字", "memory": "記憶"}。
- hp_delta 必須是整數。
- ending 必須是 null、"rescue_focused"、"truth_revealing"、"confrontation_focused" 或 "failure"。
""".strip()


def build_prompt(
    state: GameState,
    action: str,
    judge_result: dict | None = None,
    dice_result: dict | None = None,
) -> str:
    scene_name = SCENE_NAMES.get(state.current_scene, state.current_scene)
    scene_description = SCENE_DESCRIPTIONS.get(state.current_scene, "目前場景描述尚未定義。")
    notes = _format_list(state.notes, "尚未記錄")
    known_clues = _format_list(state.known_clues, "尚未發現")
    inventory = _format_list(state.inventory, "沒有道具")
    flags = _format_mapping(state.world_flags or state.flags, "尚未觸發")
    npc_memory = _format_mapping(state.npc_memory, "尚無 NPC 記憶")
    recent_actions = _format_list(state.action_log[-8:], "尚無行動紀錄")
    completed = _format_list(state.completed_objectives, "尚未完成")
    failed = _format_list(state.failed_objectives, "尚未失敗")

    return f"""
{AI_GM_INSTRUCTIONS}

Structured update schema 範本：
{json.dumps(STRUCTURED_UPDATE_SCHEMA, ensure_ascii=False, indent=2)}

冒險前提：
{ADVENTURE_PREMISE}

目前場景：{scene_name}
目前位置：{state.current_location}
場景描述：{scene_description}
內部場景 ID：{state.current_scene}
玩家角色：{state.player_name}
HP：{state.hp}/{state.max_hp}
回合數：{state.turn_count}
是否已結束：{state.ended}
目前結局：{state.ending or "尚未抵達結局"}

玩家這回合輸入：
{action}

AI Judge 結果：
{json.dumps(judge_result or {}, ensure_ascii=False, indent=2)}

骰子結果：
{json.dumps(dice_result or {}, ensure_ascii=False, indent=2)}

目前線索：
{known_clues}

狀態記錄：
{notes}

道具：
{inventory}

世界事件：
{flags}

NPC 記憶：
{npc_memory}

已完成目標：
{completed}

失敗目標：
{failed}

最近玩家行動：
{recent_actions}

請嚴格依照兩段格式輸出：先輸出 ===NARRATION===，再輸出 ===STATE_UPDATE_JSON===。
""".strip()


def ask_ai_gm(
    state: GameState,
    action: str,
    judge_result: dict | None = None,
    dice_result: dict | None = None,
) -> str:
    prompt = build_prompt(state, action, judge_result, dice_result)
    provider = os.getenv("AIGMOS_AI_PROVIDER", "ollama").lower()

    if provider == "openai":
        return ask_openai_ai_gm(prompt)

    return generate_local_response(prompt)


def ask_openai_ai_gm(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return MISSING_API_KEY_MESSAGE

    try:
        from openai import OpenAI
    except ImportError:
        return "找不到 openai 套件，請先安裝：pip install openai"

    client = OpenAI(api_key=api_key)
    model = os.getenv("AIGMOS_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    response = client.responses.create(
        model=model,
        instructions=AI_GM_INSTRUCTIONS,
        input=prompt,
        max_output_tokens=600,
    )

    return _extract_output_text(response).strip()


def _format_list(items: list[Any], empty_text: str) -> str:
    if not items:
        return f"- {empty_text}"
    return "\n".join(f"- {item}" for item in items)


def _format_mapping(mapping: dict[Any, Any], empty_text: str) -> str:
    if not mapping:
        return f"- {empty_text}"
    return "\n".join(f"- {key}: {value}" for key, value in mapping.items())


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    output = getattr(response, "output", []) or []
    parts: list[str] = []
    for item in output:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                parts.append(text)

    if parts:
        return "\n".join(parts)

    return "遊戲主持人暫時沒有回應。你要怎麼做？"
