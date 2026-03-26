import unittest

from app import app


class TestBattleApi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        start = self.client.post("/start_game", data={"faction": "0"})
        self.assertEqual(start.status_code, 200)

    def _to_action_phase(self):
        self.client.post("/take_action", json={"action": "end_phase"})

    def test_attack_returns_dice_and_battle_summary(self):
        self._to_action_phase()
        response = self.client.post("/take_action", json={"action": "attack"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertIn("battle", payload)
        battle = payload["battle"]["last"]
        self.assertIsNotNone(battle)
        self.assertIn("attack_die", battle)
        self.assertIn("defense_die", battle)
        self.assertIn("attack_total", battle)
        self.assertIn("defense_total", battle)
        self.assertIn("attacker_faction", battle)
        self.assertIn("defender_faction", battle)

    def test_state_contains_factions_and_tokens(self):
        response = self.client.get("/get_state")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertIn("factions_state", payload)
        self.assertIsInstance(payload["factions_state"], list)
        self.assertGreaterEqual(len(payload["factions_state"]), 2)
        first_faction = payload["factions_state"][0]
        self.assertIn("name", first_faction)
        self.assertIn("unit_counts", first_faction)
        self.assertIn("cavalry", first_faction["unit_counts"])
        self.assertIn("unit_types", payload)
        self.assertIn("token", payload["unit_types"]["cavalry"])


if __name__ == "__main__":
    unittest.main()
