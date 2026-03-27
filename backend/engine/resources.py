"""Resource collection and management engine."""
from __future__ import annotations

import logging

from backend.models.game_state import GameState
from backend.models.unit import Unit

logger = logging.getLogger(__name__)

BASE_INCOME = 5
TERRITORY_BONUS = 2
HEAL_COST = 3
HEAL_AMOUNT = 5
RECRUIT_COSTS: dict[str, int] = {
    "warrior": 8,
    "cavalry": 12,
    "archer": 10,
}


class ResourceEngine:
    """Handles resource collection, spending, and unit recruitment."""

    @staticmethod
    def collect_resources(state: GameState) -> dict:
        """Collect income based on controlled territory."""
        if state.player_faction is None:
            return {"success": False, "error": "Peliä ei ole aloitettu."}

        faction_id = state.player_faction.faction_id
        units = state.board.get_units_by_faction(faction_id)
        territory_count = len(units)
        income = BASE_INCOME + (territory_count * TERRITORY_BONUS)

        current = state.resources.get(faction_id, 0)
        state.resources[faction_id] = current + income

        message = f"Kerätty {income} resurssia. Yhteensä: {state.resources[faction_id]}"
        state.add_event("resource", message, income=income)

        logger.info(
            "Faction %s collected %d resources (total: %d)",
            faction_id, income, state.resources[faction_id],
        )

        return {
            "success": True,
            "message": message,
            "income": income,
            "total": state.resources[faction_id],
        }

    @staticmethod
    def heal_unit(state: GameState, unit_x: int, unit_y: int) -> dict:
        """Spend resources to heal a unit."""
        if state.player_faction is None:
            return {"success": False, "error": "Peliä ei ole aloitettu."}

        faction_id = state.player_faction.faction_id
        unit = state.board.get_unit(unit_x, unit_y)
        if unit is None:
            return {"success": False, "error": "Yksikköä ei löydy."}
        if unit.faction_id != faction_id:
            return {"success": False, "error": "Yksikkö ei kuulu sinulle."}
        if unit.hp >= unit.max_hp:
            return {"success": False, "error": "Yksikkö on täysissä voimissa."}

        available = state.resources.get(faction_id, 0)
        if available < HEAL_COST:
            return {
                "success": False,
                "error": f"Ei tarpeeksi resursseja (tarvitaan {HEAL_COST}).",
            }

        state.resources[faction_id] = available - HEAL_COST
        healed = unit.heal(HEAL_AMOUNT)
        message = f"Parannettu {healed} HP. Yksikön HP: {unit.hp}/{unit.max_hp}"
        state.add_event("heal", message)

        return {
            "success": True,
            "message": message,
            "healed": healed,
            "hp": unit.hp,
            "max_hp": unit.max_hp,
        }

    @staticmethod
    def recruit_unit(state: GameState, unit_type: str, x: int, y: int) -> dict:
        """Spend resources to place a new unit on the board."""
        if state.player_faction is None:
            return {"success": False, "error": "Peliä ei ole aloitettu."}

        faction_id = state.player_faction.faction_id
        cost = RECRUIT_COSTS.get(unit_type)
        if cost is None:
            return {"success": False, "error": f"Tuntematon yksikkötyyppi: {unit_type}"}

        available = state.resources.get(faction_id, 0)
        if available < cost:
            return {"success": False, "error": f"Ei tarpeeksi resursseja (tarvitaan {cost})."}

        new_unit = Unit.create(
            unit_type,
            faction_id,
            bonus_strength=state.player_faction.bonus_strength,
            bonus_defense=state.player_faction.bonus_defense,
        )

        if not state.board.place_unit(x, y, new_unit):
            return {"success": False, "error": "Kohderuutu on varattu tai laudan ulkopuolella."}

        state.resources[faction_id] = available - cost
        remaining = state.resources[faction_id]
        message = f"Värvätty {unit_type}! Resursseja jäljellä: {remaining}"
        state.add_event("recruit", message)

        return {
            "success": True,
            "message": message,
            "unit": new_unit.to_dict(),
            "remaining": state.resources[faction_id],
        }
