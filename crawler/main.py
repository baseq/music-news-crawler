"""
Crawler entry point.

Fetches all active sources, processes new articles, runs the AI pipeline,
and stores everything in Supabase.

Usage:
  python crawler/main.py                # full run
  python crawler/main.py --dry-run      # no DB writes
  python crawler/main.py --lang en      # one language only
  python crawler/main.py --source-id X  # one source only
"""
import asyncio
import logging
import os
import sys
import argparse
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from crawler.models import RawArticle, CleanArticle
from crawler.rss_fetcher import fetch_feed
from crawler.html_fetcher import fetch_html_source
from crawler.cleaner import clean_article
from crawler.dedup import DedupCache
from ai.pipeline import process_article

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("crawler.main")

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


def get_active_sources(client, lang: str = None, source_id: str = None) -> list[dict]:
    q = client.table("sources").select("*").eq("is_active", True)
    if lang:
        q = q.eq("language", lang)
    if source_id:
        q = q.eq("id", source_id)
    return q.execute().data


def save_article(client, article: CleanArticle, ai_result: dict):
    """Insert article + translations into Supabase."""
    row = {
        "source_id":      article.source_id,
        "url":            article.url,
        "url_hash":       article.url_hash,
        "title":          article.title,
        "author":         article.author,
        "image_url":      article.image_url,
        "published_at":   article.published_at.isoformat() if article.published_at else None,
        "raw_text":       article.clean_text[:50_000],   # cap to 50k chars
        "word_count":     article.word_count,
        "is_paywalled":   article.is_paywalled,
        "summary_en":     ai_result.get("summary"),
        "genres":         ai_result.get("genres", []),
        "content_type":   ai_result.get("content_type"),
        "sentiment":      ai_result.get("sentiment"),
        "is_processed":   bool(ai_result.get("summary")),
        "processing_error": ai_result.get("error"),
    }
    if DRY_RUN:
        logger.debug(f"[DRY RUN] Would save: {article.title[:60]}")
        return None

    result = client.table("articles").insert(row).execute()
    article_id = result.data[0]["id"]

    # Save translations (only rows where we actually have translated text)
    translations = ai_result.get("translations", {})
    for lang, translated in translations.items():
        summary_t = (translated or {}).get("summary")
        title_t   = (translated or {}).get("title")
        if summary_t or title_t:
            client.table("article_translations").insert({
                "article_id":         article_id,
                "language":           lang,
                "title_translated":   title_t,
                "summary_translated": summary_t,
            }).execute()

    return article_id


def update_source_after_crawl(client, source_id: str, error: str = None):
    if DRY_RUN:
        return
    update = {"last_crawled_at": datetime.now(timezone.utc).isoformat()}
    if error:
        client.table("sources").update({
            **update,
            "crawl_error_count": client.rpc(
                "increment", {"table": "sources", "column": "crawl_error_count", "row_id": source_id}
            ),
            "last_error": error,
        }).eq("id", source_id).execute()
    else:
        client.table("sources").update({
            **update,
            "crawl_error_count": 0,
            "last_error": None,
        }).eq("id", source_id).execute()


async def crawl_source(
    http_client: httpx.AsyncClient,
    supabase_client,
    dedup: DedupCache,
    source: dict,
    ai_counter: dict = None,
) -> dict:
    """Crawl one source. Returns stats dict."""
    stats = {"fetched": 0, "new": 0, "saved": 0, "errors": 0}
    source_name = source["name"]

    try:
        # Fetch raw articles
        if source.get("rss_url"):
            raw_articles = await fetch_feed(http_client, source)
        else:
            raw_articles = await fetch_html_source(http_client, source)

        stats["fetched"] = len(raw_articles)

        for raw in raw_articles:
            # Dedup check
            if dedup.is_known(raw.url):
                continue
            stats["new"] += 1

            # Clean text
            html = raw.raw_html or ""
            clean = clean_article(raw, html)
            if clean is None:
                logger.debug(f"  [{source_name}] Skipped (too short): {raw.title[:60]}")
                continue

            # Enforce --max-new cap: skip AI but still record the article as unprocessed
            if ai_counter and ai_counter["limit"] and ai_counter["count"] >= ai_counter["limit"]:
                logger.debug(f"  [{source_name}] AI cap reached — saving without processing: {raw.title[:60]}")
                try:
                    save_article(supabase_client, clean, {"summary": None, "genres": [], "content_type": None, "sentiment": None})
                    dedup.mark_seen(clean.url)
                    stats["saved"] += 1
                except Exception as e:
                    logger.error(f"  [{source_name}] DB save failed: {e}")
                    stats["errors"] += 1
                continue

            # AI pipeline (summarize + classify + translate)
            ai_result = await process_article(clean)
            if ai_counter:
                ai_counter["count"] += 1

            # Save to DB
            try:
                save_article(supabase_client, clean, ai_result)
                dedup.mark_seen(clean.url)
                stats["saved"] += 1
            except Exception as e:
                logger.error(f"  [{source_name}] DB save failed: {e}")
                stats["errors"] += 1

        update_source_after_crawl(supabase_client, source["id"])

    except Exception as e:
        logger.error(f"[{source_name}] Crawl failed: {e}")
        stats["errors"] += 1
        update_source_after_crawl(supabase_client, source["id"], error=str(e))

    return stats


async def main(lang: str = None, source_id: str = None, max_new: int = None):
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    sources = get_active_sources(supabase, lang=lang, source_id=source_id)
    logger.info(f"Starting crawl: {len(sources)} active sources | dry_run={DRY_RUN} | max_new={max_new or 'unlimited'}")

    dedup = DedupCache(supabase)
    preloaded = dedup.preload(since_hours=72)
    logger.info(f"Dedup cache preloaded: {preloaded} known URLs")

    totals = {"fetched": 0, "new": 0, "saved": 0, "errors": 0}

    # Shared counter to enforce --max-new cap across all sources
    ai_counter = {"count": 0, "limit": max_new}

    # Process sources with concurrency limit (be polite to servers)
    sem = asyncio.Semaphore(5)

    async with httpx.AsyncClient() as http_client:
        async def _bounded_crawl(source):
            async with sem:
                return await crawl_source(http_client, supabase, dedup, source, ai_counter)

        tasks = [_bounded_crawl(s) for s in sources]
        results = []
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Sources"):
            r = await coro
            results.append(r)

    for r in results:
        for k in totals:
            totals[k] += r.get(k, 0)

    logger.info(
        f"\n{'─'*50}\n"
        f"  Crawl complete\n"
        f"  Sources:  {len(sources)}\n"
        f"  Fetched:  {totals['fetched']} articles\n"
        f"  New:      {totals['new']} (after dedup)\n"
        f"  Saved:    {totals['saved']}\n"
        f"  Errors:   {totals['errors']}\n"
        f"{'─'*50}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Music news crawler")
    parser.add_argument("--lang",      help="Language filter (en/ro/fr/de/it/es)")
    parser.add_argument("--source-id", help="Crawl a single source by UUID")
    parser.add_argument("--dry-run",   action="store_true", help="No DB writes or emails")
    parser.add_argument("--max-new",   type=int, default=None, help="Max articles to AI-process per run")
    args = parser.parse_args()

    if args.dry_run:
        os.environ["DRY_RUN"] = "true"

    asyncio.run(main(lang=args.lang, source_id=args.source_id, max_new=args.max_new))
