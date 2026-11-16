"""
TruthScan AI Backend Master URL Configuration.
Exposes both primary (/api/...) and fallback (/...) route mounts.
Supports both with and without trailing slash.
"""

from django.urls import path, re_path, include
from django.http import JsonResponse
from accounts.views import (
    RegisterView,
    SendOtpView,
    VerifyOtpView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    UserProfileView,
    UploadAvatarView,
    ForgotPasswordView,
    VerifyResetOtpView,
    ResetPasswordView,
)
from factcheck.views import (
    CreateFactCheckView,
    CheckFileView,
    FactCheckHistoryView,
    FactCheckDetailView,
    ScanNewsView,
)
from news.views import (
    GetNewsView,
    RefreshNewsView,
    FactCheckNewsArticleView,
)
from payments.views import (
    CreateOrderView,
    VerifyPaymentView,
    WebhookView,
)
from analytics.views import (
    AnalyticsDashboardView,
    AdminUserListView,
    AdminUserDetailView,
)

def health_check(request):
    return JsonResponse({
        "success": True,
        "message": "TruthScan API is running",
    })

def route_pairs(endpoint, view, base_name):
    """Registers both /api/<endpoint> and /<endpoint> with and without trailing slash."""
    clean = endpoint.strip("/")
    routes = []
    for prefix in [f"api/{clean}", clean]:
        name_prefix = "api-" if prefix.startswith("api/") else ""
        routes.append(path(prefix, view, name=f"{name_prefix}{base_name}-noslash"))
        routes.append(path(f"{prefix}/", view, name=f"{name_prefix}{base_name}"))
    return routes

urlpatterns = [
    # Health checks
    *route_pairs("health", health_check, "health-check"),

    # Auth routes
    *route_pairs("auth/register", RegisterView.as_view(), "auth-register"),
    *route_pairs("auth/send-otp", SendOtpView.as_view(), "auth-send-otp"),
    *route_pairs("auth/verify-otp", VerifyOtpView.as_view(), "auth-verify-otp"),
    *route_pairs("auth/login", LoginView.as_view(), "auth-login"),
    *route_pairs("auth/forgot-password", ForgotPasswordView.as_view(), "auth-forgot-password"),
    *route_pairs("auth/verify-reset-otp", VerifyResetOtpView.as_view(), "auth-verify-reset-otp"),
    *route_pairs("auth/reset-password", ResetPasswordView.as_view(), "auth-reset-password"),
    *route_pairs("auth/refresh", RefreshTokenView.as_view(), "auth-refresh"),
    *route_pairs("auth/logout", LogoutView.as_view(), "auth-logout"),

    # User profile routes
    *route_pairs("users/profile", UserProfileView.as_view(), "user-profile"),
    *route_pairs("users/avatar", UploadAvatarView.as_view(), "user-avatar"),

    # Fact Check routes
    *route_pairs("fact-check", CreateFactCheckView.as_view(), "factcheck-create"),
    *route_pairs("fact-check/file", CheckFileView.as_view(), "factcheck-file"),
    *route_pairs("fact-check/history", FactCheckHistoryView.as_view(), "factcheck-history"),
    re_path(r"^api/fact-check/(?P<pk>[a-zA-Z0-9]+)/?$", FactCheckDetailView.as_view(), name="api-factcheck-detail"),
    re_path(r"^fact-check/(?P<pk>[a-zA-Z0-9]+)/?$", FactCheckDetailView.as_view(), name="factcheck-detail"),

    # Scan routes
    *route_pairs("scan", ScanNewsView.as_view(), "scan"),

    # News routes
    *route_pairs("news", GetNewsView.as_view(), "news"),
    *route_pairs("news/refresh", RefreshNewsView.as_view(), "news-refresh"),
    *route_pairs("news/fact-check", FactCheckNewsArticleView.as_view(), "news-fact-check"),

    # Payment routes
    *route_pairs("payments/create-order", CreateOrderView.as_view(), "payment-create-order"),
    *route_pairs("payments/verify", VerifyPaymentView.as_view(), "payment-verify"),
    *route_pairs("payments/webhook", WebhookView.as_view(), "payment-webhook"),

    # Analytics routes (legacy/compat)
    *route_pairs("analytics", AnalyticsDashboardView.as_view(), "analytics"),
]
