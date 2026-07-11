from __future__ import annotations


INTENT_ALIASES = {
    "kill": "attack",
    "violent_action": "attack",
    "violence": "attack",
    "hostile": "hostile_action",
    "inquiry": "ask",
    "steal": "steal",
    "theft": "steal",
    "pickpocket": "steal",
    "pilfer": "steal",
    "偷": "steal",
    "偷竊": "steal",
    "偷走": "steal",
    "竊取": "steal",
    "扒竊": "steal",
}

STEAL_MARKERS = ("偷竊", "偷走", "竊取", "扒竊", "偷")


def has_steal_semantics(text: str) -> bool:
    if any(marker in text for marker in ("偷竊", "偷走", "竊取", "扒竊")):
        return True
    return "偷" in text and "偷偷" not in text


def normalize_intent(intent: str, raw_player_input: str = "") -> tuple[str, str | None]:
    normalized_source = intent.strip().lower()
    normalized = INTENT_ALIASES.get(normalized_source, normalized_source)
    if has_steal_semantics(raw_player_input) and normalized != "steal":
        return "steal", f"模型將明確偷竊行動標為 {intent or 'empty'}；已正規化為 steal。"
    if normalized != normalized_source:
        return normalized, f"Intent alias {intent!r} 已正規化為 {normalized}。"
    return normalized, None
