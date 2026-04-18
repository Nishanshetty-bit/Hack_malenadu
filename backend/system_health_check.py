import requests
import time
import json

API = "http://localhost:8000"

def check_system():
    print("--- 🚀 STARTING SYSTEM HEALTH CHECK 🚀 ---")
    
    # 1. Check Endpoints
    try:
        res = requests.get(API)
        print(f"[OK] Root: {res.json()['message']}")
        res = requests.get(f"{API}/health")
        print(f"[OK] Health: {res.json()['status']}")
    except:
        print("[FAIL] Could not reach backend. Is main.py running?")
        return

    # 2. Reset and Load Samples
    print("\n--- 📥 DATA INGESTION ---")
    requests.post(f"{API}/reset")
    res = requests.post(f"{API}/load-samples")
    total = res.json().get('total_processed', 0)
    print(f"[OK] Loaded {total} sample reviews.")

    # 3. Verify Models
    print("\n--- 🤖 MODEL VALIDATION ---")
    
    # Test Spaced Text Detection
    test_reviews = [
        {"text": "T h i s i s f a k e r e v i e w", "rating": 5.0, "source": "test"},
        {"text": "The battery life is really bad right now.", "rating": 1.0, "source": "test"}, # Duplicate test
        {"text": "ye phone mast hai bhai 👍🔥", "rating": 5.0, "source": "test"} # Hindi/Hinglish test
    ]
    res = requests.post(f"{API}/api-feed", json={"reviews": test_reviews})
    data = res.json()
    
    # Check spaced text detection
    spaced_review = next((r for r in data['reviews'] if "spaced out text" in str(r.get('fake_flags', [])).lower() or r.get('fake_score', 0) > 0.4), None)
    if spaced_review:
        print(f"[OK] Spaced-out text detected. Score: {spaced_review['fake_score']}")
    else:
        print("[FAIL] Spaced-out text was NOT detected.")

    # Check language detection
    hindi_review = next((r for r in data['reviews'] if r['detected_language'] in ('hi', 'hinglish')), None)
    if hindi_review:
        print(f"[OK] Hinglish/Hindi detected correctly: {hindi_review['detected_language']}")
    else:
        print(f"[FAIL] Hinglish detection failed. Detected: {data['reviews'][-1].get('detected_language')}")

    # 4. Verify Trend Logic (The new Dynamic Date Detection)
    print("\n--- 📈 TREND LOGIC VALIDATION ---")
    res = requests.get(f"{API}/trends?category=Smartwatch")
    trends = res.json()
    if trends.get('status') == 'success':
        r_range = trends.get('recent_range', {})
        print(f"[OK] Trend window detected: {r_range.get('start')} to {r_range.get('end')}")
        print(f"[OK] Recent batch size: {trends.get('recent_bucket_size')}")
        print(f"[OK] Historical batch size: {trends.get('hist_bucket_size')}")
    else:
        print(f"[FAIL] Trend analysis failed: {trends.get('status')}")

    print("\n--- ✅ HEALTH CHECK COMPLETE ---")

if __name__ == "__main__":
    check_system()
