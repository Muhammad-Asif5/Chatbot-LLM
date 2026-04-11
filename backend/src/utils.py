import re
import unicodedata
from langdetect import detect
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

def translate_to_english(text: str, source_lang: str = "auto") -> str:
    """Translate text to English using offline translator."""
    if source_lang == "auto" or source_lang == "en" or not text:
        return text
    translator = get_translator()
    return translator.translate_to_english(text, source_lang)

def translate_from_english(text: str, target_lang: str = "en") -> str:
    """Translate English text to target language using offline translator."""
    if target_lang == "en" or not text:
        return text
    translator = get_translator()
    return translator.translate_from_english(text, target_lang)



def truncate_text(text: str, max_length: int = 512) -> str:
    """Truncate text to max token-safe length."""
    words = text.split()
    if len(words) > max_length:
        return " ".join(words[:max_length]) + "..."
    return text