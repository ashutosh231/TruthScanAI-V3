"""
MongoDB Atlas integration utility using PyMongo.
Preserves existing database 'TruthScanAI', collections, and document structures.
"""

import os
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from django.conf import settings

_mongo_client = None
_mongo_db = None

def get_mongo_client():
    """
    Returns a singleton MongoClient connected to MongoDB Atlas.
    """
    global _mongo_client
    if _mongo_client is None:
        mongo_uri = getattr(settings, "MONGO_URI", None) or os.getenv("MONGO_URI")
        if not mongo_uri:
            raise RuntimeError("FATAL ERROR: MONGO_URI environment variable is missing.")

        _mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
            retryWrites=True,
            appname="TruthScanDjango",
        )
    return _mongo_client

def get_db():
    """
    Returns the TruthScanAI database instance.
    """
    global _mongo_db
    if _mongo_db is None:
        client = get_mongo_client()
        try:
            default_db = client.get_default_database()
            if default_db is not None:
                _mongo_db = default_db
            else:
                _mongo_db = client[getattr(settings, "MONGO_DB_NAME", "TruthScanAI")]
        except Exception:
            _mongo_db = client[getattr(settings, "MONGO_DB_NAME", "TruthScanAI")]
    return _mongo_db

def get_users_collection():
    return get_db()["users"]

def get_factchecks_collection():
    return get_db()["factchecks"]

def get_payments_collection():
    return get_db()["payments"]

def get_news_collection():
    return get_db()["news"]

def get_categories_collection():
    return get_db()["categories"]

def get_activity_logs_collection():
    return get_db()["activity_logs"]

def get_ai_metrics_collection():
    return get_db()["ai_metrics"]

def get_admin_settings_collection():
    return get_db()["admin_settings"]

def check_mongo_connection():
    """
    Pings MongoDB to verify connection health.
    Returns (True, message) or (False, error).
    """
    try:
        client = get_mongo_client()
        client.admin.command("ping")
        return True, "MongoDB Atlas connection healthy"
    except (ConnectionFailure, PyMongoError) as err:
        return False, str(err)

def to_object_id(val):
    """
    Converts string or ObjectId to ObjectId.
    Returns None if conversion fails.
    """
    if isinstance(val, ObjectId):
        return val
    if not val or not isinstance(val, (str, bytes)):
        return None
    try:
        return ObjectId(str(val))
    except Exception:
        return None

def serialize_doc(doc):
    """
    Recursively converts BSON ObjectId, datetime, and other non-JSON types
    into standard JSON-serializable Python representations.
    """
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for k, v in doc.items():
            if k == "_id" and isinstance(v, ObjectId):
                result["_id"] = str(v)
                result["id"] = str(v)
            elif isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, dict):
                result[k] = serialize_doc(v)
            elif isinstance(v, list):
                result[k] = serialize_doc(v)
            else:
                result[k] = v
        return result
    return doc

def serialize_docs(docs):
    return [serialize_doc(d) for d in docs]
