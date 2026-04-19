# utils.py - Updated translation functions
import re
import unicodedata
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

from src.offline_translator import get_translator

# For consistent results
DetectorFactory.seed = 0

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

# Language code to full name mapping
LANGUAGE_NAMES = {
    "en": "en",
    "ur": "ur",
    "fr": "fr",
    "ar": "ar",
    "hi": "hi",
}

# Roman Urdu keywords for detection
ROMAN_URDU_KEYWORDS = {
    # Pronouns
    "kia", "hai", "ha", "hain", "haal", "ap", "aap", "tum", "main", "mein",
    "kaise", "kaisa", "kaisi", "theek", "thik", "accha", "acha", "nahi",
    "nahin", "haan", "han", "bhai", "yaar", "matlab", "kyu", "kyun", "kyon",
    "kab", "kahan", "kaun", "kon", "kuch", "sab", "bara", "bura", "aur",
    "lekin", "magar", "phir", "kal", "aaj", "abhi", "jab", "tab",
    "woh", "wo", "yeh", "ye", "iska", "uska", "mera", "tera", "humara",
    "tumhara", "unka", "mere", "tere", "dekho", "suno", "bolo", "jao",
    "jana", "ana", "khana", "peena", "rehna", "chalo", "chalein", "zaroor",
    "bilkul", "shayad", "lagta", "chahiye", "milna", "dost", "pyaar",
    "zindagi", "duniya", "waqt", "ghar", "kaam", "paise", "masla",
    "sahi", "galat", "mushkil", "asaan", "zyada", "thora", "bohot", "bahut",

    # ✅ NEW: Common verbs & conjugations
    "aya", "ayi", "aye", "gaya", "gayi", "gaye", "tha", "thi", "thy", "the",
    "kar", "karo", "karna", "karta", "karti", "karte", "karein", "kiya",
    "kiया", "raha", "rahi", "rahe", "hoga", "hogi", "honge", "ho",
    "ja", "jao", "jata", "jati", "jate", "aa", "aao", "aata", "aati",
    "de", "dena", "deta", "deti", "dete", "diya", "diया", "lo", "lena",
    "leta", "leti", "lete", "liya", "lia", "sun", "suno", "sunna",
    "dekh", "dekha", "dekhi", "socha", "sochi", "samjha", "samjho",
    "bata", "batao", "batana", "pata", "pta", "puch", "pucha", "pocha",

    # ✅ NEW: Common words in everyday sentences
    "laken", "lekin", "lakin", "magar", "par", "per", "pe", "se", "ko",
    "ka", "ki", "ke", "ne", "ni", "na", "nhi", "nai", "nay", "bhi", "hi",
    "to", "tou", "tau", "wala", "wali", "wale", "walay", "sala", "sali",
    "office", "ghar", "school", "hospital", "market", "baazar", "bazar",
    "din", "raat", "subah", "sham", "dopahar", "kal", "parso", "aj",
    "yahan", "wahan", "idhar", "udhar", "andar", "bahar", "upar", "neeche",
    "sath", "saath", "bagair", "bina", "tak", "tuk", "phir", "dobara",
    "abhi", "pehle", "baad", "jaldi", "dhire", "zyada", "kam", "sirf",
    "bas", "acha", "theek", "shukriya", "shukria", "meherbani", "please",
    "sorry", "maafi", "khuda", "allah", "inshallah", "mashallah",
    "yar", "bro", "ary", "are", "oye", "oi", "haye", "wah",

    # ✅ NEW: Sentence connectors & particles
    "ma", "mein", "mai", "may", "hy", "hwy", "sy", "ky", "ky", "py",
    "hn", "hna", "hny", "thy", "thi", "tha", "koi", "koe", "kuch",
    "sb", "sab", "hr", "har", "dosra", "doosra", "agla", "pichla",
}

ALLOWED_LANGUAGES = set(LANGUAGE_NAMES.keys())

# Remove these from ROMAN_URDU_KEYWORDS — they're too ambiguous:
AMBIGUOUS_REMOVE = {
    "are", "to", "ho", "per", "pe", "se", "hi", "na", "bhi", "bas",
    "ma", "may", "par", "please", "sorry", "bro", "aa", "de", "lo",
    "sun", "ja", "ko", "ka", "ki", "ke", "ne", "na", "the", "tha",
    "kar", "jo", "la", "le",
}

ROMAN_URDU_KEYWORDS = ROMAN_URDU_KEYWORDS - AMBIGUOUS_REMOVE

def is_roman_urdu(text: str) -> bool:
    words = text.lower().replace("?", "").replace("!", "").replace(".", "").split()
    match_count = sum(1 for word in words if word in ROMAN_URDU_KEYWORDS)
    return match_count / max(len(words), 1) >= 0.4  # raised from 0.3 → 0.4

def detect_language(text: str) -> str:
    """
    Detect language of text and return its code.
    Only allows: en, ur, fr, ar, hi
    Returns 'en' as default if language is not in allowed list.

    Args:
        text: The text to detect language for

    Returns:
        Language code: 'en', 'ur', 'fr', 'ar', or 'hi'
    """
    try:
        # Check for Roman Urdu first
        if is_roman_urdu(text):
            return LANGUAGE_NAMES["ur"]  # "ur"

        code = detect(text)

        # Return code only if it's in allowed languages, else default to 'en'
        if code in ALLOWED_LANGUAGES:
            return LANGUAGE_NAMES[code]
        else:
            return LANGUAGE_NAMES["en"]  # default to English

    except Exception:
        return LANGUAGE_NAMES["en"]  # default to English on error

def translate_to_english(text: str, source_lang: str = None) -> str: # type: ignore
    """
    Translate text to English.
    If source is already English or empty, return as-is.
    """
    if not text or not text.strip():
        return text
    
    # Auto-detect if not provided
    if not source_lang:
        source_lang = detect_language(text)
    else:
        source_lang = source_lang.lower()[:2]
    
    # Already English
    if source_lang == "en":
        return text
    
    print(f"[Translate] {source_lang} → en: '{text[:50]}...'")    
    translator = get_translator()
    result = translator.translate_to_english(text, source_lang)
    
    # If translation failed or returned same, keep original
    if not result or result == text:
        print(f"[Translate] Translation failed, keeping original")
        return text		 

    return result

def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translate English text to target language.
    If target is English or empty, return as-is.
    """
    if not text or not text.strip():
        return text
    
    # Normalize language code
    target_lang = target_lang.lower()[:2] if target_lang else "en"
    
    # Already English target - no translation needed
    if target_lang == "en":
        return text
    
    print(f"[Translate] en → {target_lang}: '{text[:50]}...'")
    translator = get_translator()
    result = translator.translate_from_english(text, target_lang)
    
    # If translation failed or returned same, keep original
    if not result or result == text:
        print(f"[Translate] Translation failed, keeping English")
        return text
    
    return result

def truncate_text(text: str, max_length: int = 512) -> str:
    """Truncate text to max token-safe length."""
    words = text.split()
    if len(words) > max_length:
        return " ".join(words[:max_length]) + "..."
    return text
