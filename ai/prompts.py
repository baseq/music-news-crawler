"""All Groq prompt templates."""

TOPICS = [
    "geopolitics", "tech", "economy", "science", "health",
    "environment", "society", "defense", "energy", "finance",
    "startups", "ai", "romania",
]

CONTENT_TYPES = [
    "breaking-news", "analysis", "opinion", "report",
    "interview", "feature", "explainer", "data",
]

SENTIMENTS = ["positive", "neutral", "negative"]

LANG_NAMES = {
    "en": "English",
    "ro": "Romanian",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "es": "Spanish",
}


ANALYZE_PROMPT = """\
You are a concise news analyst. Analyze the article below and return a JSON object.

Rules:
- "summary": exactly 3 sentences in {language_name}. Present tense. Factual and neutral. Do not start with "This article".
- "topics": 1-4 tags from this exact list: {topics}. Choose only what clearly applies. Always include "romania" if the article is specifically about Romania or Romanian entities.
- "content_type": exactly one from: {content_types}
- "sentiment": one of: {sentiments}

Article title: {{title}}

Article text (may be truncated):
{{text}}

Return ONLY valid JSON. No explanation. No markdown. Example:
{{"summary":"...", "topics":["geopolitics","defense"], "content_type":"analysis", "sentiment":"neutral"}}
""".format(
    topics=", ".join(TOPICS),
    content_types=", ".join(CONTENT_TYPES),
    sentiments=", ".join(SENTIMENTS),
    language_name="{language_name}",   # filled at call time
)


EXTRACTIVE_FALLBACK_SENTENCES = 3
