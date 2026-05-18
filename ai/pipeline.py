"""
AI pipeline orchestrator.

For each CleanArticle:
  1. Summarize + classify (Groq)
  2. Translate summary + title into 5 languages (LibreTranslate)
  3. Return combined result dict
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from crawler.models import CleanArticle
from ai.summarizer import analyze_article
from ai.translator import translate_article_summary

logger = logging.getLogger(__name__)

# Run blocking Groq + LibreTranslate calls in a thread pool
_executor = ThreadPoolExecutor(max_workers=4)


async def process_article(article: CleanArticle) -> dict:
    """
    Async wrapper around the synchronous AI pipeline.
    Returns a dict suitable for save_article().
    """
    loop = asyncio.get_event_loop()

    # Step 1 — Summarize + classify (blocking call → thread)
    ai = await loop.run_in_executor(
        _executor,
        analyze_article,
        article.title,
        article.clean_text,
    )

    summary_en = ai.get("summary") or ""

    # Step 2 — Translate (only if we have a summary)
    translations = {}
    if summary_en:
        translations = await loop.run_in_executor(
            _executor,
            translate_article_summary,
            summary_en,
            article.title,
            article.source_language,
        )
    else:
        logger.warning(f"No summary generated for: {article.title[:60]}")

    return {
        "summary":      summary_en,
        "genres":       ai.get("genres", []),
        "content_type": ai.get("content_type", "news"),
        "sentiment":    ai.get("sentiment", "neutral"),
        "translations": translations,
        "error":        ai.get("error"),
        "used_fallback": ai.get("used_fallback", False),
    }
