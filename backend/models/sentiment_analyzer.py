"""
InsightIQ 2.0 — Sentiment & Feature Sentiment Analyzer
Extracts aspect-level sentiment and flags ambiguous or sarcastic reviews.
"""

import re
from typing import Dict, List, Optional, Tuple


class SentimentAnalyzer:
    """
    Analyzes review text to:
    1. Extract features (aspects) discussed and assign sentiment/confidence to each.
    2. Compute an overall nuanced sentiment.
    3. Flag sarcastic or highly ambiguous reviews.
    """

    # Expanded taxonomy for aspect extraction
    FEATURE_TAXONOMY = {
        "battery": ["battery", "charge", "charging", "battery life", "power", "backup"],
        "camera": ["camera", "photo", "picture", "lens", "video", "selfie", "low light", "night mode", "megapixel"],
        "display": ["screen", "display", "resolution", "pixel", "brightness", "amoled", "refresh rate", "hz", "panel"],
        "performance": ["fast", "slow", "speed", "lag", "hang", "processor", "ram", "performance", "smooth", "gaming"],
        "build_quality": ["build", "quality", "material", "durability", "plastic", "glass", "premium", "fragile"],
        "price": ["price", "cost", "value", "money", "expensive", "cheap", "affordable", "deal"],
        "software": ["software", "os", "update", "ui", "interface", "bug", "glitch", "crash", "bloatware"],
        "storage": ["storage", "space", "memory", "gb"],
        "audio": ["sound", "audio", "speaker", "volume", "bass", "headphones", "mic"],
        "customer_support": ["support", "service", "customer care", "warranty", "return", "refund", "repair"],
        "delivery": ["delivery", "shipping", "shipped", "arrived", "packaging", "box"]
    }

    # Lexicons for sentiment
    POSITIVE_WORDS = {
        "good", "great", "excellent", "amazing", "awesome", "fantastic", "perfect",
        "love", "best", "superb", "brilliant", "outstanding", "impressive", "beautiful",
        "nice", "fast", "smooth", "solid", "gorgeous", "vibrant", "accurate", "happy",
        "satisfied", "incredible", "worth", "recommend"
    }

    NEGATIVE_WORDS = {
        "bad", "terrible", "horrible", "worst", "awful", "poor", "disappointing",
        "waste", "hate", "slow", "lag", "crash", "bug", "broken", "defective",
        "useless", "trash", "garbage", "unhappy", "frustrating", "drain", "poor",
        "grainy", "blurry", "scratched"
    }

    NEGATORS = {"not", "no", "never", "n't", "cannot", "hardly", "barely", "doesn't", "don't", "didn't"}
    INTENSIFIERS = {"very", "really", "extremely", "super", "so", "too", "absolutely", "insanely", "highly"}

    # Pattern for splitting text into clauses (simplified)
    CLAUSE_SPLIT_PATTERN = re.compile(r'[.,;!\n]|\b(and|but|however|although|though)\b')

    def __init__(self):
        pass

    def _get_feature_mapping(self, word: str) -> Optional[str]:
        """Map a token to a canonical feature name, else return None."""
        word_lower = word.lower()
        for feature, keywords in self.FEATURE_TAXONOMY.items():
            if word_lower in keywords:
                return feature
            # simple plural handling
            if word_lower.endswith('s') and word_lower[:-1] in keywords:
                return feature
        return None

    def _analyze_clause_sentiment(self, words: List[str]) -> Tuple[float, float]:
        """
        Analyze a list of words. Returns (polarity_score, confidence_score).
        polarity > 0: positive, polarity < 0: negative.
        """
        score = 0.0
        confidence = 0.0
        negated = False
        intensifier = 1.0

        for word in words:
            word_lower = word.lower()
            if word_lower in self.NEGATORS:
                negated = not negated
                continue
            if word_lower in self.INTENSIFIERS:
                intensifier = 1.5
                continue

            sentiment_val = 0.0
            if word_lower in self.POSITIVE_WORDS:
                sentiment_val = 1.0
            elif word_lower in self.NEGATIVE_WORDS:
                sentiment_val = -1.0

            if sentiment_val != 0:
                final_val = sentiment_val * intensifier
                if negated:
                    final_val *= -0.5  # not perfect -> typically mildly negative or neutral
                
                score += final_val
                confidence += 0.5 * intensifier
                
                # reset modifiers after applying
                negated = False
                intensifier = 1.0

        confidence = min(1.0, confidence)
        return score, confidence

    def extract_features(self, text: str) -> List[Dict]:
        """
        Extract features discussed in the text and assign sentiment.
        """
        features_found = {}
        
        # Split into clauses to localize sentiment to features mentioned nearby
        clauses = self.CLAUSE_SPLIT_PATTERN.split(text)
        
        for clause in clauses:
            if not clause or len(clause.strip()) < 3:
                continue
            
            words = [w.strip() for w in clause.split()]
            clause_features = set()
            
            for word in words:
                feat = self._get_feature_mapping(word)
                if feat:
                    clause_features.add(feat)

            if clause_features:
                polarity, confidence = self._analyze_clause_sentiment(words)
                
                for feat in clause_features:
                    if feat not in features_found:
                        features_found[feat] = {"score": 0.0, "confidence": 0.0, "mentions": 0, "evidence": clause.strip()}
                    
                    features_found[feat]["score"] += polarity
                    features_found[feat]["confidence"] = max(features_found[feat]["confidence"], confidence)
                    features_found[feat]["mentions"] += 1
                    # keep the longest evidence or aggregate
                    if len(clause.strip()) > len(features_found[feat]["evidence"]):
                        features_found[feat]["evidence"] = clause.strip()

        # Finalize feature array
        results = []
        for feat, data in features_found.items():
            avg_score = data["score"] / data["mentions"] if data["mentions"] > 0 else 0
            
            if avg_score > 0.5:
                sentiment_str = "positive"
            elif avg_score < -0.5:
                sentiment_str = "negative"
            elif -0.5 <= avg_score <= 0.5 and data["mentions"] > 1 and abs(data["score"]) < 1.0:
                sentiment_str = "mixed"
            else:
                sentiment_str = "neutral"

            # Base confidence bump if mentioned multiple times
            final_conf = min(1.0, data["confidence"] + (0.1 * (data["mentions"] - 1)))
            if final_conf < 0.2:
                final_conf = 0.5 # default moderate confidence if implied

            results.append({
                "feature": feat,
                "sentiment": sentiment_str,
                "confidence": round(final_conf, 2),
                "evidence": data["evidence"]
            })

        return results

    def detect_ambiguity(self, text: str, rating: Optional[float], features: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Detect if a review is sarcastic, contradictory, or ambiguous.
        """
        flags = []
        is_ambiguous = False
        text_lower = text.lower()

        # 1. Rating Mismatch
        has_positive_features = any(f["sentiment"] == "positive" for f in features)
        has_negative_features = any(f["sentiment"] == "negative" for f in features)
        
        words = [w.strip() for w in text_lower.split()]
        overall_pol, _ = self._analyze_clause_sentiment(words)

        if rating is not None:
            if rating >= 4 and (has_negative_features and not has_positive_features):
                flags.append("High rating but solely negative features extracted")
                is_ambiguous = True
            elif rating >= 4 and overall_pol < -1.0:
                flags.append("High rating but strong negative text")
                is_ambiguous = True
            elif rating <= 2 and (has_positive_features and not has_negative_features):
                flags.append("Low rating but solely positive features extracted")
                is_ambiguous = True
            elif rating <= 2 and overall_pol > 1.0:
                flags.append("Low rating but strong positive text")
                is_ambiguous = True

        # 2. Sarcasm Patterns
        sarcasm_patterns = [
            r"oh great",
            r"just what i needed",
            r"love how it does\s?n't",
            r"what a joke",
            r"thanks for nothing",
            r"brilliant design", # when negative rating
            r"yeah, right"
        ]
        
        for pat in sarcasm_patterns:
            if re.search(pat, text_lower):
                if rating is not None and rating <= 3:
                     flags.append(f"Potential sarcasm detected ('{pat.replace(r'\s?', ' ')}')")
                     is_ambiguous = True

        # 3. Exactly Mixed (Conflict)
        if len(features) >= 2 and has_positive_features and has_negative_features:
            pos_len = len([f for f in features if f["sentiment"] == "positive"])
            neg_len = len([f for f in features if f["sentiment"] == "negative"])
            # If equally split, we don't necessarily call it *ambiguous*, just 'mixed' overall.
            # But if the rating is extreme (1 or 5), it's mildly contradictory.
            if pos_len == neg_len and rating in [1, 5, 1.0, 5.0]:
                flags.append(f"Extreme rating ({rating}★) but perfectly mixed feedback")
                is_ambiguous = True

        return is_ambiguous, flags

    def analyze(self, text: str, rating: Optional[float] = None) -> Dict:
        """
        Full analysis suite for a review returning features, overall sentiment, and ambiguity.
        """
        features_extracted = self.extract_features(text)
        is_ambig, ambig_flags = self.detect_ambiguity(text, rating, features_extracted)

        # Compute overall sentiment
        words = text.split()
        overall_pol, _ = self._analyze_clause_sentiment(words)
        
        # Consider features
        feature_score = 0
        for f in features_extracted:
            if f["sentiment"] == "positive": feature_score += 1.0
            elif f["sentiment"] == "negative": feature_score -= 1.0
            
        combined_score = overall_pol + feature_score
        
        pos_f = sum(1 for f in features_extracted if f["sentiment"] == "positive")
        neg_f = sum(1 for f in features_extracted if f["sentiment"] == "negative")

        if is_ambig and 'sarcasm' in (' '.join(ambig_flags)).lower():
            # If it's pure sarcasm typically it's negative in reality, or mixed
            sentiment_label = "mixed"
        elif pos_f > 0 and neg_f > 0 and abs(pos_f - neg_f) <= 1:
            sentiment_label = "mixed"
        elif combined_score >= 3.0:
            sentiment_label = "very_positive"
        elif combined_score > 0.5:
            sentiment_label = "positive"
        elif combined_score <= -3.0:
            sentiment_label = "very_negative"
        elif combined_score < -0.5:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        return {
            "overall_sentiment": sentiment_label,
            "overall_sentiment_score": round(combined_score, 2),
            "features": features_extracted,
            "is_ambiguous": is_ambig,
            "ambiguity_flags": ambig_flags
        }
