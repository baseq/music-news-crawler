"""
Newsletter builder.

For each active channel:
  1. Query articles from the last 24h matching the channel's filters
  2. For each subscriber, pick the right translation of each summary
  3. Render the Jinja2 HTML template
  4. Pass to sender

Returns a list of email payloads ready for Resend.
"""
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, date
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from supabase import Client

logger = logging.getLogger(__name__)

APP_BASE_URL = os.environ.get("APP_BASE_URL", "https://music-digest.org")
MIN_ARTICLES_TO_SEND = 1   # skip digest only if no articles at all

LANGUAGE_LABELS = {
    "en": "English", "ro": "Română", "fr": "Français",
    "de": "Deutsch", "it": "Italiano", "es": "Español",
}

_jinja_env = Environment(
    loader=FileSystemLoader(os.path.dirname(__file__)),
    autoescape=True,
)


@dataclass
class EmailPayload:
    to_email: str
    subject: str
    html: str
    channel_id: str
    subscription_id: str
    unsubscribe_token: str


def _format_date(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return f"{dt.day} {dt.strftime('%b %Y')}"   # e.g. "18 May 2026"


def _get_channel_articles(
    supabase: Client,
    channel: dict,
    since_hours: int = 48,
) -> list[dict]:
    """Query articles matching a channel's genre/content filters."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()

    q = (
        supabase.table("articles")
        .select(
            "id, source_id, title, url, author, image_url, published_at, "
            "summary_en, genres, content_type, sentiment, "
            "sources(name, language)"
        )
        .eq("is_processed", True)
        .gte("crawled_at", cutoff)
        .order("published_at", desc=True)
        .limit(60)   # fetch more so we have enough after per-source grouping
    )

    articles = q.execute().data

    # Apply channel filters to get the "ideal" set
    filtered = articles
    genre_filters = channel.get("genre_filters")
    if genre_filters:
        filtered = [
            a for a in filtered
            if any(g in (a.get("genres") or []) for g in genre_filters)
        ]
    content_filters = channel.get("content_filters")
    if content_filters:
        filtered = [
            a for a in filtered
            if (a.get("content_type") or "") in content_filters
        ]

    # Guarantee at least one article per source that has new content.
    # Add the most recent article from any source not already represented.
    included_sources = {a.get("source_id") for a in filtered}
    for article in articles:
        sid = article.get("source_id")
        if sid and sid not in included_sources:
            filtered.append(article)
            included_sources.add(sid)

    # Re-sort by published_at desc after merge
    filtered.sort(key=lambda a: a.get("published_at") or "", reverse=True)

    return filtered[:20]   # cap at 20 per digest


def _get_translation(supabase: Client, article_id: str, language: str) -> Optional[str]:
    """Fetch translated summary for a given article + language."""
    if language == "en":
        return None  # caller uses summary_en directly

    rows = (
        supabase.table("article_translations")
        .select("summary_translated")
        .eq("article_id", article_id)
        .eq("language", language)
        .limit(1)
        .execute()
        .data
    )
    if rows:
        return rows[0]["summary_translated"]
    return None


def _get_subscribers(supabase: Client, channel_id: str) -> list[dict]:
    return (
        supabase.table("subscriptions")
        .select("id, email, preferred_language, unsubscribe_token")
        .eq("channel_id", channel_id)
        .eq("is_active", True)
        .execute()
        .data
    )


def _render_email(
    channel: dict,
    articles: list[dict],
    subscriber: dict,
    translations_cache: dict,   # {article_id: {lang: summary}}
) -> str:
    lang        = subscriber["preferred_language"]
    unsub_token = subscriber["unsubscribe_token"]
    today       = date.today()

    article_contexts = []
    for a in articles:
        art_id = a["id"]

        # Determine the article's original language from its source
        src = a.get("sources")
        if isinstance(src, list):
            src = src[0] if src else {}
        src = src or {}
        article_lang = src.get("language", "en")

        # Priority: original-language translation → subscriber preferred language → English
        art_translations = translations_cache.get(art_id, {})
        if article_lang != "en" and article_lang in art_translations:
            summary = art_translations[article_lang]
        elif lang != "en" and lang in art_translations:
            summary = art_translations[lang]
        else:
            summary = a.get("summary_en") or ""

        pub_dt = None
        if a.get("published_at"):
            try:
                pub_dt = datetime.fromisoformat(a["published_at"].replace("Z", "+00:00"))
            except Exception:
                pass

        source_name = src.get("name", "")

        article_contexts.append({
            "url":               a["url"],
            "title":             a["title"],
            "source_name":       source_name,
            "genres":            a.get("genres") or [],
            "content_type":      (a.get("content_type") or "news").replace("-", " "),
            "summary":           summary,
            "published_at":      pub_dt,
            "published_at_formatted": _format_date(pub_dt),
        })

    template = _jinja_env.get_template("template.html")
    return template.render(
        channel_name=channel["name"],
        channel_slug=channel["slug"],
        channel_icon=channel.get("icon", "🎵"),
        article_count=len(articles),
        issue_date=today.isoformat(),
        issue_date_formatted=f"{today.day} {today.strftime('%B %Y')}",
        articles=article_contexts,
        preferred_language=lang,
        preferred_language_label=LANGUAGE_LABELS.get(lang, lang),
        unsubscribe_url=f"{APP_BASE_URL}/unsubscribe?token={unsub_token}",
        app_base_url=APP_BASE_URL,
    )


def build_emails(supabase: Client) -> list[EmailPayload]:
    """
    Main entry point. Returns all email payloads for today's digest.
    """
    channels = (
        supabase.table("channels")
        .select("*")
        .eq("is_active", True)
        .execute()
        .data
    )

    today = date.today()
    all_payloads: list[EmailPayload] = []

    for channel in channels:
        articles = _get_channel_articles(supabase, channel)

        if len(articles) < MIN_ARTICLES_TO_SEND:
            logger.info(
                f"[{channel['name']}] Only {len(articles)} articles — skipping digest"
            )
            continue

        # Pre-fetch translations for all articles in all languages
        article_ids = [a["id"] for a in articles]
        trans_rows = (
            supabase.table("article_translations")
            .select("article_id, language, summary_translated")
            .in_("article_id", article_ids)
            .execute()
            .data
        )
        translations_cache: dict[str, dict[str, str]] = {}
        for row in trans_rows:
            aid = row["article_id"]
            if aid not in translations_cache:
                translations_cache[aid] = {}
            translations_cache[aid][row["language"]] = row["summary_translated"]

        subscribers = _get_subscribers(supabase, channel["id"])
        if not subscribers:
            logger.info(f"[{channel['name']}] No subscribers — skipping")
            continue

        logger.info(
            f"[{channel['name']}] {len(articles)} articles → {len(subscribers)} subscribers"
        )

        for sub in subscribers:
            try:
                html = _render_email(channel, articles, sub, translations_cache)
                subject = (
                    f"{channel.get('icon','')} {channel['name']} — "
                    f"{today.day} {today.strftime('%b %Y')}"
                )
                all_payloads.append(EmailPayload(
                    to_email=sub["email"],
                    subject=subject,
                    html=html,
                    channel_id=channel["id"],
                    subscription_id=sub["id"],
                    unsubscribe_token=sub["unsubscribe_token"],
                ))
            except Exception as e:
                logger.error(f"  Render failed for {sub['email']}: {e}")

        # Record the issue in DB (for audit trail)
        try:
            supabase.table("newsletter_issues").upsert({
                "channel_id":   channel["id"],
                "issue_date":   today.isoformat(),
                "article_ids":  article_ids,
                "article_count": len(articles),
            }, on_conflict="channel_id,issue_date").execute()
        except Exception as e:
            logger.warning(f"  Could not record newsletter issue: {e}")

    return all_payloads
