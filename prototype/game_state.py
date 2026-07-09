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

SCENE_LOCATION_NAMES = {
    "village_inn": "酒館",
    "village_square": "村莊廣場",
    "mine_entrance": "礦坑入口",
    "mine_interior": "礦坑深處",
    "final_chamber": "礦坑最深處",
}


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
    player_name: str = "無名冒險者"
    hp: int = 10
    max_hp: int = 10
    inventory: list[str] = field(default_factory=lambda: ["提燈", "舊背包"])
    current_location: str = "酒館"
    known_clues: list[str] = field(default_factory=list)
    npc_memory: dict[str, list[str]] = field(default_factory=dict)
    world_flags: dict[str, bool] = field(default_factory=dict)
    completed_objectives: list[str] = field(default_factory=list)
    failed_objectives: list[str] = field(default_factory=list)

    @property
    def current_scene(self) -> str:
        return SCENE_IDS[self.scene_index]

    def record_action(self, action: str) -> None:
        self.turn_count += 1
        self.action_log.append(action)

    def add_note(self, note: str) -> None:
        if note not in self.notes:
            self.notes.append(note)

    def add_clue(self, clue: str) -> None:
        if clue not in self.known_clues:
            self.known_clues.append(clue)
        self.add_note(clue)

    def remember_npc(self, npc_name: str, memory: str) -> None:
        memories = self.npc_memory.setdefault(npc_name, [])
        if memory not in memories:
            memories.append(memory)

    def set_flag(self, flag: str) -> None:
        self.flags[flag] = True
        self.world_flags[flag] = True

    def has_flag(self, flag: str) -> bool:
        return self.flags.get(flag, False) or self.world_flags.get(flag, False)

    def complete_objective(self, objective: str) -> None:
        if objective not in self.completed_objectives:
            self.completed_objectives.append(objective)

    def fail_objective(self, objective: str) -> None:
        if objective not in self.failed_objectives:
            self.failed_objectives.append(objective)

    def advance_scene(self) -> None:
        if self.scene_index < len(SCENE_IDS) - 1:
            self.scene_index += 1
            self.current_location = SCENE_LOCATION_NAMES[self.current_scene]
        else:
            self.ended = True
            if self.ending is None:
                self.ending = "truth_revealing"
                self.complete_objective("完成燭芯礦坑事件")

    def move_to_scene(self, scene_id: str) -> None:
        if scene_id in SCENE_IDS:
            self.scene_index = SCENE_IDS.index(scene_id)
            self.current_location = SCENE_LOCATION_NAMES[scene_id]

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
            "player_name": self.player_name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "inventory": self.inventory,
            "current_location": self.current_location,
            "known_clues": self.known_clues,
            "npc_memory": self.npc_memory,
            "world_flags": self.world_flags,
            "completed_objectives": self.completed_objectives,
            "failed_objectives": self.failed_objectives,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        scene_index = int(data.get("scene_index", 0))
        scene_index = max(0, min(scene_index, len(SCENE_IDS) - 1))
        current_scene = SCENE_IDS[scene_index]
        return cls(
            adventure_title=data.get("adventure_title", "The Candlewick Mine Incident"),
            scene_index=scene_index,
            turn_count=int(data.get("turn_count", 0)),
            ended=bool(data.get("ended", False)),
            ending=data.get("ending"),
            flags=dict(data.get("flags", {})),
            notes=list(data.get("notes", [])),
            action_log=list(data.get("action_log", [])),
            player_name=data.get("player_name", "無名冒險者"),
            hp=int(data.get("hp", 10)),
            max_hp=int(data.get("max_hp", 10)),
            inventory=list(data.get("inventory", ["提燈", "舊背包"])),
            current_location=data.get("current_location", SCENE_LOCATION_NAMES[current_scene]),
            known_clues=list(data.get("known_clues", data.get("notes", []))),
            npc_memory=dict(data.get("npc_memory", {})),
            world_flags=dict(data.get("world_flags", data.get("flags", {}))),
            completed_objectives=list(data.get("completed_objectives", [])),
            failed_objectives=list(data.get("failed_objectives", [])),
        )
