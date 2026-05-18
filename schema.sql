-- ═══════════════════════════════════════════════════════════════════
-- Music News Crawler — Supabase PostgreSQL Schema
-- Run this in: Supabase Dashboard → SQL Editor → Run
-- ═══════════════════════════════════════════════════════════════════

-- Enable pgcrypto for gen_random_bytes / gen_random_uuid
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ─────────────────────────────────────────────────────────────────
-- SOURCES
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sources (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                TEXT NOT NULL,
  url                 TEXT NOT NULL,
  rss_url             TEXT,                   -- null = use HTML scraper
  language            CHAR(2) NOT NULL,       -- en ro fr de it es
  primary_genres      TEXT[] NOT NULL DEFAULT '{}',
  is_active           BOOLEAN NOT NULL DEFAULT TRUE,
  last_crawled_at     TIMESTAMPTZ,
  crawl_error_count   INT NOT NULL DEFAULT 0,
  last_error          TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT sources_url_unique UNIQUE (url)
);

CREATE INDEX IF NOT EXISTS idx_sources_language  ON sources(language);
CREATE INDEX IF NOT EXISTS idx_sources_active    ON sources(is_active);


-- ─────────────────────────────────────────────────────────────────
-- ARTICLES
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS articles (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id        UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  url              TEXT NOT NULL,
  url_hash         TEXT NOT NULL UNIQUE,      -- sha256(url) for fast dedup
  title            TEXT NOT NULL,
  author           TEXT,
  image_url        TEXT,
  published_at     TIMESTAMPTZ,
  crawled_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  raw_text         TEXT,
  word_count       INT,
  is_paywalled     BOOLEAN NOT NULL DEFAULT FALSE,
  -- AI-generated fields (populated after crawl)
  summary_en       TEXT,
  genres           TEXT[] DEFAULT '{}',
  content_type     TEXT,                      -- album-review news interview live ...
  sentiment        TEXT,                      -- positive neutral negative
  is_processed     BOOLEAN NOT NULL DEFAULT FALSE,
  processing_error TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_articles_source      ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_published   ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_processed   ON articles(is_processed);
CREATE INDEX IF NOT EXISTS idx_articles_genres      ON articles USING GIN(genres);
CREATE INDEX IF NOT EXISTS idx_articles_content_type ON articles(content_type);
CREATE INDEX IF NOT EXISTS idx_articles_crawled     ON articles(crawled_at DESC);


-- ─────────────────────────────────────────────────────────────────
-- ARTICLE TRANSLATIONS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS article_translations (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id          UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  language            CHAR(2) NOT NULL,
  title_translated    TEXT,
  summary_translated  TEXT NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(article_id, language)
);

CREATE INDEX IF NOT EXISTS idx_translations_article ON article_translations(article_id);


-- ─────────────────────────────────────────────────────────────────
-- CHANNELS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS channels (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug             TEXT NOT NULL UNIQUE,
  name             TEXT NOT NULL,
  description      TEXT,
  icon             TEXT,                       -- emoji
  genre_filters    TEXT[],                     -- null = match all genres
  content_filters  TEXT[],                     -- null = match all content types
  is_active        BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order       INT NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT channels_slug_unique UNIQUE (slug)
);


-- ─────────────────────────────────────────────────────────────────
-- SUBSCRIPTIONS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subscriptions (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email               TEXT NOT NULL,
  channel_id          UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  preferred_language  CHAR(2) NOT NULL DEFAULT 'en',
  unsubscribe_token   TEXT NOT NULL UNIQUE DEFAULT encode(gen_random_bytes(32), 'hex'),
  is_active           BOOLEAN NOT NULL DEFAULT TRUE,
  subscribed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_sent_at        TIMESTAMPTZ,
  UNIQUE(email, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_email     ON subscriptions(email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_channel   ON subscriptions(channel_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_active    ON subscriptions(is_active);
CREATE INDEX IF NOT EXISTS idx_subscriptions_token     ON subscriptions(unsubscribe_token);


-- ─────────────────────────────────────────────────────────────────
-- NEWSLETTER ISSUES  (audit trail — one row per channel per day)
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS newsletter_issues (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id       UUID NOT NULL REFERENCES channels(id),
  issue_date       DATE NOT NULL,
  article_ids      UUID[] DEFAULT '{}',
  article_count    INT NOT NULL DEFAULT 0,
  recipient_count  INT NOT NULL DEFAULT 0,
  sent_at          TIMESTAMPTZ,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(channel_id, issue_date)
);


-- ─────────────────────────────────────────────────────────────────
-- ROW LEVEL SECURITY
-- ─────────────────────────────────────────────────────────────────
-- Public (anon key) can only SELECT non-sensitive data.
-- Service key (used by GitHub Actions) bypasses RLS.

ALTER TABLE sources              ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles             ENABLE ROW LEVEL SECURITY;
ALTER TABLE article_translations ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels             ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions        ENABLE ROW LEVEL SECURITY;
ALTER TABLE newsletter_issues    ENABLE ROW LEVEL SECURITY;

-- Public read policies (for frontend)
CREATE POLICY "public read sources"   ON sources             FOR SELECT USING (true);
CREATE POLICY "public read articles"  ON articles            FOR SELECT USING (is_processed = true);
CREATE POLICY "public read trans"     ON article_translations FOR SELECT USING (true);
CREATE POLICY "public read channels"  ON channels            FOR SELECT USING (is_active = true);
CREATE POLICY "public read issues"    ON newsletter_issues    FOR SELECT USING (true);

-- Subscriptions: anon can INSERT their own; cannot read others
CREATE POLICY "anon insert sub"  ON subscriptions FOR INSERT WITH CHECK (true);
CREATE POLICY "anon update unsub" ON subscriptions FOR UPDATE
  USING (true)
  WITH CHECK (is_active = false);   -- anon can only deactivate (unsubscribe)


-- ─────────────────────────────────────────────────────────────────
-- HELPER FUNCTION: get article count for a channel (last 24h)
-- ─────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION channel_article_count(p_channel_id UUID, p_hours INT DEFAULT 24)
RETURNS INT AS $$
DECLARE
  v_genre_filters  TEXT[];
  v_content_filters TEXT[];
  v_count INT;
BEGIN
  SELECT genre_filters, content_filters
    INTO v_genre_filters, v_content_filters
    FROM channels WHERE id = p_channel_id;

  SELECT COUNT(*) INTO v_count
    FROM articles
   WHERE is_processed = true
     AND crawled_at >= NOW() - (p_hours || ' hours')::INTERVAL
     AND (v_genre_filters IS NULL OR genres && v_genre_filters)
     AND (v_content_filters IS NULL OR content_type = ANY(v_content_filters));

  RETURN v_count;
END;
$$ LANGUAGE plpgsql;
