"""
Business logic and helpers for accounts and authentication.
"""

import os
import uuid
from datetime import datetime, timezone
import bcrypt
import cloudinary
import cloudinary.uploader
from django.conf import settings

from core.mongodb import get_users_collection, to_object_id
from core.utils import (
    generate_access_token,
    generate_refresh_token,
    verify_refresh_token,
    generate_otp,
    send_otp_email,
    get_redis_client,
)

OTP_TTL_SECONDS = 300  # 5 minutes
REFRESH_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days

def configure_cloudinary():
    cloud_name = getattr(settings, "CLOUDINARY_CLOUD_NAME", None) or os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = getattr(settings, "CLOUDINARY_API_KEY", None) or os.getenv("CLOUDINARY_API_KEY")
    api_secret = getattr(settings, "CLOUDINARY_API_SECRET", None) or os.getenv("CLOUDINARY_API_SECRET")

    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )

def hash_password(plain_password):
    salt = bcrypt.gensalt(10)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

def check_password(plain_password, hashed_password):
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def upload_avatar_to_cloudinary(file_obj):
    configure_cloudinary()
    if hasattr(file_obj, "read"):
        file_bytes = file_obj.read()
    else:
        file_bytes = file_obj

    result = cloudinary.uploader.upload(
        file_bytes,
        folder="truthscan_avatars",
        transformation=[
            {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
            {"quality": "auto"},
            {"fetch_format": "auto"},
        ],
    )
    return result.get("secure_url") or result.get("url")
