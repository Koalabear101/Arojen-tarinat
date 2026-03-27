"""Diplomacy engine for managing inter-faction relations."""
from __future__ import annotations

import logging

from backend.models.game_state import GameState

logger = logging.getLogger(__name__)

DIPLOMACY_INCREMENT = 10
ALLIANCE_THRESHOLD = 50
WAR_THRESHOLD = -30


class DiplomacyEngine:
    """Manages diplomatic actions and relation changes."""

    @staticmethod
    def get_relation(state: GameState, target_faction: str) -> int:
        key = f"{state.player_faction.faction_id}:{target_faction}"
        return state.diplomacy_relations.get(key, 0)

    @staticmethod
    def improve_relations(state: GameState, target_faction: str) -> dict:
        """Attempt diplomacy to improve relations with target faction."""
        if state.player_faction is None:
            return {"success": False, "error": "Peliä ei ole aloitettu."}

        key = f"{state.player_faction.faction_id}:{target_faction}"
        current = state.diplomacy_relations.get(key, 0)
        new_value = current + DIPLOMACY_INCREMENT
        state.diplomacy_relations[key] = new_value

        status = DiplomacyEngine._relation_status(new_value)
        message = f"Diplomatia paransi suhteita! Suhde: {new_value} ({status})"

        logger.info(
            "Relations %s -> %s: %d (%s)",
            state.player_faction.faction_id, target_faction, new_value, status,
        )

        state.add_event("diplomacy", message, target=target_faction, value=new_value)

        return {
            "success": True,
            "message": message,
            "relation": new_value,
            "status": status,
        }

    @staticmethod
    def worsen_relations(state: GameState, target_faction: str, amount: int = 10) -> None:
        """Degrade relations (e.g. after combat)."""
        key = f"{state.player_faction.faction_id}:{target_faction}"
        current = state.diplomacy_relations.get(key, 0)
        state.diplomacy_relations[key] = current - amount

    @staticmethod
    def _relation_status(value: int) -> str:
        if value >= ALLIANCE_THRESHOLD:
            return "Liittolainen"
        if value > 0:
            return "Ystävällinen"
        if value > WAR_THRESHOLD:
            return "Neutraali"
        return "Vihamielinen"
