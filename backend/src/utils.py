import re
import unicodedata
from langdetect import detect
import argostranslate.package
import argostranslate.translate


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text or not isinstance(text, str):
        return ""
    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,!?;:\'\"-]', '', text)
    return text

def detect_language(text: str) -> str:
    """Detect language — fallback to English if uncertain."""
    try:
        # Short text is unreliable, default to English
        if len(text.split()) < 6:
            return "en"
        lang = detect(text)
        # If detected language is unexpected, fallback to English
        SUPPORTED = {"en", "ur", "ar", "fr", "de", "es", "zh", "hi"}
        return lang if lang in SUPPORTED else "en"
    except Exception:
        return "en"

def translate_to_english(text: str, source_lang: str = "en") -> str:
    if source_lang == "en":
        return text
    try:
        return argostranslate.translate.translate(text, source_lang, "en")
    except Exception:
        return text

def translate_from_english(text: str, target_lang: str = "en") -> str:
    if target_lang == "en":
        return text
    try:
        return argostranslate.translate.translate(text, "en", target_lang)
    except Exception:
        return text

def truncate_text(text: str, max_length: int = 512) -> str:
    """Truncate text to max token-safe length."""
    words = text.split()
    if len(words) > max_length:
        return " ".join(words[:max_length]) + "..."
    return text