"""
Payment Views:
POST /api/payments/create-order
POST /api/payments/verify
POST /api/payments/webhook
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.permissions import IsAuthenticatedMongoUser
from payments.services import (
    create_payment_order,
    verify_payment_signature,
    process_webhook_event,
)

class CreateOrderView(APIView):
    """
    POST /api/payments/create-order
    Initiate Razorpay checkout order.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def post(self, request):
        plan_type = request.data.get("planType", "PREMIUM_MONTHLY")
        try:
            order_data = create_payment_order(
                user_id=request.user._id,
                plan_type=plan_type,
            )
            return Response(
                {
                    "success": True,
                    "data": order_data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyPaymentView(APIView):
    """
    POST /api/payments/verify
    Verify Razorpay payment signature.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def post(self, request):
        order_id = request.data.get("razorpayOrderId")
        payment_id = request.data.get("razorpayPaymentId")
        signature = request.data.get("razorpaySignature")

        if not order_id or not payment_id or not signature:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Missing required payment verification parameters: "
                        "razorpayOrderId, razorpayPaymentId, and razorpaySignature are required."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            verification_result = verify_payment_signature(
                user_id=request.user._id,
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id,
                razorpay_signature=signature,
            )
            return Response(
                {
                    "success": True,
                    "message": "Payment successfully verified. Premium clearance activated.",
                    "data": verification_result,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class WebhookView(APIView):
    """
    POST /api/payments/webhook
    Handle Razorpay Webhook notifications.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        signature = request.headers.get("x-razorpay-signature") or request.META.get("HTTP_X_RAZORPAY_SIGNATURE")
        raw_body = getattr(request, "raw_body", None) or request.body.decode("utf-8", errors="replace")

        try:
            result = process_webhook_event(raw_body, signature)
            return Response(
                {
                    "success": True,
                    "message": "Webhook processed.",
                    "data": result,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as error:
            print(f"[PaymentWebhook] Error: {error}")
            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
