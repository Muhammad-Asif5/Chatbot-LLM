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
 
    # Common verbs & conjugations
    "aya", "ayi", "aye", "gaya", "gayi", "gaye", "tha", "thi", "thy", "the",
    "kar", "karo", "karna", "karta", "karti", "karte", "karein", "kiya",
    "raha", "rahi", "rahe", "hoga", "hogi", "honge", "ho",
    "ja", "jao", "jata", "jati", "jate", "aa", "aao", "aata", "aati",
    "de", "dena", "deta", "deti", "dete", "diya", "lo", "lena",
    "leta", "leti", "lete", "liya", "lia", "sun", "suno", "sunna",
    "dekh", "dekha", "dekhi", "socha", "sochi", "samjha", "samjho",
    "bata", "batao", "batana", "pata", "pta", "puch", "pucha", "pocha",
 
    # Common words in everyday sentences
    "laken", "lekin", "lakin", "magar", "par", "per", "pe", "se", "ko",
    "ka", "ki", "ke", "ne", "ni", "na", "nhi", "nai", "nay", "bhi", "hi",
    "to", "tou", "tau", "wala", "wali", "wale", "walay",
    "office", "ghar", "school", "hospital", "market", "baazar", "bazar",
    "din", "raat", "subah", "sham", "dopahar", "kal", "parso", "aj",
    "yahan", "wahan", "idhar", "udhar", "andar", "bahar", "upar", "neeche",
    "sath", "saath", "bagair", "bina", "tak", "tuk", "phir", "dobara",
    "abhi", "pehle", "baad", "jaldi", "dhire", "zyada", "kam", "sirf",
    "acha", "theek", "shukriya", "shukria", "meherbani",
    "maafi", "khuda", "allah", "inshallah", "mashallah",
    "yar", "oye", "haye", "wah",
 
    # Sentence connectors & particles
    "mein", "mai", "hy", "hwy", "sy", "ky", "py",
    "hn", "hna", "hny", "koi", "koe", "kuch",
    "sb", "sab", "hr", "har", "dosra", "doosra", "agla", "pichla",
 
    # ✅ NEW: Common short-form / typo style words used in chat
    "mjhy", "mujhy", "mujhe", "mjhe",           # mujhe
    "tujhy", "tujhe", "tmhy", "tumhy", "tumhe", # tumhe
    "usy", "usse", "inhy", "inhe", "unhy", "unhe",
    "ky", "kry", "kro", "krna", "kren",         # karo/karna variants
    "dy", "dyn", "den", "dou",                  # do/dena variants
    "ly", "lyn", "len", "lou",                  # lo/lena variants
    "hy", "hyn", "hen",                         # hai/hain variants
    "ny", "nay",                                # ne variants
    "sy", "say",                                # se variants
    "py", "pay",                                # pe variants
    "gy", "gay", "gi", "gay",                   # gaye/gi variants
    "sakty", "sakti", "sakte", "sakta",         # sakna
    "sakyn", "skty", "skta", "skti",
    "chahty", "chahti", "chahte", "chahta",     # chahna
    "milgy", "milgya", "milgyi",                # mil gaye
    "hogya", "hogyi", "hogia",                  # ho gaya
    "agya", "aagya", "agyi",                    # aa gaya
    "lgta", "lgti", "lagte",                    # lagta
    "smjh", "smjho", "samjho",                  # samajhna
    "btao", "bтао", "btaو",                     # batao
    "poch", "pochy", "puchna",                  # poochna
    "rakho", "rakhy", "rakh",                   # rakhna
    "dekhy", "dekhyn",                          # dekhna
    "suno", "suny", "sunyn",                    # sunna
    "jao", "jaو", "jayn",                       # jana
    "aao", "aaو", "aayn",                       # aana
    "karo", "karو", "karyn",                    # karna
    "nahi", "nhi", "nhy", "nh",                 # nahi
    "hoga", "hogi", "hongy", "hngy",            # hona future
    "tha", "thi", "thy",                        # tha/thi
    "wala", "wali", "walay", "waly",            # wala
    "kafi", "kaafi",                            # kafi
    "boht", "bhot", "bohot", "bahut",           # bohot
    "zroor", "zaroor", "zror",                  # zaroor
    "phr", "phir",                              # phir
    "abhi", "abi",                              # abhi
    "yhi", "yehi", "yahan",                     # yahan/yehi
    "whi", "wohi", "wahan",                     # wahan/wohi
    "sirf", "srf",                              # sirf
    "thora", "thora", "thodi", "thoда",         # thora
    "acha", "acha", "achha",                    # achha
    "shukar", "shukriya",                       # shukriya
    "yaar", "yr", "yar",                        # yaar
    "bhai", "bhi", "bhy",                       # bhai
}

ALLOWED_LANGUAGES = set(LANGUAGE_NAMES.keys())
# Remove ambiguous words from ROMAN_URDU_KEYWORDS
AMBIGUOUS_REMOVE = {
    "are", "the", "per", "please", "sorry", "bro",
    "jo", "la", "le",
}
ROMAN_URDU_KEYWORDS = ROMAN_URDU_KEYWORDS - AMBIGUOUS_REMOVE

# ---------------------------------------------------------------------------
# deep-translator helpers (primary)
# ---------------------------------------------------------------------------

def _deep_translate_to_english(text: str, source_lang: str = "auto") -> str | None:
    """
    Try translating `text` → English using deep-translator.
    Returns the translated string on success, None on any failure.
    """
    try:
        print(f'sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss source_lang {source_lang}')
        from deep_translator import GoogleTranslator
        result = GoogleTranslator(source=source_lang, target="en").translate(text)
        if result and result.strip() and result.strip() != text.strip():
            return result.strip()
        return None
    except Exception as e:
        print(f"[deep-translator] to_english failed: {e}")
        return None


def _deep_translate_from_english(text: str, target_lang: str) -> str | None:
    """
    Try translating English `text` → `target_lang` using deep-translator.
    Returns the translated string on success, None on any failure.
    """
    try:
        from deep_translator import GoogleTranslator
        result = GoogleTranslator(source="en", target=target_lang).translate(text)
        if result and result.strip() and result.strip() != text.strip():
            return result.strip()
        return None
    except Exception as e:
        print(f"[deep-translator] from_english failed: {e}")
        return None

# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------
def is_roman_urdu(text: str) -> bool:
    """
    Detect if text is Roman Urdu.
    Uses keyword matching with a 0.3 threshold (lowered from 0.4
    to handle short chat-style messages with typos/short forms).
    """
    words = text.lower().replace("?", "").replace("!", "").replace(".", "").replace(",", "").split()
    if not words:
        return False
    match_count = sum(1 for word in words if word in ROMAN_URDU_KEYWORDS)
    ratio = match_count / len(words)
    print(f"[RomanUrdu] words={words}, matches={match_count}, ratio={ratio:.2f}")
    return ratio >= 0.3  # lowered from 0.4 → 0.3 for short/typo-heavy messages

def detect_language(text: str) -> str:
    """
    Detect language of text and return its code.
    Only allows: en, ur, fr, ar, hi
    Returns 'en' as default if language is not in allowed list.
    """
    try:
        # Check for Roman Urdu first
        if is_roman_urdu(text):
            return "auto" #LANGUAGE_NAMES["ur"]
 
        code = detect(text)
 
        if code in ALLOWED_LANGUAGES:
            return LANGUAGE_NAMES[code]
        else:
            return LANGUAGE_NAMES["en"]
 
    except Exception:
        return LANGUAGE_NAMES["auto"]

# ---------------------------------------------------------------------------
# Public translation API
# ---------------------------------------------------------------------------
def translate_to_english(text: str, source_lang: str = None) -> str:  # type: ignore
    """
    Translate text to English.
    Strategy:
      1. Try deep-translator (online, Google Translate).
      2. On failure, fall back to offline translator.
    If source is already English or text is empty, return as-is.
    """
    if not text or not text.strip():
        return text
    # Auto-detect if not provided
    if not source_lang:
        source_lang = detect_language(text)
    else:
        source_lang = source_lang.lower()
        if source_lang == "en" and is_roman_urdu(text):
            source_lang = "ur"

    # Already English — nothing to do
    if source_lang == "en":
        return text

    print(f"[Translate] {source_lang} → en: '{text[:50]}...'")

    # ── Primary: deep-translator ──────────────────────────────────────────
    result = _deep_translate_to_english(text, source_lang)
    if result:
        print("[Translate] deep-translator succeeded")
        return result

    # ── Fallback: offline translator ──────────────────────────────────────
    print("[Translate] deep-translator failed, falling back to offline translator")
    try:
        translator = get_translator()
        result = translator.translate_to_english(text, source_lang)
        if result and result.strip() and result.strip() != text.strip():
            return result
    except Exception as e:
        print(f"[Translate] Offline translator also failed: {e}")

    # Both failed — return original text
    print("[Translate] Both translators failed, keeping original")
    return text


def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translate English text to target language.
    Strategy:
      1. Try deep-translator (online, Google Translate).
      2. On failure, fall back to offline translator.
    If target is English or text is empty, return as-is.
    """
    if not text or not text.strip():
        return text

    # Normalize language code
    target_lang = target_lang.lower()[:2] if target_lang else "en"

    # Already English target — no translation needed
    if target_lang == "en":
        return text

    print(f"[Translate] en → {target_lang}: '{text[:50]}...'")

    # ── Primary: deep-translator ──────────────────────────────────────────
    result = _deep_translate_from_english(text, target_lang)
    if result:
        print("[Translate] deep-translator succeeded")
        return result

    # ── Fallback: offline translator ──────────────────────────────────────
    print("[Translate] deep-translator failed, falling back to offline translator")
    try:
        translator = get_translator()
        result = translator.translate_from_english(text, target_lang)
        if result and result.strip() and result.strip() != text.strip():
            return result
    except Exception as e:
        print(f"[Translate] Offline translator also failed: {e}")

    # Both failed — return original text (English)
    print("[Translate] Both translators failed, keeping English")
    return text


def truncate_text(text: str, max_length: int = 512) -> str:
    """Truncate text to max token-safe length."""
    words = text.split()
    if len(words) > max_length:
        return " ".join(words[:max_length]) + "..."
    return text
