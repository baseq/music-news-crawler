"""
Translation via LibreTranslate API.
Falls back to argostranslate (offline) if the API is unreachable.
"""
import logging
import os
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

LIBRETRANSLATE_URL = os.environ.get("LIBRETRANSLATE_URL", "https://libretranslate.com")
LIBRETRANSLATE_KEY = os.environ.get("LIBRETRANSLATE_KEY", "")

TARGET_LANGUAGES = ["ro", "fr", "de", "it", "es"]  # EN is always the source


def _api_translate(text: str, source: str, target: str) -> Optional[str]:
    """Call LibreTranslate HTTP API."""
    payload = {"q": text, "source": source, "target": target, "format": "text"}
    if LIBRETRANSLATE_KEY:
        payload["api_key"] = LIBRETRANSLATE_KEY

    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(f"{LIBRETRANSLATE_URL}/translate", json=payload)
            if r.status_code == 200:
                return r.json().get("translatedText")
            logger.warning(f"LibreTranslate HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.warning(f"LibreTranslate API error ({target}): {e}")
    return None


def _offline_translate(text: str, source: str, target: str) -> Optional[str]:
    """Argostranslate offline fallback."""
    try:
        import argostranslate.package
        import argostranslate.translate

        installed = argostranslate.translate.get_installed_languages()
        src_lang = next((l for l in installed if l.code == source), None)
        tgt_lang = next((l for l in installed if l.code == target), None)

        if not src_lang or not tgt_lang:
            # Auto-install missing language pair
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()
            pkg = next(
                (p for p in available if p.from_code == source and p.to_code == target),
                None,
            )
            if pkg:
                argostranslate.package.install_from_path(pkg.download())
                installed = argostranslate.translate.get_installed_languages()
                src_lang = next((l for l in installed if l.code == source), None)
                tgt_lang = next((l for l in installed if l.code == target), None)

        if src_lang and tgt_lang:
            translation = src_lang.get_translation(tgt_lang)
            if translation:
                return translation.translate(text)
    except Exception as e:
        logger.error(f"Argostranslate fallback failed ({source}→{target}): {e}")
    return None


def translate_text(text: str, target: str, source: str = "en") -> Optional[str]:
    """Translate text from source to target language."""
    if source == target or not text.strip():
        return text

    # Try API first
    result = _api_translate(text, source, target)
    if result:
        return result

    # Offline fallback
    logger.info(f"Falling back to offline translation ({source}→{target})")
    return _offline_translate(text, source, target)


def translate_article_summary(
    summary_en: str,
    title_en: str,
    source_language: str = "en",
) -> dict[str, dict]:
    """
    Translate the English summary + title into all 5 non-English target languages.

    If the article's source language is not English, we still translate FROM
    English since the summary_en was generated in English by Groq.

    Returns: {lang_code: {"title": ..., "summary": ...}}
    """
    results = {}
    for lang in TARGET_LANGUAGES:
        summary_translated = translate_text(summary_en, target=lang, source="en")
        title_translated   = translate_text(title_en, target=lang, source="en")
        if summary_translated or title_translated:
            results[lang] = {
                "summary": summary_translated,
                "title": title_translated,
            }
            logger.debug(f"  Translated to {lang}: {(summary_translated or '')[:60]}")
        else:
            logger.debug(f"  Translation skipped for {lang} (no result from any provider)")
    return results
