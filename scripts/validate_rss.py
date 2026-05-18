"""
RSS / site validation script.

Checks every source in the DB (or in seed/sources.py if DB is not yet seeded),
verifies that the RSS feed or homepage is reachable, and outputs a report.

Usage:
  python scripts/validate_rss.py              # validate all sources from DB
  python scripts/validate_rss.py --seed-only  # validate seed data without DB
  python scripts/validate_rss.py --update-db  # write results back to Supabase
  python scripts/validate_rss.py --lang ro    # filter by language
"""
import argparse
import asyncio
import sys
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
import feedparser
from dotenv import load_dotenv

load_dotenv()

# ── Result codes ──────────────────────────────────────────────────
OK        = "✓ OK"
NO_RSS    = "~ NO_RSS"       # homepage reachable but no RSS feed
RSS_DEAD  = "✗ RSS_DEAD"     # RSS URL returned error
DEAD      = "✗ DEAD"         # homepage unreachable
TIMEOUT   = "⏱ TIMEOUT"


@dataclass
class ValidationResult:
    name: str
    url: str
    rss_url: Optional[str]
    language: str
    status: str
    working_rss: Optional[str]   # discovered or confirmed RSS URL
    entries_found: int
    response_ms: int
    note: str


COMMON_RSS_PATHS = [
    "/feed", "/feed/", "/rss", "/rss/", "/rss.xml",
    "/feed.xml", "/atom.xml", "/index.xml",
    "/news/feed", "/news/rss",
]

HEADERS = {
    "User-Agent": (
        "MusicDigestBot/1.0 (+https://github.com/your-org/music-news-crawler; "
        "RSS aggregator - music news)"
    )
}

TIMEOUT_SECS = 10


async def try_rss(client: httpx.AsyncClient, url: str) -> tuple[bool, int]:
    """Return (is_valid_feed, entry_count)."""
    try:
        r = await client.get(url, headers=HEADERS, timeout=TIMEOUT_SECS, follow_redirects=True)
        if r.status_code != 200:
            return False, 0
        feed = feedparser.parse(r.text)
        if feed.bozo and not feed.entries:
            return False, 0
        return True, len(feed.entries)
    except Exception:
        return False, 0


async def validate_source(client: httpx.AsyncClient, source: dict) -> ValidationResult:
    name     = source["name"]
    url      = source["url"]
    rss_url  = source.get("rss_url")
    language = source["language"]

    t0 = time.monotonic()

    # 1. Try declared RSS URL
    if rss_url:
        valid, entries = await try_rss(client, rss_url)
        elapsed = int((time.monotonic() - t0) * 1000)
        if valid:
            return ValidationResult(name, url, rss_url, language, OK, rss_url, entries, elapsed, "")
        else:
            # RSS declared but not working — try common paths
            pass

    # 2. Discover RSS from common paths
    for path in COMMON_RSS_PATHS:
        candidate = url.rstrip("/") + path
        valid, entries = await try_rss(client, candidate)
        if valid:
            elapsed = int((time.monotonic() - t0) * 1000)
            note = f"discovered at {path}" if not rss_url else f"declared RSS failed; discovered at {path}"
            return ValidationResult(name, url, rss_url, language, OK, candidate, entries, elapsed, note)

    # 3. Check homepage reachability
    try:
        r = await client.get(url, headers=HEADERS, timeout=TIMEOUT_SECS, follow_redirects=True)
        elapsed = int((time.monotonic() - t0) * 1000)
        if r.status_code < 400:
            status = NO_RSS if not rss_url else RSS_DEAD
            return ValidationResult(name, url, rss_url, language, status, None, 0, elapsed,
                                    "needs HTML scraper" if status == NO_RSS else "RSS URL broken")
        else:
            return ValidationResult(name, url, rss_url, language, DEAD, None, 0, elapsed,
                                    f"HTTP {r.status_code}")
    except httpx.TimeoutException:
        elapsed = int((time.monotonic() - t0) * 1000)
        return ValidationResult(name, url, rss_url, language, TIMEOUT, None, 0, elapsed, "")
    except Exception as e:
        elapsed = int((time.monotonic() - t0) * 1000)
        return ValidationResult(name, url, rss_url, language, DEAD, None, 0, elapsed, str(e)[:80])


async def validate_all(sources: list[dict], concurrency: int = 10) -> list[ValidationResult]:
    results = []
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(s):
        async with sem:
            return await validate_source(client, s)

    async with httpx.AsyncClient() as client:
        tasks = [_bounded(s) for s in sources]
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            r = await coro
            results.append(r)
            icon = r.status.split()[0]
            print(f"  [{i+1:3}/{len(sources)}] {icon} [{r.language.upper()}] {r.name}"
                  + (f" — {r.note}" if r.note else "")
                  + (f" ({r.entries_found} entries, {r.response_ms}ms)" if r.status == OK else ""))
    return results


def print_report(results: list[ValidationResult]):
    ok       = [r for r in results if r.status == OK]
    no_rss   = [r for r in results if r.status == NO_RSS]
    rss_dead = [r for r in results if r.status == RSS_DEAD]
    dead     = [r for r in results if r.status in (DEAD, TIMEOUT)]

    print("\n" + "═" * 70)
    print(f"  VALIDATION REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print("═" * 70)
    print(f"  ✓ OK        : {len(ok):3}  (RSS working)")
    print(f"  ~ NO_RSS    : {len(no_rss):3}  (site up, no RSS — will use HTML scraper)")
    print(f"  ✗ RSS_DEAD  : {len(rss_dead):3}  (RSS URL broken — needs fixing)")
    print(f"  ✗ DEAD      : {len(dead):3}  (site unreachable — will be disabled)")
    print("═" * 70)

    if no_rss:
        print("\n  Sites needing HTML scraper config:")
        for r in no_rss:
            print(f"    [{r.language.upper()}] {r.name}  →  {r.url}")

    if rss_dead:
        print("\n  Broken RSS URLs (fix or find new ones):")
        for r in rss_dead:
            print(f"    [{r.language.upper()}] {r.name}  →  declared: {r.rss_url}")

    if dead:
        print("\n  Unreachable sites (will be set inactive):")
        for r in dead:
            print(f"    [{r.language.upper()}] {r.name}  →  {r.note}")

    # Write report file
    report_path = f"crawl_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        for r in sorted(results, key=lambda x: (x.language, x.status)):
            f.write(f"{r.status}\t{r.language}\t{r.name}\t{r.working_rss or ''}\t{r.note}\n")
    print(f"\n  Full report saved → {report_path}")


def update_db(results: list[ValidationResult]):
    from supabase import create_client
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    print("\nUpdating DB...")
    for r in results:
        update = {}
        if r.status == OK and r.working_rss:
            update["rss_url"]    = r.working_rss
            update["is_active"]  = True
        elif r.status in (DEAD, TIMEOUT):
            update["is_active"]  = False
            update["last_error"] = r.note
        if update:
            client.table("sources").update(update).eq("url", r.url).execute()
    print("Done.")


def load_sources_from_seed() -> list[dict]:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from seed.sources import SOURCES
    return SOURCES


def load_sources_from_db(lang: Optional[str] = None) -> list[dict]:
    from supabase import create_client
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    q = client.table("sources").select("name,url,rss_url,language")
    if lang:
        q = q.eq("language", lang)
    return q.execute().data


def main():
    parser = argparse.ArgumentParser(description="Validate music news sources")
    parser.add_argument("--seed-only", action="store_true",
                        help="Use seed data instead of DB")
    parser.add_argument("--update-db", action="store_true",
                        help="Write validated RSS URLs + active flags back to DB")
    parser.add_argument("--lang", help="Filter by language code (en/ro/fr/de/it/es)")
    parser.add_argument("--concurrency", type=int, default=10,
                        help="Max concurrent HTTP requests (default: 10)")
    args = parser.parse_args()

    if args.seed_only:
        sources = load_sources_from_seed()
    else:
        sources = load_sources_from_db(args.lang)

    if args.lang and args.seed_only:
        sources = [s for s in sources if s["language"] == args.lang]

    print(f"Validating {len(sources)} sources (concurrency={args.concurrency})...\n")
    results = asyncio.run(validate_all(sources, concurrency=args.concurrency))
    print_report(results)

    if args.update_db:
        update_db(results)


if __name__ == "__main__":
    main()
