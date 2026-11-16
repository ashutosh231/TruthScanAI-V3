"""
TruthScan AI Admin Panel Views.
Protected by server-side RBAC (IsAdminMongoUser).
Provides dedicated admin authentication, analytics, CRUD operations,
AI monitoring, audit activity logs, and settings.
"""

import csv
import uuid
from datetime import datetime, timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from core.permissions import IsAdminMongoUser
from core.mongodb import get_users_collection, serialize_doc, to_object_id
from core.utils import (
    generate_access_token,
    generate_refresh_token,
    get_redis_client,
)
from core.ratelimit import get_client_ip, admin_login_rate_limit
from accounts.services import check_password, REFRESH_TTL_SECONDS
from admin_panel.serializers import (
    AdminLoginSerializer,
    AdminCreateUserSerializer,
    AdminUpdateUserSerializer,
    AdminReviewFactCheckSerializer,
    AdminNewsSerializer,
    AdminCategorySerializer,
    AdminDeleteCategorySerializer,
    AdminSettingsSerializer,
    AdminChangePasswordSerializer,
)
from admin_panel.services import (
    record_activity_log,
    get_admin_overview_stats,
    get_admin_dashboard_charts,
    list_admin_users,
    get_admin_user_detail,
    create_admin_user,
    update_admin_user,
    delete_admin_user,
    list_admin_factchecks,
    get_admin_factcheck_detail,
    delete_admin_factcheck,
    review_admin_factcheck,
    list_admin_news,
    get_admin_news_detail,
    create_admin_news,
    update_admin_news,
    delete_admin_news,
    list_admin_categories,
    create_admin_category,
    update_admin_category,
    delete_admin_category,
    get_ai_monitoring_data,
    list_activity_logs,
    get_admin_settings,
    update_admin_settings,
    change_admin_password,
)

is_production = getattr(settings, "NODE_ENV", "development") == "production"

def set_admin_cookie(response, token):
    response.set_cookie(
        "adminRefreshToken",
        token,
        max_age=REFRESH_TTL_SECONDS,
        httponly=True,
        secure=is_production,
        samesite="None" if is_production else "Lax",
    )


# ============================================================================
# Admin Authentication
# ============================================================================

class AdminLoginView(APIView):
    """
    POST /api/admin/login
    Dedicated administrator authentication with login rate limiting and strict role validation.
    """
    authentication_classes = []
    permission_classes = []

    @admin_login_rate_limit
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]
        ip = get_client_ip(request)

        users_col = get_users_collection()
        user_doc = users_col.find_one({"email": email, "isDeleted": {"$ne": True}})

        if not user_doc or not check_password(password, user_doc.get("password", "")):
            return Response(
                {"success": False, "message": "Invalid administrator credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Enforce server-side role check
        if user_doc.get("role") != "admin":
            return Response(
                {"success": False, "message": "Access denied: Account lacks administrative clearance."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user_doc.get("isSuspended"):
            return Response(
                {"success": False, "message": "This administrator account is suspended."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id = str(user_doc["_id"])
        access_token = generate_access_token({"userId": user_id, "role": "admin"})
        token_id = str(uuid.uuid4())
        refresh_token = generate_refresh_token({"userId": user_id, "tokenId": token_id})

        # Cache refresh token in Redis
        try:
            redis_client = get_redis_client()
            redis_client.set(f"refresh:{token_id}", user_id, ex=REFRESH_TTL_SECONDS)
        except Exception as err:
            print(f"[AdminLogin] Redis warning: {err}")

        user_data = {
            "id": user_id,
            "name": user_doc.get("name", "Administrator"),
            "email": user_doc.get("email"),
            "role": "admin",
            "isPremium": True,
            "avatar": user_doc.get("avatar", ""),
        }

        # Log audit entry
        record_activity_log(
            admin_user=type("Obj", (), {"id": user_id, "email": email, "name": user_data["name"]}),
            action="ADMIN_LOGIN",
            target_type="auth",
            target_id=user_id,
            details={"ip": ip},
            ip_address=ip,
        )

        response = Response(
            {
                "success": True,
                "message": "Administrator authentication successful.",
                "data": {
                    "accessToken": access_token,
                    "user": user_data,
                },
            },
            status=status.HTTP_200_OK,
        )
        set_admin_cookie(response, refresh_token)
        return response


class AdminLogoutView(APIView):
    """
    POST /api/admin/logout
    Terminates admin session.
    """
    permission_classes = [IsAdminMongoUser]

    def post(self, request):
        ip = get_client_ip(request)
        record_activity_log(
            admin_user=request.user,
            action="ADMIN_LOGOUT",
            target_type="auth",
            target_id=request.user.id,
            details={"ip": ip},
            ip_address=ip,
        )
        response = Response(
            {"success": True, "message": "Admin session terminated successfully."},
            status=status.HTTP_200_OK,
        )
        response.delete_cookie("adminRefreshToken")
        response.delete_cookie("refreshToken")
        return response


class AdminProfileView(APIView):
    """
    GET /api/admin/profile
    Retrieves current authenticated admin profile.
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        return Response(
            {
                "success": True,
                "data": request.user.to_dict(),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================================
# Overview & Charts
# ============================================================================

class AdminDashboardStatsView(APIView):
    """
    GET /api/admin/dashboard/stats
    Returns KPIs with period-over-period percentage growth.
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        stats = get_admin_overview_stats()
        return Response({"success": True, "data": stats}, status=status.HTTP_200_OK)


class AdminDashboardChartsView(APIView):
    """
    GET /api/admin/dashboard/charts?period=30d
    Returns aggregated charts for timeline, verdict distribution, categories,
    user growth, user activity, sources, and AI performance.
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        period = request.query_params.get("period", "30d")
        charts = get_admin_dashboard_charts(period=period)
        return Response({"success": True, "data": charts}, status=status.HTTP_200_OK)


# ============================================================================
# Users Management CRUD
# ============================================================================

class AdminUsersView(APIView):
    """
    GET /api/admin/users - Paginated user list with search & filters
    POST /api/admin/users - Create new user account
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        page = max(1, int(request.query_params.get("page", 1)))
        limit = min(100, max(1, int(request.query_params.get("limit", 20))))
        search = request.query_params.get("search", "").strip()
        role = request.query_params.get("role", "").strip()
        status_param = request.query_params.get("status", "").strip()
        date_from = request.query_params.get("dateFrom")
        date_to = request.query_params.get("dateTo")

        result = list_admin_users(
            page=page,
            limit=limit,
            search=search,
            role=role,
            status=status_param,
            date_from=date_from,
            date_to=date_to,
        )
        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminCreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid input.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            created = create_admin_user(
                serializer.validated_data,
                current_admin=request.user,
                ip=get_client_ip(request),
            )
            return Response(
                {"success": True, "message": "User created successfully.", "data": created},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdminUserDetailView(APIView):
    """
    GET /api/admin/users/:id - User details with audit volume and fact-check history
    PATCH /api/admin/users/:id - Update user details, role, status
    DELETE /api/admin/users/:id - Soft or hard delete user
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request, pk):
        user = get_admin_user_detail(pk)
        if not user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": user}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        serializer = AdminUpdateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid update input.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            updated = update_admin_user(
                pk,
                serializer.validated_data,
                current_admin=request.user,
                ip=get_client_ip(request),
            )
            if not updated:
                return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"success": True, "message": "User updated.", "data": updated}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        soft = request.query_params.get("hard") != "true"
        ok, msg = delete_admin_user(pk, current_admin=request.user, ip=get_client_ip(request), soft=soft)
        if not ok:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "message": msg}, status=status.HTTP_200_OK)


# ============================================================================
# Fact Checks CRUD
# ============================================================================

class AdminFactChecksView(APIView):
    """
    GET /api/admin/fact-checks
    Supports search, filters, pagination, and CSV export via ?export=csv
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        export = request.query_params.get("export") == "csv"
        page = max(1, int(request.query_params.get("page", 1)))
        limit = 1000 if export else min(100, max(1, int(request.query_params.get("limit", 20))))
        search = request.query_params.get("search", "").strip()
        verdict = request.query_params.get("verdict", "").strip()
        category = request.query_params.get("category", "").strip()
        user_id = request.query_params.get("userId", "").strip()
        date_from = request.query_params.get("dateFrom")
        date_to = request.query_params.get("dateTo")
        sort_by = request.query_params.get("sortBy", "-createdAt")

        result = list_admin_factchecks(
            page=page,
            limit=limit,
            search=search,
            verdict=verdict,
            category=category,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
        )

        if export:
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="truthscan_factchecks.csv"'
            writer = csv.writer(response)
            writer.writerow(["ID", "Claim / Input", "Type", "Verdict", "Confidence", "Investigator", "Date"])
            for fc in result["factChecks"]:
                writer.writerow([
                    fc.get("id"),
                    (fc.get("input") or "").replace("\n", " ")[:120],
                    fc.get("type"),
                    fc.get("verdict"),
                    fc.get("confidence"),
                    fc.get("userName") or fc.get("userEmail") or "N/A",
                    fc.get("createdAt"),
                ])
            return response

        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)


class AdminFactCheckDetailView(APIView):
    """
    GET /api/admin/fact-checks/:id
    DELETE /api/admin/fact-checks/:id
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request, pk):
        doc = get_admin_factcheck_detail(pk)
        if not doc:
            return Response({"success": False, "message": "Fact check record not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": doc}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        ok, msg = delete_admin_factcheck(pk, current_admin=request.user, ip=get_client_ip(request))
        if not ok:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "message": msg}, status=status.HTTP_200_OK)


class AdminFactCheckReviewView(APIView):
    """
    POST /api/admin/fact-checks/:id/review
    Records administrative decision/notes without overwriting original AI verdict.
    """
    permission_classes = [IsAdminMongoUser]

    def post(self, request, pk):
        serializer = AdminReviewFactCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid review data.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = review_admin_factcheck(
            pk,
            decision=serializer.validated_data["decision"],
            review_notes=serializer.validated_data["notes"],
            current_admin=request.user,
            ip=get_client_ip(request),
        )
        if not updated:
            return Response({"success": False, "message": "Fact check record not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {"success": True, "message": "Administrative review recorded.", "data": updated},
            status=status.HTTP_200_OK,
        )


# ============================================================================
# News CRUD
# ============================================================================

class AdminNewsView(APIView):
    """
    GET /api/admin/news
    POST /api/admin/news
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        page = max(1, int(request.query_params.get("page", 1)))
        limit = min(100, max(1, int(request.query_params.get("limit", 20))))
        search = request.query_params.get("search", "").strip()
        category = request.query_params.get("category", "").strip()
        status_param = request.query_params.get("status", "").strip()
        date_from = request.query_params.get("dateFrom")
        date_to = request.query_params.get("dateTo")

        result = list_admin_news(
            page=page,
            limit=limit,
            search=search,
            category=category,
            status=status_param,
            date_from=date_from,
            date_to=date_to,
        )
        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminNewsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid news data.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            created = create_admin_news(
                serializer.validated_data,
                current_admin=request.user,
                ip=get_client_ip(request),
            )
            return Response(
                {"success": True, "message": "News article published.", "data": created},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdminNewsDetailView(APIView):
    """
    GET /api/admin/news/:id
    PATCH /api/admin/news/:id
    DELETE /api/admin/news/:id
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request, pk):
        item = get_admin_news_detail(pk)
        if not item:
            return Response({"success": False, "message": "News article not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": item}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        updated = update_admin_news(pk, request.data, current_admin=request.user, ip=get_client_ip(request))
        if not updated:
            return Response({"success": False, "message": "News article not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "message": "News article updated.", "data": updated}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        ok, msg = delete_admin_news(pk, current_admin=request.user, ip=get_client_ip(request))
        if not ok:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "message": msg}, status=status.HTTP_200_OK)


# ============================================================================
# Category Management CRUD
# ============================================================================

class AdminCategoriesView(APIView):
    """
    GET /api/admin/categories - List categories with fact check references count
    POST /api/admin/categories - Create category
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        cats = list_admin_categories()
        return Response({"success": True, "data": cats}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid category data.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            created = create_admin_category(
                serializer.validated_data,
                current_admin=request.user,
                ip=get_client_ip(request),
            )
            return Response(
                {"success": True, "message": "Category created.", "data": created},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AdminCategoryDetailView(APIView):
    """
    PATCH /api/admin/categories/:id - Update category
    DELETE /api/admin/categories/:id - Safe deletion with reference check/reassignment
    """
    permission_classes = [IsAdminMongoUser]

    def patch(self, request, pk):
        serializer = AdminCategorySerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid update data.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = update_admin_category(pk, serializer.validated_data, current_admin=request.user, ip=get_client_ip(request))
        if not updated:
            return Response({"success": False, "message": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "message": "Category updated.", "data": updated}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        return self.patch(request, pk)

    def delete(self, request, pk):
        serializer = AdminDeleteCategorySerializer(data=request.query_params or request.data)
        serializer.is_valid()
        reassign_slug = serializer.validated_data.get("reassignToSlug", "")
        ok, msg = delete_admin_category(
            pk,
            reassign_to_slug=reassign_slug,
            current_admin=request.user,
            ip=get_client_ip(request),
        )
        if not ok:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "message": msg}, status=status.HTTP_200_OK)


# ============================================================================
# AI Monitoring
# ============================================================================

class AdminAiMonitoringView(APIView):
    """
    GET /api/admin/monitoring/ai
    Real aggregates of Bedrock, Textract, and Tavily requests, latency, errors.
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        data = get_ai_monitoring_data()
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)


# ============================================================================
# Activity Logs
# ============================================================================

class AdminActivityLogsView(APIView):
    """
    GET /api/admin/activity-logs
    Immutable audit trail of administrator actions.
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        page = max(1, int(request.query_params.get("page", 1)))
        limit = min(100, max(1, int(request.query_params.get("limit", 25))))
        action = request.query_params.get("action", "").strip()
        admin_id = request.query_params.get("adminId", "").strip()
        date_from = request.query_params.get("dateFrom")
        date_to = request.query_params.get("dateTo")

        result = list_activity_logs(
            page=page,
            limit=limit,
            action=action,
            admin_id=admin_id,
            date_from=date_from,
            date_to=date_to,
        )
        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)


# ============================================================================
# Settings & Password Management
# ============================================================================

class AdminSettingsView(APIView):
    """
    GET /api/admin/settings
    PATCH /api/admin/settings
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        data = get_admin_settings(request.user)
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = AdminSettingsSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Invalid settings input.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = update_admin_settings(request.user, serializer.validated_data, ip=get_client_ip(request))
        return Response({"success": True, "message": "Settings updated.", "data": updated}, status=status.HTTP_200_OK)

    def put(self, request):
        return self.patch(request)


class AdminChangePasswordView(APIView):
    """
    POST /api/admin/settings/change-password
    """
    permission_classes = [IsAdminMongoUser]

    def post(self, request):
        serializer = AdminChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Current and new passwords (min 8 chars) are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ok, msg = change_admin_password(
            request.user,
            current_password=serializer.validated_data["currentPassword"],
            new_password=serializer.validated_data["newPassword"],
            ip=get_client_ip(request),
        )
        if not ok:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "message": msg}, status=status.HTTP_200_OK)
