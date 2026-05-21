"""
AI pipeline orchestrator.

For each CleanArticle:
  1. Summarize + classify (Groq)
  2. Return result dict
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from crawler.models import CleanArticle
from ai.summarizer import analyze_article

logger = logging.getLogger(__name__)

# Single-threaded executor keeps Groq calls sequential and within free-tier
# rate limits (~30 req/min). Increase to 2 only if you have a paid Groq plan.
_executor = ThreadPoolExecutor(max_workers=1)

# Semaphore prevents any concurrent Groq calls even if the executor is shared
_groq_sem = asyncio.Semaphore(1)


async def process_article(article: CleanArticle, source_language: str = "en") -> dict:
    """
    Async wrapper around the synchronous AI pipeline.
    Returns a dict suitable for save_article().
    source_language: ISO code of the article's original language (e.g. "it", "fr").
    The summary is generated in that language and stored in translations so the
    newsletter can serve each article in its original tongue.
    """
    loop = asyncio.get_event_loop()

    # Summarize + classify — serialised through semaphore to respect Groq rate limits
    async with _groq_sem:
        ai = await loop.run_in_executor(
            _executor,
            analyze_article,
            article.title,
            article.clean_text,
            source_language,
        )
        # Groq free tier: 6,000 tokens/min; each call uses ~1,100 tokens
        # → max ~5 calls/min → need ≥12 s between calls to stay under budget
        await asyncio.sleep(13)

    summary = ai.get("summary") or ""
    if not summary:
        logger.warning(f"No summary generated for: {article.title[:60]}")

    # summary_en always holds an English summary for the frontend preview.
    # For non-English sources the original-language summary is also stored
    # in article_translations so the newsletter can use it directly.
    translations = {}
    if source_language != "en" and summary:
        translations[source_language] = {"summary": summary, "title": None}

    return {
        "summary":       summary,   # stored in summary_en (used as preview/fallback)
        "genres":        ai.get("genres", []),
        "content_type":  ai.get("content_type", "news"),
        "sentiment":     ai.get("sentiment", "neutral"),
        "translations":  translations,
        "error":         ai.get("error"),
        "used_fallback": ai.get("used_fallback", False),
    }
