from django.urls import path, re_path
from admin_panel.views import (
    AdminLoginView,
    AdminLogoutView,
    AdminProfileView,
    AdminDashboardStatsView,
    AdminDashboardChartsView,
    AdminUsersView,
    AdminUserDetailView,
    AdminFactChecksView,
    AdminFactCheckDetailView,
    AdminFactCheckReviewView,
    AdminNewsView,
    AdminNewsDetailView,
    AdminCategoriesView,
    AdminCategoryDetailView,
    AdminAiMonitoringView,
    AdminActivityLogsView,
    AdminSettingsView,
    AdminChangePasswordView,
)

def create_pair(pattern, view, name):
    clean = pattern.strip("/")
    return [
        path(clean, view, name=f"{name}-noslash"),
        path(f"{clean}/", view, name=name),
    ]

urlpatterns = [
    # Auth
    *create_pair("login", AdminLoginView.as_view(), "admin-login"),
    *create_pair("logout", AdminLogoutView.as_view(), "admin-logout"),
    *create_pair("profile", AdminProfileView.as_view(), "admin-profile"),

    # Dashboard & Charts
    *create_pair("dashboard/stats", AdminDashboardStatsView.as_view(), "admin-dashboard-stats"),
    *create_pair("dashboard/charts", AdminDashboardChartsView.as_view(), "admin-dashboard-charts"),

    # Users CRUD
    *create_pair("users", AdminUsersView.as_view(), "admin-users"),
    re_path(r"^users/(?P<pk>[a-zA-Z0-9]+)/?$", AdminUserDetailView.as_view(), name="admin-user-detail"),

    # Fact Checks CRUD
    *create_pair("fact-checks", AdminFactChecksView.as_view(), "admin-factchecks"),
    re_path(r"^fact-checks/(?P<pk>[a-zA-Z0-9]+)/review/?$", AdminFactCheckReviewView.as_view(), name="admin-factcheck-review"),
    re_path(r"^fact-checks/(?P<pk>[a-zA-Z0-9]+)/?$", AdminFactCheckDetailView.as_view(), name="admin-factcheck-detail"),

    # News CRUD
    *create_pair("news", AdminNewsView.as_view(), "admin-news"),
    re_path(r"^news/(?P<pk>[a-zA-Z0-9]+)/?$", AdminNewsDetailView.as_view(), name="admin-news-detail"),

    # Categories CRUD
    *create_pair("categories", AdminCategoriesView.as_view(), "admin-categories"),
    re_path(r"^categories/(?P<pk>[a-zA-Z0-9]+)/?$", AdminCategoryDetailView.as_view(), name="admin-category-detail"),

    # AI Monitoring
    *create_pair("monitoring/ai", AdminAiMonitoringView.as_view(), "admin-monitoring-ai"),

    # Activity Logs
    *create_pair("activity-logs", AdminActivityLogsView.as_view(), "admin-activity-logs"),

    # Settings
    *create_pair("settings", AdminSettingsView.as_view(), "admin-settings"),
    *create_pair("settings/change-password", AdminChangePasswordView.as_view(), "admin-settings-change-password"),
]
