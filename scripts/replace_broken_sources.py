"""
One-time migration: deactivate 6 broken EN sources and insert replacements.

Broken sources removed:
  - Kerrang!        (RSS 404)
  - Exclaim!        (RSS 404)
  - Metal Injection (403 on all article pages)
  - Under the Radar (403 on all article pages)
  - All About Jazz  (RSS returns 0 entries)
  - Paste Magazine  (RSS returns 1 fake "Hello World" entry)

Replacements added:
  - Loudwire
  - Brooklyn Vegan
  - Metal Sucks
  - American Songwriter
  - DownBeat
  - Uproxx Music

Usage:
  python scripts/replace_broken_sources.py
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BROKEN = [
    "Kerrang!",
    "Exclaim!",
    "Metal Injection",
    "Under the Radar",
    "All About Jazz",
    "Paste Magazine",
]

REPLACEMENTS = [
    {
        "name": "Loudwire",
        "url": "https://loudwire.com",
        "rss_url": "https://loudwire.com/feed/",
        "language": "en",
        "primary_genres": ["metal", "rock"],
        "is_active": True,
    },
    {
        "name": "Brooklyn Vegan",
        "url": "https://www.brooklynvegan.com",
        "rss_url": "https://www.brooklynvegan.com/feed/",
        "language": "en",
        "primary_genres": ["indie", "alternative", "punk"],
        "is_active": True,
    },
    {
        "name": "Metal Sucks",
        "url": "https://www.metalsucks.net",
        "rss_url": "https://www.metalsucks.net/feed/",
        "language": "en",
        "primary_genres": ["metal"],
        "is_active": True,
    },
    {
        "name": "American Songwriter",
        "url": "https://americansongwriter.com",
        "rss_url": "https://americansongwriter.com/feed/",
        "language": "en",
        "primary_genres": ["indie", "folk", "rock"],
        "is_active": True,
    },
    {
        "name": "DownBeat",
        "url": "https://downbeat.com",
        "rss_url": "https://downbeat.com/feed/",
        "language": "en",
        "primary_genres": ["jazz"],
        "is_active": True,
    },
    {
        "name": "Uproxx Music",
        "url": "https://uproxx.com/music",
        "rss_url": "https://uproxx.com/music/feed/",
        "language": "en",
        "primary_genres": ["indie", "hip-hop", "rock"],
        "is_active": True,
    },
]


def run():
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    # Step 1 — deactivate broken sources
    print("Deactivating broken sources...")
    for name in BROKEN:
        result = (
            client.table("sources")
            .update({"is_active": False})
            .eq("name", name)
            .execute()
        )
        count = len(result.data)
        if count:
            print(f"  ✓  Deactivated: {name}")
        else:
            print(f"  ~  Not found (already gone?): {name}")

    # Step 2 — insert replacements
    print("\nInserting replacement sources...")
    for source in REPLACEMENTS:
        try:
            client.table("sources").upsert(source, on_conflict="url").execute()
            print(f"  ✓  Added: {source['name']}")
        except Exception as e:
            print(f"  ✗  Failed: {source['name']} — {e}")

    print("\nDone.")


if __name__ == "__main__":
    run()
