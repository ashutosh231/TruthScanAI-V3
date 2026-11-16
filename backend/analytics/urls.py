"""
URL routing for analytics and admin endpoints.
"""

from django.urls import path
from analytics.views import (
    AnalyticsDashboardView,
    AdminUserListView,
    AdminUserDetailView,
)

urlpatterns = [
    path("analytics", AnalyticsDashboardView.as_view(), name="analytics-dashboard"),
    path("admin/analytics", AnalyticsDashboardView.as_view(), name="admin-analytics"),
    path("admin/users", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<str:pk>", AdminUserDetailView.as_view(), name="admin-user-detail"),
]
