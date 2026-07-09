from __future__ import annotations

import os
from typing import Any

from adventure import SCENE_NAMES
from game_state import GameState


MISSING_API_KEY_MESSAGE = "找不到 OPENAI_API_KEY，請先設定 API 金鑰。"
DEFAULT_MODEL = "gpt-4.1-mini"

AI_GM_INSTRUCTIONS = """
你是 AIGMOS 的 AI Game Master，負責主持一場 DND 風格的單人文字 TRPG 冒險。

請遵守以下規則：
- 一律使用繁體中文（台灣）。
- 扮演沉浸式、清楚、節制的遊戲主持人。
- 保持目前場景與「燭芯礦坑事件」的脈絡。
- 根據玩家輸入、目前場景、狀態記錄與行動紀錄回應。
- 不替玩家決定下一步行動。
- 不直接宣告玩家成功，除非行動非常簡單、沒有風險。
- 遇到危險、對抗、不確定或高風險行動時，要說明「可能需要檢定」。
- 不加入完整規則、戰鬥系統、職業、HP、裝備或法術系統。
- 不假裝有尚未實作的功能。
- 回覆最後必須問：「你要怎麼做？」

回覆長度請控制在 2 到 5 個短段落。
""".strip()


def build_prompt(state: GameState, action: str) -> str:
    scene_name = SCENE_NAMES.get(state.current_scene, state.current_scene)
    notes = _format_list(state.notes, "尚未記錄")
    flags = _format_list(sorted(state.flags.keys()), "尚未觸發")
    recent_actions = _format_list(state.action_log[-8:], "尚無行動紀錄")

    return f"""
冒險名稱：燭芯礦坑事件
目前場景：{scene_name}
內部場景 ID：{state.current_scene}
回合數：{state.turn_count}
是否已結束：{state.ended}
目前結局：{state.ending or "尚未抵達結局"}

已知線索：
{notes}

已觸發事件：
{flags}

最近玩家行動：
{recent_actions}

玩家這回合輸入：
{action}

請以 AI Game Master 的口吻回應玩家。不要輸出狀態 JSON，不要列出內部 ID。
""".strip()


def ask_ai_gm(state: GameState, action: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return MISSING_API_KEY_MESSAGE

    try:
        from openai import OpenAI
    except ImportError:
        return "找不到 openai 套件，請先安裝：pip install openai"

    client = OpenAI(api_key=api_key)
    model = os.getenv("AIGMOS_OPENAI_MODEL", DEFAULT_MODEL)

    response = client.responses.create(
        model=model,
        instructions=AI_GM_INSTRUCTIONS,
        input=build_prompt(state, action),
        max_output_tokens=600,
    )

    return _extract_output_text(response).strip()


def _format_list(items: list[Any], empty_text: str) -> str:
    if not items:
        return f"- {empty_text}"
    return "\n".join(f"- {item}" for item in items)


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
