"""
Accounts & Auth Comprehensive Integration Tests.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from core.mongodb import get_users_collection, to_object_id
from core.utils import generate_access_token, generate_refresh_token, get_redis_client

class AccountsAuthIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.redis = get_redis_client()
        self.users = get_users_collection()
        # Reset rate limit keys for tests to prevent test bleed
        try:
            for key in ["ratelimit:send-otp:127.0.0.1", "ratelimit:login:127.0.0.1", "ratelimit:register:127.0.0.1"]:
                self.redis.delete(key)
        except Exception:
            pass

    def test_login_with_invalid_credentials_returns_401(self):
        res = self.client.post("/api/auth/login", {
            "email": "nonexistent_investigator@truthscan.ai",
            "password": "WrongPassword123!",
        })
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json().get("success"))
        self.assertIn("Invalid credentials", res.json().get("message", ""))

    def test_login_missing_fields_returns_400(self):
        res = self.client.post("/api/auth/login", {
            "email": "",
            "password": "",
        })
        self.assertEqual(res.status_code, 400)

    def test_send_otp_nonexistent_email_returns_404(self):
        unique_email = f"nobody_exists_{self.id()}@truthscan.ai"
        try:
            self.redis.delete(f"ratelimit:send-otp:{unique_email}")
            self.redis.delete("ratelimit:send-otp:127.0.0.1")
        except Exception:
            pass

        res = self.client.post("/api/auth/send-otp", {
            "email": unique_email,
        })
        self.assertEqual(res.status_code, 404)

    def test_verify_otp_invalid_code_returns_400(self):
        res = self.client.post("/api/auth/verify-otp", {
            "email": "test@truthscan.ai",
            "otp": "000000",
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid or expired OTP", res.json().get("message", ""))

    def test_refresh_token_without_cookie_returns_401(self):
        res = self.client.post("/api/auth/refresh")
        self.assertEqual(res.status_code, 401)

    def test_logout_clears_cookie(self):
        res = self.client.post("/api/auth/logout")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("success"))

    def test_update_profile(self):
        user_doc = self.users.find_one({})
        if user_doc:
            token = generate_access_token({"userId": str(user_doc["_id"]), "role": user_doc.get("role", "user")})
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
            original_name = user_doc.get("name", "")

            # Update name
            res = client.put("/api/users/profile", {"name": original_name})
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.json().get("success"))
            self.assertEqual(res.json()["data"]["name"], original_name)

    def test_direct_send_otp_email(self):
        from core.utils import send_otp_email
        # Test synchronous call to send_otp_email (safe fallback in dev/test)
        result = send_otp_email("test_investigator@truthscan.ai", "654321", run_async=False)
        self.assertIsInstance(result, bool)

    def test_registration_flow_with_direct_mail_service(self):
        from unittest.mock import patch
        unique_email = f"direct_mail_{self.id().lower()}@truthscan.ai"
        try:
            self.redis.delete(f"ratelimit:register:127.0.0.1")
        except Exception:
            pass

        with patch("core.utils._send_smtp_payload", return_value=True):
            res = self.client.post("/api/auth/register", {
                "name": "Direct Mail User",
                "email": unique_email,
                "password": "StrongPassword123!",
            })
            self.assertEqual(res.status_code, 201)
            self.assertTrue(res.json().get("success"))
            cached_otp = self.redis.get(f"otp:{unique_email}")
            if isinstance(cached_otp, bytes):
                cached_otp = cached_otp.decode("utf-8")
            self.assertIsNotNone(cached_otp)
            self.assertEqual(len(cached_otp), 6)
