"""
InsightIQ 2.0 — Text Preprocessor
Handles noisy, real-world review text: emojis, typos, mixed scripts, run-on sentences.
"""

import re
import unicodedata
from typing import Dict, List, Tuple


# Common emoji → text mappings
EMOJI_MAP = {
    "😀": "happy", "😃": "happy", "😄": "happy", "😁": "grinning",
    "😆": "laughing", "😅": "relieved", "🤣": "laughing", "😂": "tears_of_joy",
    "🙂": "slightly_happy", "😊": "blushing", "😇": "angel", "🥰": "love",
    "😍": "heart_eyes", "🤩": "starstruck", "😘": "kiss", "😗": "kiss",
    "😋": "yum", "😛": "tongue", "😜": "wink_tongue", "🤪": "crazy",
    "😎": "cool", "🤓": "nerd", "🧐": "monocle", "😏": "smirk",
    "😒": "unamused", "😞": "disappointed", "😔": "pensive", "😟": "worried",
    "😕": "confused", "🙁": "frown", "☹️": "frown", "😣": "persevering",
    "😖": "confounded", "😫": "tired", "😩": "weary", "🥺": "pleading",
    "😢": "crying", "😭": "sobbing", "😤": "angry", "😠": "angry",
    "😡": "rage", "🤬": "cursing", "🤯": "mind_blown", "😳": "flushed",
    "🥵": "hot", "🥶": "cold", "😱": "screaming", "😰": "anxious",
    "😥": "sad_relieved", "😓": "downcast_sweat", "🤗": "hugging",
    "🤔": "thinking", "🤭": "hand_over_mouth", "🤫": "shushing",
    "🤥": "lying", "😶": "no_mouth", "😐": "neutral", "😑": "expressionless",
    "😬": "grimacing", "🙄": "eye_roll", "😯": "hushed", "😧": "anguished",
    "😲": "astonished", "🥱": "yawning", "😴": "sleeping", "🤤": "drooling",
    "👍": "thumbs_up", "👎": "thumbs_down", "👏": "clapping", "🙌": "raised_hands",
    "💪": "strong", "🔥": "fire", "💯": "hundred", "⭐": "star",
    "🌟": "glowing_star", "💫": "dizzy_star", "✨": "sparkles", "❤️": "heart",
    "💔": "broken_heart", "💩": "poop", "🚀": "rocket", "✅": "check",
    "❌": "cross", "⚠️": "warning", "💰": "money", "🎉": "party",
    "🎊": "confetti", "👀": "eyes", "🤦": "facepalm", "🤷": "shrug",
    "💀": "skull", "☠️": "skull_crossbones", "🙏": "prayer",
    "👌": "ok", "✌️": "peace", "🤞": "crossed_fingers",
    "❤": "heart", "💗": "heart", "💖": "heart", "💕": "hearts",
    "😊": "smile", "🥳": "partying", "😻": "heart_eyes_cat",
}

# Slang expander dictionary
SLANG_MAP = {
    "awsm": "awesome", "awsome": "awesome", "gud": "good", "gd": "good",
    "idk": "i do not know", "brb": "be right back", "lol": "laughing out loud",
    "ty": "thank you", "thx": "thanks", "plz": "please", "pls": "please",
    "u": "you", "r": "are", "n": "and", "b": "be", "v": "very",
    "bcoz": "because", "bcaz": "because", "k": "ok", "okey": "okay",
    "gr8": "great", "prodt": "product", "osm": "awesome", "nyc": "nice",
    "lve": "love", "dis": "this", "dat": "that", "wat": "what",
}

# Common template/generic phrases that indicate low-quality or bot reviews
TEMPLATE_PHRASES = [
    "i love this product",
    "best product ever",
    "worst product ever",
    "highly recommend",
    "do not buy",
    "five stars",
    "one star",
    "great product",
    "terrible product",
    "amazing product",
    "horrible product",
    "waste of money",
    "worth every penny",
    "exceeded my expectations",
    "very disappointed",
    "very satisfied",
    "must buy",
    "stay away",
    "total waste",
    "love it",
    "hate it",
    "perfect product",
    "defective product",
    "nice product good quality",
    "good product nice quality",
    "awesome product love it",
]


class TextPreprocessor:
    """Clean and normalize noisy review text for downstream analysis."""

    def __init__(self):
        # Regex patterns compiled once
        self._html_pattern = re.compile(r"<[^>]+>")
        self._url_pattern = re.compile(r"https?://\S+|www\.\S+")
        self._email_pattern = re.compile(r"\S+@\S+\.\S+")
        self._multi_space = re.compile(r"\s+")
        self._repeated_chars = re.compile(r"(.)\1{3,}")  # 4+ of same char
        self._repeated_words = re.compile(r"\b(\w+)(\s+\1){2,}\b", re.IGNORECASE)
        self._excessive_punct = re.compile(r"([!?.]){3,}")
        self._emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"
            "\u3030"
            "]+",
            flags=re.UNICODE,
        )

    def preprocess(self, text: str) -> Dict:
        """
        Full preprocessing pipeline. Returns cleaned text + metadata.
        """
        if not text or not text.strip():
            return {
                "cleaned_text": "",
                "original_text": text or "",
                "notes": ["empty_input"],
                "emoji_extracted": [],
                "char_count_original": 0,
                "char_count_cleaned": 0,
            }

        original = text
        notes = []
        emoji_extracted = []

        # Step 1: Unicode normalization
        text = unicodedata.normalize("NFKC", text)

        # Step 2: Strip HTML tags
        if self._html_pattern.search(text):
            text = self._html_pattern.sub(" ", text)
            notes.append("html_stripped")

        # Step 3: Remove URLs
        if self._url_pattern.search(text):
            text = self._url_pattern.sub("[URL]", text)
            notes.append("urls_removed")

        # Step 4: Remove emails
        if self._email_pattern.search(text):
            text = self._email_pattern.sub("[EMAIL]", text)
            notes.append("emails_removed")

        # Step 5: Extract and Purge Emojis
        emojis_found = self._emoji_pattern.findall(text)
        if emojis_found:
            for emoji_char in "".join(emojis_found):
                if emoji_char in EMOJI_MAP:
                    emoji_extracted.append({
                        "emoji": emoji_char,
                        "meaning": EMOJI_MAP[emoji_char],
                    })
            # Remove all emojis from analysis text (Strict Cleaning)
            text = self._emoji_pattern.sub(" ", text)
            notes.append("emojis_purged")

        # Step 5.5: Slang Expansion (awsm -> awesome)
        original_before_slang = text
        words = text.split()
        expanded_words = [SLANG_MAP.get(w.lower(), w) for w in words]
        text = " ".join(expanded_words)
        if text.lower() != original_before_slang.lower():
            notes.append("slang_expanded")

        # Step 6: Fix repeated characters (sooooo → so, goooood → good)
        original_before_repeat = text
        text = self._repeated_chars.sub(r"\1\1", text)
        if text != original_before_repeat:
            notes.append("repeated_chars_fixed")

        # Step 7: Fix repeated words
        original_before_words = text
        text = self._repeated_words.sub(r"\1", text)
        if text != original_before_words:
            notes.append("repeated_words_fixed")

        # Step 8: Normalize excessive punctuation
        original_before_punct = text
        text = self._excessive_punct.sub(r"\1.", text)
        if text != original_before_punct:
            notes.append("excessive_punctuation_normalized")

        # Step 9: Smart quote normalization
        smart_quotes = {
            "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
            "\u2013": "-", "\u2014": "-", "\u2026": "...",
        }
        for old, new in smart_quotes.items():
            text = text.replace(old, new)

        # Step 10: Whitespace normalization
        text = self._multi_space.sub(" ", text).strip()

        # Step 11: Basic sentence splitting for run-on text
        # If text is very long with no punctuation, add periods at likely boundaries
        if len(text) > 200 and text.count(".") < 2 and text.count("!") < 2:
            # Try splitting at common conjunctions when sentence is very long
            text = re.sub(
                r"\b(but|however|although|also|and then|then|moreover|furthermore)\b",
                r". \1",
                text,
                flags=re.IGNORECASE,
            )
            notes.append("run_on_sentence_split")

        return {
            "cleaned_text": text,
            "original_text": original,
            "notes": notes,
            "emoji_extracted": emoji_extracted,
            "char_count_original": len(original),
            "char_count_cleaned": len(text),
        }

    def is_mostly_caps(self, text: str, threshold: float = 0.7) -> bool:
        """Check if text is mostly uppercase (bot signal)."""
        alpha_chars = [c for c in text if c.isalpha()]
        if len(alpha_chars) < 5:
            return False
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        return upper_ratio >= threshold

    def get_repetition_score(self, text: str) -> float:
        """Score how repetitive the text is (0-1, higher = more repetitive)."""
        words = text.lower().split()
        if len(words) < 3:
            return 0.0
        unique = set(words)
        return 1 - (len(unique) / len(words))

    def matches_template(self, text: str) -> List[str]:
        """Check if text matches known template/generic phrases."""
        lower = text.lower().strip()
        matches = []
        for phrase in TEMPLATE_PHRASES:
            if phrase in lower:
                matches.append(phrase)
        return matches

    def count_excessive_punctuation(self, text: str) -> int:
        """Count sequences of excessive punctuation."""
        return len(re.findall(r"[!?]{3,}", text))

    def has_emoji_spam(self, text: str, threshold: int = 5) -> bool:
        """Check if text has excessive emoji usage."""
        emojis = self._emoji_pattern.findall(text)
        total_emoji_chars = sum(len(e) for e in emojis)
        return total_emoji_chars >= threshold
