"""Combat resolution engine with terrain and range support."""
from __future__ import annotations

import logging
import random

from backend.models.board import Board
from backend.models.unit import Unit

logger = logging.getLogger(__name__)

TERRAIN_DEFENSE_BONUS = 2
CRITICAL_HIT_CHANCE = 0.1
MIN_DAMAGE = 1


class CombatEngine:
    """Resolves attacks between units on the board."""

    @staticmethod
    def calculate_damage(attacker: Unit, defender: Unit, terrain_bonus: int = 0) -> int:
        """Pure damage calculation with optional terrain modifier."""
        base = attacker.strength - (defender.defense + terrain_bonus)
        damage = max(MIN_DAMAGE, base)
        if random.random() < CRITICAL_HIT_CHANCE:
            damage = int(damage * 1.5)
            logger.debug("Critical hit! Damage boosted to %d", damage)
        return damage

    @staticmethod
    def resolve_attack(
        board: Board,
        attacker_x: int,
        attacker_y: int,
        target_x: int,
        target_y: int,
    ) -> dict:
        """
        Execute an attack between two board positions.
        Returns a result dict with damage dealt and whether target was destroyed.
        """
        attacker = board.get_unit(attacker_x, attacker_y)
        defender = board.get_unit(target_x, target_y)

        if attacker is None:
            return {"success": False, "error": "Hyökkääjää ei löydy."}
        if defender is None:
            return {"success": False, "error": "Kohdetta ei löydy."}
        if attacker.faction_id == defender.faction_id:
            return {"success": False, "error": "Et voi hyökätä omia yksiköitä vastaan."}
        if attacker.has_acted:
            return {"success": False, "error": "Yksikkö on jo toiminut tällä vuorolla."}

        dist = Board.distance(attacker_x, attacker_y, target_x, target_y)
        if dist > attacker.attack_range:
            return {"success": False, "error": "Kohde on kantaman ulkopuolella."}

        damage = CombatEngine.calculate_damage(attacker, defender)
        actual = defender.take_damage(damage)
        attacker.has_acted = True
        destroyed = not defender.alive

        if destroyed:
            board.remove_unit(target_x, target_y)
            logger.info(
                "Unit %s destroyed unit %s with %d damage",
                attacker.uid, defender.uid, actual,
            )

        return {
            "success": True,
            "damage": actual,
            "destroyed": destroyed,
            "attacker_uid": attacker.uid,
            "defender_uid": defender.uid,
            "defender_hp": max(0, defender.hp),
        }
