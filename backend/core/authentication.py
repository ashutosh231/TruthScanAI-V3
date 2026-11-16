"""
TruthScan JWT Authentication for Django REST Framework.
Authenticates against existing users in MongoDB Atlas.
"""

from bson import ObjectId
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
import jwt

from core.mongodb import get_users_collection, to_object_id
from core.utils import verify_access_token

class MongoUser:
    """
    Lightweight user object wrapping MongoDB user document.
    Compatible with DRF request.user conventions.
    """
    def __init__(self, doc):
        self._doc = doc or {}
        raw_id = self._doc.get("_id")
        self._id = raw_id
        self.id = str(raw_id) if raw_id else ""
        self.email = self._doc.get("email", "")
        self.name = self._doc.get("name", "")
        self.role = self._doc.get("role", "user")
        self.isPremium = bool(self._doc.get("isPremium", False))
        self.isVerified = bool(self._doc.get("isVerified", False))
        self.avatar = self._doc.get("avatar", "")
        self.createdAt = self._doc.get("createdAt")
        self.updatedAt = self._doc.get("updatedAt")

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return True

    @property
    def is_staff(self):
        return self.role == "admin"

    @property
    def is_superuser(self):
        return self.role == "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "isPremium": self.isPremium,
            "isVerified": self.isVerified,
            "avatar": self.avatar,
        }

    def __str__(self):
        return f"MongoUser({self.email}, role={self.role})"


class TruthScanJWTAuthentication(authentication.BaseAuthentication):
    """
    Authenticates requests using Bearer JWT access tokens.
    Payload must contain { userId, role }.
    """
    def authenticate_header(self, request):
        return 'Bearer realm="api"'

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1].strip()
        if not token:
            raise AuthenticationFailed("Access denied. No authentication token provided.")

        try:
            payload = verify_access_token(token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Authentication token has expired. Please refresh your session.")
        except jwt.PyJWTError:
            raise AuthenticationFailed("Invalid authentication token. Authorization denied.")

        user_id = payload.get("userId")
        obj_id = to_object_id(user_id)
        if not obj_id:
            raise AuthenticationFailed("Malformed user identification in token.")

        users_col = get_users_collection()
        user_doc = users_col.find_one({"_id": obj_id}, {"password": 0})
        if not user_doc:
            raise AuthenticationFailed("User account associated with this token no longer exists.")

        user = MongoUser(user_doc)
        request.userToken = payload
        return (user, token)
