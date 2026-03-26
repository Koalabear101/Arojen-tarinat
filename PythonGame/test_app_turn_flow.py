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
        self.assertEqual(payload["phase"], "Suunnitteluvaihe")
        self.assertIn("horses", payload["resources"])
        self.assertIn("economic", payload["victory_progress"])
        self.assertIn("end_phase", payload["available_actions"])

    def test_action_restricted_by_phase(self):
        response = self.client.post("/take_action", json={"action": "attack"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("ei ole sallittu", payload["message"])
        self.assertEqual(payload["phase"], "Suunnitteluvaihe")

    def test_end_phase_cycles_turn_after_four_phases(self):
        for _ in range(4):
            response = self.client.post("/take_action", json={"action": "end_phase"})
            self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["phase"], "Suunnitteluvaihe")
        self.assertEqual(payload["turn"], 2)

    def test_research_path_can_trigger_technology_victory(self):
        winner = None
        for _ in range(4):
            self.client.post("/take_action", json={"action": "draw_strategy"})
            self.client.post("/take_action", json={"action": "end_phase"})
            self.client.post("/take_action", json={"action": "end_phase"})
            research_response = self.client.post("/take_action", json={"action": "research"})
            payload = research_response.get_json()
            winner = payload["winner"]
            self.client.post("/take_action", json={"action": "end_phase"})
            self.client.post("/take_action", json={"action": "end_phase"})
            if winner:
                break

        self.assertEqual(winner, "Teknologinen voitto")

    def test_attack_uses_attack_and_defense_dice_in_battle_view(self):
        self.client.post("/take_action", json={"action": "end_phase"})
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


if __name__ == "__main__":
    unittest.main()
