import unittest

from app import app, game_state


class TestBoardGameTurnFlow(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        response = self.client.post("/start_game", data={"faction": "0"})
        self.assertEqual(response.status_code, 200)
        self.start_payload = response.get_json()

    def test_game_starts_with_board_game_phases(self):
        payload = self.start_payload
        self.assertEqual(payload["status"], "started")
        self.assertEqual(payload["turn"], 1)
        self.assertEqual(payload["phase"], "Resurssivaihe")
        self.assertIn("horses", payload["resources"])
        self.assertIn("economic", payload["victory_progress"])
        self.assertIn("next_phase", payload["available_actions"])
        self.assertIn("end_turn", payload["available_actions"])

    def test_action_restricted_by_phase(self):
        response = self.client.post("/take_action", json={"action": "attack"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("ei ole sallittu", payload["message"])
        self.assertEqual(payload["phase"], "Resurssivaihe")

    def test_next_phase_cycles_after_six_phases(self):
        for _ in range(6):
            response = self.client.post("/take_action", json={"action": "next_phase"})
            self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["phase"], "Resurssivaihe")
        self.assertEqual(payload["turn"], 2)

    def test_research_path_can_trigger_technology_victory(self):
        winner = None
        for _ in range(8):
            self.client.post("/take_action", json={"action": "collect_resources"})
            self.client.post("/take_action", json={"action": "next_phase"})  # kortti
            self.client.post("/take_action", json={"action": "draw_card"})
            self.client.post("/take_action", json={"action": "next_phase"})  # liike
            self.client.post("/take_action", json={"action": "next_phase"})  # taistelu
            self.client.post("/take_action", json={"action": "next_phase"})  # hallinta
            research_response = self.client.post("/take_action", json={"action": "research"})
            payload = research_response.get_json()
            winner = payload["winner"]
            self.client.post("/take_action", json={"action": "end_turn"})
            if winner:
                break

        self.assertEqual(winner, "Teknologiavoitto")

    def test_attack_uses_attack_and_defense_dice_in_battle_view(self):
        self.client.post("/take_action", json={"action": "collect_resources"})
        self.client.post("/take_action", json={"action": "next_phase"})  # kortti
        self.client.post("/take_action", json={"action": "draw_card"})
        self.client.post("/take_action", json={"action": "next_phase"})  # liike
        player = next(f for f in self.start_payload["factions_state"] if f["is_player"])
        unit = player["units"][0]
        self.client.post("/take_action", json={"action": "hex_click", "x": unit["x"], "y": unit["y"]})
        self.client.post("/take_action", json={"action": "next_phase"})  # taistelu
        response = self.client.post("/take_action", json={"action": "attack"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertIn("battle", payload)
        battle = payload["battle"]["last"]
        self.assertIn("attack_die", battle)
        self.assertIn("defense_die", battle)
        self.assertIn("attack_total", battle)
        self.assertIn("defense_total", battle)
        self.assertIn("outcome", battle)
        self.assertGreaterEqual(battle["attack_die"], 1)
        self.assertLessEqual(battle["attack_die"], 6)
        self.assertGreaterEqual(battle["defense_die"], 1)
        self.assertLessEqual(battle["defense_die"], 6)

    def test_start_game_exposes_factions_and_tokens(self):
        payload = self.start_payload
        self.assertIn("factions", payload)
        self.assertGreaterEqual(len(payload["factions"]), 2)
        self.assertIn("unit_types", payload)
        self.assertIn("cavalry", payload["unit_types"])
        self.assertIn("factions_state", payload)
        self.assertTrue(any(item["name"] == "Mongoli-heimo" for item in payload["factions_state"]))

    def test_hex_click_selects_unit_and_reveals_moves(self):
        self.client.post("/take_action", json={"action": "collect_resources"})
        self.client.post("/take_action", json={"action": "next_phase"})
        self.client.post("/take_action", json={"action": "draw_card"})
        self.client.post("/take_action", json={"action": "next_phase"})
        player = next(f for f in self.start_payload["factions_state"] if f["is_player"])
        unit = player["units"][0]
        response = self.client.post("/take_action", json={"action": "hex_click", "x": unit["x"], "y": unit["y"]})
        payload = response.get_json()
        self.assertIn("selected_unit", payload)
        self.assertIsNotNone(payload["selected_unit"])
        self.assertGreater(len(payload["reachable_hexes"]), 0)

    def test_end_turn_advances_turn_and_runs_ai(self):
        response = self.client.post("/take_action", json={"action": "end_turn"})
        payload = response.get_json()
        self.assertEqual(payload["turn"], 2)
        self.assertEqual(payload["phase"], "Resurssivaihe")


if __name__ == "__main__":
    unittest.main()
