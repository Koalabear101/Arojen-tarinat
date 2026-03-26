import unittest

from app import app


class TestBattleApi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        start = self.client.post("/start_game", data={"faction": "0"})
        self.assertEqual(start.status_code, 200)

    def _to_battle_phase(self):
        self.client.post("/take_action", json={"action": "collect_resources"})
        self.client.post("/take_action", json={"action": "next_phase"})
        self.client.post("/take_action", json={"action": "draw_card"})
        self.client.post("/take_action", json={"action": "next_phase"})
        self.client.post("/take_action", json={"action": "next_phase"})

    def test_attack_returns_dice_and_battle_summary(self):
        self._to_battle_phase()
        state = self.client.get("/get_state").get_json()
        player = next(f for f in state["factions_state"] if f["is_player"])
        unit = player["units"][0]
        self.client.post("/take_action", json={"action": "hex_click", "x": unit["x"], "y": unit["y"]})
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
        self.assertIn("spawn_position", first_faction)
        self.assertIn("units", first_faction)
        if first_faction["units"]:
            self.assertIn("x", first_faction["units"][0])
            self.assertIn("y", first_faction["units"][0])
        self.assertIn("spawn_role", first_faction)

    def test_hex_click_selects_unit_and_exposes_targets(self):
        response = self.client.get("/get_state")
        payload = response.get_json()
        player = next(f for f in payload["factions_state"] if f["is_player"])
        unit = player["units"][0]

        self.client.post("/take_action", json={"action": "collect_resources"})
        self.client.post("/take_action", json={"action": "next_phase"})
        self.client.post("/take_action", json={"action": "draw_card"})
        self.client.post("/take_action", json={"action": "next_phase"})
        move_phase = self.client.post("/take_action", json={"action": "hex_click", "x": unit["x"], "y": unit["y"]})
        move_payload = move_phase.get_json()
        self.assertIn("Valittu yksikkö", move_payload["message"])
        self.assertIsNotNone(move_payload["selected_unit"])
        self.assertIn("reachable_hexes", move_payload)


if __name__ == "__main__":
    unittest.main()
