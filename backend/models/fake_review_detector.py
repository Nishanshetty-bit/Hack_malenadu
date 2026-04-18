"""
InsightIQ 2.0 — Fake/Bot Review Detector
Combines heuristic signals + ML confidence analysis to flag suspicious reviews.
"""

import re
from typing import Dict, List, Optional
from collections import Counter


class FakeReviewDetector:
    """
    Detect fake, bot-generated, or spam reviews using multiple signals.
    Each signal contributes a weighted score. Reviews above threshold are flagged.
    """

    FAKE_THRESHOLD = 0.45  # Score >= this → flagged as suspicious

    # Known bot/template phrases (normalized lowercase)
    TEMPLATE_PHRASES = [
        "i love this product",
        "best product ever",
        "worst product ever",
        "highly recommend this",
        "do not buy this",
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
        "stay away from this",
        "total waste",
        "perfect product",
        "defective product",
        "nice product good quality",
        "good product nice quality",
        "awesome product love it",
        "best purchase ever made",
        "worst purchase ever made",
        "exactly as described",
        "not as described",
        "fast shipping great product",
        "poor quality product",
        "excellent quality product",
        "would buy again",
        "never buying again",
        "received damaged product",
    ]

    # Signal weights — intentionally sum > 1.0 so strong multi-signal reviews
    # easily cross the threshold. Single weak signals stay low.
    WEIGHTS = {
        "too_short": 0.10,
        "too_long": 0.08,
        "all_caps": 0.22,
        "repeated_chars": 0.15,
        "repeated_words": 0.15,
        "excessive_punctuation": 0.18,
        "template_match": 0.20,
        "emoji_spam": 0.14,
        "low_info_density": 0.12,
        "rating_mismatch": 0.15,
        "spaced_text": 0.25,
    }

    def __init__(self):
        self._repeated_chars = re.compile(r"(.)\1{4,}")
        self._repeated_words = re.compile(r"\b(\w+)(\s+\1){2,}\b", re.IGNORECASE)
        self._excessive_punct = re.compile(r"[!?]{3,}")

    def analyze(
        self,
        text: str,
        rating: Optional[float] = None,
        sentiment_label: Optional[str] = None,
        sentiment_score: Optional[float] = None,
    ) -> Dict:
        """
        Analyze a review for fake/bot signals.
        Returns fake_score (0-1), is_suspicious boolean, and detailed flags.
        """
        if not text or not text.strip():
            return {
                "fake_score": 0.0,
                "is_suspicious": False,
                "flags": ["empty_review"],
                "signal_details": {},
            }

        signals = {}
        flags = []

        # ── Signal 1: Too Short ──────────────────────────
        word_count = len(text.split())
        if word_count <= 3:
            signals["too_short"] = 1.0
            flags.append(f"Very short review ({word_count} words)")
        elif word_count <= 6:
            signals["too_short"] = 0.5
            flags.append(f"Short review ({word_count} words)")
        else:
            signals["too_short"] = 0.0

        # ── Signal 2: Too Long (unusual for real reviews) ─
        if word_count > 500:
            signals["too_long"] = 0.8
            flags.append(f"Unusually long review ({word_count} words)")
        elif word_count > 300:
            signals["too_long"] = 0.4
        else:
            signals["too_long"] = 0.0

        # ── Signal 3: ALL CAPS ───────────────────────────
        alpha_chars = [c for c in text if c.isalpha()]
        if len(alpha_chars) > 5 and word_count > 4:
            caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            if caps_ratio > 0.8:
                signals["all_caps"] = 1.0
                flags.append(f"Mostly ALL CAPS ({caps_ratio:.0%})")
            elif caps_ratio > 0.5:
                signals["all_caps"] = 0.5
                flags.append(f"High caps ratio ({caps_ratio:.0%})")
            else:
                signals["all_caps"] = 0.0
        else:
            signals["all_caps"] = 0.0

        # ── Signal 4: Repeated Characters ────────────────
        repeated_matches = self._repeated_chars.findall(text)
        if len(repeated_matches) >= 3:
            signals["repeated_chars"] = 1.0
            flags.append(f"Excessive repeated characters ({len(repeated_matches)} instances)")
        elif len(repeated_matches) >= 1:
            signals["repeated_chars"] = 0.4
        else:
            signals["repeated_chars"] = 0.0

        # ── Signal 5: Repeated Words ─────────────────────
        repeated_word_matches = self._repeated_words.findall(text)
        if len(repeated_word_matches) >= 2:
            signals["repeated_words"] = 1.0
            flags.append("Excessive word repetition")
        elif len(repeated_word_matches) >= 1:
            signals["repeated_words"] = 0.5
        else:
            signals["repeated_words"] = 0.0

        # ── Signal 6: Excessive Punctuation ──────────────
        punct_matches = self._excessive_punct.findall(text)
        if len(punct_matches) >= 3:
            signals["excessive_punctuation"] = 1.0
            flags.append(f"Excessive punctuation ({len(punct_matches)} sequences)")
        elif len(punct_matches) >= 1:
            signals["excessive_punctuation"] = 0.4
        else:
            signals["excessive_punctuation"] = 0.0

        # ── Signal 7: Template/Generic Phrase Match ──────
        lower_text = text.lower().strip()
        template_matches = [p for p in self.TEMPLATE_PHRASES if p in lower_text]
        if len(template_matches) >= 2:
            signals["template_match"] = 1.0
            flags.append(f"Multiple template phrases detected: {template_matches[:3]}")
        elif len(template_matches) >= 1:
            # Check if the review is ONLY the template phrase
            if len(lower_text.split()) <= len(template_matches[0].split()) + 3:
                signals["template_match"] = 0.9
                flags.append(f"Review is mostly a template phrase: '{template_matches[0]}'")
            else:
                signals["template_match"] = 0.3
        else:
            signals["template_match"] = 0.0

        # ── Signal 8: Emoji Spam ─────────────────────────
        emoji_count = len(re.findall(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001f926-\U0001f937]",
            text,
        ))
        if emoji_count >= 8:
            signals["emoji_spam"] = 1.0
            flags.append(f"Emoji spam ({emoji_count} emojis)")
        elif emoji_count >= 4:
            signals["emoji_spam"] = 0.5
        else:
            signals["emoji_spam"] = 0.0

        # ── Signal 9: Low Information Density ────────────
        if word_count >= 5:
            unique_words = len(set(text.lower().split()))
            info_density = unique_words / word_count
            if info_density < 0.4:
                signals["low_info_density"] = 1.0
                flags.append(f"Low information density ({info_density:.0%} unique words)")
            elif info_density < 0.6:
                signals["low_info_density"] = 0.5
            else:
                signals["low_info_density"] = 0.0
        else:
            signals["low_info_density"] = 0.0

        # ── Signal 10: Rating-Sentiment Mismatch ────────
        if rating is not None and sentiment_label:
            mismatch = False
            if rating >= 4 and sentiment_label.lower() in ("negative", "very_negative"):
                mismatch = True
            elif rating <= 2 and sentiment_label.lower() in ("positive", "very_positive"):
                mismatch = True

            if mismatch:
                signals["rating_mismatch"] = 1.0
                flags.append(f"Rating ({rating}★) contradicts sentiment ({sentiment_label})")
            else:
                signals["rating_mismatch"] = 0.0
        else:
            signals["rating_mismatch"] = 0.0
        # ── Signal 11: Spaced Out Text (Obfuscation) ────
        if word_count > 4:
            # Count single characters separated by spaces
            single_char_words = [w for w in text.split() if len(w) == 1 and w.isalpha()]
            spaced_ratio = len(single_char_words) / word_count
            if spaced_ratio > 0.6:
                signals["spaced_text"] = 1.0
                flags.append(f"Spaced out text detected (obfuscation risk: {spaced_ratio:.0%})")
            elif spaced_ratio > 0.3:
                signals["spaced_text"] = 0.5
            else:
                signals["spaced_text"] = 0.0
        else:
            signals["spaced_text"] = 0.0

        # ── Compute weighted score ───────────────────────
        total_score = 0.0
        for signal_name, signal_value in signals.items():
            weight = self.WEIGHTS.get(signal_name, 0.1)
            total_score += signal_value * weight

        # Multi-signal boost: if 3+ signals fire (value > 0.3), amplify
        active_signals = sum(1 for v in signals.values() if v > 0.3)
        if active_signals >= 3:
            total_score *= 1.3
            flags.append(f"Multiple bot signals detected ({active_signals} signals)")

        # Normalize to 0-1 range
        fake_score = min(total_score, 1.0)

        return {
            "fake_score": round(fake_score, 3),
            "is_suspicious": fake_score >= self.FAKE_THRESHOLD,
            "flags": flags,
            "signal_details": {k: round(v, 3) for k, v in signals.items()},
        }

    def batch_analyze(
        self,
        reviews: List[Dict],
    ) -> List[Dict]:
        """
        Analyze a batch of reviews.
        Detects cross-review patterns (duplicates) and user-level bot behavior.
        """
        results = []
        texts_seen = Counter()
        users_seen = {} # user_id -> count

        # First pass: gather statistics
        for review in reviews:
            text = review.get("text", review.get("original_text", "")).strip().lower()
            u_id = review.get("user_id")
            
            # Simple fingerprint: strip spaces and non-alpha
            fingerprint = re.sub(r"[^a-z]", "", text)
            if len(fingerprint) > 5:
                texts_seen[fingerprint] += 1
            
            if u_id:
                if u_id not in users_seen:
                    users_seen[u_id] = {"count": 0, "texts": set(), "flags": []}
                users_seen[u_id]["count"] += 1
                users_seen[u_id]["texts"].add(fingerprint)

        # Second pass: analyze each review
        for review in reviews:
            text = review.get("text", review.get("original_text", ""))
            rating = review.get("rating")
            sentiment = review.get("sentiment_label")
            score = review.get("sentiment_score")
            u_id = review.get("user_id")

            result = self.analyze(text, rating, sentiment, score)
            
            # 1. Global Duplicate Check
            normalized = re.sub(r"[^a-z]", "", text.lower())
            if len(normalized) > 5 and texts_seen.get(normalized, 0) > 1:
                result["flags"].append(f"Identical text found across {texts_seen[normalized]} reviews")
                result["fake_score"] = min(result["fake_score"] + 0.25, 1.0)
            
            # 2. User-Level Bot Logic
            if u_id and u_id in users_seen:
                u_data = users_seen[u_id]
                is_bot_user = False
                
                # Signal: High frequency from one user
                if u_data["count"] > 3:
                    result["flags"].append(f"Customer flagged: Hyper-active user ({u_data['count']} reviews in batch)")
                    is_bot_user = True
                
                # Signal: User repeating themselves
                if u_data["count"] > 1 and len(u_data["texts"]) < u_data["count"]:
                    result["flags"].append("Customer flagged: User repeating identical text across products")
                    is_bot_user = True
                
                result["is_bot_user"] = 1 if is_bot_user else 0
                if is_bot_user:
                    result["fake_score"] = min(result["fake_score"] + 0.3, 1.0)

            result["is_suspicious"] = result["fake_score"] >= self.FAKE_THRESHOLD
            results.append(result)

        return results
