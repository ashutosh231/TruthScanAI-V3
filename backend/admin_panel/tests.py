"""
Admin Panel Comprehensive Test Suite.
Tests:
- Admin login with rate limiting & RBAC verification
- Normal user 403 rejection on all admin endpoints
- Dashboard KPIs & charts aggregation
- Users Management complete CRUD (including primary admin protection)
- Fact Check Management CRUD & manual review recording
- News Management CRUD
- Categories Management CRUD with safe reference checks
- AI Monitoring & Activity audit logs
- Admin settings management
"""

import os
from django.test import TestCase
from rest_framework.test import APIClient
from core.mongodb import (
    get_users_collection,
    get_factchecks_collection,
    get_news_collection,
    get_categories_collection,
    get_activity_logs_collection,
    to_object_id,
)
from core.utils import generate_access_token, get_redis_client
from accounts.services import hash_password

class AdminPanelTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.redis = get_redis_client()
        self.users_col = get_users_collection()
        self.factchecks_col = get_factchecks_collection()
        self.news_col = get_news_collection()
        self.categories_col = get_categories_collection()
        self.logs_col = get_activity_logs_collection()

        # Flush rate limit keys
        try:
            for k in ["ratelimit:admin-login:127.0.0.1", "ratelimit:admin-login:admin_email:id-admin@gmail.com"]:
                self.redis.delete(k)
        except Exception:
            pass

        # Create/ensure admin user exists
        admin_doc = self.users_col.find_one({"email": "id-admin@gmail.com"})
        if not admin_doc:
            res = self.users_col.insert_one({
                "name": "Super Admin",
                "email": "id-admin@gmail.com",
                "password": hash_password("AdminSecure2026!#Scan"),
                "role": "admin",
                "isVerified": True,
                "isPremium": True,
            })
            self.admin_id = str(res.inserted_id)
        else:
            self.admin_id = str(admin_doc["_id"])

        self.admin_token = generate_access_token({"userId": self.admin_id, "role": "admin"})

        # Create/ensure normal user exists
        user_doc = self.users_col.find_one({"email": "regular_user_test@truthscan.ai"})
        if not user_doc:
            res_u = self.users_col.insert_one({
                "name": "Regular User",
                "email": "regular_user_test@truthscan.ai",
                "password": hash_password("UserPassword123!"),
                "role": "user",
                "isVerified": True,
                "isPremium": False,
            })
            self.user_id = str(res_u.inserted_id)
        else:
            self.user_id = str(user_doc["_id"])

        self.user_token = generate_access_token({"userId": self.user_id, "role": "user"})

        # Authenticated admin client
        self.admin_client = APIClient()
        self.admin_client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")

        # Authenticated normal user client
        self.normal_client = APIClient()
        self.normal_client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")

    def test_admin_login_success(self):
        res = self.client.post("/api/admin/login", {
            "email": "id-admin@gmail.com",
            "password": "AdminSecure2026!#Scan",
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("success"))
        self.assertEqual(res.json()["data"]["user"]["role"], "admin")
        self.assertIn("accessToken", res.json()["data"])

    def test_admin_login_invalid_password_returns_401(self):
        res = self.client.post("/api/admin/login", {
            "email": "id-admin@gmail.com",
            "password": "WrongPasswordXYZ!",
        })
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json().get("success"))

    def test_normal_user_denied_admin_login(self):
        res = self.client.post("/api/admin/login", {
            "email": "regular_user_test@truthscan.ai",
            "password": "UserPassword123!",
        })
        self.assertEqual(res.status_code, 403)
        self.assertFalse(res.json().get("success"))

    def test_unauthenticated_request_to_admin_endpoint_returns_401(self):
        res = self.client.get("/api/admin/dashboard/stats")
        self.assertEqual(res.status_code, 401)

    def test_normal_user_denied_access_to_admin_endpoints(self):
        res = self.normal_client.get("/api/admin/dashboard/stats")
        self.assertEqual(res.status_code, 403)

    def test_admin_dashboard_stats(self):
        res = self.admin_client.get("/api/admin/dashboard/stats")
        self.assertEqual(res.status_code, 200)
        kpis = res.json()["data"]["kpis"]
        self.assertIn("totalUsers", kpis)
        self.assertIn("totalFactChecks", kpis)
        self.assertIn("verifiedClaims", kpis)
        self.assertIn("falseClaims", kpis)

    def test_admin_dashboard_charts(self):
        res = self.admin_client.get("/api/admin/dashboard/charts?period=30d")
        self.assertEqual(res.status_code, 200)
        data = res.json()["data"]
        self.assertIn("factChecksOverTime", data)
        self.assertIn("verdictDistribution", data)
        self.assertIn("userGrowth", data)
        self.assertIn("categories", data)
        self.assertIn("aiPerformance", data)

    def test_admin_users_crud_lifecycle(self):
        # 1. List users
        list_res = self.admin_client.get("/api/admin/users")
        self.assertEqual(list_res.status_code, 200)
        self.assertGreaterEqual(list_res.json()["data"]["total"], 2)

        # 2. Create user
        new_email = f"crud_test_{self.id().lower().replace('.', '_')}@truthscan.ai"
        create_res = self.admin_client.post("/api/admin/users", {
            "name": "CRUD Test User",
            "email": new_email,
            "password": "StrongPassword999!",
            "role": "user",
            "isVerified": True,
            "isPremium": False,
        })
        self.assertEqual(create_res.status_code, 201)
        created_id = create_res.json()["data"]["_id"]

        # 3. Read detail
        detail_res = self.admin_client.get(f"/api/admin/users/{created_id}")
        self.assertEqual(detail_res.status_code, 200)
        self.assertEqual(detail_res.json()["data"]["email"], new_email)

        # 4. Update user
        update_res = self.admin_client.patch(f"/api/admin/users/{created_id}", {
            "name": "Updated Name",
            "isPremium": True,
        })
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["data"]["name"], "Updated Name")
        self.assertTrue(update_res.json()["data"]["isPremium"])

        # 5. Delete user
        del_res = self.admin_client.delete(f"/api/admin/users/{created_id}?hard=true")
        self.assertEqual(del_res.status_code, 200)

    def test_primary_admin_cannot_be_deleted_or_demoted(self):
        # Attempt to demote primary admin
        demote_res = self.admin_client.patch(f"/api/admin/users/{self.admin_id}", {
            "role": "user",
        })
        self.assertEqual(demote_res.status_code, 400)
        self.assertIn("primary administrator", demote_res.json()["message"])

        # Attempt to delete primary admin
        del_res = self.admin_client.delete(f"/api/admin/users/{self.admin_id}")
        self.assertEqual(del_res.status_code, 400)
        self.assertIn("cannot be deleted", del_res.json()["message"])

    def test_fact_checks_management_and_review(self):
        # 1. List fact checks
        list_res = self.admin_client.get("/api/admin/fact-checks?limit=5")
        self.assertEqual(list_res.status_code, 200)
        fcs = list_res.json()["data"]["factChecks"]
        self.assertGreater(len(fcs), 0)

        sample_id = fcs[0]["id"]

        # 2. Detail
        detail_res = self.admin_client.get(f"/api/admin/fact-checks/{sample_id}")
        self.assertEqual(detail_res.status_code, 200)

        # 3. Admin review
        review_res = self.admin_client.post(f"/api/admin/fact-checks/{sample_id}/review", {
            "decision": "CONFIRMED",
            "notes": "Verified by primary administrative investigator team.",
        })
        self.assertEqual(review_res.status_code, 200)
        self.assertEqual(review_res.json()["data"]["manualReview"]["decision"], "CONFIRMED")

    def test_news_crud(self):
        # Create news
        create_res = self.admin_client.post("/api/admin/news", {
            "title": "Admin Test Breaking Wire Dispatch",
            "description": "Critical news summary for tests.",
            "source": "FactCheck Wire",
            "category": "Technology",
            "isPublished": True,
        })
        self.assertEqual(create_res.status_code, 201)
        news_id = create_res.json()["data"]["_id"]

        # List
        list_res = self.admin_client.get("/api/admin/news?search=Breaking")
        self.assertEqual(list_res.status_code, 200)

        # Delete
        del_res = self.admin_client.delete(f"/api/admin/news/{news_id}")
        self.assertEqual(del_res.status_code, 200)

    def test_categories_crud(self):
        # Create category
        create_res = self.admin_client.post("/api/admin/categories", {
            "name": f"Test Category {self.id().split('.')[-1]}",
            "description": "Category for unit test suite",
            "color": "#6366F1",
            "icon": "shield",
            "isActive": True,
        })
        self.assertEqual(create_res.status_code, 201)
        cat_id = create_res.json()["data"]["_id"]

        # List
        list_res = self.admin_client.get("/api/admin/categories")
        self.assertEqual(list_res.status_code, 200)

        # Delete
        del_res = self.admin_client.delete(f"/api/admin/categories/{cat_id}")
        self.assertEqual(del_res.status_code, 200)

    def test_ai_monitoring_and_activity_logs(self):
        ai_res = self.admin_client.get("/api/admin/monitoring/ai")
        self.assertEqual(ai_res.status_code, 200)
        self.assertIn("summary", ai_res.json()["data"])
        self.assertIn("models", ai_res.json()["data"])

        logs_res = self.admin_client.get("/api/admin/activity-logs")
        self.assertEqual(logs_res.status_code, 200)
        self.assertIn("logs", logs_res.json()["data"])

    def test_admin_settings_view_and_patch(self):
        get_res = self.admin_client.get("/api/admin/settings")
        self.assertEqual(get_res.status_code, 200)

        patch_res = self.admin_client.patch("/api/admin/settings", {
            "theme": "dark",
            "dashboardDateDefault": "90d",
            "emailAlerts": True,
        })
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["data"]["theme"], "dark")
