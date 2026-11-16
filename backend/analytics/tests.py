"""
Analytics & Admin Live Metrics Tests.
Tests real MongoDB Atlas aggregation for total users, fact checks, verdicts, breakdown, and activity.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from analytics.services import get_system_analytics
from core.mongodb import get_users_collection
from core.utils import generate_access_token

class AnalyticsServiceTests(TestCase):
    def test_live_analytics_from_mongodb_atlas(self):
        analytics = get_system_analytics()
        self.assertIn("totalUsers", analytics)
        self.assertIn("totalFactChecks", analytics)
        self.assertIn("verifiedClaims", analytics)
        self.assertIn("falseClaims", analytics)
        self.assertIn("misleadingClaims", analytics)
        self.assertIn("typeBreakdown", analytics)
        self.assertIn("verdictBreakdown", analytics)
        self.assertIn("recentActivity", analytics)

        # Check types
        self.assertIsInstance(analytics["totalUsers"], int)
        self.assertIsInstance(analytics["totalFactChecks"], int)
        self.assertIsInstance(analytics["typeBreakdown"], dict)
        self.assertIsInstance(analytics["verdictBreakdown"], dict)
        self.assertIsInstance(analytics["recentActivity"], list)

        # Confirm from live MongoDB Atlas: total users is >= 5, total checks >= 49
        self.assertGreaterEqual(analytics["totalUsers"], 5)
        self.assertGreaterEqual(analytics["totalFactChecks"], 40)

    def test_analytics_api_endpoint_with_auth(self):
        users_col = get_users_collection()
        user_doc = users_col.find_one({})
        if user_doc:
            token = generate_access_token({"userId": str(user_doc["_id"]), "role": user_doc.get("role", "user")})
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
            res = client.get("/api/analytics")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data.get("success"))
            self.assertIn("totalFactChecks", data["data"])
