"""
Tavily Search Research Service
Replaces @tavily/core and tavilySearchTool.js in Python.
Handles live web evidence gathering, commercial spam rejection, semantic relevance checks,
and bounded query refinement.
"""

import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from django.conf import settings

MAX_SNIPPET_LENGTH = 600
DEFAULT_MAX_RESULTS = 5
DEFAULT_TIMEOUT_SEC = 10

COMMERCIAL_SPAM_PATTERNS = [
    re.compile(r"\bcoffee\s*(maker|machine)?s?\b", re.IGNORECASE),
    re.compile(r"\bespresso\s*(machine)?s?\b", re.IGNORECASE),
    re.compile(r"\bair\s*fryers?\b", re.IGNORECASE),
    re.compile(r"\btoaster\s*ovens?\b", re.IGNORECASE),
    re.compile(r"\bkitchen\s*appliances?\b", re.IGNORECASE),
    re.compile(r"\bmattress\s*(review|deals)?s?\b", re.IGNORECASE),
    re.compile(r"\bcoupon\s*codes?\b", re.IGNORECASE),
    re.compile(r"\bpromo\s*codes?\b", re.IGNORECASE),
    re.compile(r"\bdiscount\s*codes?\b", re.IGNORECASE),
    re.compile(r"\baffiliate\b", re.IGNORECASE),
    re.compile(r"\bweight\s*loss\s*gummies\b", re.IGNORECASE),
    re.compile(r"\bketo\s*gummies\b", re.IGNORECASE),
    re.compile(r"\bdiet\s*pills\b", re.IGNORECASE),
    re.compile(r"\bcasino\s*(bonus|slots|games)?\b", re.IGNORECASE),
    re.compile(r"\bfree\s*spins\b", re.IGNORECASE),
    re.compile(r"\bslot\s*machines?\b", re.IGNORECASE),
    re.compile(r"\bbest\s+deals?\s+on\b", re.IGNORECASE),
]

STOP_WORDS = {
    "is", "are", "was", "were", "am", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "the", "a", "an", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "by", "from", "up", "about",
    "into", "over", "after", "today", "yesterday", "now", "tomorrow",
    "this", "that", "these", "those", "what", "which", "who", "whom",
    "whose", "why", "how", "where", "when", "there", "their", "they",
    "not", "can", "could", "will", "would", "shall", "should",
}

def extract_publisher(url):
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if host.startswith("www."):
            host = host[4:]
        if re.search(r"tavily|newsapi|eventregistry", host, re.IGNORECASE):
            return "Web Source"
        return host or "Web Source"
    except Exception:
        return "Web Source"

def extract_claim_entities(claim):
    if not claim or not isinstance(claim, str):
        return []
    words = re.sub(r"[^a-z0-9\s]", " ", claim.lower()).split()
    filtered = [w for w in words if len(w) > 2 and w not in STOP_WORDS]
    # Deduplicate preserving order
    seen = set()
    result = []
    for w in filtered:
        if w not in seen:
            seen.add(w)
            result.append(w)
    return result

def assess_evidence_relevance(claim, item):
    if not item or not isinstance(item, dict):
        return False, 0.0, "Empty or invalid result item"

    title = (item.get("title") or "").lower()
    snippet = (item.get("snippet") or item.get("content") or "").lower()
    combined = f"{title} {snippet}"

    claim_lower = (claim or "").lower()
    is_claim_shopping = bool(re.search(r"coffee|appliance|product|buy|coupon|deal|fryer|mattress", claim_lower, re.I))

    if not is_claim_shopping:
        for pattern in COMMERCIAL_SPAM_PATTERNS:
            if pattern.search(title) or pattern.search(snippet):
                return False, 0.0, "Unrelated commercial or affiliate product page rejected"

    claim_terms = extract_claim_entities(claim)
    if not claim_terms:
        return True, 1.0, "No specific entities extracted; default accepted"

    matched_count = sum(1 for term in claim_terms if term in combined)
    match_ratio = matched_count / len(claim_terms)

    is_death_claim = bool(re.search(r"died|death|passed\s+away|killed|hospital|alive|fatal", claim_lower, re.I))
    if is_death_claim:
        subject_terms = [t for t in claim_terms if t not in ["died", "death", "kill", "killed", "hospital", "alive", "today"]]
        if subject_terms:
            has_subject = any(t in combined for t in subject_terms)
            if not has_subject:
                return False, 0.0, "Missing primary subject entity for sensitive claim"

    if len(claim_terms) >= 2 and matched_count == 0:
        return False, 0.0, "Zero matching entities between claim and retrieved content"

    if matched_count > 0 and (match_ratio >= 0.25 or (claim_terms and claim_terms[0] in title)):
        return True, match_ratio, "Entity and semantic overlap verified"

    return False, match_ratio, f"Insufficient semantic relevance to claim (score: {match_ratio:.2f})"

def generate_search_query(claim):
    if not claim or not isinstance(claim, str):
        return ""

    cleaned = claim
    cleaned = re.sub(r"ignore\s+(all\s+)?(previous\s+)?instructions", "", cleaned, flags=re.I)
    cleaned = re.sub(r"system\s*:\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"assistant\s*:\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
    cleaned = re.sub(r'["“”\'‘’]', " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) > 180:
        sentences = re.split(r"(?<=[.?!])\s+", cleaned)
        if sentences and len(sentences[0]) >= 20:
            cleaned = " ".join(sentences[:2])

    if len(cleaned) > 250:
        cleaned = cleaned[:250].strip()

    return cleaned

def generate_refined_search_query(claim):
    terms = extract_claim_entities(claim)
    claim_lower = (claim or "").lower()

    if re.search(r"died|death|killed|hospital|passed\s+away|arrested|resigned", claim_lower, re.I):
        subjects = [t for t in terms if t not in ["died", "death", "killed", "hospital", "today"]]
        subject_str = " ".join(subjects)
        return {
            "query": f'"{subject_str}" news official statement updates',
            "topic": "news",
        }

    return {
        "query": f'{" ".join(terms[:5])} fact check news report',
        "topic": "news",
    }


class ResearchCollector:
    """Collects retrieved live evidence sources and tracks research metadata."""
    def __init__(self):
        self.searchSucceeded = False
        self.webSearchSucceeded = False
        self.resultsCount = 0
        self.webResultsCount = 0
        self.searchProvider = "Live Web Research"
        self.searchQuery = ""
        self.searchError = None
        self.hasRelevantEvidence = False
        self.sources = []
        self.rawResults = []
        self.seenUrls = set()

    def add_sources(self, new_sources):
        if not isinstance(new_sources, list):
            return
        for src in new_sources:
            if src and isinstance(src, dict) and src.get("url"):
                url = src["url"]
                if url not in self.seenUrls:
                    self.seenUrls.add(url)
                    item = dict(src)
                    item.setdefault("retrievedAt", datetime.now(timezone.utc).isoformat())
                    item.setdefault("sourceType", "web")
                    item.setdefault("relevance", "Retrieved live web evidence")
                    self.sources.append(item)
        self.resultsCount = len(self.sources)
        self.webResultsCount = len(self.sources)
        self.hasRelevantEvidence = len(self.sources) > 0

    def get_metadata(self):
        return {
            "searchSucceeded": self.searchSucceeded,
            "resultsCount": self.resultsCount,
            "searchProvider": "Live Web Research",
            "searchQuery": self.searchQuery,
            "searchError": "Research service temporarily unavailable" if self.searchError else None,
            "hasRelevantEvidence": self.hasRelevantEvidence,
            "webSearchSucceeded": self.searchSucceeded,
            "newsSearchSucceeded": False,
            "webResultsCount": self.resultsCount,
            "newsResultsCount": 0,
        }


def search_tavily(raw_query, options=None):
    """
    Executes live search via Tavily API with relevance filtering and 1 bounded retry.
    """
    options = options or {}
    query = generate_search_query(raw_query)

    api_key = (
        options.get("apiKey")
        or getattr(settings, "TAVILY_API_KEY", None)
        or os.getenv("TAVILY_API_KEY", "")
    ).split("#")[0].strip()

    if not api_key:
        return {
            "success": False,
            "count": 0,
            "rawCount": 0,
            "query": query,
            "results": [],
            "rawResults": [],
            "hasRelevantEvidence": False,
            "error": "TAVILY_API_KEY is not configured.",
            "errorCode": "MISSING_API_KEY",
        }

    if not query:
        return {
            "success": False,
            "count": 0,
            "rawCount": 0,
            "query": "",
            "results": [],
            "rawResults": [],
            "hasRelevantEvidence": False,
            "error": "Search query must be a non-empty string.",
            "errorCode": "EMPTY_QUERY",
        }

    max_results = options.get("maxResults", DEFAULT_MAX_RESULTS)
    timeout_sec = options.get("timeoutSec", DEFAULT_TIMEOUT_SEC)
    search_depth = "advanced" if options.get("searchDepth") == "advanced" else "basic"

    is_news_event = bool(re.search(r"died|death|killed|hospital|passed\s+away|arrested|resigned|today|breaking", raw_query, re.I))
    topic = options.get("topic") or ("news" if is_news_event else "general")

    def execute_api_search(target_query, target_topic):
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": target_query,
            "search_depth": search_depth,
            "topic": target_topic,
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        res = requests.post(url, json=payload, timeout=timeout_sec)
        if not res.ok:
            raise RuntimeError(f"Tavily API error {res.status_code}: {res.text}")
        data = res.json()
        return data.get("results") or []

    try:
        raw_items = execute_api_search(query, topic)

        def normalize(items):
            normalized = []
            for idx, item in enumerate(items):
                title = (item.get("title") or "Untitled Web Resource").strip()
                url = item.get("url", "")
                pub = extract_publisher(url)
                date = item.get("published_date") or None
                content = (item.get("content") or "")
                snippet = re.sub(r"\s+", " ", content).strip()[:MAX_SNIPPET_LENGTH]

                normalized.append({
                    "id": f"source-{idx + 1}",
                    "title": title,
                    "url": url,
                    "publisher": pub,
                    "publishedAt": date,
                    "retrievedAt": datetime.now(timezone.utc).isoformat(),
                    "sourceType": "web",
                    "snippet": snippet,
                    "score": item.get("score"),
                    "relevance": f'Live web evidence search for: "{query[:100]}"',
                })
            return normalized

        all_raw_items = normalize(raw_items)

        # Relevance filtering
        relevant_items = [
            it for it in all_raw_items
            if assess_evidence_relevance(raw_query, it)[0]
        ]

        # Bounded retry if 0 relevant
        if not relevant_items and all_raw_items:
            refined = generate_refined_search_query(raw_query)
            try:
                retry_raw = execute_api_search(refined["query"], refined["topic"])
                retry_norm = normalize(retry_raw)
                all_raw_items.extend(retry_norm)
                retry_rel = [
                    it for it in retry_norm
                    if assess_evidence_relevance(raw_query, it)[0]
                ]
                if retry_rel:
                    relevant_items = retry_rel
            except Exception as retry_err:
                print(f"[TavilySearch] Refined query retry warning: {retry_err}")

        return {
            "success": True,
            "count": len(relevant_items),
            "rawCount": len(all_raw_items),
            "query": query,
            "results": relevant_items,
            "rawResults": all_raw_items,
            "hasRelevantEvidence": len(relevant_items) > 0,
        }

    except Exception as err:
        err_msg = str(err)
        error_code = "PROVIDER_ERROR"
        if "timed out" in err_msg.lower():
            error_code = "SEARCH_TIMEOUT"
        elif "401" in err_msg or "unauthorized" in err_msg.lower():
            error_code = "INVALID_API_KEY"
        elif "429" in err_msg or "rate limit" in err_msg.lower():
            error_code = "RATE_LIMIT_EXCEEDED"

        print(f"[TavilySearch] Web search error ({error_code}): {err_msg}")
        return {
            "success": False,
            "count": 0,
            "rawCount": 0,
            "query": query,
            "results": [],
            "rawResults": [],
            "hasRelevantEvidence": False,
            "error": f"Live web research service unavailable: {err_msg}",
            "errorCode": error_code,
        }
