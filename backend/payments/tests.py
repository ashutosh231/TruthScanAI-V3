"""
Payments Integration Tests.
"""

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from core.mongodb import get_users_collection, get_payments_collection
from core.utils import generate_access_token
import hmac, hashlib

class PaymentsIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.users = get_users_collection()
        self.payments = get_payments_collection()

    def test_create_order_requires_auth(self):
        res = self.client.post("/api/payments/create-order", {"planType": "PREMIUM_MONTHLY"})
        self.assertEqual(res.status_code, 401)

    def test_verify_payment_requires_auth(self):
        res = self.client.post("/api/payments/verify", {
            "razorpayOrderId": "order_123",
            "razorpayPaymentId": "pay_123",
            "razorpaySignature": "sig_123",
        })
        self.assertEqual(res.status_code, 401)

    def test_verify_payment_missing_params_returns_400(self):
        user_doc = self.users.find_one({})
        if user_doc:
            token = generate_access_token({"userId": str(user_doc["_id"]), "role": user_doc.get("role", "user")})
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
            res = client.post("/api/payments/verify", {})
            self.assertEqual(res.status_code, 400)
            self.assertIn("Missing required payment verification parameters", res.json().get("message", ""))

    @override_settings(RAZORPAY_WEBHOOK_SECRET="test_webhook_secret_key")
    def test_webhook_handles_empty_or_invalid_signature(self):
        res = self.client.post(
            "/api/payments/webhook",
            data='{"event": "dummy"}',
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE="invalid_signature",
        )
        # Should return 400 with error message
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json().get("success"))
        self.assertIn("Invalid webhook signature", res.json().get("message", ""))
