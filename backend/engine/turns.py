"""Turn and phase management."""
from __future__ import annotations

import logging

from backend.models.game_state import GameState

logger = logging.getLogger(__name__)


class TurnManager:
    """Controls turn and phase progression with validation."""

    @staticmethod
    def end_phase(state: GameState) -> dict:
        """Advance to the next phase (or next turn if last phase)."""
        if state.game_over:
            return {"success": False, "error": "Peli on päättynyt."}

        old_phase = state.phase
        new_phase = state.advance_phase()
        new_turn = state.turn

        logger.info("Phase %s -> %s (turn %d)", old_phase.value, new_phase.value, new_turn)

        return {
            "success": True,
            "previous_phase": old_phase.value,
            "new_phase": new_phase.value,
            "phase_label": new_phase.label,
            "phase_description": new_phase.description,
            "turn": new_turn,
            "allowed_actions": sorted(state.allowed_actions),
        }

    @staticmethod
    def get_phase_info(state: GameState) -> dict:
        """Return current phase information."""
        return {
            "phase": state.phase.value,
            "phase_label": state.phase.label,
            "phase_description": state.phase.description,
            "turn": state.turn,
            "allowed_actions": sorted(state.allowed_actions),
        }
