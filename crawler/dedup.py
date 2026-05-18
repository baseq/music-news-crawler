"""URL deduplication — checks article URLs against Supabase before processing."""
import hashlib
from typing import Optional
from supabase import Client


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


class DedupCache:
    """
    Maintains a local set of known URL hashes during a single crawl run
    (to avoid repeated DB round-trips) and uses Supabase for persistence.
    """

    def __init__(self, supabase: Client):
        self._client = supabase
        self._seen: set[str] = set()

    def preload(self, since_hours: int = 72):
        """
        Pre-load recent URL hashes from DB into the local set,
        so we avoid individual lookups for recently crawled articles.
        """
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
        rows = (
            self._client.table("articles")
            .select("url_hash")
            .gte("crawled_at", cutoff)
            .execute()
            .data
        )
        self._seen = {r["url_hash"] for r in rows}
        return len(self._seen)

    def is_known(self, url: str) -> bool:
        h = url_hash(url)
        if h in self._seen:
            return True
        # Fallback DB check (for hashes not in recent window)
        rows = (
            self._client.table("articles")
            .select("id")
            .eq("url_hash", h)
            .limit(1)
            .execute()
            .data
        )
        if rows:
            self._seen.add(h)
            return True
        return False

    def mark_seen(self, url: str):
        self._seen.add(url_hash(url))
