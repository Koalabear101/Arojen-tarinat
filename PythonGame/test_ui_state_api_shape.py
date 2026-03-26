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


if __name__ == "__main__":
    unittest.main()
