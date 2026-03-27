"""Tests for game engine subsystems."""
import unittest

from backend.engine.game_engine import GameEngine
from backend.engine.combat import CombatEngine
from backend.engine.diplomacy import DiplomacyEngine
from backend.engine.resources import ResourceEngine
from backend.engine.turns import TurnManager
from backend.engine.victory import VictoryManager
from backend.models.unit import Unit
from backend.models.board import Board
from backend.models.game_state import GameState, Phase
from backend.models.faction import FACTIONS


class TestCombatEngine(unittest.TestCase):
    def test_calculate_damage_positive(self):
        a = Unit.create("cavalry", "a")
        d = Unit.create("archer", "b")
        dmg = CombatEngine.calculate_damage(a, d)
        self.assertGreater(dmg, 0)

    def test_calculate_damage_minimum(self):
        a = Unit.create("archer", "a")
        d = Unit.create("chief", "b")
        dmg = CombatEngine.calculate_damage(a, d)
        self.assertGreaterEqual(dmg, 1)

    def test_resolve_attack_success(self):
        board = Board(10, 10)
        attacker = Unit.create("warrior", "a")
        defender = Unit.create("warrior", "b")
        board.place_unit(0, 0, attacker)
        board.place_unit(1, 0, defender)
        result = CombatEngine.resolve_attack(board, 0, 0, 1, 0)
        self.assertTrue(result["success"])
        self.assertGreater(result["damage"], 0)

    def test_resolve_attack_out_of_range(self):
        board = Board(10, 10)
        attacker = Unit.create("warrior", "a")
        defender = Unit.create("warrior", "b")
        board.place_unit(0, 0, attacker)
        board.place_unit(5, 5, defender)
        result = CombatEngine.resolve_attack(board, 0, 0, 5, 5)
        self.assertFalse(result["success"])

    def test_resolve_attack_friendly_fire(self):
        board = Board(10, 10)
        a = Unit.create("warrior", "same")
        b = Unit.create("warrior", "same")
        board.place_unit(0, 0, a)
        board.place_unit(1, 0, b)
        result = CombatEngine.resolve_attack(board, 0, 0, 1, 0)
        self.assertFalse(result["success"])

    def test_resolve_attack_already_acted(self):
        board = Board(10, 10)
        a = Unit.create("warrior", "a")
        a.has_acted = True
        b = Unit.create("warrior", "b")
        board.place_unit(0, 0, a)
        board.place_unit(1, 0, b)
        result = CombatEngine.resolve_attack(board, 0, 0, 1, 0)
        self.assertFalse(result["success"])


class TestDiplomacyEngine(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.state.player_faction = FACTIONS[0]
        self.state.enemy_faction = FACTIONS[2]

    def test_improve_relations(self):
        result = DiplomacyEngine.improve_relations(self.state, "persia")
        self.assertTrue(result["success"])
        self.assertEqual(result["relation"], 10)

    def test_cumulative_improvement(self):
        DiplomacyEngine.improve_relations(self.state, "persia")
        result = DiplomacyEngine.improve_relations(self.state, "persia")
        self.assertEqual(result["relation"], 20)

    def test_get_relation(self):
        rel = DiplomacyEngine.get_relation(self.state, "persia")
        self.assertEqual(rel, 0)

    def test_worsen_relations(self):
        DiplomacyEngine.improve_relations(self.state, "persia")
        DiplomacyEngine.worsen_relations(self.state, "persia", 5)
        rel = DiplomacyEngine.get_relation(self.state, "persia")
        self.assertEqual(rel, 5)


class TestResourceEngine(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.state.player_faction = FACTIONS[0]
        self.state.resources = {"mongol": 20}

    def test_collect_resources(self):
        result = ResourceEngine.collect_resources(self.state)
        self.assertTrue(result["success"])
        self.assertGreater(result["total"], 20)

    def test_heal_unit(self):
        u = Unit.create("warrior", "mongol")
        u.take_damage(10)
        self.state.board.place_unit(0, 0, u)
        result = ResourceEngine.heal_unit(self.state, 0, 0)
        self.assertTrue(result["success"])

    def test_heal_full_hp(self):
        u = Unit.create("warrior", "mongol")
        self.state.board.place_unit(0, 0, u)
        result = ResourceEngine.heal_unit(self.state, 0, 0)
        self.assertFalse(result["success"])

    def test_recruit_unit(self):
        result = ResourceEngine.recruit_unit(self.state, "warrior", 5, 5)
        self.assertTrue(result["success"])
        self.assertIsNotNone(self.state.board.get_unit(5, 5))

    def test_recruit_insufficient_resources(self):
        self.state.resources = {"mongol": 0}
        result = ResourceEngine.recruit_unit(self.state, "warrior", 5, 5)
        self.assertFalse(result["success"])


class TestTurnManager(unittest.TestCase):
    def test_end_phase(self):
        state = GameState()
        result = TurnManager.end_phase(state)
        self.assertTrue(result["success"])
        self.assertEqual(result["new_phase"], "combat")

    def test_full_turn_cycle(self):
        state = GameState()
        for _ in range(4):
            TurnManager.end_phase(state)
        self.assertEqual(state.turn, 1)
        self.assertEqual(state.phase, Phase.MOVEMENT)


class TestVictoryManager(unittest.TestCase):
    def test_no_victory_initially(self):
        state = GameState()
        state.player_faction = FACTIONS[0]
        state.enemy_faction = FACTIONS[2]
        Unit.create("warrior", "mongol")
        state.board.place_unit(0, 0, Unit.create("warrior", "mongol"))
        state.board.place_unit(9, 9, Unit.create("warrior", "persia"))
        result = VictoryManager.check_victory(state)
        self.assertFalse(result["game_over"])

    def test_military_victory(self):
        state = GameState()
        state.player_faction = FACTIONS[0]
        state.enemy_faction = FACTIONS[2]
        state.board.place_unit(0, 0, Unit.create("warrior", "mongol"))
        result = VictoryManager.check_victory(state)
        self.assertTrue(result["game_over"])
        self.assertEqual(result["winner"], "mongol")

    def test_diplomatic_victory(self):
        state = GameState()
        state.player_faction = FACTIONS[0]
        state.enemy_faction = FACTIONS[2]
        state.board.place_unit(0, 0, Unit.create("warrior", "mongol"))
        state.board.place_unit(9, 9, Unit.create("warrior", "persia"))
        state.diplomacy_relations["mongol:persia"] = 50
        result = VictoryManager.check_victory(state)
        self.assertTrue(result["game_over"])
        self.assertEqual(result["type"], "diplomacy")

    def test_turn_limit_victory(self):
        state = GameState(max_turns=5)
        state.player_faction = FACTIONS[0]
        state.enemy_faction = FACTIONS[2]
        state.turn = 5
        state.board.place_unit(0, 0, Unit.create("warrior", "mongol"))
        state.board.place_unit(1, 0, Unit.create("warrior", "mongol"))
        state.board.place_unit(9, 9, Unit.create("warrior", "persia"))
        result = VictoryManager.check_victory(state)
        self.assertTrue(result["game_over"])
        self.assertEqual(result["winner"], "mongol")


class TestGameEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.new_game(0)

    def test_new_game(self):
        self.assertIsNotNone(self.engine.state)
        self.assertEqual(self.engine.state.player_faction.faction_id, "mongol")

    def test_invalid_faction(self):
        engine = GameEngine()
        result = engine.new_game(99)
        self.assertFalse(result["success"])

    def test_get_state(self):
        state = self.engine.get_state()
        self.assertIn("board", state)
        self.assertIn("turn", state)
        self.assertIn("phase", state)

    def test_action_validation(self):
        result = self.engine.perform_action("attack")
        self.assertFalse(result["success"])

    def test_end_phase(self):
        result = self.engine.perform_action("end_phase")
        self.assertTrue(result["success"])
        self.assertEqual(self.engine.state.phase, Phase.COMBAT)

    def test_move_action(self):
        # Use a clean engine with manually placed unit to avoid spawn crowding
        engine = GameEngine()
        engine.new_game(0)
        state = engine.state
        # Clear the board and place one unit in the middle
        state.board = Board(10, 10)
        u = Unit.create("cavalry", "mongol", bonus_strength=2)
        state.board.place_unit(5, 5, u)
        state.board.place_unit(9, 9, Unit.create("warrior", "persia"))
        result = engine.perform_action("move", from_x=5, from_y=5, to_x=5, to_y=4)
        self.assertTrue(result["success"])
        self.assertIsNone(state.board.get_unit(5, 5))
        self.assertIsNotNone(state.board.get_unit(5, 4))

    def test_collect_resources(self):
        for _ in range(3):
            self.engine.perform_action("end_phase")
        result = self.engine.perform_action("collect")
        self.assertTrue(result["success"])

    def test_diplomacy_action(self):
        self.engine.perform_action("end_phase")
        self.engine.perform_action("end_phase")
        result = self.engine.perform_action("diplomacy")
        self.assertTrue(result["success"])

    def test_full_turn_cycle(self):
        for _ in range(4):
            self.engine.perform_action("end_phase")
        self.assertEqual(self.engine.state.turn, 1)
        self.assertEqual(self.engine.state.phase, Phase.MOVEMENT)


class TestAPIRoutes(unittest.TestCase):
    def setUp(self):
        from backend.app import create_app
        from backend.routes.api import _engines
        _engines.clear()
        app = create_app("testing")
        self.client = app.test_client()

    def test_index_page(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_list_factions(self):
        resp = self.client.get("/api/factions")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data["factions"]), 4)

    def test_start_game(self):
        resp = self.client.post("/api/start_game", json={"faction": 0})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])

    def test_start_game_missing_faction(self):
        resp = self.client.post("/api/start_game", json={})
        self.assertEqual(resp.status_code, 400)

    def test_get_state_before_start(self):
        resp = self.client.get("/api/state")
        self.assertEqual(resp.status_code, 400)

    def test_get_state_after_start(self):
        self.client.post("/api/start_game", json={"faction": 0})
        resp = self.client.get("/api/state")
        self.assertEqual(resp.status_code, 200)

    def test_perform_action(self):
        self.client.post("/api/start_game", json={"faction": 1})
        resp = self.client.post("/api/action", json={"action": "end_phase"})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])

    def test_invalid_action(self):
        self.client.post("/api/start_game", json={"faction": 0})
        resp = self.client.post("/api/action", json={"action": "attack"})
        self.assertEqual(resp.status_code, 400)

    def test_highlights_before_start(self):
        resp = self.client.get("/api/highlights?x=0&y=0")
        self.assertEqual(resp.status_code, 400)

    def test_highlights_empty_cell(self):
        self.client.post("/api/start_game", json={"faction": 0})
        resp = self.client.get("/api/highlights?x=5&y=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["move"], [])
        self.assertEqual(data["attack"], [])

    def test_highlights_player_unit(self):
        self.client.post("/api/start_game", json={"faction": 0})
        resp = self.client.get("/api/highlights?x=0&y=0")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("move", data)
        self.assertIn("attack", data)
        self.assertIn("unit", data)
        self.assertIsInstance(data["move"], list)

    def test_faction_data_has_passive(self):
        resp = self.client.get("/api/factions")
        data = resp.get_json()
        for faction in data["factions"]:
            self.assertIn("passive_name", faction)
            self.assertIn("passive_description", faction)
            self.assertIn("playstyle", faction)
            self.assertIn("signature_unit", faction)
            self.assertTrue(len(faction["passive_name"]) > 0)

    def test_state_includes_faction_identity(self):
        self.client.post("/api/start_game", json={"faction": 0})
        resp = self.client.get("/api/state")
        data = resp.get_json()
        pf = data["player_faction"]
        self.assertIn("passive_name", pf)
        self.assertEqual(pf["id"], "mongol")


if __name__ == "__main__":
    unittest.main()
