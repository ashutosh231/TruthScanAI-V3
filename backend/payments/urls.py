"""
URL routing for payment endpoints.
"""

from django.urls import path
from payments.views import CreateOrderView, VerifyPaymentView, WebhookView

urlpatterns = [
    path("create-order", CreateOrderView.as_view(), name="payment-create-order"),
    path("verify", VerifyPaymentView.as_view(), name="payment-verify"),
    path("webhook", WebhookView.as_view(), name="payment-webhook"),
]
