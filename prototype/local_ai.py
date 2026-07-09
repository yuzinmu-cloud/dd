from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_LOCAL_MODEL = "qwen2.5:7b"
CONNECTION_ERROR_MESSAGE = "無法連接本機 AI。請確認 Ollama 已啟動，並已安裝模型。"
MODEL_NOT_FOUND_MESSAGE = "找不到指定模型。請先執行：ollama run qwen2.5:7b"


def get_local_model() -> str:
    return os.getenv("AIGMOS_LOCAL_MODEL", DEFAULT_LOCAL_MODEL)


def generate_local_response(prompt: str) -> str:
    model = get_local_model()
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
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
            return MODEL_NOT_FOUND_MESSAGE
        return f"本機 AI 回傳錯誤：HTTP {error.code}"
    except (URLError, TimeoutError, ConnectionError):
        return CONNECTION_ERROR_MESSAGE
    except json.JSONDecodeError:
        return "本機 AI 回應格式無法解析。請確認 Ollama 是否正常運作。"

    if "error" in data:
        error_text = str(data["error"])
        if _looks_like_missing_model(error_text):
            return MODEL_NOT_FOUND_MESSAGE
        return f"本機 AI 回傳錯誤：{error_text}"

    return str(data.get("response", "本機 AI 沒有回應。你要怎麼做？")).strip()


def _looks_like_missing_model(text: str) -> bool:
    lowered = text.lower()
    return "not found" in lowered or "model" in lowered and "pull" in lowered
