"""
Seed script — inserts channels into Supabase.
Run: python seed/channels.py
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

CHANNELS = [
    {
        "slug": "world-news",
        "name": "World News",
        "description": "The most important global stories — politics, conflicts, diplomacy, and international affairs from top news agencies.",
        "icon": "🌍",
        "genre_filters": ["geopolitics", "defense", "society"],
        "content_filters": None,
        "sort_order": 1,
    },
    {
        "slug": "geopolitics",
        "name": "Geopolitics",
        "description": "In-depth coverage of international relations, conflicts, diplomacy, and global power dynamics.",
        "icon": "🗺️",
        "genre_filters": ["geopolitics", "defense"],
        "content_filters": None,
        "sort_order": 2,
    },
    {
        "slug": "tech",
        "name": "Tech",
        "description": "Technology news, AI breakthroughs, startups, and the companies shaping our digital future.",
        "icon": "💻",
        "genre_filters": ["tech", "ai", "startups"],
        "content_filters": None,
        "sort_order": 3,
    },
    {
        "slug": "economy",
        "name": "Economy",
        "description": "Markets, finance, trade, energy, and the economic forces driving global growth and crises.",
        "icon": "📈",
        "genre_filters": ["economy", "finance", "energy"],
        "content_filters": None,
        "sort_order": 4,
    },
    {
        "slug": "romania",
        "name": "România",
        "description": "Local Romanian news — politics, economy, society, and tech from the best Romanian sources.",
        "icon": "🇷🇴",
        "genre_filters": ["romania"],
        "content_filters": None,
        "sort_order": 5,
    },
    {
        "slug": "romania-tech",
        "name": "România Tech",
        "description": "Romanian startups, tech companies, and digital economy news.",
        "icon": "🇷🇴",
        "genre_filters": ["romania", "tech", "startups"],
        "content_filters": None,
        "sort_order": 6,
    },
    {
        "slug": "all-news",
        "name": "Everything",
        "description": "The full feed — every article from every source, every topic, worldwide and local.",
        "icon": "📰",
        "genre_filters": None,
        "content_filters": None,
        "sort_order": 7,
    },
]


def seed_channels():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    client = create_client(url, key)

    print(f"Seeding {len(CHANNELS)} channels...")
    for ch in CHANNELS:
        try:
            client.table("channels").upsert(ch, on_conflict="slug").execute()
            print(f"  ✓  {ch['icon']} {ch['name']}")
        except Exception as e:
            print(f"  ✗  {ch['name']} — {e}")

    print(f"\nDone. {len(CHANNELS)} channels seeded.")


if __name__ == "__main__":
    seed_channels()
