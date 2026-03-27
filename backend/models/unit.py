"""Unit model with type enumeration and stat tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import uuid


class UnitType(str, Enum):
    """Types of units available in the game."""

    WARRIOR = "warrior"
    CAVALRY = "cavalry"
    ARCHER = "archer"
    CHIEF = "chief"


UNIT_BASE_STATS: dict[UnitType, dict[str, int]] = {
    UnitType.WARRIOR: {"strength": 8, "defense": 6, "speed": 1, "range": 1, "max_hp": 20},
    UnitType.CAVALRY: {"strength": 10, "defense": 4, "speed": 3, "range": 1, "max_hp": 18},
    UnitType.ARCHER: {"strength": 6, "defense": 3, "speed": 1, "range": 3, "max_hp": 12},
    UnitType.CHIEF: {"strength": 12, "defense": 8, "speed": 2, "range": 1, "max_hp": 30},
}


@dataclass
class Unit:
    """A single game unit on the board."""

    unit_type: UnitType
    faction_id: str
    strength: int = 0
    defense: int = 0
    speed: int = 0
    attack_range: int = 1
    hp: int = 0
    max_hp: int = 0
    uid: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    has_acted: bool = False

    def __post_init__(self) -> None:
        base = UNIT_BASE_STATS[self.unit_type]
        if self.strength == 0:
            self.strength = base["strength"]
        if self.defense == 0:
            self.defense = base["defense"]
        if self.speed == 0:
            self.speed = base["speed"]
        if self.attack_range == 1 and base["range"] != 1:
            self.attack_range = base["range"]
        if self.max_hp == 0:
            self.max_hp = base["max_hp"]
        if self.hp == 0:
            self.hp = self.max_hp

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """Apply damage and return actual damage dealt."""
        actual = min(amount, self.hp)
        self.hp -= actual
        return actual

    def heal(self, amount: int) -> int:
        """Heal unit and return actual amount healed."""
        actual = min(amount, self.max_hp - self.hp)
        self.hp += actual
        return actual

    def reset_turn(self) -> None:
        """Reset per-turn flags."""
        self.has_acted = False

    def to_dict(self) -> dict:
        """Serialize for API responses."""
        return {
            "uid": self.uid,
            "type": self.unit_type.value,
            "faction_id": self.faction_id,
            "strength": self.strength,
            "defense": self.defense,
            "speed": self.speed,
            "range": self.attack_range,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "has_acted": self.has_acted,
        }

    @classmethod
    def create(
        cls,
        unit_type: UnitType | str,
        faction_id: str,
        bonus_strength: int = 0,
        bonus_defense: int = 0,
    ) -> Unit:
        """Factory with optional faction bonuses applied."""
        if isinstance(unit_type, str):
            unit_type = UnitType(unit_type)
        unit = cls(unit_type=unit_type, faction_id=faction_id)
        unit.strength += bonus_strength
        unit.defense += bonus_defense
        return unit
