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

def detect_language(text: str) -> str:
    """Detect language from text content."""
    if not text or not text.strip():
        return "en"  # Default to English for empty text
    
    SUPPORTED = {"en", "ur", "ar", "fr", "de", "es", "zh-cn", "zh-tw", "hi"}
    
    try:
        # Clean the text
        text = text.strip()
        
        # Detect language
        lang = detect(text)
        
        # Normalize Chinese variants
        if lang.startswith("zh"):
            lang = "zh-cn"  # or keep as "zh" based on your needs
            
        # Return detected language if supported, otherwise English
        return lang if lang in SUPPORTED else "en"
        
    except LangDetectException:
        # If detection fails, try with a cleaned version or return default
        try:
            # Remove any problematic characters
            cleaned = ''.join(c for c in text if c.isprintable())
            if cleaned and len(cleaned) > 10:  # Only try if we have enough content
                lang = detect(cleaned)
                if lang.startswith("zh"):
                    lang = "zh-cn"
                return lang if lang in SUPPORTED else "en"
        except:
            pass
        return "en"
    except Exception:
        return "en"

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
