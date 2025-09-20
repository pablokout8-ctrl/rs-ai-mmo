"""Skill definitions and experience calculations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

MAX_LEVEL = 99
MAX_XP = 200_000_000

SKILL_NAMES = [
    "attack",
    "defence",
    "strength",
    "hitpoints",
    "ranged",
    "prayer",
    "magic",
    "cooking",
    "woodcutting",
    "fletching",
    "fishing",
    "firemaking",
    "crafting",
    "smithing",
    "mining",
    "herblore",
    "agility",
    "thieving",
    "slayer",
    "farming",
    "runecrafting",
    "hunter",
    "construction",
    "summoning",
    "dungeoneering",
]

# Pre-compute RuneScape XP table for 1-99 based on Jagex formula.
_EXPERIENCE_TABLE = [0]
_acc = 0.0
for level in range(1, MAX_LEVEL + 1):
    _acc += level + 300.0 * 2 ** (level / 7)
    _EXPERIENCE_TABLE.append(int(_acc / 4))


def level_for_xp(xp: int) -> int:
    """Return the combat level for the provided experience."""

    xp = max(0, min(int(xp), MAX_XP))
    for level in range(1, MAX_LEVEL + 1):
        if xp < _EXPERIENCE_TABLE[level]:
            return level - 1
    return MAX_LEVEL


def xp_for_level(level: int) -> int:
    """Return the minimum XP required to reach a given level."""

    level = max(1, min(int(level), MAX_LEVEL))
    return _EXPERIENCE_TABLE[level]


@dataclass
class Skill:
    name: str
    level: int
    xp: int

    def add_xp(self, amount: int) -> None:
        """Increase experience and adjust level."""

        if amount <= 0:
            return
        self.xp = min(MAX_XP, self.xp + int(amount))
        new_level = level_for_xp(self.xp)
        if new_level > self.level:
            self.level = new_level


class SkillSet(dict):
    """Dictionary-like container for player skills."""

    def __init__(self) -> None:
        super().__init__({name: Skill(name, 1 if name != "hitpoints" else 10, 0) for name in SKILL_NAMES})

    def total_level(self) -> int:
        return sum(skill.level for skill in self.values())

    def to_dict(self) -> Dict[str, Dict[str, int]]:
        return {name: {"level": skill.level, "xp": skill.xp} for name, skill in self.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Dict[str, int]]) -> "SkillSet":
        skillset = cls()
        for name, skill_data in data.items():
            if name in skillset:
                skill = skillset[name]
                skill.level = int(skill_data.get("level", skill.level))
                skill.xp = int(skill_data.get("xp", skill.xp))
        return skillset
