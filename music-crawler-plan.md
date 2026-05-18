# Music News Crawler & Newsletter Platform — Implementation Plan

> **Stack philosophy:** 100% free tier. No credit card required to get to production.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Interest & Channel Taxonomy](#2-interest--channel-taxonomy)
3. [Site Inventory (150 Sources)](#3-site-inventory-150-sources)
4. [System Architecture](#4-system-architecture)
5. [Database Schema](#5-database-schema)
6. [Tech Stack — Free Tier Breakdown](#6-tech-stack--free-tier-breakdown)
7. [Phase-by-Phase Implementation](#7-phase-by-phase-implementation)
8. [AI Pipeline Detail](#8-ai-pipeline-detail)
9. [Newsletter Engine Detail](#9-newsletter-engine-detail)
10. [Frontend / Channel Website Detail](#10-frontend--channel-website-detail)
11. [Cost Summary](#11-cost-summary)

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions (Cron: daily 06:00 UTC)                     │
│                                                             │
│  1. Crawler runs → fetches RSS + HTML for 150 sources       │
│  2. Deduplication against DB                                │
│  3. AI Pipeline: summarize + classify + tag                 │
│  4. Translation: summaries → 6 languages                    │
│  5. Newsletter builder → sends via email                    │
└────────────────────┬────────────────────────────────────────┘
                     │ read/write
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Supabase (PostgreSQL + Auth-less API)                      │
│  tables: sources, articles, translations,                   │
│          channels, subscriptions, newsletter_issues         │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Next.js on Vercel (Frontend)                               │
│  /channels     — browse all channels                        │
│  /channels/[slug] — channel page with latest articles       │
│  /subscribe    — pick channels + language + enter email     │
│  /unsubscribe  — one-click unsubscribe via token            │
└─────────────────────────────────────────────────────────────┘
```

**Daily flow in plain English:**
1. GitHub Actions wakes up at 6am UTC
2. Python crawler fetches each source's RSS feed (HTML fallback if no RSS)
3. New articles get their text cleaned and stored
4. Groq (Llama 3) generates a 3-sentence summary + genre tags + content type
5. LibreTranslate translates each summary into all 6 languages
6. The newsletter builder groups articles by channel, builds HTML emails
7. Resend sends each subscriber their personalised digest in their chosen language

---

## 2. Interest & Channel Taxonomy

### 2.1 Genre Tags (applied to every article by AI)

| Tag | Description |
|-----|-------------|
| `indie` | Independent/alternative music, lo-fi, bedroom pop |
| `rock` | Classic rock, alternative rock, garage rock |
| `metal` | All metal subgenres (heavy, thrash, doom, black, death, prog) |
| `jazz` | Jazz, fusion, free jazz, nu-jazz |
| `electronic` | Electronic music broadly (house, ambient, IDM) |
| `techno` | Techno, acid, industrial techno, EBM |
| `underground` | DIY, hardcore, noise, avant-garde, zine culture |
| `hip-hop` | Hip-hop, rap, trap, boom-bap |
| `folk` | Folk, americana, country, singer-songwriter |
| `classical` | Classical, contemporary classical, neoclassical |
| `pop` | Mainstream pop, synth-pop, dream pop |
| `experimental` | Avant-garde, sound art, electroacoustic |
| `punk` | Punk, post-punk, emo, hardcore |

### 2.2 Content Type Tags (applied to every article by AI)

| Tag | Description |
|-----|-------------|
| `album-review` | Full album or EP review |
| `track-premiere` | New track/video debut |
| `new-release` | Album/EP/single announcement |
| `interview` | Artist interview or profile |
| `news` | Industry news, label/distribution news |
| `live` | Concert review, tour announcement, festival news |
| `list` | Best-of lists, recommendations |
| `obituary` | Artist death / tribute |
| `feature` | Long-form essay or feature piece |

### 2.3 Region Tags (applied based on article content + source language)

| Tag | Description |
|-----|-------------|
| `global` | International / no specific region |
| `north-america` | USA and Canada |
| `uk-ireland` | United Kingdom and Ireland |
| `western-europe` | France, Germany, Benelux, Spain, Italy |
| `eastern-europe` | Romania, Poland, Czech Republic, etc. |
| `latin-america` | Mexico, Brazil, Argentina, etc. |
| `scandinavia` | Nordic countries |

### 2.4 Predefined Channels

Channels are curated combinations of genre + content-type filters. Users subscribe to one or more channels.

| Channel Slug | Name | Genre Filter | Content Filter | Notes |
|---|---|---|---|---|
| `indie-daily` | Indie Daily | indie | all | Broad indie coverage |
| `metal-daily` | Metal Daily | metal | all | All metal news |
| `jazz-notes` | Jazz Notes | jazz | all | Jazz coverage |
| `electronic-pulse` | Electronic Pulse | electronic, techno | all | Club/rave culture |
| `underground-wire` | Underground Wire | underground, experimental, punk | all | DIY/avant-garde |
| `rock-solid` | Rock Solid | rock, punk | all | Rock news |
| `new-releases` | New Releases | all | new-release, track-premiere, album-review | Release-focused |
| `interviews-only` | Artist Voices | all | interview, feature | Interviews & long reads |
| `live-music` | Live & Touring | all | live | Concerts, tours, festivals |
| `folk-americana` | Folk & Americana | folk | all | Folk/americana/country |
| `all-genres` | Everything | all | all | Full firehose |
| `metal-reviews` | Metal Reviews | metal | album-review | Metal album reviews only |
| `electronic-reviews` | Electronic Reviews | electronic, techno | album-review | Electronic album reviews |
| `indie-rock-reviews` | Indie/Rock Reviews | indie, rock | album-review | Indie/rock album reviews |

### 2.5 Language Preference

Every subscriber picks one display language. Summaries are auto-translated to that language. Links always point to the original article in its source language.

| Code | Language |
|------|----------|
| `en` | English |
| `ro` | Romanian |
| `fr` | French |
| `de` | German |
| `it` | Italian |
| `es` | Spanish |

---

## 3. Site Inventory (150 Sources)

> RSS availability marked as ✓ (confirmed), ~ (likely), ? (needs verification).
> Sites marked [scrape] require HTML parsing instead of RSS.

### 🇬🇧 English (25 Sites)

| # | Site | URL | Genre(s) | RSS |
|---|------|-----|----------|-----|
| 1 | Pitchfork | pitchfork.com | Indie, Alternative | ✓ |
| 2 | Stereogum | stereogum.com | Indie, Rock | ✓ |
| 3 | NME | nme.com | Rock, Pop, Indie | ✓ |
| 4 | Consequence | consequence.net | Multi-genre | ✓ |
| 5 | The Quietus | thequietus.com | Experimental, Metal, Indie | ✓ |
| 6 | Resident Advisor | ra.co | Electronic, Techno | ✓ |
| 7 | FACT Magazine | factmag.com | Electronic, Underground | ✓ |
| 8 | DJ Mag | djmag.com | Electronic, Dance | ✓ |
| 9 | Louder Sound | loudersound.com | Metal, Rock | ✓ |
| 10 | Kerrang! | kerrang.com | Metal, Rock | ✓ |
| 11 | Metal Injection | metalinjection.net | Metal | ✓ |
| 12 | Blabbermouth | blabbermouth.net | Metal, Rock | ✓ |
| 13 | Bandcamp Daily | daily.bandcamp.com | Underground, Independent | ✓ |
| 14 | The Wire | thewire.co.uk | Experimental, Jazz, Electronic | ✓ |
| 15 | Jazz Times | jazztimes.com | Jazz | ✓ |
| 16 | All About Jazz | allaboutjazz.com | Jazz | ✓ |
| 17 | Under the Radar | undertheradarmag.com | Indie | ✓ |
| 18 | The Line of Best Fit | thelineofbestfit.com | Indie | ✓ |
| 19 | Exclaim! | exclaim.ca | Indie, Alternative | ✓ |
| 20 | Spin | spin.com | Rock, Indie | ✓ |
| 21 | Paste Magazine | pastemagazine.com | Indie, Folk | ✓ |
| 22 | Clash Music | clashmusic.com | Indie, Electronic | ✓ |
| 23 | PopMatters | popmatters.com | Multi-genre | ✓ |
| 24 | No Ripcord | noripcord.com | Indie, Alternative | ~ |
| 25 | Treble | treblemag.com | Indie, Rock, Experimental | ✓ |

### 🇷🇴 Romanian (25 Sites)

| # | Site | URL | Genre(s) | RSS |
|---|------|-----|----------|-----|
| 1 | Metalhead.ro | metalhead.ro | Metal | ✓ |
| 2 | Zeppelin | zeppelin.ro | Rock, Alternative | ~ |
| 3 | Cinetic | cinetic.ro | Alternative, Underground | ? |
| 4 | Scena9 | scena9.ro | Culture, Indie, Alternative | ✓ |
| 5 | LaPunkt | lapunkt.ro | Jazz, World, Experimental | ~ |
| 6 | Observator Cultural | observatorcultural.ro | Culture, Criticism | ~ |
| 7 | RFI România | rfi.ro | Multi-genre (culture section) | ✓ |
| 8 | Radio Guerrilla | guerrilla.ro | Rock, Alternative | ~ |
| 9 | Muzici și Faze | muzicisifaze.ro | Metal, Underground | ? |
| 10 | ProFM | profm.ro | Pop, Electronic | ~ |
| 11 | Rock FM | rockfm.ro | Rock | ~ |
| 12 | HipHop.ro | hiphop.ro | Hip-Hop, Urban | ~ |
| 13 | Music.ro | music.ro | Multi-genre | ~ |
| 14 | The ARK | theark.ro | Culture, Indie | ? |
| 15 | DoR (Decât o Revistă) | dor.ro | Culture, Long-form | ~ |
| 16 | Digi24 Cultură | digi24.ro/cultura | Multi-genre | ✓ |
| 17 | Recorder | recorder.ro | Culture, Documentary | ~ |
| 18 | Vibe.ro | vibe.ro | Pop, R&B | ~ |
| 19 | Untold Festival News | untold.com/news | Electronic, Festival | ? |
| 20 | Electric Castle Blog | electriccastle.ro/blog | Electronic, Indie, Festival | ? |
| 21 | Artgasm | artgasm.ro | Multi-genre | ~ |
| 22 | Libertatea Cultură | libertatea.ro/entertainment | Multi-genre | ✓ |
| 23 | Gandul Cultură | gandul.ro/cultura | Multi-genre | ~ |
| 24 | Adevărul Cultură | adevarul.ro/cultura | Multi-genre | ✓ |
| 25 | Modernism | modernism.ro | Electronic, Culture | ? |

### 🇫🇷 French (25 Sites)

| # | Site | URL | Genre(s) | RSS |
|---|------|-----|----------|-----|
| 1 | Les Inrockuptibles | lesinrocks.com | Indie, Alternative, Pop | ✓ |
| 2 | Télérama Musique | telerama.fr | Multi-genre | ✓ |
| 3 | Rolling Stone FR | rollingstone.fr | Multi-genre | ✓ |
| 4 | Tsugi | tsugi.fr | Electronic, Techno | ✓ |
| 5 | Trax Magazine | traxmag.com | Electronic, Techno | ✓ |
| 6 | Gonzaï | gonzai.com | Indie, Underground, Alternative | ✓ |
| 7 | Metallian | metallian.com | Metal | ✓ |
| 8 | Hard Force | hard-force.com | Metal, Rock | ✓ |
| 9 | Jazz Magazine | jazzmagazine.com | Jazz | ✓ |
| 10 | Improjazz | improjazz.net | Jazz, Experimental, Improv | ~ |
| 11 | Mouvement | mouvement.net | Experimental, Electronic | ~ |
| 12 | Chronicart | chronicart.com | Multi-genre | ✓ |
| 13 | Magic! | magic.fr | Rock, Classic Rock | ~ |
| 14 | IndieMag | indiemag.fr | Indie | ✓ |
| 15 | Charts in France | chartsinfrance.net | Pop, Charts | ✓ |
| 16 | Sourdoreille | sourdoreille.net | Indie, World | ✓ |
| 17 | Obskure | obskure.com | Gothic, Darkwave, Electronic | ~ |
| 18 | DBD Magazine | dbdmag.fr | Doom, Black, Death Metal | ~ |
| 19 | Radio Nova | nova.fr | World, Electronic, Afrobeats | ✓ |
| 20 | Néosphère | neosphere.com | Electronic, Experimental | ? |
| 21 | Longueur d'Ondes | longueurdondes.com | World, Folk, Jazz | ~ |
| 22 | Libération Next | liberation.fr/culture | Multi-genre | ✓ |
| 23 | Le Monde Culture | lemonde.fr/culture | Multi-genre | ✓ |
| 24 | Le Son du Rock | leson-durock.com | Rock, Indie | ~ |
| 25 | Brain Magazine | brain-magazine.fr | Hip-Hop, Electronic, Indie | ✓ |

### 🇩🇪 German (25 Sites)

| # | Site | URL | Genre(s) | RSS |
|---|------|-----|----------|-----|
| 1 | Laut.de | laut.de | Multi-genre | ✓ |
| 2 | Musikexpress | musikexpress.de | Pop, Rock, Indie | ✓ |
| 3 | Rolling Stone DE | rollingstone.de | Multi-genre | ✓ |
| 4 | Metal Hammer DE | metal-hammer.de | Metal | ✓ |
| 5 | Rock Hard | rock-hard.de | Rock, Metal | ✓ |
| 6 | Intro | intro.de | Indie, Alternative | ✓ |
| 7 | Visions | visions.de | Indie, Alternative, Metal | ✓ |
| 8 | Jazzthing | jazzthing.de | Jazz | ✓ |
| 9 | Jazzzeitung | jazzzeitung.de | Jazz | ~ |
| 10 | Slam Magazine | slam.de | Hip-Hop | ✓ |
| 11 | Juice | juice.de | Hip-Hop | ✓ |
| 12 | Ox Fanzine | ox-fanzine.de | Punk, Hardcore | ~ |
| 13 | Eclipsed | eclipsed.de | Progressive, Krautrock | ~ |
| 14 | Diffus Magazine | diffus.de | Electronic, Indie | ~ |
| 15 | Byte.fm Blog | byte.fm | Electronic, Indie | ~ |
| 16 | Plattentests | plattentests.de | Multi-genre (reviews) | ✓ |
| 17 | Musikreviews | musikreviews.de | Multi-genre (reviews) | ~ |
| 18 | Subculture Magazine | subculture-magazin.de | Underground, Electronic | ? |
| 19 | Folk World | folk-world.eu | Folk, World | ~ |
| 20 | Terrorverlag | terrorverlag.de | Metal, Punk | ? |
| 21 | Unter Schafen | unterschafen.com | Indie, Alternative | ~ |
| 22 | NBHAP | nbhap.com | Electronic, Indie | ✓ |
| 23 | Resident Advisor DE | ra.co/de | Electronic (German content) | ✓ |
| 24 | taz Musik | taz.de | Multi-genre | ✓ |
| 25 | Spex Archive / Spex.de | spex.de | Indie, Electronic (archive) | ? |

### 🇮🇹 Italian (25 Sites)

| # | Site | URL | Genre(s) | RSS |
|---|------|-----|----------|-----|
| 1 | Sentireascoltare | sentireascoltare.com | Indie, Alternative, Multi | ✓ |
| 2 | Rumore Magazine | rumoremag.com | Indie, Alternative | ✓ |
| 3 | Ondarock | ondarock.it | Rock, Alternative | ✓ |
| 4 | Kalporz | kalporz.com | Indie, Alternative | ✓ |
| 5 | Rolling Stone IT | rollingstone.it | Multi-genre | ✓ |
| 6 | All Music Italia | allmusicitalia.it | Multi-genre | ✓ |
| 7 | Soundwall | soundwall.it | Electronic, Dance | ✓ |
| 8 | Jazzit | jazzit.it | Jazz | ~ |
| 9 | Musica Jazz | musicajazz.it | Jazz | ~ |
| 10 | Blow Up | blowupmagazine.it | Electronic, Experimental | ~ |
| 11 | Metal.it | metal.it | Metal | ✓ |
| 12 | Necromance IT | necromance.it | Metal | ~ |
| 13 | Il Mucchio | mucchio.it | Rock, Indie | ✓ |
| 14 | Rockit | rockit.it | Italian Indie | ✓ |
| 15 | Indie for Bunnies | indieforbunnies.com | Indie | ✓ |
| 16 | Bad Taste Musica | badtaste.it/musica | Multi-genre | ✓ |
| 17 | Seenoise | seenoise.it | Indie, Alternative | ~ |
| 18 | XL Repubblica | xl.repubblica.it | Indie, Alternative | ✓ |
| 19 | Wired IT Musica | wired.it/play/musica | Multi-genre | ✓ |
| 20 | Pitchfork IT | pitchfork.com/reviews (IT content) | Indie | ✓ |
| 21 | Classic Rock IT | classicrockmag.it | Rock, Classic Rock | ~ |
| 22 | Loud and Proud | loudandproud.it | Rock, Metal | ~ |
| 23 | Hit Week | hitweek.it | Multi-genre | ~ |
| 24 | Stordisco | stordisco.com | Electronic, Techno | ~ |
| 25 | Frigidaire / Mucchio Extra | (mucchio.it/extra) | Underground, Experimental | ? |

### 🇪🇸 Spanish (25 Sites)

| # | Site | URL | Genre(s) | RSS |
|---|------|-----|----------|-----|
| 1 | Mondosonoro | mondosonoro.com | Indie, Alternative | ✓ |
| 2 | Rolling Stone ES | rollingstone.es | Multi-genre | ✓ |
| 3 | Rockdelux | rockdelux.com | Multi-genre | ✓ |
| 4 | Playground | playgroundmag.net | Electronic, Urban | ✓ |
| 5 | Jenesaispop | jenesaispop.com | Pop, Indie | ✓ |
| 6 | Go! Mag | go-mag.com | Electronic, Indie | ✓ |
| 7 | Rock Zone | rockzone.es | Rock, Metal | ~ |
| 8 | Muzikalia | muzikalia.com | Multi-genre | ✓ |
| 9 | Tomajazz | tomajazz.com | Jazz | ✓ |
| 10 | Cuadernos de Jazz | cuadernosdejazz.com | Jazz | ~ |
| 11 | Metal Hammer ES | metal-hammer.es | Metal | ~ |
| 12 | Necromance ES | necromance.es | Metal | ~ |
| 13 | La Fonoteca | lafonoteca.net | Multi-genre (reviews) | ~ |
| 14 | Face B | faceb.es | Electronic, Techno | ~ |
| 15 | Ruta 66 | ruta66.es | Rock, Blues, Americana | ~ |
| 16 | Slowkiss Magazine | slowkiss.es | Indie, Dream Pop | ~ |
| 17 | Indie Rocks! | indiericksmagazine.com | Indie | ~ |
| 18 | Zona de Obras | zonadeobras.com | Electronic, Indie | ~ |
| 19 | El Diario Cultura | eldiario.es/cultura/musica | Multi-genre | ✓ |
| 20 | El País Música | elpais.com/cultura/musica | Multi-genre | ✓ |
| 21 | Hipersónica | hipersonica.com | Electronic, Experimental | ~ |
| 22 | KEXP en Español | kexp.org (Spanish content) | Multi-genre | ✓ |
| 23 | Conexión Rock | conexionrock.com | Rock, Metal | ~ |
| 24 | Radio 3 Blog | rtve.es/radio/radio3 | Indie, World, Jazz | ✓ |
| 25 | Louder ES | loudersound.com/es | Rock, Metal (ES) | ~ |

> **Note:** Sites marked `?` need manual RSS verification before inclusion. Sites marked `~` likely have RSS but must be confirmed. A verification script is included in Phase 1.

---

## 4. System Architecture

### 4.1 Component Map

```
┌───────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS RUNNER                      │
│                                                               │
│  ┌────────────┐   ┌──────────────┐   ┌─────────────────────┐ │
│  │  Crawler   │──▶│  AI Pipeline │──▶│  Newsletter Builder │ │
│  │  (Python)  │   │  (Groq API)  │   │  (Python + Resend)  │ │
│  └────────────┘   └──────────────┘   └─────────────────────┘ │
│        │                 │                      │             │
│        ▼                 ▼                      ▼             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │             Supabase PostgreSQL Database                 │ │
│  │  sources │ articles │ translations │ channels │          │ │
│  │  subscriptions │ newsletter_issues                       │ │
│  └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                              │
                         REST API
                              │
              ┌───────────────▼──────────────┐
              │     Vercel (Next.js 14)       │
              │                              │
              │  /              landing page │
              │  /channels      channel list │
              │  /channels/[s]  channel page │
              │  /subscribe     signup flow  │
              │  /unsubscribe   opt-out      │
              └──────────────────────────────┘
```

### 4.2 Data Flow Per Article

```
RSS Feed / HTML page
        │
        ▼
  Raw Article (title, url, html, pub_date, author)
        │
        ▼
  Text Extraction (trafilatura)
        │
        ▼
  Deduplication check (URL hash in DB)
        │
  [new] ▼
  Groq (Llama 3.1-8b):
    → 3-sentence English summary
    → genre tags (multi-label)
    → content type tag
    → sentiment (positive/neutral/negative)
        │
        ▼
  LibreTranslate:
    → translate summary → ro, fr, de, it, es
    (skip EN — already in EN)
        │
        ▼
  Store article + translations in Supabase
        │
        ▼
  6:30am UTC: Newsletter builder queries articles from last 24h
              Groups by channel filters
              Renders HTML email per subscriber
              Sends via Resend
```

---

## 5. Database Schema

```sql
-- ─────────────────────────────────────────
-- SOURCES
-- ─────────────────────────────────────────
CREATE TABLE sources (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  url           TEXT NOT NULL,
  rss_url       TEXT,                     -- null = use HTML scraper
  language      CHAR(2) NOT NULL,         -- en, ro, fr, de, it, es
  primary_genres TEXT[] NOT NULL,
  is_active     BOOLEAN DEFAULT TRUE,
  last_crawled_at TIMESTAMPTZ,
  crawl_error_count INT DEFAULT 0,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- ARTICLES
-- ─────────────────────────────────────────
CREATE TABLE articles (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id       UUID REFERENCES sources(id) ON DELETE CASCADE,
  url             TEXT UNIQUE NOT NULL,
  url_hash        TEXT UNIQUE NOT NULL,   -- sha256 of url for fast dedup
  title           TEXT NOT NULL,
  author          TEXT,
  image_url       TEXT,
  published_at    TIMESTAMPTZ,
  crawled_at      TIMESTAMPTZ DEFAULT NOW(),
  raw_text        TEXT,                   -- full extracted text
  -- AI-generated
  summary_en      TEXT,                   -- English summary (3 sentences)
  genres          TEXT[],                 -- e.g. ['metal', 'underground']
  content_type    TEXT,                   -- album-review / news / interview ...
  sentiment       TEXT,                   -- positive / neutral / negative
  is_processed    BOOLEAN DEFAULT FALSE,
  processing_error TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_genres    ON articles USING GIN(genres);
CREATE INDEX idx_articles_type      ON articles(content_type);

-- ─────────────────────────────────────────
-- ARTICLE TRANSLATIONS
-- ─────────────────────────────────────────
CREATE TABLE article_translations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id  UUID REFERENCES articles(id) ON DELETE CASCADE,
  language    CHAR(2) NOT NULL,
  title_translated   TEXT,
  summary_translated TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(article_id, language)
);

-- ─────────────────────────────────────────
-- CHANNELS
-- ─────────────────────────────────────────
CREATE TABLE channels (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug             TEXT UNIQUE NOT NULL,
  name             TEXT NOT NULL,
  description      TEXT,
  icon             TEXT,                  -- emoji or icon name
  genre_filters    TEXT[],               -- null = all genres
  content_filters  TEXT[],               -- null = all content types
  is_active        BOOLEAN DEFAULT TRUE,
  sort_order       INT DEFAULT 0,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- SUBSCRIPTIONS
-- ─────────────────────────────────────────
CREATE TABLE subscriptions (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email              TEXT NOT NULL,
  channel_id         UUID REFERENCES channels(id) ON DELETE CASCADE,
  preferred_language CHAR(2) NOT NULL DEFAULT 'en',
  unsubscribe_token  TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
  is_active          BOOLEAN DEFAULT TRUE,
  subscribed_at      TIMESTAMPTZ DEFAULT NOW(),
  last_sent_at       TIMESTAMPTZ,
  UNIQUE(email, channel_id)
);

CREATE INDEX idx_subscriptions_email ON subscriptions(email);

-- ─────────────────────────────────────────
-- NEWSLETTER ISSUES (audit trail)
-- ─────────────────────────────────────────
CREATE TABLE newsletter_issues (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id     UUID REFERENCES channels(id),
  issue_date     DATE NOT NULL,
  article_count  INT,
  recipient_count INT,
  sent_at        TIMESTAMPTZ,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(channel_id, issue_date)
);
```

---

## 6. Tech Stack — Free Tier Breakdown

| Component | Tool | Free Tier Limit | Notes |
|-----------|------|-----------------|-------|
| **Database** | Supabase | 500MB, 50k API calls/mo | PostgreSQL; also provides REST API |
| **Crawler host** | GitHub Actions | 2,000 min/mo (public repo) | Cron job, ~10–20 min/run |
| **Frontend host** | Vercel | Unlimited for hobby projects | Next.js 14 App Router |
| **AI (summarize/classify)** | Groq API | 14,400 requests/day (free) | Llama 3.1-8b-instant |
| **Translation** | LibreTranslate | Self-hosted OR libre.translate.de | Open-source, no key needed |
| **Email sending** | Resend | 3,000 emails/mo, 100/day | Generous free tier; HTML emails |
| **Secrets storage** | GitHub Secrets | Free | API keys stored here |
| **Domain** | Vercel subdomain | Free | yourproject.vercel.app |

### When you outgrow free tier

- **More emails:** Brevo (300/day free), or Mailgun (1,000/mo free)
- **More AI calls:** Switch to Groq paid ($0.05/1M tokens) or add Hugging Face Inference API as backup
- **More DB:** Supabase paid ($25/mo) or migrate to Neon (10GB free)
- **Custom domain:** ~$10/year via Cloudflare Registrar

---

## 7. Phase-by-Phase Implementation

### Phase 0 — Account Setup (Day 1, ~2 hours)

Register all required free accounts:

1. **GitHub** — create a repo `music-news-crawler` (public, for free Actions minutes)
2. **Supabase** — create project, note: URL + anon key + service key
3. **Groq** — sign up at console.groq.com, generate API key
4. **Resend** — sign up at resend.com, verify your sending domain (or use `onboarding@resend.dev` for testing)
5. **Vercel** — sign up, connect GitHub account
6. **LibreTranslate** — either use `https://libretranslate.com` (free with key) or deploy self-hosted instance on Render.com free tier

Store all keys as GitHub Secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GROQ_API_KEY`, `RESEND_API_KEY`, `LIBRETRANSLATE_URL`, `LIBRETRANSLATE_KEY`.

---

### Phase 1 — Database & Seed Data (Days 2–3, ~4 hours)

1. Run the SQL schema above in Supabase SQL editor
2. Create a seed script (`seed/sources.py`) to insert all 150 sources
3. Create a seed script (`seed/channels.py`) to insert all 14 channels
4. Write a validation script (`scripts/validate_rss.py`) that:
   - Iterates over all sources
   - Tries to parse each RSS URL with `feedparser`
   - Tries to fetch the HTML homepage as fallback
   - Outputs a report: `✓ OK | ✗ DEAD | ~ NO_RSS` per source
   - Updates the `is_active` and `rss_url` fields accordingly
5. Run validation — expect ~80–100% success rate; manually fix failed sources

**Deliverable:** All 150 sources in DB with validated RSS URLs.

---

### Phase 2 — Crawler (Days 4–6, ~8 hours)

Build `crawler/main.py`:

```
crawler/
  main.py          # entry point
  rss_fetcher.py   # feedparser-based RSS reader
  html_fetcher.py  # httpx + trafilatura for non-RSS sites
  dedup.py         # URL hash deduplication against Supabase
  cleaner.py       # text normalization (strip HTML, fix encoding)
  models.py        # dataclasses: RawArticle, CleanArticle
```

**RSS Fetcher logic:**
- Fetch feed → parse entries → extract: title, url, published_date, author, summary, image
- Use `trafilatura.fetch_url()` on article URL to get clean full text
- Rate limit: 1 request/second per domain

**HTML Fetcher logic (fallback):**
- For sites without RSS, scrape article list page
- Use CSS selectors defined per-source in a `selectors.json` config file
- Extract article URLs, then use `trafilatura` on each

**Deduplication:**
- Before processing, compute `sha256(url)` and query `articles.url_hash`
- Skip if already exists

**Run locally first:** `python crawler/main.py --sources 5 --dry-run`

**GitHub Actions workflow** (`.github/workflows/daily_crawl.yml`):
```yaml
name: Daily Crawl
on:
  schedule:
    - cron: '0 6 * * *'   # 6am UTC daily
  workflow_dispatch:        # manual trigger for testing
jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: python crawler/main.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          LIBRETRANSLATE_URL: ${{ secrets.LIBRETRANSLATE_URL }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
```

---

### Phase 3 — AI Pipeline (Days 7–9, ~8 hours)

Build `ai/pipeline.py`:

```
ai/
  pipeline.py       # orchestrator: summarize → classify → translate
  summarizer.py     # Groq: 3-sentence English summary
  classifier.py     # Groq: genre tags + content type
  translator.py     # LibreTranslate: EN → ro/fr/de/it/es
  prompts.py        # all prompt templates
```

**Groq Prompt — Summary + Classification (single call):**
```
You are a music journalism analyst. Given the article text below, return a JSON object with:
- "summary": a 3-sentence summary of the article in English, factual and neutral
- "genres": an array of genre tags from this list: [indie, rock, metal, jazz, electronic, techno, underground, hip-hop, folk, classical, pop, experimental, punk]. Include 1-3 tags max.
- "content_type": one of [album-review, track-premiere, new-release, interview, news, live, list, obituary, feature]
- "sentiment": one of [positive, neutral, negative]

Article title: {title}
Article text: {text[:3000]}

Return only valid JSON.
```

**Translation:**
- POST to LibreTranslate API: `{ "q": summary_en, "source": "en", "target": "ro" }`
- Translate title + summary for each non-EN language
- Batch: translate all 5 languages sequentially, ~0.5s each

**Rate limiting:**
- Groq free: 14,400 req/day → safe for up to ~200 articles/day
- LibreTranslate: self-hosted = unlimited; public API = ~1 req/sec

---

### Phase 4 — Newsletter Engine (Days 10–12, ~8 hours)

Build `newsletter/builder.py` and `newsletter/sender.py`:

```
newsletter/
  builder.py        # query articles, build per-subscriber email content
  template.html     # Jinja2 HTML email template
  sender.py         # Resend API calls
  scheduler.py      # entry point, runs after crawler
```

**Builder logic:**
1. For each active channel, query articles from last 24h matching the channel's genre/content filters
2. Sort by published_at DESC, take top 15
3. For each active subscription on that channel:
   - Get subscriber's preferred_language
   - For each article, fetch the translated summary in that language (fallback: EN)
   - Render HTML email from Jinja2 template
4. Pass rendered emails to sender

**Email template structure:**
```html
Subject: [Channel Name] — Daily Digest · {date}

Header: channel name + logo
─────────────────────────────
For each article:
  📰 [Article Title] (linked to original URL)
  🔤 Summary in user's chosen language (3 sentences)
  🏷️  Genre tags  |  📅  Published date  |  🌐  Source name
  [Read Original Article →]
─────────────────────────────
Footer:
  "You're subscribed to {channel} in {language}."
  "Unsubscribe" (uses unique token: /unsubscribe?token=xxx)
```

**Sender:**
- Uses Resend Python SDK
- Sends in batches of 10 (to stay well under rate limits)
- Records sent newsletters in `newsletter_issues` table

---

### Phase 5 — Frontend Website (Days 13–18, ~12 hours)

**Stack:** Next.js 14 App Router + Tailwind CSS + Supabase JS client

```
app/
  page.tsx                  # Landing page
  channels/
    page.tsx                # All channels grid
    [slug]/
      page.tsx              # Channel detail (latest 20 articles)
  subscribe/
    page.tsx                # Subscription form
  unsubscribe/
    page.tsx                # Unsubscribe confirmation
  api/
    subscribe/route.ts      # POST: create subscription
    unsubscribe/route.ts    # POST: deactivate subscription
```

**Landing page content:**
- Brief description of the platform
- Featured channels grid (3-4 highlighted channels)
- CTA: "Browse all channels →" and "Subscribe to a newsletter →"
- Stats: number of sources, languages, articles indexed

**Channel list page (`/channels`):**
- Grid of all 14 channel cards
- Each card: icon, name, description, genre tags, subscriber count (public)
- Filter by genre tag
- Click → channel detail page

**Channel detail page (`/channels/[slug]`):**
- Latest 20 articles in the channel
- Each article: title (linked), source name, published date, summary (in EN by default)
- Language switcher for summary preview (dropdown: EN/RO/FR/DE/IT/ES)
- "Subscribe to this channel" button → opens subscribe modal

**Subscribe flow:**
1. User clicks subscribe on a channel page (or goes to /subscribe)
2. Form: email address + language preference (dropdown) + channel checkboxes (multi-select)
3. Submit → POST /api/subscribe → inserts into `subscriptions` table
4. Success message: "You'll receive your first digest tomorrow morning!"
5. No email confirmation needed (keep it simple)

**Unsubscribe:**
- One-click link in every email: `/unsubscribe?token=xxx`
- Sets `subscriptions.is_active = false`
- Shows friendly confirmation page

**Deploy to Vercel:**
```bash
vercel deploy
# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
```

---

### Phase 6 — Integration & Testing (Days 19–21, ~6 hours)

1. **End-to-end test:** trigger crawler manually via GitHub Actions `workflow_dispatch`
2. **Check DB:** verify articles are being stored with correct genre tags
3. **Translation check:** manually inspect translations for 5 articles in each language
4. **Newsletter dry run:** use Resend test mode, inspect rendered emails
5. **Frontend review:** test subscription flow, channel browsing, unsubscribe
6. **Fix edge cases:**
   - Articles with no image
   - Very short articles (< 200 words) — skip summarization, use raw text
   - Paywalled articles — detect (< 300 chars extracted) and flag as `is_paywalled`
   - Duplicate articles from multiple sources — use URL hash dedup + title similarity

---

### Phase 7 — Hardening & Monitoring (Days 22–25, ~6 hours)

1. **Error alerting:** email yourself on crawler failure (Resend + GitHub Actions on-failure step)
2. **Source health monitoring:** if a source fails 3 days in a row, set `is_active = false` and alert
3. **Translation quality:** add language detection on translated output; re-translate if wrong language detected
4. **Groq fallback:** if Groq rate limit hit, fall back to a simple extractive summarizer (`sumy` Python library)
5. **LibreTranslate fallback:** if self-hosted instance is down, fallback to `argostranslate` (offline Python library)
6. **Supabase RLS:** enable Row Level Security — subscriptions table read-protected; only service key can write
7. **Vercel Analytics:** enable free analytics to see channel page traffic

---

## 8. AI Pipeline Detail

### Groq Model Selection

Use `llama-3.1-8b-instant` for speed and quota efficiency:
- ~200 tokens input (article text truncated to 3000 chars)
- ~150 tokens output (JSON with summary + tags)
- Speed: ~0.3s per article
- Cost: free up to 14,400 req/day

For long-form features (> 5000 words), use `llama-3.1-70b-versatile` (slower but more accurate).

### Prompt Engineering Tips

**Summary quality:** Instruct the model to write summaries in present tense, avoid spoilers for reviews, and not start with "This article...".

**Genre classification:** Provide few-shot examples in the prompt for ambiguous genres (e.g., post-rock = `rock` + `experimental`).

**Fallback:** If Groq returns malformed JSON, use `json.loads()` with a try/except. On failure, retry once with temperature=0. On second failure, store article without AI tags and flag for manual review.

---

## 9. Newsletter Engine Detail

### Email Frequency Logic

- Run newsletter builder at 6:30am UTC (30 min after crawler finishes)
- Query: `WHERE crawled_at >= NOW() - INTERVAL '24 hours'`
- If a channel has < 3 new articles, skip that day's digest for that channel (avoid empty/thin emails)
- Track per-subscriber: `last_sent_at` — don't send twice in same day

### Personalization

Even though there's no login, each subscriber gets:
- Their chosen language for summaries (translated)
- Only articles matching their subscribed channels
- Their unique unsubscribe token in every email

### HTML Email Template Notes

- Use inline CSS (email clients strip `<style>` blocks)
- Max-width: 600px for compatibility
- Always include a plain-text fallback version
- Test across Gmail, Outlook, Apple Mail using Resend's email preview

---

## 10. Frontend / Channel Website Detail

### URL Structure

```
/                         Landing page
/channels                 All channels
/channels/metal-daily     Metal Daily channel page
/channels/jazz-notes      Jazz Notes channel page
/subscribe                Subscribe form
/unsubscribe              Unsubscribe (via token query param)
```

### Multilingual Summary Preview on Channel Pages

Channel pages show article summaries in the user's browser language by default (via `navigator.language`). Users can override with a language switcher dropdown. This is purely frontend — translations are already in the DB.

### SEO

Each channel page is server-side rendered (Next.js SSR) with:
- `<title>Metal Daily — Latest Metal News</title>`
- `<meta description>` with channel description
- OpenGraph tags
- Sitemap generated via `next-sitemap`

### Making It Look Good (Free UI Components)

- Use **shadcn/ui** components (free, Tailwind-based)
- Dark mode toggle
- Channel cards with genre tag pills
- Article cards with image thumbnails (use `next/image` for optimization)

---

## 11. Cost Summary

| Service | Monthly Cost |
|---------|-------------|
| Supabase | **$0** (free tier: 500MB, 50K requests) |
| GitHub Actions | **$0** (public repo, ~20 min/run × 30 runs = 600 min) |
| Vercel | **$0** (hobby plan) |
| Groq API | **$0** (free tier: 14,400 req/day) |
| LibreTranslate | **$0** (self-hosted on Render free tier) |
| Resend | **$0** (3,000 emails/mo free) |
| **Total** | **$0/month** |

**Scale limits before costs kick in:**
- Emails: up to ~3,000 newsletter sends/month free (e.g. 100 subscribers across all channels)
- Articles: up to ~200 new articles/day processable within Groq free limits
- DB: ~500MB covers roughly 500K articles with summaries

---

## Appendix A — Repository Structure

```
music-news-crawler/
├── .github/
│   └── workflows/
│       └── daily_crawl.yml
├── crawler/
│   ├── main.py
│   ├── rss_fetcher.py
│   ├── html_fetcher.py
│   ├── dedup.py
│   └── cleaner.py
├── ai/
│   ├── pipeline.py
│   ├── summarizer.py
│   ├── classifier.py
│   ├── translator.py
│   └── prompts.py
├── newsletter/
│   ├── builder.py
│   ├── sender.py
│   └── template.html
├── seed/
│   ├── sources.py
│   └── channels.py
├── scripts/
│   └── validate_rss.py
├── frontend/              ← Next.js app (deploy separately on Vercel)
│   ├── app/
│   ├── components/
│   └── package.json
├── requirements.txt
└── README.md
```

---

## Appendix B — Python Dependencies

```txt
# requirements.txt
feedparser==6.0.11
httpx==0.27.0
trafilatura==1.12.0
supabase==2.4.0
groq==0.11.0
jinja2==3.1.4
resend==2.0.0
python-dotenv==1.0.1
argostranslate==1.9.6    # offline translation fallback
sumy==0.11.0             # extractive summarization fallback
hashlib                  # stdlib, for URL dedup
```

---

*End of plan. Total estimated implementation time: 3–4 weeks of part-time work.*
*All services run entirely on free tiers. Zero monthly cost.*
