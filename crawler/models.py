"""Shared data models for the crawler pipeline."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RawArticle:
    """An article as fetched from RSS or HTML — not yet cleaned."""
    source_id: str
    source_name: str
    source_language: str
    url: str
    title: str
    author: Optional[str] = None
    image_url: Optional[str] = None
    published_at: Optional[datetime] = None
    raw_html: Optional[str] = None
    raw_text: Optional[str] = None   # may be prefilled from RSS <description>


@dataclass
class CleanArticle:
    """An article after text extraction and cleaning — ready for AI pipeline."""
    source_id: str
    source_name: str
    source_language: str
    url: str
    url_hash: str
    title: str
    author: Optional[str]
    image_url: Optional[str]
    published_at: Optional[datetime]
    clean_text: str
    word_count: int
    is_paywalled: bool = False
