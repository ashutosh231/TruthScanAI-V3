"""
Core Unit Tests:
- URL Security & SSRF validation
- Response Sanitization
- Token generation & validation
- MongoDB Atlas connection
"""

from django.test import TestCase
from core.utils import (
    validate_safe_url,
    sanitize_text,
    sanitize_string_list,
    sanitize_sources,
    sanitize_research_metadata,
    sanitize_public_report,
    generate_access_token,
    verify_access_token,
    generate_refresh_token,
    verify_refresh_token,
    generate_otp,
)
from core.mongodb import check_mongo_connection, get_db

class CoreSecurityAndSanitizationTests(TestCase):
    def test_ssrf_prohibits_localhost_and_private_ips(self):
        # Localhost
        valid, err = validate_safe_url("http://localhost:8080/admin")
        self.assertFalse(valid)
        self.assertIn("prohibited", err)

        # 127.0.0.1
        valid, err = validate_safe_url("http://127.0.0.1:5000/api")
        self.assertFalse(valid)

        # Cloud metadata IP (169.254.169.254)
        valid, err = validate_safe_url("http://169.254.169.254/latest/meta-data/")
        self.assertFalse(valid)

        # Private IPv4 (10.0.0.1, 192.168.1.1)
        valid, err = validate_safe_url("http://10.0.0.1/status")
        self.assertFalse(valid)
        valid, err = validate_safe_url("http://192.168.1.1/router")
        self.assertFalse(valid)

        # Prohibited protocols (ftp, file)
        valid, err = validate_safe_url("ftp://example.com/file.txt")
        self.assertFalse(valid)

        # Valid public URL
        valid, err = validate_safe_url("https://www.reuters.com/world/news-article")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_response_sanitization_shields_internal_providers(self):
        dirty_text = (
            "Verified via AWS Bedrock DeepSeek V3.2 model with Tavily Search API "
            "and Amazon Textract OCR Engine using LangChain Agent."
        )
        cleaned = sanitize_text(dirty_text)

        self.assertNotIn("AWS Bedrock", cleaned)
        self.assertNotIn("DeepSeek", cleaned)
        self.assertNotIn("Tavily", cleaned)
        self.assertNotIn("Textract", cleaned)
        self.assertNotIn("LangChain", cleaned)

        self.assertIn("TruthScan AI Analysis", cleaned)
        self.assertIn("Optical Document Reader", cleaned)

    def test_sanitize_sources_removes_provider_names_from_publishers(self):
        sources = [
            {"publisher": "Tavily Search", "url": "https://example.com/article1"},
            {"publisher": "Associated Press", "url": "https://apnews.com/article2"},
        ]
        sanitized = sanitize_sources(sources)
        self.assertEqual(sanitized[0]["publisher"], "Live Web Source")
        self.assertEqual(sanitized[1]["publisher"], "Associated Press")

    def test_jwt_generation_and_verification(self):
        payload = {"userId": "507f1f77bcf86cd799439011", "role": "investigator"}
        token = generate_access_token(payload)
        self.assertIsInstance(token, str)

        decoded = verify_access_token(token)
        self.assertEqual(decoded["userId"], payload["userId"])
        self.assertEqual(decoded["role"], payload["role"])

    def test_otp_generation(self):
        otp = generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_mongo_atlas_connection(self):
        healthy, msg = check_mongo_connection()
        self.assertTrue(healthy, f"MongoDB connection check failed: {msg}")
        db = get_db()
        self.assertIsNotNone(db)
        self.assertEqual(db.name, "TruthScanAI")
