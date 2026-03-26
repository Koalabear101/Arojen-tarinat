import unittest

from app import app


class TestUIStateApiShape(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        start = self.client.post("/start_game", data={"faction": "1"})
        self.assertEqual(start.status_code, 200)

    def test_get_state_contains_visualization_payload(self):
        response = self.client.get("/get_state")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertIn("board", payload)
        self.assertTrue(len(payload["board"]) >= 10)
        self.assertTrue(all(len(row) >= 10 for row in payload["board"]))
        self.assertIn("resources", payload)
        self.assertIn("victory_progress", payload)
        self.assertIn("available_actions", payload)
        self.assertIn("action_labels", payload)
        self.assertIn("hexes", payload)
        self.assertEqual(len(payload["hexes"]), 20)
        self.assertTrue(all(len(row) == 20 for row in payload["hexes"]))
        self.assertIn("map_size", payload)
        self.assertEqual(payload["map_size"]["width"], 20)
        self.assertEqual(payload["map_size"]["height"], 20)
        self.assertIn("terrain_types", payload)
        self.assertIn("forest", payload["terrain_types"])
        self.assertIn("battle_positions", payload)

    def test_faction_spawn_positions_exposed(self):
        response = self.client.get("/get_state")
        payload = response.get_json()
        factions = payload["factions_state"]
        self.assertTrue(len(factions) >= 4)
        for faction in factions:
            self.assertIn("spawn_position", faction)
            spawn = faction["spawn_position"]
            self.assertIn("x", spawn)
            self.assertIn("y", spawn)
            self.assertIn("units", faction)
        self.assertIn("factions_state", payload)
        self.assertTrue(isinstance(payload["factions_state"], list))
        self.assertTrue(len(payload["factions_state"]) >= 4)
        self.assertIn("battle", payload)
        self.assertIn("last", payload["battle"])
        self.assertIn("factions_state", payload)
        self.assertIn("battle", payload)


if __name__ == "__main__":
    unittest.main()
