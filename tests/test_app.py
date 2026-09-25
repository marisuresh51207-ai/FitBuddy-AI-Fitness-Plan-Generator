import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from google.genai.errors import APIError

from app.database import SessionLocal, delete_user, get_user
from app import gemini_client
from app.main import app


class FitBuddyAppTests(unittest.TestCase):
    user_id = "TEST-FITBUDDY-20260925"

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        db = SessionLocal()
        delete_user(db, cls.user_id)
        db.close()

    @classmethod
    def tearDownClass(cls):
        db = SessionLocal()
        delete_user(db, cls.user_id)
        db.close()

    def user_form(self, username="Test User"):
        return {
            "username": username,
            "user_id": self.user_id,
            "age": "30",
            "weight": "75",
            "goal": "General Wellness",
            "intensity": "Medium",
        }

    def test_health_and_homepage(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "healthy")

        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertIn('name="username"', home.text)
        self.assertIn('name="intensity"', home.text)

    def test_validation_returns_422(self):
        response = self.client.post(
            "/generate-workout",
            data={**self.user_form(), "age": "0"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("Please check your input", response.text)

    @patch("app.routes.generate_workout_gemini", return_value="ORIGINAL PLAN")
    @patch("app.routes.generate_nutrition_tip_with_flash", return_value="RECOVERY TIP")
    @patch("app.routes.update_workout_plan", return_value="UPDATED PLAN")
    def test_complete_user_flow(self, update_plan, nutrition_tip, workout_plan):
        generated = self.client.post("/generate-workout", data=self.user_form())
        self.assertEqual(generated.status_code, 200)
        self.assertIn("ORIGINAL PLAN", generated.text)
        self.assertIn("RECOVERY TIP", generated.text)

        db = SessionLocal()
        user = get_user(db, self.user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.original_plan, "ORIGINAL PLAN")
        self.assertIsNone(user.updated_plan)
        db.close()

        regenerated = self.client.post(
            "/generate-workout",
            data=self.user_form(username="Updated Test User"),
        )
        self.assertEqual(regenerated.status_code, 200)

        feedback = self.client.post(
            "/submit-feedback",
            data={"user_id": self.user_id, "feedback": "Add one recovery day."},
        )
        self.assertEqual(feedback.status_code, 200)
        self.assertIn("UPDATED PLAN", feedback.text)
        self.assertIn("updated successfully", feedback.text)

        users = self.client.get("/view-all-users")
        self.assertEqual(users.status_code, 200)
        self.assertIn(self.user_id, users.text)
        self.assertIn("UPDATED PLAN", users.text)

        deleted = self.client.post(f"/delete-user/{self.user_id}", follow_redirects=False)
        self.assertEqual(deleted.status_code, 303)
        db = SessionLocal()
        self.assertIsNone(get_user(db, self.user_id))
        db.close()

        self.assertEqual(self.client.get("/view-all-users").status_code, 200)
        workout_plan.assert_called()
        nutrition_tip.assert_called()
        update_plan.assert_called_once()

    def test_missing_feedback_user_returns_404(self):
        response = self.client.post(
            "/submit-feedback",
            data={"user_id": "DOES-NOT-EXIST", "feedback": "More rest."},
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("User ID not found", response.text)

    def test_model_status_prefers_available_flash_model(self):
        fake_client = SimpleNamespace(
            models=SimpleNamespace(
                list=lambda: [
                    SimpleNamespace(name="models/gemini-3.1-pro-preview", supported_actions=["generateContent"]),
                    SimpleNamespace(name="models/gemini-3.8-flash", supported_actions=["generateContent"]),
                ]
            )
        )
        with patch.object(gemini_client, "client", fake_client), patch.object(gemini_client, "API_KEY", "test-key"):
            status = gemini_client.get_model_status()
        self.assertTrue(status["api_key_detected"])
        self.assertEqual(status["selected_workout_model"], "gemini-3.8-flash")
        self.assertEqual(status["selected_nutrition_model"], "gemini-3.8-flash")

    def test_quota_error_falls_back_without_repeating_zero_quota_model(self):
        calls = []

        def generate_content(model, contents):
            calls.append(model)
            if model == "gemini-3.8-flash":
                raise APIError(
                    429,
                    {"error": {"status": "RESOURCE_EXHAUSTED", "message": "limit: 0"}},
                )
            return SimpleNamespace(text="fallback response")

        fake_client = SimpleNamespace(
            models=SimpleNamespace(
                list=lambda: [
                    SimpleNamespace(name="models/gemini-3.8-flash", supported_actions=["generateContent"]),
                    SimpleNamespace(name="models/gemini-3.5-flash", supported_actions=["generateContent"]),
                ],
                generate_content=generate_content,
            )
        )
        with patch.object(gemini_client, "client", fake_client):
            result = gemini_client.generate_text("test prompt", ["gemini-3.8-flash", "gemini-3.5-flash"])
        self.assertEqual(result, "fallback response")
        self.assertEqual(calls, ["gemini-3.8-flash", "gemini-3.5-flash"])

    def test_all_quota_failures_name_attempted_models(self):
        def generate_content(model, contents):
            raise APIError(
                429,
                {"error": {"status": "RESOURCE_EXHAUSTED", "message": "free_tier limit: 0"}},
            )

        fake_client = SimpleNamespace(
            models=SimpleNamespace(
                list=lambda: [
                    SimpleNamespace(name="models/gemini-3.8-flash", supported_actions=["generateContent"]),
                    SimpleNamespace(name="models/gemini-3.5-flash", supported_actions=["generateContent"]),
                ],
                generate_content=generate_content,
            )
        )
        with patch.object(gemini_client, "client", fake_client):
            with self.assertRaises(gemini_client.GeminiGenerationError) as context:
                gemini_client.generate_text("test prompt", ["gemini-3.8-flash", "gemini-3.5-flash"])
        self.assertTrue(context.exception.quota_exhausted)
        self.assertIn("gemini-3.8-flash", str(context.exception))
        self.assertIn("gemini-3.5-flash", str(context.exception))


if __name__ == "__main__":
    unittest.main()
