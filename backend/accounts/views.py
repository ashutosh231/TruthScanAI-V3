"""
Authentication & User Profile Views.
Directly maps all authController.js & userController.js endpoints to DRF.
"""

import os
import uuid
from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from core.mongodb import (
    get_users_collection,
    get_factchecks_collection,
    to_object_id,
    serialize_doc,
)
from core.permissions import IsAuthenticatedMongoUser
from core.utils import (
    generate_access_token,
    generate_refresh_token,
    verify_refresh_token,
    generate_otp,
    send_otp_email,
    get_redis_client,
)
from core.ratelimit import (
    register_rate_limit,
    send_otp_rate_limit,
    verify_otp_rate_limit,
    login_rate_limit,
)
from accounts.serializers import (
    RegisterSerializer,
    SendOtpSerializer,
    VerifyOtpSerializer,
    LoginSerializer,
    UpdateProfileSerializer,
)
from accounts.services import (
    hash_password,
    check_password,
    upload_avatar_to_cloudinary,
    OTP_TTL_SECONDS,
    REFRESH_TTL_SECONDS,
)

is_production = getattr(settings, "NODE_ENV", os.getenv("NODE_ENV")) == "production"

def set_refresh_cookie(response, token):
    response.set_cookie(
        "refreshToken",
        token,
        max_age=REFRESH_TTL_SECONDS,
        httponly=True,
        secure=is_production,
        samesite="None" if is_production else "Lax",
    )

class RegisterView(APIView):
    """
    POST /api/auth/register
    Register a new user and dispatch 6-digit OTP.
    """
    authentication_classes = []
    permission_classes = []

    @register_rate_limit
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            first_err = list(serializer.errors.values())[0][0]
            return Response(
                {"success": False, "message": str(first_err)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = serializer.validated_data["name"].strip()
        email = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]

        users_col = get_users_collection()
        existing_user = users_col.find_one({"email": email})

        now = datetime.now(timezone.utc)
        if existing_user:
            if existing_user.get("isVerified"):
                return Response(
                    {
                        "success": False,
                        "message": "An account with this email address already exists.",
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            # Update password and name for unverified user
            hashed = hash_password(password)
            users_col.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "name": name,
                        "password": hashed,
                        "updatedAt": now,
                    }
                },
            )
        else:
            hashed = hash_password(password)
            users_col.insert_one(
                {
                    "name": name,
                    "email": email,
                    "password": hashed,
                    "isVerified": False,
                    "role": "user",
                    "isPremium": False,
                    "avatar": "",
                    "createdAt": now,
                    "updatedAt": now,
                }
            )

        # Generate 6-digit OTP
        otp = generate_otp()
        redis_client = get_redis_client()
        redis_client.set(f"otp:{email}", otp, ex=OTP_TTL_SECONDS)

        # Directly dispatch verification OTP email
        try:
            send_otp_email(email, otp)
        except Exception as e:
            print(f"[RegisterView] Email dispatch warning: {e}")

        return Response(
            {
                "success": True,
                "message": "Registration initiated. Verification OTP has been dispatched to your email.",
                "data": {
                    "email": email,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class SendOtpView(APIView):
    """
    POST /api/auth/send-otp
    Request or resend an OTP.
    """
    authentication_classes = []
    permission_classes = []

    @send_otp_rate_limit
    def post(self, request):
        serializer = SendOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Email address is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower().strip()
        users_col = get_users_collection()
        user = users_col.find_one({"email": email})

        if not user:
            return Response(
                {"success": False, "message": "User with this email was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        otp = generate_otp()
        redis_client = get_redis_client()
        redis_client.set(f"otp:{email}", otp, ex=OTP_TTL_SECONDS)

        # Directly dispatch verification OTP email
        try:
            send_otp_email(email, otp)
        except Exception as e:
            print(f"[SendOtpView] Email dispatch warning: {e}")

        return Response(
            {
                "success": True,
                "message": "A fresh verification OTP has been dispatched to your email.",
            },
            status=status.HTTP_200_OK,
        )


class VerifyOtpView(APIView):
    """
    POST /api/auth/verify-otp
    Verify OTP code and authenticate user.
    """
    authentication_classes = []
    permission_classes = []

    @verify_otp_rate_limit
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Email and OTP code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower().strip()
        otp = serializer.validated_data["otp"].strip()

        redis_client = get_redis_client()
        cached_otp = redis_client.get(f"otp:{email}")

        if not cached_otp or cached_otp != otp:
            return Response(
                {"success": False, "message": "Invalid or expired OTP code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        redis_client.delete(f"otp:{email}")

        users_col = get_users_collection()
        now = datetime.now(timezone.utc)
        user = users_col.find_one_and_update(
            {"email": email},
            {"$set": {"isVerified": True, "updatedAt": now}},
            return_document=True,
        )

        if not user:
            return Response(
                {"success": False, "message": "User record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_id_str = str(user["_id"])
        role = user.get("role", "user")

        access_token = generate_access_token({"userId": user_id_str, "role": role})
        token_id = str(uuid.uuid4())
        refresh_token = generate_refresh_token({"userId": user_id_str, "tokenId": token_id})

        redis_client.set(f"refresh:{token_id}", user_id_str, ex=REFRESH_TTL_SECONDS)

        response = Response(
            {
                "success": True,
                "message": "Account verified and authenticated successfully.",
                "data": {
                    "accessToken": access_token,
                    "user": {
                        "id": user_id_str,
                        "name": user.get("name", ""),
                        "email": user.get("email", ""),
                        "role": role,
                        "isPremium": bool(user.get("isPremium", False)),
                    },
                },
            },
            status=status.HTTP_200_OK,
        )
        set_refresh_cookie(response, refresh_token)
        return response


class LoginView(APIView):
    """
    POST /api/auth/login
    Login with email and password.
    """
    authentication_classes = []
    permission_classes = []

    @login_rate_limit
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]

        users_col = get_users_collection()
        user = users_col.find_one({"email": email})

        if not user or not check_password(password, user.get("password", "")):
            return Response(
                {
                    "success": False,
                    "message": "Invalid credentials. Please verify your email and password.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.get("isVerified", False):
            return Response(
                {
                    "success": False,
                    "message": "Account not verified. Please verify your OTP code first.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id_str = str(user["_id"])
        role = user.get("role", "user")

        access_token = generate_access_token({"userId": user_id_str, "role": role})
        token_id = str(uuid.uuid4())
        refresh_token = generate_refresh_token({"userId": user_id_str, "tokenId": token_id})

        redis_client = get_redis_client()
        redis_client.set(f"refresh:{token_id}", user_id_str, ex=REFRESH_TTL_SECONDS)

        response = Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": {
                    "accessToken": access_token,
                    "user": {
                        "id": user_id_str,
                        "name": user.get("name", ""),
                        "email": user.get("email", ""),
                        "role": role,
                        "isPremium": bool(user.get("isPremium", False)),
                    },
                },
            },
            status=status.HTTP_200_OK,
        )
        set_refresh_cookie(response, refresh_token)
        return response


class RefreshTokenView(APIView):
    """
    POST /api/auth/refresh
    Issue new access token from httpOnly refreshToken cookie.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        token = request.COOKIES.get("refreshToken")
        if not token:
            return Response(
                {"success": False, "message": "No refresh token found in request cookies."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            decoded = verify_refresh_token(token)
        except Exception:
            return Response(
                {"success": False, "message": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user_id_str = decoded.get("userId")
        token_id = decoded.get("tokenId")

        redis_client = get_redis_client()
        stored_user_id = redis_client.get(f"refresh:{token_id}")

        if not stored_user_id or stored_user_id != user_id_str:
            return Response(
                {"success": False, "message": "Refresh token revoked or expired in cache."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        users_col = get_users_collection()
        user = users_col.find_one({"_id": to_object_id(user_id_str)})
        if not user:
            return Response(
                {"success": False, "message": "User account no longer exists."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        new_access_token = generate_access_token({
            "userId": user_id_str,
            "role": user.get("role", "user"),
        })

        return Response(
            {
                "success": True,
                "message": "Session token refreshed.",
                "data": {
                    "accessToken": new_access_token,
                },
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout
    Revoke refresh token and clear cookie.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        token = request.COOKIES.get("refreshToken")
        if token:
            try:
                decoded = verify_refresh_token(token)
                token_id = decoded.get("tokenId")
                if token_id:
                    redis_client = get_redis_client()
                    redis_client.delete(f"refresh:{token_id}")
            except Exception:
                pass

        response = Response(
            {
                "success": True,
                "message": "Session logged out and refresh token revoked successfully.",
            },
            status=status.HTTP_200_OK,
        )
        response.delete_cookie(
            "refreshToken",
            samesite="None" if is_production else "Lax",
        )
        return response


class UserProfileView(APIView):
    """
    GET /api/users/profile
    PUT /api/users/profile
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request):
        users_col = get_users_collection()
        factchecks_col = get_factchecks_collection()

        user = users_col.find_one({"_id": request.user._id})
        if not user:
            return Response(
                {"success": False, "message": "User record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        trials_used = factchecks_col.count_documents({"user": user["_id"]})
        is_premium = bool(user.get("isPremium", False))

        created_at_val = user.get("createdAt")
        created_at_str = created_at_val.isoformat() if isinstance(created_at_val, datetime) else str(created_at_val or "")

        return Response(
            {
                "success": True,
                "data": {
                    "id": str(user["_id"]),
                    "name": user.get("name", ""),
                    "email": user.get("email", ""),
                    "role": user.get("role", "user"),
                    "isVerified": bool(user.get("isVerified", False)),
                    "isPremium": is_premium,
                    "avatar": user.get("avatar", ""),
                    "trialsUsed": trials_used,
                    "trialsRemaining": None if is_premium else max(0, 2 - trials_used),
                    "trialLimit": 2,
                    "createdAt": created_at_str,
                },
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        serializer = UpdateProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid profile update data."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = serializer.validated_data.get("name")
        users_col = get_users_collection()

        update_fields = {"updatedAt": datetime.now(timezone.utc)}
        if name is not None:
            update_fields["name"] = name.strip()

        user = users_col.find_one_and_update(
            {"_id": request.user._id},
            {"$set": update_fields},
            return_document=True,
        )

        if not user:
            return Response(
                {"success": False, "message": "User record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "success": True,
                "message": "Profile updated successfully.",
                "data": {
                    "id": str(user["_id"]),
                    "name": user.get("name", ""),
                    "email": user.get("email", ""),
                    "role": user.get("role", "user"),
                    "isPremium": bool(user.get("isPremium", False)),
                    "avatar": user.get("avatar", ""),
                },
            },
            status=status.HTTP_200_OK,
        )


class UploadAvatarView(APIView):
    """
    POST /api/users/avatar
    Upload profile photo to Cloudinary.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def post(self, request):
        avatar_file = request.FILES.get("avatar")
        if not avatar_file:
            return Response(
                {"success": False, "message": "No image file provided for profile photo upload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            avatar_url = upload_avatar_to_cloudinary(avatar_file)
        except Exception as e:
            return Response(
                {"success": False, "message": f"Cloudinary upload failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        users_col = get_users_collection()
        user = users_col.find_one_and_update(
            {"_id": request.user._id},
            {
                "$set": {
                    "avatar": avatar_url,
                    "updatedAt": datetime.now(timezone.utc),
                }
            },
            return_document=True,
        )

        if not user:
            return Response(
                {"success": False, "message": "User record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "success": True,
                "message": "Profile photo uploaded and updated successfully.",
                "data": {
                    "avatar": avatar_url,
                    "user": {
                        "id": str(user["_id"]),
                        "name": user.get("name", ""),
                        "email": user.get("email", ""),
                        "role": user.get("role", "user"),
                        "isPremium": bool(user.get("isPremium", False)),
                        "avatar": avatar_url,
                    },
                },
            },
            status=status.HTTP_200_OK,
        )
