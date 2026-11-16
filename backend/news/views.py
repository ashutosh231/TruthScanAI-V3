"""
News Views:
GET /api/news
GET /api/news/refresh
POST /api/news/fact-check
"""

from datetime import datetime, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.mongodb import get_factchecks_collection
from core.utils import sanitize_public_report
from news.services import get_latest_news, refresh_news_cache
from ai_engine.bedrock_service import fact_check_with_ai

class GetNewsView(APIView):
    """
    GET /api/news?category=all&q=keyword&refresh=true
    Get latest news articles or search live web for news.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        category = request.query_params.get("category", "all")
        query = request.query_params.get("q") or request.query_params.get("search") or ""
        is_refresh = request.query_params.get("refresh", "").lower() in ["true", "1", "yes"]

        result = get_latest_news(category=category, force_refresh=is_refresh, query=query)

        return Response(
            {
                "success": True,
                "cached": result["cached"],
                "count": len(result["articles"]),
                "data": result["articles"],
                "query": query,
                "category": category,
            },
            status=status.HTTP_200_OK,
        )


class RefreshNewsView(APIView):
    """
    GET /api/news/refresh?category=all&q=keyword
    Force-refresh news wire from live web providers.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        category = request.query_params.get("category", "all")
        query = request.query_params.get("q") or request.query_params.get("search") or ""

        result = refresh_news_cache(category=category, query=query)

        return Response(
            {
                "success": True,
                "message": "News cache successfully refreshed from provider and web.",
                "cached": False,
                "count": len(result["articles"]),
                "data": result["articles"],
                "query": query,
                "category": category,
            },
            status=status.HTTP_200_OK,
        )


class FactCheckNewsArticleView(APIView):
    """
    POST /api/news/fact-check
    Fact check a news wire article.
    Optional authentication: if user is logged in, saved to their history.
    """
    permission_classes = []

    def post(self, request):
        title = request.data.get("title", "")
        description = request.data.get("description", "")
        url = request.data.get("url", "")
        article_id = request.data.get("articleId", "")

        if not title and not description:
            return Response(
                {"success": False, "message": "Article title or description is required for fact-checking."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        claim_text = f"{title or ''}. {description or ''}".strip()
        ai_result = fact_check_with_ai(claim_text)

        verdict = ai_result.get("verdict", "MISLEADING")
        confidence = round(ai_result.get("confidence", 85))
        explanation = (ai_result.get("explanation") or "").strip()

        saved_record_id = None
        user_id = getattr(request.user, "_id", None) if request.user and getattr(request.user, "is_authenticated", False) else None

        if user_id:
            try:
                factchecks_col = get_factchecks_collection()
                now = datetime.now(timezone.utc)
                doc_to_insert = {
                    "user": user_id,
                    "input": claim_text,
                    "type": "news",
                    "verdict": verdict,
                    "confidence": confidence,
                    "explanation": explanation,
                    "sources": ai_result.get("sources", []),
                    "researchMetadata": ai_result.get("researchMetadata", {}),
                    "metadata": {
                        "articleId": article_id,
                        "title": title,
                        "url": url,
                        "timelineAndContext": ai_result.get("timelineAndContext", ""),
                        "debunkingEvidence": ai_result.get("debunkingEvidence", []),
                        "keySignals": ai_result.get("keySignals", []),
                        "tactics": ai_result.get("tactics", []),
                        "sourcesChecked": ai_result.get("sourcesChecked", []),
                        "advisory": ai_result.get("advisory", ""),
                        "sources": ai_result.get("sources", []),
                        "researchMetadata": ai_result.get("researchMetadata", {}),
                    },
                    "createdAt": now,
                    "updatedAt": now,
                }
                res = factchecks_col.insert_one(doc_to_insert)
                saved_record_id = str(res.inserted_id)
            except Exception as db_err:
                print(f"[NewsView DB Save Notice]: {db_err}")

        public_data = sanitize_public_report({
            "verdict": verdict,
            "confidence": confidence,
            "explanation": explanation,
            "timelineAndContext": ai_result.get("timelineAndContext", ""),
            "debunkingEvidence": ai_result.get("debunkingEvidence", []),
            "keySignals": ai_result.get("keySignals", []),
            "tactics": ai_result.get("tactics", []),
            "sourcesChecked": ai_result.get("sourcesChecked", []),
            "advisory": ai_result.get("advisory", ""),
            "claimAnalyzed": claim_text,
            "sources": ai_result.get("sources", []),
            "researchMetadata": ai_result.get("researchMetadata", {}),
            "recordId": saved_record_id,
        })

        return Response(
            {
                "success": True,
                **public_data,
                "data": public_data,
            },
            status=status.HTTP_200_OK,
        )
