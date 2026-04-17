"""
InsightIQ 2.0 — Language Processor
Handles language detection and translation for multilingual reviews.
Uses langdetect for detection and Helsinki-NLP MarianMT models for translation.
"""

import re
from typing import Dict, Optional, Tuple

# Try importing langdetect - gracefully degrade if not available
try:
    from langdetect import detect, detect_langs, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# Try importing transformers for translation
try:
    from transformers import MarianMTModel, MarianTokenizer
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False


# Language code → display name mapping
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "ru": "Russian",
    "it": "Italian",
    "nl": "Dutch",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
}

# MarianMT model mapping: source_lang → model_name
# Helsinki-NLP models use ISO 639-1 codes
TRANSLATION_MODELS = {
    "hi": "Helsinki-NLP/opus-mt-hi-en",
    "fr": "Helsinki-NLP/opus-mt-fr-en",
    "de": "Helsinki-NLP/opus-mt-de-en",
    "es": "Helsinki-NLP/opus-mt-es-en",
    "pt": "Helsinki-NLP/opus-mt-pt-en",
    "zh": "Helsinki-NLP/opus-mt-zh-en",
    "ja": "Helsinki-NLP/opus-mt-ja-en",
    "ko": "Helsinki-NLP/opus-mt-ko-en",
    "ar": "Helsinki-NLP/opus-mt-ar-en",
    "ru": "Helsinki-NLP/opus-mt-ru-en",
    "it": "Helsinki-NLP/opus-mt-it-en",
    "nl": "Helsinki-NLP/opus-mt-nl-en",
    "ta": "Helsinki-NLP/opus-mt-ta-en",
    "ml": "Helsinki-NLP/opus-mt-ml-en",
    # For languages without direct models, we use multi-source
    "kn": "Helsinki-NLP/opus-mt-mul-en",
    "te": "Helsinki-NLP/opus-mt-mul-en",
    "mr": "Helsinki-NLP/opus-mt-mul-en",
    "bn": "Helsinki-NLP/opus-mt-mul-en",
    "gu": "Helsinki-NLP/opus-mt-mul-en",
    "pa": "Helsinki-NLP/opus-mt-mul-en",
    "ur": "Helsinki-NLP/opus-mt-mul-en",
}


class LanguageProcessor:
    """Detect language and translate non-English reviews to English."""

    def __init__(self):
        self._model_cache = {}  # Cache loaded translation models
        self._tokenizer_cache = {}

    def detect_language(self, text: str) -> Dict:
        """
        Detect the language of the given text.
        Returns dict with language code, name, and confidence.
        """
        if not text or not text.strip():
            return {
                "language_code": "unknown",
                "language_name": "Unknown",
                "confidence": 0.0,
            }

        # Clean text for detection
        clean = re.sub(r"https?://\S+", "", text)
        clean = re.sub(r"[0-9]+", "", clean)
        clean = re.sub(r"\[.*?\]", "", clean)
        clean = clean.strip().lower()

        if len(clean) < 3:
            return {"language_code": "en", "language_name": "English", "confidence": 0.5}

        # ── Dialect Heuristics (Hinglish/Kanglish) ──
        hinglish_markers = {"boht", "accha", "hai", "nahi", "kar", "sahi", "badhiya", "mast", "bekaar"}
        kanglish_markers = {"alla", "ide", "chennagide", "maadi", "neene", "beku", "superagide"}
        
        words = set(clean.split())
        if words.intersection(hinglish_markers):
            return {"language_code": "hinglish", "language_name": "Hinglish", "confidence": 0.8}
        if words.intersection(kanglish_markers):
            return {"language_code": "kanglish", "language_name": "Kanglish", "confidence": 0.8}

        if not LANGDETECT_AVAILABLE:
            return self._heuristic_detect(clean)

        try:
            lang_probs = detect_langs(clean)
            top = lang_probs[0]
            code = str(top.lang)
            if code in ("zh-cn", "zh-tw", "zh"): code = "zh"

            return {
                "language_code": code,
                "language_name": LANGUAGE_NAMES.get(code, code.upper()),
                "confidence": round(float(top.prob), 3),
            }
        except LangDetectException:
            return {"language_code": "en", "language_name": "English", "confidence": 0.3}

    def _heuristic_detect(self, text: str) -> Dict:
        """Fallback heuristic language detection using Unicode ranges."""
        # Devanagari (Hindi, Marathi)
        if re.search(r"[\u0900-\u097F]", text):
            return {"language_code": "hi", "language_name": "Hindi", "confidence": 0.7}
        # Kannada
        if re.search(r"[\u0C80-\u0CFF]", text):
            return {"language_code": "kn", "language_name": "Kannada", "confidence": 0.7}
        # Tamil
        if re.search(r"[\u0B80-\u0BFF]", text):
            return {"language_code": "ta", "language_name": "Tamil", "confidence": 0.7}
        # Telugu
        if re.search(r"[\u0C00-\u0C7F]", text):
            return {"language_code": "te", "language_name": "Telugu", "confidence": 0.7}
        # Arabic
        if re.search(r"[\u0600-\u06FF]", text):
            return {"language_code": "ar", "language_name": "Arabic", "confidence": 0.7}
        # CJK (Chinese)
        if re.search(r"[\u4e00-\u9fff]", text):
            return {"language_code": "zh", "language_name": "Chinese", "confidence": 0.7}
        # Japanese (Hiragana/Katakana)
        if re.search(r"[\u3040-\u30ff]", text):
            return {"language_code": "ja", "language_name": "Japanese", "confidence": 0.7}
        # Korean
        if re.search(r"[\uac00-\ud7af]", text):
            return {"language_code": "ko", "language_name": "Korean", "confidence": 0.7}
        # Default to English
        return {"language_code": "en", "language_name": "English", "confidence": 0.5}

    def translate_to_english(self, text: str, source_lang: str) -> Dict:
        """
        Translate text from source language to English.
        Returns dict with translated text and metadata.
        """
        if source_lang == "en" or not text.strip():
            return {
                "translated_text": text,
                "original_text": text,
                "source_language": source_lang,
                "was_translated": False,
            }

        if not TRANSLATION_AVAILABLE:
            return {
                "translated_text": text,
                "original_text": text,
                "source_language": source_lang,
                "was_translated": False,
                "error": "Translation models not available (install transformers + sentencepiece)",
            }

        # Map dialects to base languages for model lookup
        model_lookup = source_lang
        if source_lang == "hinglish": model_lookup = "hi"
        if source_lang == "kanglish": model_lookup = "kn"

        model_name = TRANSLATION_MODELS.get(model_lookup)
        if not model_name:
            # Try multi-language model as fallback
            model_name = "Helsinki-NLP/opus-mt-mul-en"

        try:
            tokenizer, model = self._load_model(model_name)
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            outputs = model.generate(**inputs, max_length=512)
            translated = tokenizer.decode(outputs[0], skip_special_tokens=True)

            return {
                "translated_text": translated,
                "original_text": text,
                "source_language": source_lang,
                "was_translated": True,
                "model_used": model_name,
            }
        except Exception as e:
            return {
                "translated_text": text,
                "original_text": text,
                "source_language": source_lang,
                "was_translated": False,
                "error": str(e),
            }

    def _load_model(self, model_name: str):
        """Load and cache a translation model."""
        if model_name not in self._model_cache:
            print(f"[LanguageProcessor] Loading translation model: {model_name}")
            self._tokenizer_cache[model_name] = MarianTokenizer.from_pretrained(model_name)
            self._model_cache[model_name] = MarianMTModel.from_pretrained(model_name)
            print(f"[LanguageProcessor] Model loaded: {model_name}")
        return self._tokenizer_cache[model_name], self._model_cache[model_name]

    def process_review(self, text: str) -> Dict:
        """
        Full language processing pipeline for a single review.
        Detect language → translate if needed → return results.
        """
        detection = self.detect_language(text)
        lang_code = detection["language_code"]

        if lang_code != "en" and detection["confidence"] > 0.4:
            translation = self.translate_to_english(text, lang_code)
        else:
            translation = {
                "translated_text": text,
                "original_text": text,
                "source_language": lang_code,
                "was_translated": False,
            }

        return {
            **detection,
            **translation,
        }
