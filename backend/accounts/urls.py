"""
URL routing for accounts and auth endpoints.
"""

from django.urls import path
from accounts.views import (
    RegisterView,
    SendOtpView,
    VerifyOtpView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    UserProfileView,
    UploadAvatarView,
)

auth_urlpatterns = [
    path("register", RegisterView.as_view(), name="auth-register"),
    path("send-otp", SendOtpView.as_view(), name="auth-send-otp"),
    path("verify-otp", VerifyOtpView.as_view(), name="auth-verify-otp"),
    path("login", LoginView.as_view(), name="auth-login"),
    path("refresh", RefreshTokenView.as_view(), name="auth-refresh"),
    path("logout", LogoutView.as_view(), name="auth-logout"),
]

user_urlpatterns = [
    path("profile", UserProfileView.as_view(), name="user-profile"),
    path("avatar", UploadAvatarView.as_view(), name="user-avatar"),
]

urlpatterns = auth_urlpatterns
