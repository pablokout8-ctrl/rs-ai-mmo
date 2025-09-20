"""NPC domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .player import Position


@dataclass
class NpcDefinition:
    npc_id: int
    name: str
    combat_level: int
    hitpoints: int
    respawn_ticks: int

    @classmethod
    def from_dict(cls, data: Dict) -> "NpcDefinition":
        return cls(
            npc_id=int(data["id"]),
            name=data.get("name", "Unknown"),
            combat_level=int(data.get("combat_level", 1)),
            hitpoints=int(data.get("hitpoints", 10)),
            respawn_ticks=int(data.get("respawn_ticks", 10)),
        )


@dataclass
class NpcSpawn:
    definition: NpcDefinition
    position: Position
    current_hitpoints: int = field(init=False)
    respawn_timer: int = 0

    def __post_init__(self) -> None:
        self.current_hitpoints = self.definition.hitpoints

    def is_alive(self) -> bool:
        return self.current_hitpoints > 0

    def damage(self, value: int) -> None:
        self.current_hitpoints = max(0, self.current_hitpoints - max(0, value))
        if self.current_hitpoints == 0:
            self.respawn_timer = self.definition.respawn_ticks

    def tick(self) -> None:
        if self.is_alive():
            return
        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            if self.respawn_timer == 0:
                self.current_hitpoints = self.definition.hitpoints
