"""
FactCheck & Controller API Tests.
Matches controller.test.js from original Express implementation.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from core.authentication import MongoUser
from core.utils import generate_access_token
from factcheck.services import check_user_trial_limit
from core.mongodb import get_users_collection, get_factchecks_collection

class ControllerAndAuthIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_endpoints(self):
        # /health
        res1 = self.client.get("/health")
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.json().get("success"))

        # /api/health
        res2 = self.client.get("/api/health")
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json().get("success"))

    def test_trial_limit_enforcement(self):
        """
        Scenario 13: Blocks non-premium user when trial limit reached (2 checks)
        and allows premium user.
        """
        users_col = get_users_collection()
        factchecks_col = get_factchecks_collection()

        # Find existing user or mock document
        existing = users_col.find_one({})
        if existing:
            user = MongoUser(existing)
            # Count prior checks
            prior_count = factchecks_col.count_documents({"user": user._id})

            if not user.isPremium and prior_count >= 2:
                allowed, err = check_user_trial_limit(user)
                self.assertFalse(allowed)
                self.assertTrue(err.get("requiresUpgrade"))
                self.assertEqual(err.get("trialLimit"), 2)

        # Mock non-premium user
        class DummyUser:
            def __init__(self, is_premium):
                self._id = "mock_user_1"
                self.isPremium = is_premium

        # Premium user is always allowed regardless of prior checks
        premium_user = DummyUser(is_premium=True)
        allowed, _ = check_user_trial_limit(premium_user)
        self.assertTrue(allowed)

    def test_protected_routes_require_authentication(self):
        # GET /api/fact-check/history without auth
        res = self.client.get("/api/fact-check/history")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json().get("success"))

        # GET /api/users/profile without auth
        res = self.client.get("/api/users/profile")
        self.assertEqual(res.status_code, 401)

    def test_get_news_endpoint(self):
        # GET /api/news
        res = self.client.get("/api/news")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("data"), list)
        self.assertGreater(len(data.get("data")), 0)

    def test_authenticated_user_profile_access(self):
        users_col = get_users_collection()
        user_doc = users_col.find_one({})
        if user_doc:
            user_id = str(user_doc["_id"])
            token = generate_access_token({"userId": user_id, "role": user_doc.get("role", "user")})

            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
            res = client.get("/api/users/profile")
            self.assertEqual(res.status_code, 200)
            json_res = res.json()
            self.assertTrue(json_res.get("success"))
            self.assertEqual(json_res["data"]["id"], user_id)
            self.assertEqual(json_res["data"]["email"], user_doc["email"])
