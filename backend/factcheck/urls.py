"""
URL routing for fact-checking endpoints.
"""

from django.urls import path
from factcheck.views import (
    CreateFactCheckView,
    CheckFileView,
    FactCheckHistoryView,
    FactCheckDetailView,
)

urlpatterns = [
    path("", CreateFactCheckView.as_view(), name="factcheck-create"),
    path("file", CheckFileView.as_view(), name="factcheck-file"),
    path("history", FactCheckHistoryView.as_view(), name="factcheck-history"),
    path("<str:pk>", FactCheckDetailView.as_view(), name="factcheck-detail"),
]
