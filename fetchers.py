"""Pulls articles from RSS feeds and NewsAPI.org, normalized to a common shape."""

import hashlib
import logging

import feedparser
import requests

logger = logging.getLogger(__name__)


def _make_id(link: str) -> str:
    return hashlib.sha256(link.encode("utf-8")).hexdigest()


def fetch_rss(feeds: list) -> list:
    """Returns a list of dicts: {id, title, link, source, summary, published}"""
    articles = []
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed["url"])
            for entry in parsed.entries:
                link = entry.get("link", "")
                if not link:
                    continue
                articles.append(
                    {
                        "id": _make_id(link),
                        "title": entry.get("title", "Untitled"),
                        "link": link,
                        "source": feed.get("name") or parsed.feed.get("title", "RSS"),
                        "summary": (entry.get("summary", "") or "")[:400],
                        "published": entry.get("published", ""),
                    }
                )
        except Exception as e:
            logger.warning("Failed to fetch RSS feed %s: %s", feed.get("url"), e)
    return articles


def fetch_newsapi(api_key: str, cfg: dict) -> list:
    """Fetches top headlines from NewsAPI.org. Returns [] if no key or on error."""
    if not api_key:
        logger.warning("NewsAPI enabled but NEWSAPI_KEY is not set; skipping.")
        return []

    params = {
        "apiKey": api_key,
        "pageSize": cfg.get("page_size", 10),
        "language": cfg.get("language", "en"),
    }
    if cfg.get("country"):
        params["country"] = cfg["country"]
    if cfg.get("category"):
        params["category"] = cfg["category"]
    if cfg.get("query"):
        params["q"] = cfg["query"]

    try:
        resp = requests.get("https://newsapi.org/v2/top-headlines", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Failed to fetch NewsAPI: %s", e)
        return []

    articles = []
    for a in data.get("articles", []):
        link = a.get("url", "")
        if not link:
            continue
        articles.append(
            {
                "id": _make_id(link),
                "title": a.get("title", "Untitled"),
                "link": link,
                "source": (a.get("source") or {}).get("name", "NewsAPI"),
                "summary": (a.get("description") or "")[:400],
                "published": a.get("publishedAt", ""),
            }
        )
    return articles
