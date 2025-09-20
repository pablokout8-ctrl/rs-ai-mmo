"""Player related domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .skills import SkillSet


@dataclass
class Position:
    x: int
    y: int
    plane: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {"x": self.x, "y": self.y, "plane": self.plane}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "Position":
        return cls(int(data.get("x", 0)), int(data.get("y", 0)), int(data.get("plane", 0)))


@dataclass
class ItemStack:
    item_id: int
    amount: int = 1

    def add(self, value: int) -> None:
        self.amount = max(0, self.amount + value)

    def to_dict(self) -> Dict[str, int]:
        return {"item_id": self.item_id, "amount": self.amount}


@dataclass
class Inventory:
    slots: List[Optional[ItemStack]] = field(default_factory=lambda: [None] * 28)

    def add_item(self, item_id: int, amount: int = 1) -> bool:
        for slot in self.slots:
            if slot and slot.item_id == item_id:
                slot.add(amount)
                return True
        for index, slot in enumerate(self.slots):
            if slot is None:
                self.slots[index] = ItemStack(item_id, amount)
                return True
        return False

    def remove_item(self, item_id: int, amount: int = 1) -> bool:
        for index, slot in enumerate(self.slots):
            if slot and slot.item_id == item_id:
                if slot.amount > amount:
                    slot.add(-amount)
                    return True
                if slot.amount == amount:
                    self.slots[index] = None
                    return True
        return False

    def to_dict(self) -> List[Optional[Dict[str, int]]]:
        result: List[Optional[Dict[str, int]]] = []
        for slot in self.slots:
            result.append(slot.to_dict() if slot else None)
        return result

    @classmethod
    def from_dict(cls, data: List[Optional[Dict[str, int]]]) -> "Inventory":
        inv = cls()
        for index, slot in enumerate(data):
            if slot:
                inv.slots[index] = ItemStack(int(slot["item_id"]), int(slot.get("amount", 1)))
        return inv


@dataclass
class Player:
    username: str
    rights: str = "player"
    position: Position = field(default_factory=lambda: Position(3222, 3218, 0))
    skills: SkillSet = field(default_factory=SkillSet)
    inventory: Inventory = field(default_factory=Inventory)
    chat_messages: List[str] = field(default_factory=list)

    def is_admin(self) -> bool:
        return self.rights == "admin"

    def queue_message(self, message: str) -> None:
        self.chat_messages.append(message)

    def pop_messages(self) -> List[str]:
        messages = list(self.chat_messages)
        self.chat_messages.clear()
        return messages

    def teleport(self, x: int, y: int, plane: int = 0) -> None:
        self.position = Position(x, y, plane)

    def gain_xp(self, skill: str, amount: int) -> None:
        if skill not in self.skills:
            raise KeyError(f"Unknown skill: {skill}")
        self.skills[skill].add_xp(amount)

    def to_dict(self) -> Dict:
        return {
            "username": self.username,
            "rights": self.rights,
            "position": self.position.to_dict(),
            "skills": self.skills.to_dict(),
            "inventory": self.inventory.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Player":
        player = cls(
            username=data["username"],
            rights=data.get("rights", "player"),
        )
        player.position = Position.from_dict(data.get("position", {}))
        player.skills = SkillSet.from_dict(data.get("skills", {}))
        if inventory := data.get("inventory"):
            player.inventory = Inventory.from_dict(inventory)
        return player
