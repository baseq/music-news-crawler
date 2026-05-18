"""
HTML scraper fallback for sources without RSS.

Uses a per-source CSS selector config (selectors.json) to find article links
on the source's homepage, then fetches each article page individually.
"""
import json
import logging
import os
import asyncio
from typing import Optional
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from crawler.models import RawArticle

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "MusicDigestBot/1.0 (+https://github.com/baseq/music-news-crawler)",
}

MAX_ARTICLES_PER_SOURCE = int(os.environ.get("MAX_ARTICLES_PER_SOURCE", "20"))

# Load selector config (created alongside this file)
_SELECTOR_FILE = os.path.join(os.path.dirname(__file__), "selectors.json")
_SELECTORS: dict = {}
if os.path.exists(_SELECTOR_FILE):
    with open(_SELECTOR_FILE) as f:
        _SELECTORS = json.load(f)


def _default_selectors() -> dict:
    """Generic selectors that work on many news sites."""
    return {
        "article_links": "article a[href], .post a[href], h2 a[href], h3 a[href]",
        "title": "h1",
        "author": "[class*='author'], [rel='author']",
        "image": "article img, .post img, [class*='hero'] img",
    }


async def _fetch(client: httpx.AsyncClient, url: str) -> Optional[str]:
    try:
        r = await client.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        return r.text if r.status_code == 200 else None
    except Exception as e:
        logger.debug(f"Fetch failed {url}: {e}")
        return None


def _extract_links(html: str, base_url: str, selector: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    seen = set()
    for a in soup.select(selector):
        href = a.get("href", "")
        if not href or href.startswith("#"):
            continue
        full = urljoin(base_url, href)
        # Only same-domain links
        from urllib.parse import urlparse
        if urlparse(full).netloc == urlparse(base_url).netloc and full not in seen:
            seen.add(full)
            links.append(full)
    return links[:MAX_ARTICLES_PER_SOURCE]


def _extract_meta(html: str, selectors: dict) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title = None
    author = None
    image_url = None

    t = soup.select_one(selectors.get("title", "h1"))
    if t:
        title = t.get_text(strip=True)

    a = soup.select_one(selectors.get("author", "[class*='author']"))
    if a:
        author = a.get_text(strip=True)[:100]

    # Try OG image first
    og_img = soup.find("meta", property="og:image")
    if og_img:
        image_url = og_img.get("content")
    else:
        img = soup.select_one(selectors.get("image", "article img"))
        if img:
            image_url = img.get("src")

    # OG title fallback
    if not title:
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", "")

    return {"title": title or "Untitled", "author": author, "image_url": image_url}


async def fetch_html_source(
    client: httpx.AsyncClient,
    source: dict,
) -> list[RawArticle]:
    """
    Scrape a source's homepage to find article URLs, then fetch each.
    """
    src_url  = source["url"]
    src_name = source["name"]
    selectors = _SELECTORS.get(src_url, _SELECTORS.get(src_name, _default_selectors()))

    homepage_html = await _fetch(client, src_url)
    if not homepage_html:
        logger.warning(f"[{src_name}] Homepage unreachable")
        return []

    links = _extract_links(homepage_html, src_url, selectors["article_links"])
    logger.info(f"[{src_name}] Found {len(links)} candidate links")

    sem = asyncio.Semaphore(3)

    async def _process(url: str) -> Optional[RawArticle]:
        async with sem:
            html = await _fetch(client, url)
        if not html:
            return None
        meta = _extract_meta(html, selectors)
        return RawArticle(
            source_id=source["id"],
            source_name=src_name,
            source_language=source["language"],
            url=url,
            title=meta["title"],
            author=meta["author"],
            image_url=meta["image_url"],
            published_at=None,
            raw_html=html,
            raw_text=None,
        )

    tasks = [_process(link) for link in links]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]
