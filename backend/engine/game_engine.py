"""Central game engine that orchestrates all subsystems."""
from __future__ import annotations

import logging
from typing import Optional

from backend.models.game_state import GameState
from backend.models.board import Board
from backend.models.faction import Faction, FACTIONS, get_faction_by_index
from backend.models.unit import Unit
from backend.engine.combat import CombatEngine
from backend.engine.diplomacy import DiplomacyEngine
from backend.engine.resources import ResourceEngine
from backend.engine.turns import TurnManager
from backend.engine.victory import VictoryManager

logger = logging.getLogger(__name__)

ENEMY_SPAWN_POSITIONS: list[tuple[int, int]] = [
    (9, 9), (8, 9), (9, 8), (8, 8), (7, 9), (9, 7),
]

PLAYER_SPAWN_POSITIONS: list[tuple[int, int]] = [
    (0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2),
]


class GameEngine:
    """Top-level controller: all game actions go through here."""

    def __init__(self, width: int = 10, height: int = 10, max_turns: int = 30) -> None:
        self._width = width
        self._height = height
        self._max_turns = max_turns
        self._state: Optional[GameState] = None

    @property
    def state(self) -> Optional[GameState]:
        return self._state

    def new_game(self, faction_index: int) -> dict:
        """Initialize a new game with the chosen faction."""
        faction = get_faction_by_index(faction_index)
        if faction is None:
            return {"success": False, "error": f"Virheellinen heimovalinta: {faction_index}"}

        enemy_faction = FACTIONS[(faction_index + 2) % len(FACTIONS)]

        state = GameState(
            board=Board(self._width, self._height),
            player_faction=faction,
            enemy_faction=enemy_faction,
            max_turns=self._max_turns,
            resources={faction.faction_id: 10, enemy_faction.faction_id: 10},
        )

        self._spawn_units(state, faction, PLAYER_SPAWN_POSITIONS)
        self._spawn_units(state, enemy_faction, ENEMY_SPAWN_POSITIONS)

        state.add_event("game_start", f"Peli alkoi! Heimosi: {faction.name}")
        self._state = state

        logger.info(
            "New game started: %s vs %s", faction.name, enemy_faction.name
        )

        return {
            "success": True,
            "status": "started",
            "game_id": state.game_id,
            "faction": faction.to_dict(),
            "enemy_faction": enemy_faction.to_dict(),
        }

    def _spawn_units(
        self, state: GameState, faction: Faction, positions: list[tuple[int, int]]
    ) -> None:
        for i, unit_type_str in enumerate(faction.start_units):
            if i >= len(positions):
                break
            x, y = positions[i]
            unit = Unit.create(
                unit_type_str,
                faction.faction_id,
                bonus_strength=faction.bonus_strength,
                bonus_defense=faction.bonus_defense,
            )
            state.board.place_unit(x, y, unit)

    def get_state(self) -> dict:
        """Return full serialized game state."""
        if self._state is None:
            return {"error": "Peliä ei ole aloitettu."}
        result = self._state.to_dict()
        victory = VictoryManager.check_victory(self._state)
        result["victory_check"] = victory
        return result

    def perform_action(self, action: str, **params: object) -> dict:
        """Single entry point for all game actions with validation."""
        if self._state is None:
            return {"success": False, "error": "Peliä ei ole aloitettu."}

        if not self._state.validate_action(action):
            phase_name = self._state.phase.label
            return {
                "success": False,
                "error": f"Toiminto '{action}' ei ole sallittu "
                         f"vaiheessa '{phase_name}'.",
                "allowed": sorted(self._state.allowed_actions),
            }

        handlers = {
            "move": self._handle_move,
            "attack": self._handle_attack,
            "diplomacy": self._handle_diplomacy,
            "collect": self._handle_collect,
            "heal": self._handle_heal,
            "recruit": self._handle_recruit,
            "end_phase": self._handle_end_phase,
        }

        handler = handlers.get(action)
        if handler is None:
            return {"success": False, "error": f"Tuntematon toiminto: {action}"}

        result = handler(**params)

        victory = VictoryManager.check_victory(self._state)
        result["victory_check"] = victory

        return result

    def _handle_move(self, **params: object) -> dict:
        from_x = int(params.get("from_x", -1))
        from_y = int(params.get("from_y", -1))
        to_x = int(params.get("to_x", -1))
        to_y = int(params.get("to_y", -1))

        unit = self._state.board.get_unit(from_x, from_y)
        if unit is None:
            return {"success": False, "error": "Yksikköä ei löydy lähtöruudusta."}
        if unit.faction_id != self._state.player_faction.faction_id:
            return {"success": False, "error": "Yksikkö ei kuulu sinulle."}
        if unit.has_acted:
            return {"success": False, "error": "Yksikkö on jo liikkunut tällä vuorolla."}

        if not self._state.board.move_unit(from_x, from_y, to_x, to_y):
            return {
                "success": False,
                "error": "Siirto ei onnistu (varattu ruutu tai liian kaukana).",
            }

        unit.has_acted = True
        message = f"Yksikkö siirtyi ({from_x},{from_y}) -> ({to_x},{to_y})"
        self._state.add_event("move", message)
        return {"success": True, "message": message}

    def _handle_attack(self, **params: object) -> dict:
        ax = int(params.get("attacker_x", -1))
        ay = int(params.get("attacker_y", -1))
        tx = int(params.get("target_x", -1))
        ty = int(params.get("target_y", -1))

        result = CombatEngine.resolve_attack(self._state.board, ax, ay, tx, ty)
        if result["success"]:
            msg = f"Hyökkäys aiheutti {result['damage']} vahinkoa!"
            if result["destroyed"]:
                msg += " Vihollinen tuhottu!"
            self._state.add_event("combat", msg)
            result["message"] = msg

            if self._state.enemy_faction:
                enemy_id = self._state.enemy_faction.faction_id
                DiplomacyEngine.worsen_relations(self._state, enemy_id, 5)
        return result

    def _handle_diplomacy(self, **params: object) -> dict:
        default_target = ""
        if self._state.enemy_faction:
            default_target = self._state.enemy_faction.faction_id
        target = str(params.get("target", default_target))
        return DiplomacyEngine.improve_relations(self._state, target)

    def _handle_collect(self, **_params: object) -> dict:
        return ResourceEngine.collect_resources(self._state)

    def _handle_heal(self, **params: object) -> dict:
        x = int(params.get("x", -1))
        y = int(params.get("y", -1))
        return ResourceEngine.heal_unit(self._state, x, y)

    def _handle_recruit(self, **params: object) -> dict:
        unit_type = str(params.get("unit_type", ""))
        x = int(params.get("x", -1))
        y = int(params.get("y", -1))
        return ResourceEngine.recruit_unit(self._state, unit_type, x, y)

    def _handle_end_phase(self, **_params: object) -> dict:
        return TurnManager.end_phase(self._state)
