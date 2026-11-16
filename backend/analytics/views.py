"""
Analytics & Admin Management Views.
Implements:
- GET /api/analytics & GET /api/admin/analytics
- GET /api/admin/users
- GET /api/admin/users/:id
- PUT /api/admin/users/:id
- DELETE /api/admin/users/:id
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.permissions import IsAuthenticatedMongoUser, IsAdminMongoUser
from core.mongodb import (
    get_users_collection,
    get_factchecks_collection,
    to_object_id,
    serialize_doc,
)
from analytics.services import get_system_analytics, list_users

class AnalyticsDashboardView(APIView):
    """
    GET /api/analytics
    GET /api/admin/analytics
    Returns full aggregate system analytics from actual MongoDB records.
    """
    permission_classes = [IsAuthenticatedMongoUser]

    def get(self, request):
        stats = get_system_analytics()
        return Response(
            {
                "success": True,
                "data": stats,
            },
            status=status.HTTP_200_OK,
        )


class AdminUserListView(APIView):
    """
    GET /api/admin/users
    Paginated list of users with search.
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request):
        page = max(1, int(request.query_params.get("page", 1)))
        limit = min(100, max(1, int(request.query_params.get("limit", 20))))
        search = request.query_params.get("search", "").strip()

        result = list_users(page=page, limit=limit, search=search)
        return Response(
            {
                "success": True,
                "data": result["users"],
                "total": result["total"],
                "page": page,
                "limit": limit,
            },
            status=status.HTTP_200_OK,
        )


class AdminUserDetailView(APIView):
    """
    GET /api/admin/users/:id
    PUT /api/admin/users/:id
    DELETE /api/admin/users/:id
    """
    permission_classes = [IsAdminMongoUser]

    def get(self, request, pk):
        obj_id = to_object_id(pk)
        if not obj_id:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        users_col = get_users_collection()
        factchecks_col = get_factchecks_collection()

        user = users_col.find_one({"_id": obj_id}, {"password": 0})
        if not user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        doc = serialize_doc(user)
        doc["factChecksCount"] = factchecks_col.count_documents({"user": obj_id})
        return Response({"success": True, "data": doc}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj_id = to_object_id(pk)
        if not obj_id:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        users_col = get_users_collection()
        update_fields = {}
        for field in ["role", "isPremium", "isVerified", "name"]:
            if field in request.data:
                update_fields[field] = request.data[field]

        user = users_col.find_one_and_update(
            {"_id": obj_id},
            {"$set": update_fields},
            return_document=True,
            projection={"password": 0},
        )
        if not user:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"success": True, "data": serialize_doc(user)}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        obj_id = to_object_id(pk)
        if not obj_id:
            return Response({"success": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        users_col = get_users_collection()
        factchecks_col = get_factchecks_collection()

        users_col.delete_one({"_id": obj_id})
        factchecks_col.delete_many({"user": obj_id})

        return Response(
            {"success": True, "message": "User and associated records deleted."},
            status=status.HTTP_200_OK,
        )
