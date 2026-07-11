from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_LOCAL_MODEL = "qwen2.5:7b"


def get_local_model() -> str:
    return os.getenv("AIGMOS_LOCAL_MODEL", DEFAULT_LOCAL_MODEL)


def generate_structured_response(prompt: str, schema: dict[str, Any]) -> tuple[str | None, str | None]:
    payload = {
        "model": get_local_model(),
        "prompt": prompt,
        "stream": False,
        "format": schema,
    }

    request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        if _looks_like_missing_model(body):
            return None, f"找不到指定模型。請先執行：ollama run {DEFAULT_LOCAL_MODEL}"
        return None, f"本機 AI 回傳錯誤：HTTP {error.code}"
    except (URLError, TimeoutError, ConnectionError):
        return None, "無法連接本機 AI。請確認 Ollama 已啟動，並已安裝模型。"
    except json.JSONDecodeError:
        return None, "本機 AI 回應格式無法解析。"

    if "error" in data:
        error_text = str(data["error"])
        if _looks_like_missing_model(error_text):
            return None, f"找不到指定模型。請先執行：ollama run {DEFAULT_LOCAL_MODEL}"
        return None, f"本機 AI 回傳錯誤：{error_text}"

    return str(data.get("response", "")).strip(), None


def _looks_like_missing_model(text: str) -> bool:
    lowered = text.lower()
    return "not found" in lowered or ("model" in lowered and "pull" in lowered)
