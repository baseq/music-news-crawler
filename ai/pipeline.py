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


async def process_article(article: CleanArticle) -> dict:
    """
    Async wrapper around the synchronous AI pipeline.
    Returns a dict suitable for save_article().
    """
    loop = asyncio.get_event_loop()

    # Summarize + classify — serialised through semaphore to respect Groq rate limits
    async with _groq_sem:
        ai = await loop.run_in_executor(
            _executor,
            analyze_article,
            article.title,
            article.clean_text,
        )
        # Groq free tier: 6,000 tokens/min; each call uses ~1,100 tokens
        # → max ~5 calls/min → need ≥12 s between calls to stay under budget
        await asyncio.sleep(13)

    summary_en = ai.get("summary") or ""
    if not summary_en:
        logger.warning(f"No summary generated for: {article.title[:60]}")

    return {
        "summary":       summary_en,
        "genres":        ai.get("genres", []),
        "content_type":  ai.get("content_type", "news"),
        "sentiment":     ai.get("sentiment", "neutral"),
        "translations":  {},
        "error":         ai.get("error"),
        "used_fallback": ai.get("used_fallback", False),
    }
