# Music Digest — Setup & Deploy Guide

> Daily music news across 150 sources, 6 languages, 14 channels. **Total cost: $0/month.**

---

## Architecture

```
GitHub Actions (daily cron)
  └─ crawler/main.py        → fetches 150 sources, extracts text
  └─ ai/pipeline.py         → Groq summarises + classifies + translates
  └─ newsletter/sender.py   → Resend delivers daily digests

Supabase                    → PostgreSQL database + REST API

Vercel (Next.js)            → Channel website + subscribe/unsubscribe pages
```

---

## Step 1 — Create free accounts

| Service | URL | What you need |
|---------|-----|---------------|
| **GitHub** | github.com | Create a public repo (free Actions minutes) |
| **Supabase** | supabase.com | Create a project; note URL + anon key + service key |
| **Groq** | console.groq.com | Sign up; create API key |
| **LibreTranslate** | libretranslate.com | Sign up for free API key (or self-host — see below) |
| **Resend** | resend.com | Sign up; verify a sending domain (or use onboarding@resend.dev for testing) |
| **Vercel** | vercel.com | Sign up; connect your GitHub account |

---

## Step 2 — Set up the database

1. Open your Supabase project → **SQL Editor**
2. Paste the contents of `schema.sql` and click **Run**
3. Verify the tables were created: Tables → you should see `sources`, `articles`, `channels`, `subscriptions`, `article_translations`, `newsletter_issues`

---

## Step 3 — Add GitHub Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add each of these:

| Secret name | Where to find it |
|------------|-----------------|
| `SUPABASE_URL` | Supabase → Project Settings → API |
| `SUPABASE_SERVICE_KEY` | Supabase → Project Settings → API → service_role key |
| `GROQ_API_KEY` | console.groq.com → API Keys |
| `LIBRETRANSLATE_URL` | `https://libretranslate.com` (or your self-hosted URL) |
| `LIBRETRANSLATE_KEY` | libretranslate.com → Account |
| `RESEND_API_KEY` | resend.com → API Keys |
| `RESEND_FROM_EMAIL` | e.g. `digest@yourdomain.com` (must be verified in Resend) |
| `RESEND_FROM_NAME` | `Music Digest` |
| `APP_BASE_URL` | Your Vercel URL e.g. `https://music-digest.vercel.app` |
| `ALERT_EMAIL` | Your personal email for failure alerts |

---

## Step 4 — Seed the database

```bash
# Install Python deps
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and fill in your env file
cp .env.example .env
# Edit .env with your Supabase URL and service key

# Seed sources (150 music news sites)
python seed/sources.py

# Seed channels (14 channels)
python seed/channels.py
```

---

## Step 5 — Validate sources

```bash
# Check which sources have working RSS feeds
python scripts/validate_rss.py --seed-only

# After seeding the DB, validate from DB and update active flags:
python scripts/validate_rss.py --update-db
```

This generates a `crawl_report_YYYYMMDD_HHMM.txt` file. Sources with ✗ will be disabled automatically if you pass `--update-db`. Sources with `~ NO_RSS` will use the HTML scraper — add their CSS selectors to `crawler/selectors.json`.

---

## Step 6 — Test the crawler locally

```bash
# Dry run — no DB writes, no emails
python crawler/main.py --dry-run --lang en

# Real run on English sources only
python crawler/main.py --lang en

# Full run (all languages)
python crawler/main.py
```

---

## Step 7 — Test the newsletter

```bash
# Send a test newsletter (make sure you've subscribed via the website first)
python newsletter/sender.py

# Or dry run (no actual emails)
DRY_RUN=true python newsletter/sender.py
```

---

## Step 8 — Deploy the frontend to Vercel

```bash
cd frontend
npm install

# Test locally first
cp .env.local.example .env.local
# Fill in NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY

npm run dev   # → http://localhost:3000
```

**Deploy to Vercel:**

1. Push your repo to GitHub
2. Go to vercel.com → New Project → Import your repo
3. Set **Root Directory** to `frontend`
4. Add environment variables in Vercel dashboard:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_KEY`
5. Click Deploy

---

## Step 9 — Trigger the first crawl

Go to your GitHub repo → **Actions → Daily Music News Crawl → Run workflow**

Set `dry_run` to `false` and click **Run workflow**.

Watch the logs. After the first successful run you should see articles in your Supabase `articles` table.

---

## Self-hosting LibreTranslate (optional, fully free)

If you want to avoid rate limits on the public LibreTranslate API, deploy your own instance on Render.com:

1. Create a new **Web Service** on Render
2. Use this Docker image: `libretranslate/libretranslate`
3. Free tier — note the instance spins down after 15 min of inactivity (the first translation after sleep takes ~30s)
4. Set `LIBRETRANSLATE_URL` to your Render URL (no key needed for self-hosted)

---

## Daily schedule

| Time (UTC) | Event |
|-----------|-------|
| 06:00 | GitHub Actions starts — crawler fetches all 150 sources |
| ~06:20 | AI pipeline finishes (Groq summarisation + LibreTranslate) |
| ~06:30 | Newsletter builder runs — sends digests via Resend |

---

## Useful commands

```bash
# Validate all sources and update DB
python scripts/validate_rss.py --update-db

# Crawl a single source by UUID
python crawler/main.py --source-id <uuid>

# Crawl only Romanian sources
python crawler/main.py --lang ro

# Re-seed channels after changes
python seed/channels.py
```

---

## Free tier limits

| Service | Limit | At risk when |
|---------|-------|-------------|
| Supabase | 500MB DB | ~500K articles |
| GitHub Actions | 2,000 min/mo | ~100 sources × 20min = covered |
| Groq | 14,400 req/day | >200 new articles/day |
| Resend | 3,000 emails/mo | >100 active subscribers |
| Vercel | Unlimited (hobby) | Never |

---

## Project structure

```
music-news-crawler/
├── .github/workflows/daily_crawl.yml   ← GitHub Actions cron
├── crawler/                            ← RSS + HTML fetcher
│   ├── main.py
│   ├── rss_fetcher.py
│   ├── html_fetcher.py
│   ├── selectors.json                  ← per-site CSS selectors
│   ├── cleaner.py
│   ├── dedup.py
│   └── models.py
├── ai/                                 ← Groq + LibreTranslate
│   ├── pipeline.py
│   ├── summarizer.py
│   ├── translator.py
│   └── prompts.py
├── newsletter/                         ← builder + Resend sender
│   ├── builder.py
│   ├── sender.py
│   └── template.html
├── seed/                               ← one-time DB population
│   ├── sources.py                      ← 150 music news sites
│   └── channels.py                     ← 14 channels
├── scripts/
│   └── validate_rss.py                 ← source health checker
├── frontend/                           ← Next.js app (deploy on Vercel)
│   └── src/app/
│       ├── page.tsx                    ← landing page
│       ├── channels/page.tsx           ← all channels
│       ├── channels/[slug]/page.tsx    ← channel detail
│       ├── subscribe/page.tsx          ← subscription form
│       ├── unsubscribe/page.tsx        ← opt-out
│       └── api/subscribe|unsubscribe/  ← API routes
├── schema.sql                          ← run in Supabase SQL editor
├── requirements.txt
└── .env.example
```
