import json
from models.fake_review_detector import FakeReviewDetector
from models.deduplicator import ReviewDeduplicator
from models.sentiment_analyzer import SentimentAnalyzer

def test_fake_detector():
    detector = FakeReviewDetector()
    samples = [
        "Good product",
        "AWESOME!!",
        "Great.",
        "Exactly as described. I love this product. Fast shipping great product. Five stars.",
        "Terrible product. Battery drains instantly after taking it off the charger.",
        "T h i s i s f a k e a a a a a",
    ]
    print("--- FAKE DETECTOR ---")
    for text in samples:
        res = detector.analyze(text)
        print(f"Score: {res['fake_score']:<5} | Sus: {res['is_suspicious']:<5} | Text: {text}")

def test_deduplicator():
    dedup = ReviewDeduplicator()
    samples = [
        "The battery life is really bad right now.",
        "The battery life is really bad right now..",
        "Battery life is really bad right now.",
        "The screen crackd easily",
        "screen cracked easily",
        "completely different review here"
    ]
    print("\n--- DEDUPLICATOR ---")
    res = dedup.deduplicate(samples)
    print("Exact Groups:", len(res["exact_duplicates"]))
    print("Near Groups:", len(res["near_duplicate_clusters"]))
    for g in res["near_duplicate_clusters"]:
        print(f"Cluster texts:")
        for idx in g["indices"]:
            print(f" - {samples[idx]}")

def test_sentiment():
    analyzer = SentimentAnalyzer()
    samples = [
        "The battry is terrible but the scren is so gorgeous",
        "Not entirely bad overall",
        "Yeah, right, totally a brilliant design",
    ]
    print("\n--- SENTIMENT & ASPECT ---")
    for s in samples:
        res = analyzer.analyze(s, rating=2.0)
        print(f"Text: {s}")
        print(f" Overall: {res['overall_sentiment']}")
        for f in res['features']:
            print(f"  Feature: {f['feature']} -> {f['sentiment']} ({f['confidence']})")
        print(f"  Ambig: {res['is_ambiguous']} -> {res['ambiguity_flags']}")

if __name__ == "__main__":
    test_fake_detector()
    test_deduplicator()
    test_sentiment()
