"""
Razorpay Payment Gateway Service.
Handles order creation, signature verification, and webhook processing.
"""

import os
import hmac
import hashlib
import json
from datetime import datetime, timezone
import razorpay
from django.conf import settings

from core.mongodb import (
    get_payments_collection,
    get_users_collection,
    to_object_id,
)

PLANS_CATALOG = {
    "PREMIUM_MONTHLY": {
        "name": "PREMIUM INVESTIGATOR",
        "amount": 20000,  # INR 200.00 in paise (Rs 200/month)
        "currency": "INR",
    },
    "PREMIUM_ANNUAL": {
        "name": "PREMIUM INVESTIGATOR ANNUAL",
        "amount": 200000,  # INR 2,000.00 in paise (Rs 2,000/year)
        "currency": "INR",
    },
}

_razorpay_client = None

def get_razorpay_client():
    global _razorpay_client
    if _razorpay_client is None:
        key_id = getattr(settings, "RAZORPAY_KEY_ID", None) or os.getenv("RAZORPAY_KEY_ID")
        key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", None) or os.getenv("RAZORPAY_KEY_SECRET")
        if key_id and key_secret:
            _razorpay_client = razorpay.Client(auth=(key_id, key_secret))
    return _razorpay_client

def create_payment_order(user_id, plan_type="PREMIUM_MONTHLY"):
    plan = PLANS_CATALOG.get(plan_type, PLANS_CATALOG["PREMIUM_MONTHLY"])
    client = get_razorpay_client()
    if not client:
        raise RuntimeError("Razorpay payment gateway is not initialized on the server.")

    user_obj_id = to_object_id(user_id)
    receipt_id = f"rcpt_{str(user_obj_id)[-6:]}_{int(datetime.now().timestamp() * 1000)}"

    options = {
        "amount": plan["amount"],
        "currency": plan["currency"],
        "receipt": receipt_id,
        "notes": {
            "userId": str(user_obj_id),
            "planType": plan_type,
        },
    }

    order = client.order.create(data=options)

    payments_col = get_payments_collection()
    now = datetime.now(timezone.utc)
    payment_record = payments_col.insert_one(
        {
            "user": user_obj_id,
            "razorpayOrderId": order["id"],
            "amount": plan["amount"],
            "currency": plan["currency"],
            "plan": plan_type,
            "status": "created",
            "createdAt": now,
            "updatedAt": now,
        }
    )

    key_id = getattr(settings, "RAZORPAY_KEY_ID", None) or os.getenv("RAZORPAY_KEY_ID")

    return {
        "orderId": order["id"],
        "keyId": key_id,
        "amount": order["amount"],
        "currency": order["currency"],
        "paymentRecordId": str(payment_record.inserted_id),
    }

def verify_payment_signature(user_id, razorpay_order_id, razorpay_payment_id, razorpay_signature):
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", None) or os.getenv("RAZORPAY_KEY_SECRET")
    if not key_secret:
        raise RuntimeError("RAZORPAY_KEY_SECRET is not configured on the server.")

    data_to_sign = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
    generated_sig = hmac.new(
        key_secret.encode("utf-8"),
        data_to_sign,
        hashlib.sha256,
    ).hexdigest()

    if generated_sig != razorpay_signature:
        raise ValueError("Invalid payment signature. Verification failed.")

    user_obj_id = to_object_id(user_id)
    payments_col = get_payments_collection()
    now = datetime.now(timezone.utc)

    payment = payments_col.find_one_and_update(
        {"razorpayOrderId": razorpay_order_id, "user": user_obj_id},
        {
            "$set": {
                "razorpayPaymentId": razorpay_payment_id,
                "razorpaySignature": razorpay_signature,
                "status": "paid",
                "updatedAt": now,
            }
        },
        return_document=True,
    )

    if not payment:
        raise ValueError("Payment record for this order was not found.")

    # Elevate user to premium
    users_col = get_users_collection()
    users_col.update_one({"_id": user_obj_id}, {"$set": {"isPremium": True, "updatedAt": now}})

    return {
        "verified": True,
        "paymentId": str(payment["_id"]),
        "status": "paid",
    }

def process_webhook_event(raw_body, signature):
    webhook_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", None) or os.getenv("RAZORPAY_WEBHOOK_SECRET")

    if webhook_secret and webhook_secret != "your_webhook_secret":
        if isinstance(raw_body, str):
            raw_bytes = raw_body.encode("utf-8")
        else:
            raw_bytes = raw_body

        expected_sig = hmac.new(
            webhook_secret.encode("utf-8"),
            raw_bytes,
            hashlib.sha256,
        ).hexdigest()

        if expected_sig != signature:
            raise ValueError("Invalid webhook signature.")

    event = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    event_type = event.get("event")
    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})

    payments_col = get_payments_collection()
    users_col = get_users_collection()
    now = datetime.now(timezone.utc)

    if event_type == "payment.captured" and payment_entity:
        order_id = payment_entity.get("order_id")
        payment = payments_col.find_one_and_update(
            {"razorpayOrderId": order_id},
            {
                "$set": {
                    "razorpayPaymentId": payment_entity.get("id"),
                    "status": "paid",
                    "updatedAt": now,
                }
            },
            return_document=True,
        )
        if payment and payment.get("user"):
            users_col.update_one({"_id": payment["user"]}, {"$set": {"isPremium": True, "updatedAt": now}})

    elif event_type == "payment.failed" and payment_entity:
        order_id = payment_entity.get("order_id")
        payments_col.update_one(
            {"razorpayOrderId": order_id},
            {
                "$set": {
                    "razorpayPaymentId": payment_entity.get("id"),
                    "status": "failed",
                    "updatedAt": now,
                }
            },
        )

    return {"received": True, "event": event_type}
