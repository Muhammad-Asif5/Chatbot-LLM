"""
Offline translation using Argos Translate.
No internet connection required after initial model download.
"""

import os
from typing import Optional

# Set offline mode
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

class OfflineTranslator:
    """Offline translator using Argos Translate."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._argos_available = False
        self._check_argos()
    
    def _check_argos(self):
        """Check if Argos Translate is available."""
        try:
            import argostranslate.package
            import argostranslate.translate
            self.argostranslate = argostranslate
            self._argos_available = True
            print("[Translator] Argos Translate available (offline)")
        except ImportError as e:
            print(f"[Translator] Argos Translate not found: {e}")
            self._argos_available = False
    
    def _ensure_package_installed(self, from_lang: str, to_lang: str) -> bool:
        """Ensure translation package is installed."""
        if not self._argos_available:
            return False
        
        try:
            # Check if already installed
            installed_packages = self.argostranslate.package.get_installed_packages()
            for pkg in installed_packages:
                if pkg.from_code == from_lang and pkg.to_code == to_lang:
                    return True
            
            # Install the package
            print(f"[Translator] Installing package: {from_lang}->{to_lang}")
            self.argostranslate.package.update_package_index()
            available_packages = self.argostranslate.package.get_available_packages()
            
            for pkg in available_packages:
                if pkg.from_code == from_lang and pkg.to_code == to_lang:
                    package_path = pkg.download()
                    self.argostranslate.package.install_from_path(package_path)
                    print(f"[Translator] Successfully installed {from_lang}->{to_lang}")
                    return True
            
            print(f"[Translator] No package found for {from_lang}->{to_lang}")
            return False
            
        except Exception as e:
            print(f"\n\n[Translator] Error ensuring package: {e}\n\n")
            return False
    
    def translate(self, text: str, from_lang: str, to_lang: str) -> str:
        """Translate text using Argos Translate."""
        if not text or not text.strip():
            return text
        
        if from_lang == to_lang:
            return text
        
        # Normalize language codes
        from_lang = from_lang.lower()[:2]
        to_lang = to_lang.lower()[:2]
        
        if not self._argos_available:
            return text
        
        try:
            # Ensure package is installed
            if not self._ensure_package_installed(from_lang, to_lang):
                return text
            
            # Perform translation
            from argostranslate.translate import translate
            result = translate(text, from_lang, to_lang)
            return result if result else text
            
        except Exception as e:
            print(f"[Translator] Translation error: {e}")
            return text
    
    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translate text to English."""
        if source_lang == "en" or not text:
            return text
        return self.translate(text, source_lang, "en")
    
    def translate_from_english(self, text: str, target_lang: str) -> str:
        """Translate English text to target language."""
        if target_lang == "en" or not text:
            return text
        return self.translate(text, "en", target_lang)


# Singleton instance
_translator = None

def get_translator() -> OfflineTranslator:
    """Get or create translator instance."""
    global _translator
    if _translator is None:
        _translator = OfflineTranslator()
    return _translator


# # Direct functions (no recursion)
# def translate_to_english(text: str, source_lang: str = "auto") -> str:
#     """Translate text to English using offline translator."""
#     if source_lang == "auto" or source_lang == "en" or not text:
#         return text
#     translator = get_translator()
#     return translator.translate_to_english(text, source_lang)


# def translate_from_english(text: str, target_lang: str = "en") -> str:
#     """Translate English text to target language using offline translator."""
#     if target_lang == "en" or not text:
#         return text
#     translator = get_translator()
#     return translator.translate_from_english(text, target_lang)


# def download_all_packages():
#     """Download all common translation packages."""
#     translator = get_translator()
    
#     pairs = [
#         ("en", "ur"), ("ur", "en"),
#         ("en", "ar"), ("ar", "en"),
#         ("en", "fr"), ("fr", "en"),
#         ("en", "de"), ("de", "en"),
#         ("en", "es"), ("es", "en"),
#         ("en", "zh"), ("zh", "en"),
#         ("en", "hi"), ("hi", "en"),
#         ("en", "tr"), ("tr", "en"),
#         ("en", "ru"), ("ru", "en"),
#         ("en", "pt"), ("pt", "en"),
#         ("en", "it"), ("it", "en"),
#     ]
    
#     print("[Translator] Downloading all translation packages...")
#     for from_lang, to_lang in pairs:
#         translator._ensure_package_installed(from_lang, to_lang)
    
#     print("[Translator] All packages downloaded!")
    