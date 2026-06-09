"""
Seed script — inserts general news sources into Supabase.
Run: python seed/sources.py
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SOURCES = [
    # ─────────────────────────────────────────
    # ENGLISH — World / Geopolitics
    # ─────────────────────────────────────────
    {"name": "Reuters World",       "url": "https://reuters.com",               "rss_url": "https://feeds.reuters.com/reuters/worldNews",                   "language": "en", "primary_genres": ["geopolitics"]},
    {"name": "Reuters Top News",    "url": "https://reuters.com",               "rss_url": "https://feeds.reuters.com/reuters/topNews",                     "language": "en", "primary_genres": ["geopolitics", "economy"]},
    {"name": "BBC World News",      "url": "https://bbc.com/news/world",        "rss_url": "http://feeds.bbci.co.uk/news/world/rss.xml",                    "language": "en", "primary_genres": ["geopolitics"]},
    {"name": "Al Jazeera",          "url": "https://aljazeera.com",             "rss_url": "https://www.aljazeera.com/xml/rss/all.xml",                     "language": "en", "primary_genres": ["geopolitics", "society"]},
    {"name": "DW News",             "url": "https://dw.com",                    "rss_url": "https://rss.dw.com/xml/rss-en-all",                             "language": "en", "primary_genres": ["geopolitics", "society"]},
    {"name": "France 24 English",   "url": "https://france24.com/en",           "rss_url": "https://www.france24.com/en/rss",                               "language": "en", "primary_genres": ["geopolitics"]},
    {"name": "The Guardian World",  "url": "https://theguardian.com/world",     "rss_url": "https://www.theguardian.com/world/rss",                         "language": "en", "primary_genres": ["geopolitics", "society"]},
    {"name": "Foreign Policy",      "url": "https://foreignpolicy.com",         "rss_url": "https://foreignpolicy.com/feed/",                               "language": "en", "primary_genres": ["geopolitics", "defense"]},
    {"name": "The Economist",       "url": "https://economist.com",             "rss_url": "https://www.economist.com/latest/rss.xml",                      "language": "en", "primary_genres": ["geopolitics", "economy"]},
    {"name": "Associated Press",    "url": "https://apnews.com",                "rss_url": "https://rsshub.app/apnews/topics/apf-topnews",                  "language": "en", "primary_genres": ["geopolitics"]},

    # ─────────────────────────────────────────
    # ENGLISH — Tech
    # ─────────────────────────────────────────
    {"name": "TechCrunch",          "url": "https://techcrunch.com",            "rss_url": "https://techcrunch.com/feed/",                                  "language": "en", "primary_genres": ["tech", "startups"]},
    {"name": "The Verge",           "url": "https://theverge.com",              "rss_url": "https://www.theverge.com/rss/index.xml",                        "language": "en", "primary_genres": ["tech"]},
    {"name": "Ars Technica",        "url": "https://arstechnica.com",           "rss_url": "https://feeds.arstechnica.com/arstechnica/index/",              "language": "en", "primary_genres": ["tech", "science"]},
    {"name": "Wired",               "url": "https://wired.com",                 "rss_url": "https://www.wired.com/feed/rss",                                "language": "en", "primary_genres": ["tech", "society"]},
    {"name": "MIT Technology Review","url": "https://technologyreview.com",     "rss_url": "https://www.technologyreview.com/feed/",                        "language": "en", "primary_genres": ["tech", "ai", "science"]},
    {"name": "VentureBeat",         "url": "https://venturebeat.com",           "rss_url": "https://venturebeat.com/feed/",                                 "language": "en", "primary_genres": ["tech", "ai", "startups"]},
    {"name": "BBC Tech",            "url": "https://bbc.com/news/technology",   "rss_url": "http://feeds.bbci.co.uk/news/technology/rss.xml",               "language": "en", "primary_genres": ["tech"]},
    {"name": "The Guardian Tech",   "url": "https://theguardian.com/technology","rss_url": "https://www.theguardian.com/technology/rss",                    "language": "en", "primary_genres": ["tech", "ai"]},

    # ─────────────────────────────────────────
    # ENGLISH — Economy / Finance
    # ─────────────────────────────────────────
    {"name": "Reuters Business",    "url": "https://reuters.com/business",      "rss_url": "https://feeds.reuters.com/reuters/businessNews",                "language": "en", "primary_genres": ["economy", "finance"]},
    {"name": "CNBC",                "url": "https://cnbc.com",                  "rss_url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",         "language": "en", "primary_genres": ["economy", "finance"]},
    {"name": "MarketWatch",         "url": "https://marketwatch.com",           "rss_url": "https://feeds.marketwatch.com/marketwatch/topstories/",         "language": "en", "primary_genres": ["economy", "finance"]},
    {"name": "Bloomberg Tech",      "url": "https://bloomberg.com",             "rss_url": "https://feeds.bloomberg.com/technology/news.rss",               "language": "en", "primary_genres": ["tech", "economy"]},
    {"name": "Financial Times",     "url": "https://ft.com",                    "rss_url": "https://www.ft.com/?format=rss",                                "language": "en", "primary_genres": ["economy", "finance"]},
    {"name": "The Guardian Business","url": "https://theguardian.com/business", "rss_url": "https://www.theguardian.com/business/rss",                      "language": "en", "primary_genres": ["economy", "finance"]},

    # ─────────────────────────────────────────
    # ROMANIAN — General / Geopolitics
    # ─────────────────────────────────────────
    {"name": "Digi24",              "url": "https://digi24.ro",                 "rss_url": "https://www.digi24.ro/rss.xml",                                 "language": "ro", "primary_genres": ["romania", "geopolitics"]},
    {"name": "G4Media",             "url": "https://g4media.ro",                "rss_url": "https://www.g4media.ro/feed",                                   "language": "ro", "primary_genres": ["romania", "geopolitics", "society"]},
    {"name": "HotNews",             "url": "https://hotnews.ro",                "rss_url": "https://www.hotnews.ro/rss/actualitate.xml",                    "language": "ro", "primary_genres": ["romania", "geopolitics"]},
    {"name": "ProTV Știri",         "url": "https://stirileprotv.ro",           "rss_url": "https://stirileprotv.ro/rss.xml",                               "language": "ro", "primary_genres": ["romania", "society"]},
    {"name": "Mediafax",            "url": "https://mediafax.ro",               "rss_url": "https://www.mediafax.ro/rss/",                                  "language": "ro", "primary_genres": ["romania", "geopolitics", "economy"]},
    {"name": "Ziare.com",           "url": "https://ziare.com",                 "rss_url": "https://www.ziare.com/rss/stiri.xml",                           "language": "ro", "primary_genres": ["romania"]},
    {"name": "Adevărul",            "url": "https://adevarul.ro",               "rss_url": "https://adevarul.ro/rss",                                       "language": "ro", "primary_genres": ["romania", "geopolitics", "society"]},
    {"name": "Libertatea",          "url": "https://libertatea.ro",             "rss_url": "https://www.libertatea.ro/rss",                                 "language": "ro", "primary_genres": ["romania", "society"]},
    {"name": "DoR",                 "url": "https://dor.ro",                    "rss_url": "https://www.dor.ro/feed/",                                      "language": "ro", "primary_genres": ["romania", "society", "feature"]},
    {"name": "Recorder",            "url": "https://recorder.ro",               "rss_url": "https://recorder.ro/feed/",                                     "language": "ro", "primary_genres": ["romania", "society", "geopolitics"]},

    # ─────────────────────────────────────────
    # ROMANIAN — Economy / Business / Tech
    # ─────────────────────────────────────────
    {"name": "Economica.net",       "url": "https://economica.net",             "rss_url": "https://economica.net/rss/",                                    "language": "ro", "primary_genres": ["romania", "economy", "finance"]},
    {"name": "StartupCafe",         "url": "https://startupcafe.ro",            "rss_url": "https://www.startupcafe.ro/rss.xml",                            "language": "ro", "primary_genres": ["romania", "startups", "tech"]},
    {"name": "Digi24 Economie",     "url": "https://digi24.ro/stiri/economie",  "rss_url": "https://www.digi24.ro/rss/stiri-economie",                      "language": "ro", "primary_genres": ["romania", "economy"]},
    {"name": "Wall-Street.ro",      "url": "https://wall-street.ro",            "rss_url": "https://www.wall-street.ro/rss.xml",                            "language": "ro", "primary_genres": ["romania", "economy", "finance"]},
    {"name": "Profit.ro",           "url": "https://profit.ro",                 "rss_url": "https://www.profit.ro/rss/",                                    "language": "ro", "primary_genres": ["romania", "economy", "finance"]},
    {"name": "Biz.ro",              "url": "https://biz.ro",                    "rss_url": "https://www.biz.ro/feed/",                                      "language": "ro", "primary_genres": ["romania", "economy", "startups"]},
    {"name": "IQads",               "url": "https://iqads.ro",                  "rss_url": "https://www.iqads.ro/rss.xml",                                  "language": "ro", "primary_genres": ["romania", "tech", "society"]},
]


def seed_sources():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    client = create_client(url, key)

    print(f"Seeding {len(SOURCES)} sources...")
    inserted = 0
    errors = 0

    for source in SOURCES:
        try:
            client.table("sources").upsert(source, on_conflict="url").execute()
            inserted += 1
            print(f"  ✓  [{source['language'].upper()}] {source['name']}")
        except Exception as e:
            errors += 1
            print(f"  ✗  [{source['language'].upper()}] {source['name']} — {e}")

    print(f"\nDone. inserted/updated={inserted}  errors={errors}")


if __name__ == "__main__":
    seed_sources()
