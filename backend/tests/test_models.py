"""Tests for game domain models."""
import unittest

from backend.models.unit import Unit, UnitType
from backend.models.board import Board
from backend.models.faction import FACTIONS, get_faction, get_faction_by_index
from backend.models.game_state import GameState, Phase


class TestUnit(unittest.TestCase):
    def test_create_warrior(self):
        u = Unit.create("warrior", "mongol")
        self.assertEqual(u.unit_type, UnitType.WARRIOR)
        self.assertEqual(u.faction_id, "mongol")
        self.assertGreater(u.strength, 0)
        self.assertGreater(u.hp, 0)
        self.assertTrue(u.alive)

    def test_create_with_bonus(self):
        u = Unit.create("warrior", "mongol", bonus_strength=3)
        base = Unit.create("warrior", "mongol")
        self.assertEqual(u.strength, base.strength + 3)

    def test_take_damage(self):
        u = Unit.create("warrior", "test")
        initial_hp = u.hp
        actual = u.take_damage(5)
        self.assertEqual(actual, 5)
        self.assertEqual(u.hp, initial_hp - 5)

    def test_take_lethal_damage(self):
        u = Unit.create("warrior", "test")
        u.take_damage(u.hp + 10)
        self.assertFalse(u.alive)
        self.assertEqual(u.hp, 0)

    def test_heal(self):
        u = Unit.create("warrior", "test")
        u.take_damage(10)
        healed = u.heal(5)
        self.assertEqual(healed, 5)

    def test_heal_no_overheal(self):
        u = Unit.create("warrior", "test")
        u.take_damage(3)
        healed = u.heal(100)
        self.assertEqual(healed, 3)
        self.assertEqual(u.hp, u.max_hp)

    def test_to_dict(self):
        u = Unit.create("cavalry", "mongol")
        d = u.to_dict()
        self.assertEqual(d["type"], "cavalry")
        self.assertEqual(d["faction_id"], "mongol")
        self.assertIn("uid", d)

    def test_reset_turn(self):
        u = Unit.create("warrior", "test")
        u.has_acted = True
        u.reset_turn()
        self.assertFalse(u.has_acted)


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board(10, 10)
        self.unit = Unit.create("warrior", "test")

    def test_place_and_get(self):
        self.assertTrue(self.board.place_unit(3, 4, self.unit))
        self.assertIs(self.board.get_unit(3, 4), self.unit)

    def test_place_out_of_bounds(self):
        self.assertFalse(self.board.place_unit(-1, 0, self.unit))
        self.assertFalse(self.board.place_unit(10, 0, self.unit))

    def test_place_occupied(self):
        self.board.place_unit(0, 0, self.unit)
        other = Unit.create("warrior", "other")
        self.assertFalse(self.board.place_unit(0, 0, other))

    def test_remove_unit(self):
        self.board.place_unit(5, 5, self.unit)
        removed = self.board.remove_unit(5, 5)
        self.assertIs(removed, self.unit)
        self.assertIsNone(self.board.get_unit(5, 5))

    def test_move_unit(self):
        self.board.place_unit(0, 0, self.unit)
        self.assertTrue(self.board.move_unit(0, 0, 1, 0))
        self.assertIsNone(self.board.get_unit(0, 0))
        self.assertIs(self.board.get_unit(1, 0), self.unit)

    def test_move_too_far(self):
        self.board.place_unit(0, 0, self.unit)
        self.assertFalse(self.board.move_unit(0, 0, 5, 5))

    def test_find_unit(self):
        self.board.place_unit(3, 7, self.unit)
        pos = self.board.find_unit(self.unit.uid)
        self.assertEqual(pos, (3, 7))

    def test_find_missing_unit(self):
        self.assertIsNone(self.board.find_unit("nonexistent"))

    def test_get_units_by_faction(self):
        u1 = Unit.create("warrior", "a")
        u2 = Unit.create("cavalry", "a")
        u3 = Unit.create("warrior", "b")
        self.board.place_unit(0, 0, u1)
        self.board.place_unit(1, 0, u2)
        self.board.place_unit(2, 0, u3)
        faction_a = self.board.get_units_by_faction("a")
        self.assertEqual(len(faction_a), 2)

    def test_distance(self):
        self.assertEqual(Board.distance(0, 0, 3, 4), 4)
        self.assertEqual(Board.distance(0, 0, 0, 0), 0)
        self.assertEqual(Board.distance(1, 1, 2, 2), 1)

    def test_to_list(self):
        self.board.place_unit(0, 0, self.unit)
        data = self.board.to_list()
        self.assertEqual(len(data), 10)
        self.assertEqual(len(data[0]), 10)
        self.assertIsNotNone(data[0][0])
        self.assertIsNone(data[0][1])


class TestFaction(unittest.TestCase):
    def test_factions_exist(self):
        self.assertEqual(len(FACTIONS), 4)

    def test_get_faction_by_id(self):
        f = get_faction("mongol")
        self.assertIsNotNone(f)
        self.assertEqual(f.name, "Mongoli-heimo")

    def test_get_faction_by_index(self):
        f = get_faction_by_index(0)
        self.assertIsNotNone(f)
        f_invalid = get_faction_by_index(99)
        self.assertIsNone(f_invalid)

    def test_faction_to_dict(self):
        f = FACTIONS[0]
        d = f.to_dict()
        self.assertIn("id", d)
        self.assertIn("name", d)
        self.assertIn("color", d)


class TestGameState(unittest.TestCase):
    def test_initial_phase(self):
        gs = GameState()
        self.assertEqual(gs.phase, Phase.MOVEMENT)
        self.assertEqual(gs.turn, 0)

    def test_advance_phase(self):
        gs = GameState()
        gs.advance_phase()
        self.assertEqual(gs.phase, Phase.COMBAT)
        gs.advance_phase()
        self.assertEqual(gs.phase, Phase.DIPLOMACY)
        gs.advance_phase()
        self.assertEqual(gs.phase, Phase.RESOURCE)
        gs.advance_phase()
        self.assertEqual(gs.phase, Phase.MOVEMENT)
        self.assertEqual(gs.turn, 1)

    def test_allowed_actions(self):
        gs = GameState()
        self.assertIn("move", gs.allowed_actions)
        self.assertIn("end_phase", gs.allowed_actions)
        self.assertNotIn("attack", gs.allowed_actions)

    def test_validate_action(self):
        gs = GameState()
        self.assertTrue(gs.validate_action("move"))
        self.assertFalse(gs.validate_action("attack"))

    def test_add_event(self):
        gs = GameState()
        gs.add_event("test", "hello")
        self.assertEqual(len(gs.events), 1)
        self.assertEqual(gs.events[0]["message"], "hello")

    def test_game_over_actions(self):
        gs = GameState()
        gs.game_over = True
        self.assertEqual(gs.allowed_actions, {"new_game"})


if __name__ == "__main__":
    unittest.main()
