"""Victory condition evaluation."""
from __future__ import annotations

import logging

from backend.models.game_state import GameState

logger = logging.getLogger(__name__)


class VictoryManager:
    """Evaluates win/loss conditions each turn."""

    @staticmethod
    def check_victory(state: GameState) -> dict:
        """
        Check all victory conditions and update game state if met.

        Conditions:
        1. Military: all enemy units destroyed.
        2. Diplomatic: alliance threshold reached with all enemies.
        3. Turn limit: most units remaining wins.
        """
        if state.game_over:
            return {"game_over": True, "winner": state.winner}

        if state.player_faction is None or state.enemy_faction is None:
            return {"game_over": False}

        player_id = state.player_faction.faction_id
        enemy_id = state.enemy_faction.faction_id

        player_units = state.board.get_units_by_faction(player_id)
        enemy_units = state.board.get_units_by_faction(enemy_id)

        if len(enemy_units) == 0:
            state.game_over = True
            state.winner = player_id
            state.add_event("victory", "Sotilaallinen voitto! Kaikki viholliset tuhottu!")
            logger.info("Victory: %s wins by military conquest", player_id)
            return {"game_over": True, "winner": player_id, "type": "military"}

        if len(player_units) == 0:
            state.game_over = True
            state.winner = enemy_id
            state.add_event("defeat", "Tappio! Kaikki yksikösi on tuhottu.")
            logger.info("Defeat: %s loses all units", player_id)
            return {"game_over": True, "winner": enemy_id, "type": "military"}

        rel_key = f"{player_id}:{enemy_id}"
        if state.diplomacy_relations.get(rel_key, 0) >= 50:
            state.game_over = True
            state.winner = player_id
            state.add_event("victory", "Diplomaattinen voitto! Liittolaisuus saavutettu!")
            logger.info("Victory: %s wins by diplomacy", player_id)
            return {"game_over": True, "winner": player_id, "type": "diplomacy"}

        if state.turn >= state.max_turns:
            if len(player_units) >= len(enemy_units):
                winner = player_id
                state.add_event("victory", "Voitto! Enemmän yksiköitä kuin vihollisella.")
            else:
                winner = enemy_id
                state.add_event("defeat", "Tappio! Vihollisella oli enemmän yksiköitä.")
            state.game_over = True
            state.winner = winner
            logger.info("Victory by turn limit: %s", winner)
            return {"game_over": True, "winner": winner, "type": "attrition"}

        return {"game_over": False}
