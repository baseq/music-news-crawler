"""
RSS feed fetcher.

Fetches all RSS entries for a source, then fetches the full article HTML
for each entry (to get clean body text via trafilatura).
"""
import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import httpx
import feedparser

from crawler.models import RawArticle

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "MusicDigestBot/1.0 (+https://github.com/baseq/music-news-crawler)"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

REQUEST_TIMEOUT  = 15   # seconds
ARTICLE_TIMEOUT  = 20
MAX_ARTICLES_PER_SOURCE = int(__import__("os").environ.get("MAX_ARTICLES_PER_SOURCE", "20"))


def parse_date(entry) -> Optional[datetime]:
    """Parse published date from an RSS entry."""
    for attr in ("published", "updated", "created"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return parsedate_to_datetime(val).astimezone(timezone.utc)
            except Exception:
                pass
    # Try struct_time fields
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def extract_image(entry) -> Optional[str]:
    """Try to find a thumbnail/image URL in an RSS entry."""
    # media:thumbnail
    media = getattr(entry, "media_thumbnail", None)
    if media and isinstance(media, list) and media:
        return media[0].get("url")
    # enclosures
    enclosures = getattr(entry, "enclosures", [])
    for enc in enclosures:
        if enc.get("type", "").startswith("image/"):
            return enc.get("href") or enc.get("url")
    return None


async def fetch_article_html(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """Fetch the full article page HTML."""
    try:
        r = await client.get(url, headers=HEADERS, timeout=ARTICLE_TIMEOUT, follow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        logger.debug(f"Failed to fetch article {url}: {e}")
    return None


async def fetch_feed(
    client: httpx.AsyncClient,
    source: dict,
) -> list[RawArticle]:
    """
    Fetch an RSS feed and return raw articles.
    `source` is a dict from Supabase: {id, name, language, rss_url, url, ...}
    """
    rss_url = source["rss_url"]
    articles: list[RawArticle] = []

    try:
        r = await client.get(rss_url, headers=HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            logger.warning(f"[{source['name']}] RSS returned HTTP {r.status_code}")
            return []
        feed = feedparser.parse(r.text)
    except Exception as e:
        logger.error(f"[{source['name']}] RSS fetch failed: {e}")
        return []

    entries = feed.entries[:MAX_ARTICLES_PER_SOURCE]

    # Fetch full article HTML concurrently (max 5 at once per source)
    sem = asyncio.Semaphore(5)

    async def _fetch_entry(entry) -> Optional[RawArticle]:
        url = getattr(entry, "link", None)
        if not url:
            return None
        async with sem:
            html = await fetch_article_html(client, url)

        # RSS description as fallback text
        summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
        if summary:
            from bs4 import BeautifulSoup
            summary = BeautifulSoup(summary, "lxml").get_text(" ", strip=True)

        return RawArticle(
            source_id=source["id"],
            source_name=source["name"],
            source_language=source["language"],
            url=url,
            title=getattr(entry, "title", "Untitled"),
            author=getattr(entry, "author", None),
            image_url=extract_image(entry),
            published_at=parse_date(entry),
            raw_html=html,
            raw_text=summary,
        )

    tasks = [_fetch_entry(e) for e in entries]
    results = await asyncio.gather(*tasks)
    articles = [a for a in results if a is not None]

    logger.info(f"[{source['name']}] RSS: {len(entries)} entries, {len(articles)} fetched")
    return articles
