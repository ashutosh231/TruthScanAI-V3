import os
import getpass
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.conf import settings
from core.mongodb import (
    get_users_collection,
    get_categories_collection,
    get_news_collection,
    get_admin_settings_collection,
    get_activity_logs_collection,
)
from accounts.services import hash_password
from news.services import FALLBACK_NEWS

DEFAULT_CATEGORIES = [
    {"name": "Politics", "slug": "politics", "description": "Government policy, diplomatic affairs, electoral integrity, and political rhetoric.", "color": "#EF4444", "icon": "landmark", "isActive": True},
    {"name": "Technology", "slug": "technology", "description": "Artificial intelligence, cybersecurity, consumer electronics, and software infrastructure.", "color": "#3B82F6", "icon": "cpu", "isActive": True},
    {"name": "Health", "slug": "health", "description": "Epidemiology, clinical trials, medical interventions, pharmaceuticals, and public health guidance.", "color": "#10B981", "icon": "activity", "isActive": True},
    {"name": "Finance", "slug": "finance", "description": "Banking systems, monetary policy, market manipulation, cryptocurrencies, and financial fraud.", "color": "#F59E0B", "icon": "dollar-sign", "isActive": True},
    {"name": "Science", "slug": "science", "description": "Astrophysics, climate science, biological research, space exploration, and empirical physics.", "color": "#8B5CF6", "icon": "atom", "isActive": True},
    {"name": "Entertainment", "slug": "entertainment", "description": "Media figures, cinema, viral celebrity rumors, digital influencers, and cultural commentary.", "color": "#EC4899", "icon": "film", "isActive": True},
    {"name": "Climate", "slug": "climate", "description": "Meteorological events, carbon emissions, sea ice anomalies, and environmental legislation.", "color": "#06B6D4", "icon": "globe", "isActive": True},
    {"name": "General", "slug": "general", "description": "Broad public interest claims, civic notices, and unclassified narrative verification.", "color": "#6B7280", "icon": "file-text", "isActive": True},
]

class Command(BaseCommand):
    help = "Initializes the TruthScan administrator account, initial categories, news wire records, and settings."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, default="id-admin@gmail.com", help="Admin email address")
        parser.add_argument("--password", type=str, default=None, help="Admin password (reads DJANGO_SUPERUSER_PASSWORD if omitted)")
        parser.add_argument("--name", type=str, default="TruthScan Administrator", help="Admin display name")

    def handle(self, *args, **options):
        email = options["email"].lower().strip()
        name = options["name"].strip()
        password = options["password"]

        if not password:
            password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not password:
            if hasattr(self.stdin, "isatty") and self.stdin.isatty():
                password = getpass.getpass("Enter password for administrator account: ")
            else:
                self.stderr.write("ERROR: DJANGO_SUPERUSER_PASSWORD environment variable or --password flag is required.")
                return

        users_col = get_users_collection()
        now = datetime.now(timezone.utc)
        hashed_password = hash_password(password)

        existing = users_col.find_one({"email": email})
        if existing:
            users_col.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "name": name,
                        "password": hashed_password,
                        "role": "admin",
                        "isVerified": True,
                        "isPremium": True,
                        "updatedAt": now,
                    }
                },
            )
            admin_id = existing["_id"]
            self.stdout.write(self.style.SUCCESS(f"Updated existing user '{email}' to administrator clearance with verified credentials."))
        else:
            res = users_col.insert_one(
                {
                    "name": name,
                    "email": email,
                    "password": hashed_password,
                    "role": "admin",
                    "isVerified": True,
                    "isPremium": True,
                    "avatar": "",
                    "createdAt": now,
                    "updatedAt": now,
                }
            )
            admin_id = res.inserted_id
            self.stdout.write(self.style.SUCCESS(f"Created new primary administrator '{email}' successfully."))

        # Seed categories if collection is empty
        cat_col = get_categories_collection()
        if cat_col.count_documents({}) == 0:
            for cat in DEFAULT_CATEGORIES:
                cat["createdAt"] = now
                cat["updatedAt"] = now
            cat_col.insert_many(DEFAULT_CATEGORIES)
            self.stdout.write(self.style.SUCCESS(f"Seeded {len(DEFAULT_CATEGORIES)} operational categories into MongoDB."))

        # Seed initial news articles if collection is empty
        news_col = get_news_collection()
        if news_col.count_documents({}) == 0:
            news_docs = []
            for item in FALLBACK_NEWS:
                news_docs.append({
                    "title": item["title"],
                    "description": item["description"],
                    "url": item["url"],
                    "image": item["image"],
                    "source": item["source"],
                    "category": item.get("category", "General"),
                    "isPublished": True,
                    "status": "published",
                    "publishedAt": datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00")),
                    "createdAt": now,
                    "updatedAt": now,
                })
            news_col.insert_many(news_docs)
            self.stdout.write(self.style.SUCCESS(f"Seeded {len(news_docs)} published news wire items into MongoDB."))

        # Seed default admin settings if empty
        settings_col = get_admin_settings_collection()
        if settings_col.count_documents({}) == 0:
            settings_col.insert_one({
                "theme": "navy",
                "dashboardDateDefault": "30d",
                "emailAlerts": True,
                "notifyOnNewUser": True,
                "notifyOnFailedAi": True,
                "autoRefreshInterval": 30,
                "updatedAt": now,
            })
            self.stdout.write(self.style.SUCCESS("Initialized default administrator system preferences."))

        # Audit activity log
        logs_col = get_activity_logs_collection()
        logs_col.insert_one({
            "action": "ADMIN_SETUP_COMMAND",
            "adminId": str(admin_id),
            "adminEmail": email,
            "adminName": name,
            "targetType": "auth",
            "targetId": str(admin_id),
            "details": {"event": "Administrator initialized or refreshed via setup_admin command."},
            "ipAddress": "127.0.0.1",
            "createdAt": now,
        })
        self.stdout.write(self.style.SUCCESS("Admin setup finished successfully."))
