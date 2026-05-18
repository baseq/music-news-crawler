"""
Backfill AI summaries for articles saved before the Groq fix.

Fetches all articles where is_processed=False and raw_text is non-empty,
runs them through the Groq summarizer, and updates the DB row.

Usage:
  python scripts/backfill_summaries.py           # process all unprocessed
  python scripts/backfill_summaries.py --limit 20  # process first 20 only
  python scripts/backfill_summaries.py --dry-run   # print titles, no writes
"""
import argparse
import logging
import os
import sys
import time

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai.summarizer import analyze_article

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("backfill")

# Groq free tier: ~5 calls/min (token-limited). 13 s gap keeps us clean.
GROQ_DELAY = 13


def run(limit: int = None, dry_run: bool = False):
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    # Fetch unprocessed articles that have text to work with
    q = (
        client.table("articles")
        .select("id, title, raw_text, word_count")
        .eq("is_processed", False)
        .neq("raw_text", "")
        .not_.is_("raw_text", "null")
        .order("crawled_at", desc=False)   # oldest first
    )
    if limit:
        q = q.limit(limit)

    rows = q.execute().data
    logger.info(f"Found {len(rows)} unprocessed articles with text")

    ok = skipped = errors = 0

    for i, row in enumerate(rows):
        title    = row.get("title") or ""
        raw_text = row.get("raw_text") or ""
        art_id   = row["id"]

        if not raw_text.strip():
            logger.debug(f"  [{i+1}/{len(rows)}] Skipping (no text): {title[:60]}")
            skipped += 1
            continue

        logger.info(f"  [{i+1}/{len(rows)}] {title[:70]}")

        if dry_run:
            ok += 1
            continue

        ai = analyze_article(title, raw_text)

        if ai.get("error") and not ai.get("summary"):
            logger.warning(f"    AI error: {ai['error']}")
            errors += 1
        else:
            update = {
                "summary_en":        ai.get("summary") or "",
                "genres":            ai.get("genres", []),
                "content_type":      ai.get("content_type", "news"),
                "sentiment":         ai.get("sentiment", "neutral"),
                "is_processed":      bool(ai.get("summary")),
                "processing_error":  ai.get("error"),
            }
            client.table("articles").update(update).eq("id", art_id).execute()
            ok += 1

        # Rate-limit guard — skip delay after the last article
        if i < len(rows) - 1:
            time.sleep(GROQ_DELAY)

    logger.info(
        f"\n{'─'*50}\n"
        f"  Backfill {'(dry run) ' if dry_run else ''}complete\n"
        f"  Processed : {ok}\n"
        f"  Skipped   : {skipped}\n"
        f"  Errors    : {errors}\n"
        f"{'─'*50}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill Groq summaries")
    parser.add_argument("--limit",   type=int, help="Max articles to process")
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    args = parser.parse_args()
    run(limit=args.limit, dry_run=args.dry_run)
