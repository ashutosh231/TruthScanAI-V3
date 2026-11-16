"""
News Wire Service with Live Web Search, Provider Integration (NewsAPI & Tavily), and Redis Caching.
Supports live headline fetching, category filtering, keyword web search, and forced cache refresh.
"""

import os
import json
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus, urlparse
import requests
from django.conf import settings
from core.utils import get_redis_client

NEWS_CACHE_TTL = 300  # 5 minutes

CATEGORY_IMAGES = {
    "technology": "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=800&auto=format&fit=crop",
    "science": "https://images.unsplash.com/photo-1507668077129-56e32842fceb?q=80&w=800&auto=format&fit=crop",
    "politics": "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?q=80&w=800&auto=format&fit=crop",
    "health": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?q=80&w=800&auto=format&fit=crop",
    "climate": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=800&auto=format&fit=crop",
    "general": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop",
}

FALLBACK_NEWS = [
    {
        "id": "fb-news-1",
        "title": "NASA James Webb Space Telescope Detects Atmospheric Water Vapor on Habitable-Zone Exoplanet",
        "description": "Astronomers confirm atmospheric signatures consistent with water vapor and possible methane on a sub-Neptune exoplanet 120 light years away.",
        "url": "https://www.nasa.gov",
        "image": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop",
        "source": "NASA Science Wire",
        "publishedAt": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
        "category": "Science",
    },
    {
        "id": "fb-news-2",
        "title": "Viral Audio Deepfake Fabricates Emergency Bank Shutdown Leading to Global Financial Panic",
        "description": "Financial authorities investigate synthetic voice cloning impersonating central bankers that triggered automated bank runs.",
        "url": "https://www.reuters.com",
        "image": "https://images.unsplash.com/photo-1563986768609-322da13575f3?q=80&w=800&auto=format&fit=crop",
        "source": "Global Financial Monitor",
        "publishedAt": (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat(),
        "category": "Technology",
    },
    {
        "id": "fb-news-3",
        "title": "International Regulatory Body Proposes Cryptographic Provenance Standards for Synthetic Media",
        "description": "Draft standards aim to mandate machine-readable cryptographic signatures on commercial AI foundation models.",
        "url": "https://www.apnews.com",
        "image": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=800&auto=format&fit=crop",
        "source": "Policy Review",
        "publishedAt": (datetime.now(timezone.utc) - timedelta(minutes=120)).isoformat(),
        "category": "Politics",
    },
    {
        "id": "fb-news-4",
        "title": "Phase 3 Trials Confirm 91% Protective Efficacy in Next-Gen Universal mRNA Vaccine Candidate",
        "description": "Peer-reviewed multicenter clinical trials confirm broad neutralization against mutating respiratory pathogens.",
        "url": "https://www.who.int",
        "image": "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?q=80&w=800&auto=format&fit=crop",
        "source": "Health Dispatch",
        "publishedAt": (datetime.now(timezone.utc) - timedelta(minutes=180)).isoformat(),
        "category": "Health",
    },
    {
        "id": "fb-news-5",
        "title": "Unverified Claims Circulate Alleging Arctic Sea Ice Extent Reached Record Seasonal Highs",
        "description": "Satellite telemetry from NSIDC clarifies that polar sea ice extent remains near historic record lows despite viral claims.",
        "url": "https://nsidc.org",
        "image": "https://images.unsplash.com/photo-1483664852095-d6cc6870702d?q=80&w=800&auto=format&fit=crop",
        "source": "Climate Watch",
        "publishedAt": (datetime.now(timezone.utc) - timedelta(minutes=240)).isoformat(),
        "category": "Climate",
    },
    {
        "id": "fb-news-6",
        "title": "Quantum Benchmark Paper Withdrawn Following Cryptographic Peer Review",
        "description": "Researchers retract claims of factoring RSA-4096 after fault-tolerant simulation was shown to contain logical shortcuts.",
        "url": "https://www.nature.com",
        "image": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=800&auto=format&fit=crop",
        "source": "Cyber Intel",
        "publishedAt": (datetime.now(timezone.utc) - timedelta(minutes=360)).isoformat(),
        "category": "Technology",
    },
]


def _get_api_keys():
    news_key = (
        getattr(settings, "NEWSAPI_AI_KEY", None)
        or os.getenv("NEWSAPI_AI_KEY")
        or os.getenv("newsapi")
        or ""
    ).split("#")[0].strip()

    tavily_key = (
        getattr(settings, "TAVILY_API_KEY", None)
        or os.getenv("TAVILY_API_KEY")
        or ""
    ).split("#")[0].strip()

    return news_key, tavily_key


def _get_category_image(cat_name):
    cat_lower = (cat_name or "general").lower()
    return CATEGORY_IMAGES.get(cat_lower, CATEGORY_IMAGES["general"])


def _extract_source_name(url, fallback="Global Wire"):
    if not url:
        return fallback
    try:
        netloc = urlparse(url).netloc.lower()
        clean = re.sub(r"^www\.", "", netloc)
        parts = clean.split(".")
        if len(parts) >= 2:
            domain_name = parts[0]
            # Map well-known news domains to clean names
            known = {
                "reuters": "Reuters",
                "apnews": "Associated Press",
                "bbc": "BBC News",
                "cnn": "CNN",
                "nytimes": "New York Times",
                "theguardian": "The Guardian",
                "bloomberg": "Bloomberg",
                "aljazeera": "Al Jazeera",
                "nature": "Nature",
                "nasa": "NASA",
                "techcrunch": "TechCrunch",
                "theverge": "The Verge",
                "wired": "Wired",
                "forbes": "Forbes",
                "wsj": "Wall Street Journal",
                "cnbc": "CNBC",
            }
            return known.get(domain_name, domain_name.capitalize())
        return clean or fallback
    except Exception:
        return fallback


def fetch_from_tavily(query_text, max_results=12, category="General"):
    """
    Search the live web for news using Tavily News topic.
    """
    _, tavily_key = _get_api_keys()
    if not tavily_key:
        return []

    try:
        payload = {
            "api_key": tavily_key,
            "query": f"{query_text}",
            "topic": "news",
            "include_images": True,
            "max_results": max_results,
        }
        res = requests.post("https://api.tavily.com/search", json=payload, timeout=12)
        if not res.ok:
            return []

        data = res.json()
        results = data.get("results") or []
        images = data.get("images") or []

        normalized = []
        for idx, item in enumerate(results):
            title = (item.get("title") or "").strip()
            item_url = item.get("url") or ""
            if not title or not item_url:
                continue

            desc = (item.get("content") or "").strip() or "Live dispatch retrieved from global news coverage."
            # Prefer article-specific image if present, otherwise Tavily images array, else fallback
            img = None
            if idx < len(images) and images[idx]:
                img = images[idx]
            if not img:
                img = _get_category_image(category)

            source = _extract_source_name(item_url, "Web News Wire")
            published_at = item.get("published_date") or datetime.now(timezone.utc).isoformat()

            normalized.append({
                "id": item_url or f"tavily-{idx}-{int(datetime.now().timestamp())}",
                "title": title,
                "description": desc,
                "url": item_url,
                "image": img,
                "source": source,
                "publishedAt": published_at,
                "category": category if category != "all" else "General",
            })

        return normalized
    except Exception as e:
        print(f"[NewsService] Tavily news search error: {e}")
        return []


def search_news_from_web(query, category="all"):
    """
    Search for any news topic on the live web using NewsAPI and Tavily.
    Combines results and deduplicates by URL and title.
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return fetch_and_normalize_from_provider(category)

    news_key, tavily_key = _get_api_keys()
    articles = []
    seen_urls = set()
    seen_titles = set()

    # 1. Search NewsAPI `everything` endpoint
    if news_key:
        try:
            encoded = quote_plus(cleaned_query)
            url = f"https://newsapi.org/v2/everything?q={encoded}&language=en&sortBy=publishedAt&pageSize=15&apiKey={news_key}"
            res = requests.get(
                url,
                headers={"Accept": "application/json", "User-Agent": "TruthScanAI/1.0"},
                timeout=10,
            )
            if res.ok:
                data = res.json()
                for idx, item in enumerate(data.get("articles") or []):
                    title = (item.get("title") or "").strip()
                    item_url = (item.get("url") or "").strip()
                    if not title or "[Removed]" in title or not item_url:
                        continue

                    norm_title = re.sub(r"\W+", "", title.lower())
                    if item_url in seen_urls or norm_title in seen_titles:
                        continue

                    desc = item.get("description") or (item.get("content") or "").split("[+")[0] or "News dispatch reported via global wire service."
                    image = item.get("urlToImage") or _get_category_image(category)
                    source_name = item.get("source", {}).get("name") if isinstance(item.get("source"), dict) else _extract_source_name(item_url)

                    seen_urls.add(item_url)
                    seen_titles.add(norm_title)
                    articles.append({
                        "id": item_url or f"news-{idx}-{int(datetime.now().timestamp())}",
                        "title": title,
                        "description": desc,
                        "url": item_url,
                        "image": image,
                        "source": source_name,
                        "publishedAt": item.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
                        "category": category if category != "all" else "General",
                    })
        except Exception as e:
            print(f"[NewsService] NewsAPI search error: {e}")

    # 2. Complement or fallback with Tavily live web news search
    if len(articles) < 10 and tavily_key:
        tavily_results = fetch_from_tavily(f"{cleaned_query} news", max_results=12, category=category)
        for item in tavily_results:
            item_url = item.get("url", "")
            norm_title = re.sub(r"\W+", "", item.get("title", "").lower())
            if item_url in seen_urls or norm_title in seen_titles:
                continue

            seen_urls.add(item_url)
            seen_titles.add(norm_title)
            articles.append(item)

    # 3. If zero articles found from both providers, fallback to filtered fallback
    if not articles:
        q_lower = cleaned_query.lower()
        matched = [
            fb for fb in FALLBACK_NEWS
            if q_lower in fb["title"].lower() or q_lower in fb["description"].lower()
        ]
        return matched if matched else FALLBACK_NEWS

    return articles


def fetch_and_normalize_from_provider(category="all"):
    """
    Fetch top breaking headlines for the wire from NewsAPI or Tavily.
    """
    news_key, tavily_key = _get_api_keys()

    if news_key:
        try:
            cat_lower = (category or "").lower()
            valid_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
            target_cat = cat_lower if cat_lower in valid_categories else "general"

            if cat_lower and cat_lower != "all" and cat_lower != "climate":
                url = f"https://newsapi.org/v2/top-headlines?language=en&category={target_cat}&pageSize=15&apiKey={news_key}"
            elif cat_lower == "climate":
                url = f"https://newsapi.org/v2/everything?q=climate+environment&language=en&sortBy=publishedAt&pageSize=15&apiKey={news_key}"
            else:
                url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=15&apiKey={news_key}"

            res = requests.get(
                url,
                headers={"Accept": "application/json", "User-Agent": "TruthScanAI/1.0"},
                timeout=10,
            )
            if res.ok:
                data = res.json()
                items = data.get("articles") or []
                normalized = []
                for idx, item in enumerate(items):
                    title = (item.get("title") or "").strip()
                    item_url = (item.get("url") or "").strip()
                    if not title or "[Removed]" in title:
                        continue

                    desc = item.get("description") or (item.get("content") or "").split("[+")[0] or "Breaking dispatch verified across global news networks."
                    image = item.get("urlToImage") or _get_category_image(category)
                    source_name = item.get("source", {}).get("name") if isinstance(item.get("source"), dict) else _extract_source_name(item_url)

                    normalized.append({
                        "id": item_url or f"news-{idx}-{int(datetime.now().timestamp())}",
                        "title": title,
                        "description": desc,
                        "url": item_url or "https://news.google.com",
                        "image": image,
                        "source": source_name,
                        "publishedAt": item.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
                        "category": category.capitalize() if category != "all" else "General",
                    })

                if normalized:
                    return normalized
        except Exception as e:
            print(f"[NewsService] NewsAPI headlines error: {e}")

    # Fallback to Tavily live web headlines
    if tavily_key:
        query_text = f"latest {category} news" if category and category != "all" else "breaking world news headlines today"
        tavily_items = fetch_from_tavily(query_text, max_results=12, category=category)
        if tavily_items:
            return tavily_items

    # Ultimate fallback
    if category and category != "all":
        cat_lower = category.lower()
        matched = [fb for fb in FALLBACK_NEWS if fb.get("category", "").lower() == cat_lower]
        if matched:
            return matched

    return FALLBACK_NEWS


def get_latest_news(category="all", force_refresh=False, query=None):
    """
    Get latest news articles. If query is provided, searches the web via NewsAPI & Tavily.
    Supports force_refresh to bypass and update Redis cache.
    """
    cleaned_query = (query or "").strip()
    redis_client = get_redis_client()

    if cleaned_query:
        cache_key = f"news:search:{cleaned_query.lower()}:{(category or 'all').lower()}"
    else:
        cache_key = f"news:{(category or 'all').lower()}"

    # Check cache if not forcing refresh
    if not force_refresh:
        try:
            cached_val = redis_client.get(cache_key)
            if cached_val:
                return {
                    "cached": True,
                    "articles": json.loads(cached_val),
                }
        except Exception as err:
            print(f"[NewsService] Redis cache read warning: {err}")

    # Fetch fresh articles
    if cleaned_query:
        articles = search_news_from_web(cleaned_query, category)
    else:
        articles = fetch_and_normalize_from_provider(category)

    # Cache fresh articles in Redis
    try:
        redis_client.set(cache_key, json.dumps(articles), ex=NEWS_CACHE_TTL)
    except Exception as err:
        print(f"[NewsService] Redis cache write warning: {err}")

    return {
        "cached": False,
        "articles": articles,
    }


def refresh_news_cache(category="all", query=None):
    """
    Force-refreshes the news cache from live web providers.
    """
    return get_latest_news(category=category, force_refresh=True, query=query)
