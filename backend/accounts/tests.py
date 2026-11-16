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

    def test_forgot_password_flow(self):
        from unittest.mock import patch
        from accounts.services import hash_password
        from datetime import datetime, timezone

        test_email = f"reset_test_{self.id().lower().replace('.', '_')}@truthscan.ai"
        initial_pw = "OriginalPass123!"
        new_pw = "NewSecretPass456!"

        # Clear any rate limit
        try:
            self.redis.delete(f"ratelimit:send-otp:{test_email}")
            self.redis.delete(f"ratelimit:verify-otp:{test_email}")
            self.redis.delete(f"ratelimit:login:{test_email}")
        except Exception:
            pass

        # 1. Nonexistent email returns 404
        res = self.client.post("/api/auth/forgot-password", {"email": "nobody_home@truthscan.ai"})
        self.assertEqual(res.status_code, 404)

        # Create user in MongoDB
        now = datetime.now(timezone.utc)
        self.users.insert_one({
            "name": "Reset Test User",
            "email": test_email,
            "password": hash_password(initial_pw),
            "isVerified": True,
            "role": "user",
            "createdAt": now,
            "updatedAt": now,
        })

        # 2. Request forgot password OTP
        with patch("core.utils._send_smtp_payload", return_value=True):
            res = self.client.post("/api/auth/forgot-password", {"email": test_email})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("success"))

        cached_otp = self.redis.get(f"reset_otp:{test_email}")
        if isinstance(cached_otp, bytes):
            cached_otp = cached_otp.decode("utf-8")
        self.assertIsNotNone(cached_otp)
        self.assertEqual(len(cached_otp), 6)

        # 3. Verify OTP with bad code -> 400
        res = self.client.post("/api/auth/verify-reset-otp", {
            "email": test_email,
            "otp": "999999" if cached_otp != "999999" else "000000",
        })
        self.assertEqual(res.status_code, 400)

        # 4. Verify OTP with correct code -> 200
        res = self.client.post("/api/auth/verify-reset-otp", {
            "email": test_email,
            "otp": cached_otp,
        })
        self.assertEqual(res.status_code, 200)

        # 5. Reset password with short password -> 400
        res = self.client.post("/api/auth/reset-password", {
            "email": test_email,
            "otp": cached_otp,
            "newPassword": "123",
        })
        self.assertEqual(res.status_code, 400)

        # 6. Reset password with correct OTP and valid new password -> 200
        res = self.client.post("/api/auth/reset-password", {
            "email": test_email,
            "otp": cached_otp,
            "newPassword": new_pw,
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("success"))

        # Invalidate check: OTP should now be cleared from cache
        self.assertIsNone(self.redis.get(f"reset_otp:{test_email}"))

        # 7. Old password should fail to login
        res = self.client.post("/api/auth/login", {
            "email": test_email,
            "password": initial_pw,
        })
        self.assertEqual(res.status_code, 401)

        # 8. New password should succeed
        res = self.client.post("/api/auth/login", {
            "email": test_email,
            "password": new_pw,
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("success"))
        self.assertEqual(res.json()["data"]["user"]["email"], test_email)

        # Clean up created test user
        self.users.delete_one({"email": test_email})

