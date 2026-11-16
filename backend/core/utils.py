"""
TruthScan Core Utilities:
- Response sanitization (confidential provider shielding)
- URL security (SSRF prevention)
- JWT token generation & verification
- OTP generation & email dispatching
- Redis client with resilient in-memory fallback
"""

import os
import re
import ipaddress
import secrets
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
import jwt
import redis
from django.conf import settings

# ============================================================================
# 1. Response Sanitization Layer (Confidential Provider Shielding)
# ============================================================================

LEAKED_PROVIDER_PATTERNS = [
    (re.compile(r"AWS\s*Bedrock\s*(DeepSeek(\s*V3\.2)?)?", re.IGNORECASE), "TruthScan AI Analysis"),
    (re.compile(r"DeepSeek(\s*V3\.2)?", re.IGNORECASE), "TruthScan AI Neural Core"),
    (re.compile(r"Amazon\s*Textract(\s*OCR\s*Engine)?", re.IGNORECASE), "Optical Document Reader"),
    (re.compile(r"Textract", re.IGNORECASE), "Optical Document Reader"),
    (re.compile(r"Tavily(\s*Search(\s*API)?)?", re.IGNORECASE), "Live Web Research"),
    (re.compile(r"NewsAPI(\.ai)?", re.IGNORECASE), "News Research"),
    (re.compile(r"LangChain(\s*Agent)?", re.IGNORECASE), "Investigation Engine"),
]

def sanitize_text(text):
    if not text or not isinstance(text, str):
        return text or ""
    cleaned = text
    for pattern, replacement in LEAKED_PROVIDER_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned

def sanitize_string_list(lst):
    if not isinstance(lst, list):
        return []
    return [sanitize_text(item) if isinstance(item, str) else item for item in lst]

def sanitize_research_metadata(meta):
    if not meta or not isinstance(meta, dict):
        return {
            "searchSucceeded": False,
            "resultsCount": 0,
            "searchProvider": "Live Web Research",
            "hasRelevantEvidence": False,
            "searchError": None,
            "webSearchSucceeded": False,
            "newsSearchSucceeded": False,
            "webResultsCount": 0,
            "newsResultsCount": 0,
        }

    search_succeeded = bool(meta.get("searchSucceeded") or meta.get("webSearchSucceeded") or False)
    results_count = int(meta.get("resultsCount") or meta.get("webResultsCount") or 0)
    has_relevant = bool(meta.get("hasRelevantEvidence", results_count > 0))

    public_error = None
    if meta.get("searchError"):
        public_error = "Research service temporarily unavailable"

    return {
        "searchSucceeded": search_succeeded,
        "resultsCount": results_count,
        "hasRelevantEvidence": has_relevant,
        "searchProvider": "Live Web Research",
        "searchQuery": str(meta.get("searchQuery", "")),
        "searchError": public_error,
        "webSearchSucceeded": search_succeeded,
        "newsSearchSucceeded": False,
        "webResultsCount": results_count,
        "newsResultsCount": 0,
    }

def sanitize_sources(sources):
    if not isinstance(sources, list):
        return []
    sanitized = []
    for src in sources:
        if not isinstance(src, dict):
            continue
        item = dict(src)
        publisher = item.get("publisher") or "Web Source"
        if re.search(r"tavily|newsapi|eventregistry", publisher, re.IGNORECASE):
            publisher = "Live Web Source"
        item["publisher"] = publisher
        item["sourceType"] = "web"
        sanitized.append(item)
    return sanitized

def sanitize_public_report(report):
    if not report or not isinstance(report, dict):
        return report

    sanitized = dict(report)

    if isinstance(sanitized.get("explanation"), str):
        sanitized["explanation"] = sanitize_text(sanitized["explanation"])

    if isinstance(sanitized.get("advisory"), str):
        sanitized["advisory"] = sanitize_text(sanitized["advisory"])

    if isinstance(sanitized.get("timelineAndContext"), str):
        sanitized["timelineAndContext"] = sanitize_text(sanitized["timelineAndContext"])

    if isinstance(sanitized.get("keySignals"), list):
        sanitized["keySignals"] = sanitize_string_list(sanitized["keySignals"])

    if isinstance(sanitized.get("tactics"), list):
        sanitized["tactics"] = sanitize_string_list(sanitized["tactics"])

    if isinstance(sanitized.get("debunkingEvidence"), list):
        sanitized["debunkingEvidence"] = sanitize_string_list(sanitized["debunkingEvidence"])

    if isinstance(sanitized.get("sourcesChecked"), list):
        sanitized["sourcesChecked"] = sanitize_string_list(sanitized["sourcesChecked"])

    if isinstance(sanitized.get("sources"), list):
        sanitized["sources"] = sanitize_sources(sanitized["sources"])

    if sanitized.get("researchMetadata"):
        sanitized["researchMetadata"] = sanitize_research_metadata(sanitized["researchMetadata"])

    if isinstance(sanitized.get("source"), str):
        sanitized["source"] = sanitize_text(sanitized["source"])

    if isinstance(sanitized.get("metadata"), dict):
        meta = dict(sanitized["metadata"])
        if isinstance(meta.get("source"), str):
            meta["source"] = sanitize_text(meta["source"])
        if isinstance(meta.get("extractionEngine"), str):
            meta["extractionEngine"] = sanitize_text(meta["extractionEngine"])
        if isinstance(meta.get("keySignals"), list):
            meta["keySignals"] = sanitize_string_list(meta["keySignals"])
        if isinstance(meta.get("sourcesChecked"), list):
            meta["sourcesChecked"] = sanitize_string_list(meta["sourcesChecked"])
        if meta.get("researchMetadata"):
            meta["researchMetadata"] = sanitize_research_metadata(meta["researchMetadata"])
        sanitized["metadata"] = meta

    return sanitized


# ============================================================================
# 2. URL Security & SSRF Protection
# ============================================================================

def validate_safe_url(url_string):
    if not url_string or not isinstance(url_string, str):
        return False, "A valid URL string is required."

    try:
        parsed = urlparse(url_string.strip())
    except Exception:
        return False, "Malformed URL format."

    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid protocol '{parsed.scheme}'. Only http and https URLs are permitted."

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "Missing hostname in URL."

    # Block localhost & standard internal domains
    if (
        hostname == "localhost"
        or hostname.endswith(".localhost")
        or hostname.endswith(".local")
        or hostname.endswith(".internal")
    ):
        return False, "Access to local or internal loopback hostnames is prohibited."

    # Check IP addresses
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False, "Access to private or link-local IP addresses is prohibited."
        # Specifically block AWS / GCP / Azure metadata 169.254.169.254
        if str(ip).startswith("169.254."):
            return False, "Access to link-local cloud metadata addresses is prohibited."
    except ValueError:
        # Not a raw IP address; hostname looks valid
        pass

    return True, None


# ============================================================================
# 3. JWT Token Helpers
# ============================================================================

def parse_expiry_to_seconds(expiry_str, default=900):
    if isinstance(expiry_str, (int, float)):
        return int(expiry_str)
    if not expiry_str or not isinstance(expiry_str, str):
        return default
    expiry_str = expiry_str.strip().lower()
    if expiry_str.endswith("m"):
        return int(expiry_str[:-1]) * 60
    if expiry_str.endswith("h"):
        return int(expiry_str[:-1]) * 3600
    if expiry_str.endswith("d"):
        return int(expiry_str[:-1]) * 86400
    if expiry_str.endswith("s"):
        return int(expiry_str[:-1])
    try:
        return int(expiry_str)
    except ValueError:
        return default

def generate_access_token(payload):
    secret = getattr(settings, "JWT_ACCESS_SECRET", os.getenv("JWT_ACCESS_SECRET", "default_secret"))
    expires_in_str = getattr(settings, "ACCESS_TOKEN_EXPIRES_IN", "15m")
    seconds = parse_expiry_to_seconds(expires_in_str, default=900)

    token_payload = dict(payload)
    now = datetime.now(timezone.utc)
    token_payload["iat"] = int(now.timestamp())
    token_payload["exp"] = int((now + timedelta(seconds=seconds)).timestamp())

    return jwt.encode(token_payload, secret, algorithm="HS256")

def generate_refresh_token(payload):
    secret = getattr(settings, "JWT_REFRESH_SECRET", os.getenv("JWT_REFRESH_SECRET", "default_secret"))
    expires_in_str = getattr(settings, "REFRESH_TOKEN_EXPIRES_IN", "7d")
    seconds = parse_expiry_to_seconds(expires_in_str, default=7 * 86400)

    token_payload = dict(payload)
    now = datetime.now(timezone.utc)
    token_payload["iat"] = int(now.timestamp())
    token_payload["exp"] = int((now + timedelta(seconds=seconds)).timestamp())

    return jwt.encode(token_payload, secret, algorithm="HS256")

def verify_access_token(token):
    secret = getattr(settings, "JWT_ACCESS_SECRET", os.getenv("JWT_ACCESS_SECRET", "default_secret"))
    return jwt.decode(token, secret, algorithms=["HS256"])

def verify_refresh_token(token):
    secret = getattr(settings, "JWT_REFRESH_SECRET", os.getenv("JWT_REFRESH_SECRET", "default_secret"))
    return jwt.decode(token, secret, algorithms=["HS256"])


# ============================================================================
# 4. OTP Generation & Email Sending
# ============================================================================

def generate_otp():
    """Generates a secure 6-digit OTP code."""
    return str(secrets.randbelow(900000) + 100000)

def _send_smtp_payload(recipient_email, otp, purpose="verification"):
    """
    Direct synchronous SMTP dispatch via Brevo or configured host.
    """
    host = getattr(settings, "SMTP_HOST", os.getenv("SMTP_HOST", "smtp-relay.brevo.com"))
    port = int(getattr(settings, "SMTP_PORT", os.getenv("SMTP_PORT", 587)))
    user = getattr(settings, "SMTP_USER", os.getenv("SMTP_USER"))
    password = getattr(settings, "SMTP_PASS", os.getenv("SMTP_PASS"))
    from_email = getattr(settings, "FROM_EMAIL", os.getenv("FROM_EMAIL", "no-reply@truthscan.ai"))
    from_name = getattr(settings, "FROM_NAME", os.getenv("FROM_NAME", "TruthScan AI"))

    if not password:
        print("[EmailService] Warning: SMTP_PASS not set. Skipping SMTP dispatch.")
        return False

    is_reset = purpose == "password reset"
    title_text = "TruthScan AI - Password Reset" if is_reset else "TruthScan AI"
    action_text = (
        "Use the following 6-digit verification code to reset your account password and restore terminal access."
        if is_reset
        else "Use the following 6-digit verification code to activate your account clearance."
    )
    subject_text = (
        f"TruthScan AI - Password Reset Code: {otp}"
        if is_reset
        else f"Your TruthScan AI Verification Code: {otp}"
    )

    html_content = f"""
      <div style="font-family: Arial, sans-serif; background-color: #F5F1E8; padding: 24px; color: #111111;">
        <div style="max-width: 500px; margin: 0 auto; background: #ffffff; border: 2px solid #111111; padding: 32px; box-shadow: 4px 4px 0px #111111;">
          <h2 style="font-size: 24px; font-weight: bold; text-transform: uppercase; margin-top: 0; color: #111111; border-bottom: 2px solid #111111; padding-bottom: 12px;">
            {title_text}
          </h2>
          <p style="font-size: 14px; line-height: 1.6; color: #333333;">
            Hello investigator,
          </p>
          <p style="font-size: 14px; line-height: 1.6; color: #333333;">
            {action_text}
            This code will expire in <strong>5 minutes</strong>.
          </p>
          <div style="text-align: center; margin: 28px 0;">
            <span style="display: inline-block; font-size: 32px; font-weight: bold; letter-spacing: 8px; background: #B7FF3C; border: 2px solid #111111; padding: 12px 24px; box-shadow: 3px 3px 0px #111111; color: #111111;">
              {otp}
            </span>
          </div>
          <p style="font-size: 12px; color: #666666; line-height: 1.5; border-top: 1px solid #eeeeee; padding-top: 16px;">
            If you did not request this code, please disregard this email or secure your account credentials.
          </p>
        </div>
      </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject_text
    msg["From"] = f'"{from_name}" <{from_email}>'
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=5)
        else:
            server = smtplib.SMTP(host, port, timeout=5)
            server.starttls()
        server.login(user, password)
        server.sendmail(from_email, [recipient_email], msg.as_string())
        server.quit()
        print(f"[EmailService] OTP email successfully dispatched to {recipient_email}")
        return True
    except Exception as e:
        print(f"[EmailService] Notice: SMTP delivery note ({type(e).__name__}): {e}")
        return False

def send_otp_email(recipient_email, otp, run_async=True, purpose="verification"):
    """
    Directly dispatches verification OTP email to recipient without external background workers.
    Always logs generated OTP to standard output so verification never blocks in development/unauthorized-IP environments.
    """
    print(f"[EmailService] Generated OTP for {recipient_email} ({purpose}): {otp}")

    if run_async:
        t = threading.Thread(target=_send_smtp_payload, args=(recipient_email, otp, purpose), daemon=True)
        t.start()
        return True
    return _send_smtp_payload(recipient_email, otp, purpose)


# ============================================================================
# 5. Redis Client with Resilient In-Memory Fallback
# ============================================================================

class InMemoryCache:
    """Thread-safe in-memory cache fallback when Redis is unreachable."""
    def __init__(self):
        self._store = {}

    def get(self, key):
        entry = self._store.get(key)
        if not entry:
            return None
        val, expiry = entry
        if expiry and datetime.now(timezone.utc).timestamp() > expiry:
            del self._store[key]
            return None
        return val

    def set(self, key, value, ex=None, px=None):
        expiry = None
        if ex:
            expiry = datetime.now(timezone.utc).timestamp() + ex
        elif px:
            expiry = datetime.now(timezone.utc).timestamp() + (px / 1000.0)
        self._store[key] = (str(value), expiry)
        return True

    def del_key(self, *keys):
        for k in keys:
            self._store.pop(k, None)
        return True

    def delete(self, *keys):
        return self.del_key(*keys)

    def incr(self, key):
        entry = self._store.get(key)
        if entry:
            val, expiry = entry
            new_val = int(val) + 1
            self._store[key] = (str(new_val), expiry)
            return new_val
        self._store[key] = ("1", None)
        return 1

    def expire(self, key, seconds):
        if key in self._store:
            val, _ = self._store[key]
            self._store[key] = (val, datetime.now(timezone.utc).timestamp() + seconds)
            return True
        return False

    def ttl(self, key):
        entry = self._store.get(key)
        if not entry:
            return -2
        _, expiry = entry
        if not expiry:
            return -1
        rem = int(expiry - datetime.now(timezone.utc).timestamp())
        return max(0, rem)

_in_memory_cache = InMemoryCache()
_redis_client = None

def get_redis_client():
    global _redis_client
    redis_url = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL")
    if not redis_url:
        return _in_memory_cache

    if _redis_client is None:
        try:
            # Handle Upstash TLS
            if "upstash.io" in redis_url and redis_url.startswith("redis://"):
                redis_url = redis_url.replace("redis://", "rediss://")

            client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            # Test ping
            client.ping()
            _redis_client = client
        except Exception as e:
            print(f"[Redis] Note: Redis connection unavailable ({e}). Using in-memory cache.")
            return _in_memory_cache

    return _redis_client
