"""
Seed script — inserts all 14 channels into Supabase.
Run: python seed/channels.py
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

CHANNELS = [
    {
        "slug": "indie-daily",
        "name": "Indie Daily",
        "description": "Independent music, bedroom pop, lo-fi, and the alternative fringes. Fresh discoveries every morning.",
        "icon": "🎸",
        "genre_filters": ["indie", "alternative"],
        "content_filters": None,
        "sort_order": 1,
    },
    {
        "slug": "metal-daily",
        "name": "Metal Daily",
        "description": "Everything metal — heavy, thrash, doom, black, death, prog. News, reviews, and new releases.",
        "icon": "🤘",
        "genre_filters": ["metal"],
        "content_filters": None,
        "sort_order": 2,
    },
    {
        "slug": "jazz-notes",
        "name": "Jazz Notes",
        "description": "Jazz, fusion, free jazz, nu-jazz, and improvised music from labels and scenes worldwide.",
        "icon": "🎷",
        "genre_filters": ["jazz"],
        "content_filters": None,
        "sort_order": 3,
    },
    {
        "slug": "electronic-pulse",
        "name": "Electronic Pulse",
        "description": "Club culture, techno, house, ambient, IDM — the full spectrum of electronic music.",
        "icon": "🎛️",
        "genre_filters": ["electronic", "techno"],
        "content_filters": None,
        "sort_order": 4,
    },
    {
        "slug": "underground-wire",
        "name": "Underground Wire",
        "description": "DIY labels, noise, avant-garde, hardcore, and anything operating outside the mainstream.",
        "icon": "📡",
        "genre_filters": ["underground", "experimental", "punk"],
        "content_filters": None,
        "sort_order": 5,
    },
    {
        "slug": "rock-solid",
        "name": "Rock Solid",
        "description": "Classic rock, alternative, garage, grunge — guitars, drums, and everything in between.",
        "icon": "🎵",
        "genre_filters": ["rock", "punk"],
        "content_filters": None,
        "sort_order": 6,
    },
    {
        "slug": "new-releases",
        "name": "New Releases",
        "description": "Albums, EPs, and singles across all genres. The freshest drops in one place.",
        "icon": "💿",
        "genre_filters": None,
        "content_filters": ["album-review", "track-premiere", "new-release"],
        "sort_order": 7,
    },
    {
        "slug": "interviews-only",
        "name": "Artist Voices",
        "description": "In-depth interviews, profiles, and long-form essays from the world's best music journalists.",
        "icon": "🎤",
        "genre_filters": None,
        "content_filters": ["interview", "feature"],
        "sort_order": 8,
    },
    {
        "slug": "live-music",
        "name": "Live & Touring",
        "description": "Concert reviews, tour announcements, festival lineups, and live session coverage.",
        "icon": "🎪",
        "genre_filters": None,
        "content_filters": ["live"],
        "sort_order": 9,
    },
    {
        "slug": "folk-americana",
        "name": "Folk & Americana",
        "description": "Folk, americana, country, bluegrass, and singer-songwriter traditions old and new.",
        "icon": "🪕",
        "genre_filters": ["folk"],
        "content_filters": None,
        "sort_order": 10,
    },
    {
        "slug": "hip-hop-beats",
        "name": "Hip-Hop & Beats",
        "description": "Hip-hop, rap, trap, boom-bap, and beat music from underground crews to top charts.",
        "icon": "🎧",
        "genre_filters": ["hip-hop"],
        "content_filters": None,
        "sort_order": 11,
    },
    {
        "slug": "metal-reviews",
        "name": "Metal Reviews",
        "description": "Only album and EP reviews from the metal world. No noise, just verdicts.",
        "icon": "⚔️",
        "genre_filters": ["metal"],
        "content_filters": ["album-review"],
        "sort_order": 12,
    },
    {
        "slug": "electronic-reviews",
        "name": "Electronic Reviews",
        "description": "Album reviews from the electronic and techno world — label releases, DJ albums, ambient LPs.",
        "icon": "🔊",
        "genre_filters": ["electronic", "techno"],
        "content_filters": ["album-review"],
        "sort_order": 13,
    },
    {
        "slug": "all-genres",
        "name": "Everything",
        "description": "The full firehose — every article from every source, every genre, every language.",
        "icon": "🌍",
        "genre_filters": None,
        "content_filters": None,
        "sort_order": 14,
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
