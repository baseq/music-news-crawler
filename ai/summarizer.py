"""
Article summarizer + classifier using Groq (Llama 3.1-8b-instant).
Falls back to extractive summarization (sumy) if Groq is rate-limited.
"""
import json
import logging
import os
import re
from typing import Optional

from groq import Groq, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ai.prompts import ANALYZE_PROMPT, EXTRACTIVE_FALLBACK_SENTENCES

logger = logging.getLogger(__name__)

_groq_client: Optional[Groq] = None

def get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _groq_client


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
)
def _call_groq(title: str, text: str) -> dict:
    prompt = ANALYZE_PROMPT.format(title=title, text=text[:3500])
    response = get_groq().chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=400,
    )
    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


def _extractive_fallback(text: str) -> str:
    """Extractive summary using sumy (no API needed)."""
    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        sentences = summarizer(parser.document, EXTRACTIVE_FALLBACK_SENTENCES)
        return " ".join(str(s) for s in sentences)
    except Exception as e:
        logger.warning(f"Extractive fallback failed: {e}")
        # Last resort: first N sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return " ".join(sentences[:3])


def analyze_article(title: str, text: str) -> dict:
    """
    Returns:
      {
        "summary": str,
        "genres": list[str],
        "content_type": str,
        "sentiment": str,
        "error": str | None,
        "used_fallback": bool,
      }
    """
    result = {
        "summary": None,
        "genres": [],
        "content_type": "news",
        "sentiment": "neutral",
        "error": None,
        "used_fallback": False,
    }

    try:
        data = _call_groq(title, text)
        result["summary"]      = data.get("summary") or ""
        result["genres"]       = data.get("genres") or []
        result["content_type"] = data.get("content_type") or "news"
        result["sentiment"]    = data.get("sentiment") or "neutral"
    except RateLimitError:
        logger.warning(f"Groq rate limit hit for '{title[:50]}' — using extractive fallback")
        result["summary"]      = _extractive_fallback(text)
        result["used_fallback"] = True
    except json.JSONDecodeError as e:
        logger.error(f"Groq JSON parse error for '{title[:50]}': {e}")
        result["summary"]      = _extractive_fallback(text)
        result["used_fallback"] = True
        result["error"]        = f"json_parse_error: {e}"
    except Exception as e:
        logger.error(f"Groq error for '{title[:50]}': {e}")
        result["error"] = str(e)

    return result
