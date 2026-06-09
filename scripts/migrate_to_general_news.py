"""
One-time migration: switch from music news to general news.

  1. Deactivates all existing music sources and channels
  2. Seeds new general news sources and channels
  3. Leaves existing articles untouched (they'll age out naturally)

Run once:
  python scripts/migrate_to_general_news.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

from seed.sources import SOURCES, seed_sources
from seed.channels import CHANNELS, seed_channels


def migrate():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    client = create_client(url, key)

    # ── 1. Deactivate all existing sources ──────────────────────────
    print("Deactivating old sources...")
    result = client.table("sources").update({"is_active": False}).neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print(f"  Deactivated {len(result.data)} sources")

    # ── 2. Deactivate all existing channels ─────────────────────────
    print("Deactivating old channels...")
    result = client.table("channels").update({"is_active": False}).neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print(f"  Deactivated {len(result.data)} channels")

    # ── 3. Seed new sources ──────────────────────────────────────────
    print(f"\nSeeding {len(SOURCES)} new sources...")
    inserted = 0
    for source in SOURCES:
        try:
            client.table("sources").upsert(
                {**source, "is_active": True},
                on_conflict="url"
            ).execute()
            inserted += 1
            print(f"  ✓  [{source['language'].upper()}] {source['name']}")
        except Exception as e:
            print(f"  ✗  {source['name']} — {e}")
    print(f"  Done: {inserted}/{len(SOURCES)} sources active")

    # ── 4. Seed new channels ─────────────────────────────────────────
    print(f"\nSeeding {len(CHANNELS)} new channels...")
    for ch in CHANNELS:
        try:
            client.table("channels").upsert(
                {**ch, "is_active": True},
                on_conflict="slug"
            ).execute()
            print(f"  ✓  {ch['icon']} {ch['name']}")
        except Exception as e:
            print(f"  ✗  {ch['name']} — {e}")

    print("\n✅  Migration complete.")
    print("   Next step: run  python crawler/main.py  to start crawling general news.")


if __name__ == "__main__":
    migrate()
