from __future__ import annotations

from typing import Any

try:
    from .ai_provider import AIClient
    from .orchestrator import TurnOrchestrator
    from .schemas import model_to_dict
except ImportError:
    from ai_provider import AIClient
    from orchestrator import TurnOrchestrator
    from schemas import model_to_dict


__all__ = ["process_turn"]


def process_turn(turn_input: Any, ai_client: AIClient | None = None) -> dict[str, Any]:
    """Process one turn exclusively through the Turn Orchestrator."""
    return model_to_dict(TurnOrchestrator(ai_client=ai_client).process(turn_input))
