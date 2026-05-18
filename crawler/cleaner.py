"""
Text extraction and cleaning.

Uses trafilatura as the primary extractor (handles most sites well),
with BeautifulSoup as a lightweight fallback for simple pages.
"""
import re
import hashlib
from typing import Optional
from datetime import datetime

import trafilatura
from bs4 import BeautifulSoup

from crawler.models import RawArticle, CleanArticle
from crawler.dedup import url_hash

MIN_TEXT_LENGTH   = int(__import__("os").environ.get("MIN_ARTICLE_TEXT_LENGTH", "200"))
PAYWALL_THRESHOLD = 150   # chars — probably paywalled if less than this


def extract_text(html: str, url: str) -> Optional[str]:
    """Extract clean article text from HTML using trafilatura."""
    text = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
        favor_recall=True,
    )
    if text:
        return text.strip()

    # Fallback: BeautifulSoup paragraph extraction
    soup = BeautifulSoup(html, "lxml")
    paragraphs = soup.find_all("p")
    text = " ".join(p.get_text(" ", strip=True) for p in paragraphs if len(p.get_text()) > 40)
    return text.strip() if text else None


def detect_paywall(text: Optional[str]) -> bool:
    """Heuristic: if extracted text is very short, it's likely paywalled."""
    if not text:
        return True
    return len(text) < PAYWALL_THRESHOLD


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def clean_article(raw: RawArticle, html: str) -> Optional[CleanArticle]:
    """
    Given a RawArticle and its HTML, extract and clean text.
    Returns None if the article is too short or unextractable.
    """
    text = extract_text(html, raw.url)
    text = normalize_whitespace(text) if text else None
    paywalled = detect_paywall(text)

    # If paywalled but we have RSS description text, use that instead
    if paywalled and raw.raw_text and len(raw.raw_text) >= MIN_TEXT_LENGTH:
        text = normalize_whitespace(raw.raw_text)
        paywalled = False

    if not text or (len(text) < MIN_TEXT_LENGTH and not paywalled):
        return None  # skip — nothing useful to work with

    word_count = len(text.split())

    return CleanArticle(
        source_id=raw.source_id,
        source_name=raw.source_name,
        source_language=raw.source_language,
        url=raw.url,
        url_hash=url_hash(raw.url),
        title=raw.title.strip(),
        author=raw.author,
        image_url=raw.image_url,
        published_at=raw.published_at,
        clean_text=text,
        word_count=word_count,
        is_paywalled=paywalled,
    )
