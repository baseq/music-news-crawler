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

from ai.prompts import ANALYZE_PROMPT, EXTRACTIVE_FALLBACK_SENTENCES, LANG_NAMES

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
def _extract_json(raw: str) -> dict:
    """Try increasingly lenient strategies to get a dict out of a Groq response."""
    # 1. Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. Extract first {...} block (handles leading/trailing text)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    # 3. Replace any unescaped double quotes inside string values (heuristic)
    cleaned = re.sub(r'(?<=[:{,\[])\s*"(.*?)"(?=\s*[,}\]])',
                     lambda mo: '"' + mo.group(1).replace('"', "'") + '"',
                     raw, flags=re.DOTALL)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    raise json.JSONDecodeError("All parse strategies failed", raw, 0)


def _call_groq(title: str, text: str, language: str = "en") -> dict:
    safe_title = title.replace('"', "'")
    lang_name  = LANG_NAMES.get(language, "English")
    prompt = (
        ANALYZE_PROMPT
        .replace("{language_name}", lang_name)
        .replace("{title}", safe_title)
        .replace("{text}", text[:3500])
    )
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

    return _extract_json(raw)


def _extractive_fallback(text: str) -> str:
    """Extractive summary: first 3 sentences of the article text."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(s for s in sentences[:3] if s)


def analyze_article(title: str, text: str, language: str = "en") -> dict:
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
        data = _call_groq(title, text, language)
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
