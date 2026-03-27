"""Game engine — combat, diplomacy, resources, turns, victory."""

from backend.engine.combat import CombatEngine
from backend.engine.diplomacy import DiplomacyEngine
from backend.engine.resources import ResourceEngine
from backend.engine.turns import TurnManager
from backend.engine.victory import VictoryManager
from backend.engine.game_engine import GameEngine

__all__ = [
    "CombatEngine",
    "DiplomacyEngine",
    "ResourceEngine",
    "TurnManager",
    "VictoryManager",
    "GameEngine",
]
