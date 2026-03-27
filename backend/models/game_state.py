"""Central game state container with phase/turn management."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid

from backend.models.board import Board
from backend.models.faction import Faction


class Phase(str, Enum):
    """Turn phases in strict order."""

    MOVEMENT = "movement"
    COMBAT = "combat"
    DIPLOMACY = "diplomacy"
    RESOURCE = "resource"

    @property
    def next_phase(self) -> Optional[Phase]:
        phases = list(Phase)
        idx = phases.index(self)
        if idx + 1 < len(phases):
            return phases[idx + 1]
        return None

    @property
    def label(self) -> str:
        return {
            Phase.MOVEMENT: "Liike",
            Phase.COMBAT: "Taistelu",
            Phase.DIPLOMACY: "Diplomatia",
            Phase.RESOURCE: "Resurssit",
        }[self]

    @property
    def description(self) -> str:
        return {
            Phase.MOVEMENT: "Siirrä yksiköitäsi laudalla.",
            Phase.COMBAT: "Hyökkää vihollisyksiköitä vastaan.",
            Phase.DIPLOMACY: "Neuvottele muiden heimojen kanssa.",
            Phase.RESOURCE: "Kerää resursseja ja paranna yksiköitä.",
        }[self]


PHASE_ACTIONS: dict[Phase, set[str]] = {
    Phase.MOVEMENT: {"move", "end_phase"},
    Phase.COMBAT: {"attack", "end_phase"},
    Phase.DIPLOMACY: {"diplomacy", "end_phase"},
    Phase.RESOURCE: {"collect", "heal", "recruit", "end_phase"},
}


@dataclass
class GameState:
    """Encapsulates all mutable state for one game session."""

    game_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    board: Board = field(default_factory=lambda: Board(10, 10))
    player_faction: Optional[Faction] = None
    enemy_faction: Optional[Faction] = None
    turn: int = 0
    phase: Phase = Phase.MOVEMENT
    max_turns: int = 30
    resources: dict[str, int] = field(default_factory=dict)
    diplomacy_relations: dict[str, int] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    game_over: bool = False
    winner: Optional[str] = None

    def add_event(self, event_type: str, message: str, **extra: object) -> None:
        self.events.append({
            "turn": self.turn,
            "phase": self.phase.value,
            "type": event_type,
            "message": message,
            **extra,
        })

    @property
    def allowed_actions(self) -> set[str]:
        if self.game_over:
            return {"new_game"}
        return PHASE_ACTIONS.get(self.phase, set())

    def validate_action(self, action: str) -> bool:
        return action in self.allowed_actions

    def advance_phase(self) -> Phase:
        """Move to the next phase; wraps to MOVEMENT and increments turn."""
        next_p = self.phase.next_phase
        if next_p is None:
            self.turn += 1
            self._reset_units()
            self.phase = Phase.MOVEMENT
        else:
            self.phase = next_p
        return self.phase

    def _reset_units(self) -> None:
        for y in range(self.board.height):
            for x in range(self.board.width):
                u = self.board.get_unit(x, y)
                if u is not None:
                    u.reset_turn()

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "turn": self.turn,
            "phase": self.phase.value,
            "phase_label": self.phase.label,
            "phase_description": self.phase.description,
            "player_faction": self.player_faction.to_dict() if self.player_faction else None,
            "enemy_faction": self.enemy_faction.to_dict() if self.enemy_faction else None,
            "board": self.board.to_list(),
            "resources": self.resources,
            "diplomacy": self.diplomacy_relations,
            "allowed_actions": sorted(self.allowed_actions),
            "game_over": self.game_over,
            "winner": self.winner,
            "events": self.events[-10:],
            "max_turns": self.max_turns,
        }
