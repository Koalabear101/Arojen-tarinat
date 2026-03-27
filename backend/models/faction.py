"""Faction definitions — single source of truth for all faction data."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Faction:
    """Immutable faction descriptor."""

    faction_id: str
    name: str
    color: str
    bonus_description: str
    bonus_strength: int = 0
    bonus_defense: int = 0
    start_units: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "id": self.faction_id,
            "name": self.name,
            "color": self.color,
            "bonus": self.bonus_description,
            "start_units": list(self.start_units),
        }


FACTIONS: tuple[Faction, ...] = (
    Faction(
        faction_id="mongol",
        name="Mongoli-heimo",
        color="#D4A017",
        bonus_description="Ratsuväen bonus, nopea liikkeelläolo",
        bonus_strength=2,
        bonus_defense=0,
        start_units=("cavalry", "cavalry", "cavalry", "warrior", "warrior", "chief"),
    ),
    Faction(
        faction_id="china",
        name="Kiinan dynastia",
        color="#C62828",
        bonus_description="Linnoitukset, teknologia-edistykset",
        bonus_strength=0,
        bonus_defense=2,
        start_units=("warrior", "warrior", "warrior", "archer", "archer", "chief"),
    ),
    Faction(
        faction_id="persia",
        name="Persialainen valtakunta",
        color="#1565C0",
        bonus_description="Kauppataidot, kulttuuriresurssit",
        bonus_strength=1,
        bonus_defense=1,
        start_units=("warrior", "warrior", "cavalry", "cavalry", "archer", "chief"),
    ),
    Faction(
        faction_id="russia",
        name="Venäläiset ruhtinaskunnat",
        color="#2E7D32",
        bonus_description="Talvisotataktiikat, metsäresurssit",
        bonus_strength=1,
        bonus_defense=1,
        start_units=("warrior", "warrior", "warrior", "cavalry", "archer", "chief"),
    ),
)

FACTION_MAP: dict[str, Faction] = {f.faction_id: f for f in FACTIONS}


def get_faction(faction_id: str) -> Optional[Faction]:
    """Look up a faction by id."""
    return FACTION_MAP.get(faction_id)


def get_faction_by_index(index: int) -> Optional[Faction]:
    """Look up a faction by its ordinal index (0-based)."""
    if 0 <= index < len(FACTIONS):
        return FACTIONS[index]
    return None
