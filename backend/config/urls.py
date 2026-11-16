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

def create_route_pairs(prefix, view, name):
    """Creates both with and without trailing slash route patterns."""
    clean_prefix = prefix.strip("/")
    return [
        path(clean_prefix, view, name=f"{name}-noslash"),
        path(f"{clean_prefix}/", view, name=name),
    ]

urlpatterns = [
    # Health checks
    *create_route_pairs("health", health_check, "health-check"),
    *create_route_pairs("api/health", health_check, "api-health-check"),

    # Auth routes
    *create_route_pairs("api/auth/register", RegisterView.as_view(), "api-auth-register"),
    *create_route_pairs("auth/register", RegisterView.as_view(), "auth-register"),
    *create_route_pairs("api/auth/send-otp", SendOtpView.as_view(), "api-auth-send-otp"),
    *create_route_pairs("auth/send-otp", SendOtpView.as_view(), "auth-send-otp"),
    *create_route_pairs("api/auth/verify-otp", VerifyOtpView.as_view(), "api-auth-verify-otp"),
    *create_route_pairs("auth/verify-otp", VerifyOtpView.as_view(), "auth-verify-otp"),
    *create_route_pairs("api/auth/login", LoginView.as_view(), "api-auth-login"),
    *create_route_pairs("auth/login", LoginView.as_view(), "auth-login"),
    *create_route_pairs("api/auth/forgot-password", ForgotPasswordView.as_view(), "api-auth-forgot-password"),
    *create_route_pairs("auth/forgot-password", ForgotPasswordView.as_view(), "auth-forgot-password"),
    *create_route_pairs("api/auth/verify-reset-otp", VerifyResetOtpView.as_view(), "api-auth-verify-reset-otp"),
    *create_route_pairs("auth/verify-reset-otp", VerifyResetOtpView.as_view(), "auth-verify-reset-otp"),
    *create_route_pairs("api/auth/reset-password", ResetPasswordView.as_view(), "api-auth-reset-password"),
    *create_route_pairs("auth/reset-password", ResetPasswordView.as_view(), "auth-reset-password"),
    *create_route_pairs("api/auth/refresh", RefreshTokenView.as_view(), "api-auth-refresh"),
    *create_route_pairs("auth/refresh", RefreshTokenView.as_view(), "auth-refresh"),
    *create_route_pairs("api/auth/logout", LogoutView.as_view(), "api-auth-logout"),
    *create_route_pairs("auth/logout", LogoutView.as_view(), "auth-logout"),

    # User profile routes
    *create_route_pairs("api/users/profile", UserProfileView.as_view(), "api-user-profile"),
    *create_route_pairs("users/profile", UserProfileView.as_view(), "user-profile"),
    *create_route_pairs("api/users/avatar", UploadAvatarView.as_view(), "api-user-avatar"),
    *create_route_pairs("users/avatar", UploadAvatarView.as_view(), "user-avatar"),

    # Fact Check routes
    *create_route_pairs("api/fact-check", CreateFactCheckView.as_view(), "api-factcheck-create"),
    *create_route_pairs("fact-check", CreateFactCheckView.as_view(), "factcheck-create"),
    *create_route_pairs("api/fact-check/file", CheckFileView.as_view(), "api-factcheck-file"),
    *create_route_pairs("fact-check/file", CheckFileView.as_view(), "factcheck-file"),
    *create_route_pairs("api/fact-check/history", FactCheckHistoryView.as_view(), "api-factcheck-history"),
    *create_route_pairs("fact-check/history", FactCheckHistoryView.as_view(), "factcheck-history"),
    re_path(r"^api/fact-check/(?P<pk>[a-zA-Z0-9]+)/?$", FactCheckDetailView.as_view(), name="api-factcheck-detail"),
    re_path(r"^fact-check/(?P<pk>[a-zA-Z0-9]+)/?$", FactCheckDetailView.as_view(), name="factcheck-detail"),

    # Scan routes
    *create_route_pairs("api/scan", ScanNewsView.as_view(), "api-scan"),
    *create_route_pairs("scan", ScanNewsView.as_view(), "scan"),

    # News routes
    *create_route_pairs("api/news", GetNewsView.as_view(), "api-news"),
    *create_route_pairs("news", GetNewsView.as_view(), "news"),
    *create_route_pairs("api/news/refresh", RefreshNewsView.as_view(), "api-news-refresh"),
    *create_route_pairs("news/refresh", RefreshNewsView.as_view(), "news-refresh"),
    *create_route_pairs("api/news/fact-check", FactCheckNewsArticleView.as_view(), "api-news-fact-check"),
    *create_route_pairs("news/fact-check", FactCheckNewsArticleView.as_view(), "news-fact-check"),

    # Payment routes
    *create_route_pairs("api/payments/create-order", CreateOrderView.as_view(), "api-payment-create-order"),
    *create_route_pairs("payments/create-order", CreateOrderView.as_view(), "payment-create-order"),
    *create_route_pairs("api/payments/verify", VerifyPaymentView.as_view(), "api-payment-verify"),
    *create_route_pairs("payments/verify", VerifyPaymentView.as_view(), "payment-verify"),
    *create_route_pairs("api/payments/webhook", WebhookView.as_view(), "api-payment-webhook"),
    *create_route_pairs("payments/webhook", WebhookView.as_view(), "payment-webhook"),

    # Analytics routes (legacy/compat)
    *create_route_pairs("api/analytics", AnalyticsDashboardView.as_view(), "api-analytics"),
    *create_route_pairs("analytics", AnalyticsDashboardView.as_view(), "analytics"),
]
