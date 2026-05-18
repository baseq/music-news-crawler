"""All Groq prompt templates."""

GENRES = [
    "indie", "rock", "metal", "jazz", "electronic", "techno",
    "underground", "hip-hop", "folk", "classical", "pop",
    "experimental", "punk",
]

CONTENT_TYPES = [
    "album-review", "track-premiere", "new-release", "interview",
    "news", "live", "list", "obituary", "feature",
]

SENTIMENTS = ["positive", "neutral", "negative"]


ANALYZE_PROMPT = """\
You are a concise music journalism analyst. Analyze the article below and return a JSON object.

Rules:
- "summary": exactly 3 sentences in English. Present tense. Factual and neutral. Do not start with "This article".
- "genres": 1-3 tags from this exact list: {genres}. Choose only what clearly applies.
- "content_type": exactly one from: {content_types}
- "sentiment": one of: {sentiments}

Article title: {title}

Article text (may be truncated):
{text}

Return ONLY valid JSON. No explanation. No markdown. Example:
{{"summary":"...", "genres":["metal","underground"], "content_type":"album-review", "sentiment":"positive"}}
""".format(
    genres=", ".join(GENRES),
    content_types=", ".join(CONTENT_TYPES),
    sentiments=", ".join(SENTIMENTS),
    title="{title}",
    text="{text}",
)


EXTRACTIVE_FALLBACK_SENTENCES = 3   # for sumy fallback
