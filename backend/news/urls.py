"""
URL routing for news endpoints.
"""

from django.urls import path
from news.views import GetNewsView, RefreshNewsView, FactCheckNewsArticleView

urlpatterns = [
    path("", GetNewsView.as_view(), name="news-list"),
    path("refresh", RefreshNewsView.as_view(), name="news-refresh"),
    path("fact-check", FactCheckNewsArticleView.as_view(), name="news-fact-check"),
]
