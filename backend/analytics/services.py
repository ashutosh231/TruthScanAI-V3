"""
Analytics & Admin Services.
Calculates real metrics directly from MongoDB Atlas collections: users, factchecks, payments.
"""

from core.mongodb import (
    get_db,
    get_users_collection,
    get_factchecks_collection,
    get_payments_collection,
    serialize_doc,
    serialize_docs,
    to_object_id,
)

def get_system_analytics():
    """
    Computes live aggregate analytics from MongoDB collections.
    """
    users_col = get_users_collection()
    factchecks_col = get_factchecks_collection()
    payments_col = get_payments_collection()

    total_users = users_col.count_documents({})
    verified_users = users_col.count_documents({"isVerified": True})
    premium_users = users_col.count_documents({"isPremium": True})

    total_fact_checks = factchecks_col.count_documents({})
    verified_claims = factchecks_col.count_documents({"verdict": "TRUE"})
    false_claims = factchecks_col.count_documents({"verdict": "FALSE"})
    misleading_claims = factchecks_col.count_documents({"verdict": "MISLEADING"})
    uncertain_claims = factchecks_col.count_documents(
        {"verdict": {"$in": ["UNCERTAIN", "UNVERIFIED", "VERIFICATION_UNAVAILABLE"]}}
    )

    # Category / Type Breakdown aggregation
    type_pipeline = [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
    ]
    type_breakdown = {item["_id"] or "other": item["count"] for item in factchecks_col.aggregate(type_pipeline)}

    # Verdict Breakdown aggregation
    verdict_pipeline = [
        {"$group": {"_id": "$verdict", "count": {"$sum": 1}}},
    ]
    verdict_breakdown = {item["_id"] or "other": item["count"] for item in factchecks_col.aggregate(verdict_pipeline)}

    # Total revenue from paid transactions
    revenue_pipeline = [
        {"$match": {"status": "paid"}},
        {"$group": {"_id": None, "totalAmount": {"$sum": "$amount"}}},
    ]
    revenue_res = list(payments_col.aggregate(revenue_pipeline))
    total_revenue_paise = revenue_res[0]["totalAmount"] if revenue_res else 0
    total_revenue_rupees = total_revenue_paise / 100.0

    # Recent 10 activity records
    recent_cursor = factchecks_col.find({}).sort("createdAt", -1).limit(10)
    recent_activity = []
    for doc in recent_cursor:
        serialized = serialize_doc(doc)
        user_id = doc.get("user")
        if user_id:
            user = users_col.find_one({"_id": user_id}, {"name": 1, "email": 1})
            if user:
                serialized["userName"] = user.get("name")
                serialized["userEmail"] = user.get("email")
        recent_activity.append(serialized)

    return {
        "totalUsers": total_users,
        "verifiedUsers": verified_users,
        "premiumUsers": premium_users,
        "totalFactChecks": total_fact_checks,
        "verifiedClaims": verified_claims,
        "falseClaims": false_claims,
        "misleadingClaims": misleading_claims,
        "uncertainClaims": uncertain_claims,
        "typeBreakdown": type_breakdown,
        "verdictBreakdown": verdict_breakdown,
        "totalRevenue": total_revenue_rupees,
        "recentActivity": recent_activity,
    }

def list_users(page=1, limit=20, search=""):
    users_col = get_users_collection()
    factchecks_col = get_factchecks_collection()

    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    total = users_col.count_documents(query)
    skip = (page - 1) * limit

    cursor = users_col.find(query, {"password": 0}).sort("createdAt", -1).skip(skip).limit(limit)
    users = []
    for u in cursor:
        user_dict = serialize_doc(u)
        user_dict["factChecksCount"] = factchecks_col.count_documents({"user": u["_id"]})
        users.append(user_dict)

    return {
        "users": users,
        "total": total,
        "page": page,
        "limit": limit,
    }
