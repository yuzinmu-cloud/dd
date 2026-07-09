from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


SCENE_IDS = [
    "village_inn",
    "village_square",
    "mine_entrance",
    "mine_interior",
    "final_chamber",
]


@dataclass
class GameState:
    adventure_title: str = "The Candlewick Mine Incident"
    scene_index: int = 0
    turn_count: int = 0
    ended: bool = False
    ending: Optional[str] = None
    flags: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    action_log: list[str] = field(default_factory=list)

    @property
    def current_scene(self) -> str:
        return SCENE_IDS[self.scene_index]

    def record_action(self, action: str) -> None:
        self.turn_count += 1
        self.action_log.append(action)

    def add_note(self, note: str) -> None:
        if note not in self.notes:
            self.notes.append(note)

    def set_flag(self, flag: str) -> None:
        self.flags[flag] = True

    def has_flag(self, flag: str) -> bool:
        return self.flags.get(flag, False)

    def advance_scene(self) -> None:
        if self.scene_index < len(SCENE_IDS) - 1:
            self.scene_index += 1
        else:
            self.ended = True
            if self.ending is None:
                self.ending = "truth_revealing"

    def to_dict(self) -> dict[str, Any]:
        return {
            "adventure_title": self.adventure_title,
            "scene_index": self.scene_index,
            "turn_count": self.turn_count,
            "ended": self.ended,
            "ending": self.ending,
            "flags": self.flags,
            "notes": self.notes,
            "action_log": self.action_log,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        return cls(
            adventure_title=data.get("adventure_title", "The Candlewick Mine Incident"),
            scene_index=int(data.get("scene_index", 0)),
            turn_count=int(data.get("turn_count", 0)),
            ended=bool(data.get("ended", False)),
            ending=data.get("ending"),
            flags=dict(data.get("flags", {})),
            notes=list(data.get("notes", [])),
            action_log=list(data.get("action_log", [])),
        )
