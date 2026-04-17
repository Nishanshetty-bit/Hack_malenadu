"""
Generates 200+ synthetic reviews across three categories: Smartphone, Smartwatch, and Headphones.
Includes dates to simulate history, noise, multiple languages, and a specific seeded anomaly
in the Smartwatch category (battery issues emerging in the last 2 weeks).
"""
import json
import random
import os
from datetime import datetime, timedelta

def get_random_date(start_days_ago, end_days_ago):
    delta = start_days_ago - end_days_ago
    random_days = random.randint(0, delta)
    random_hours = random.randint(0, 23)
    return (datetime.now() - timedelta(days=end_days_ago + random_days, hours=random_hours)).isoformat()

def generate_data():
    reviews = []
    
    # --- Category: Smartphone (General noise, some positive, some negative) ---
    smartphone_templates = [
        ("The camera on this phone is out of this world! But battery life is just okay.", 4),
        ("Terrible build quality. The screen cracked after a week.", 1),
        ("ye phone bohot accha hai 🔥 camera mast hai", 5),
        ("Software updates have been consistent. The UI is very smooth.", 5),
        ("GPS is totally broken. Very frustrating when driving.", 2),
        ("Overall decent phone. Price could be better though.", 3),
        ("Fast charging is insane! Fully charged in 30 mins.", 5),
        ("Phone gets very hot during gaming...", 2),
        ("Amazing product. Love the display and audio.", 5),
        ("Speaker quality is mediocre. Sounds tinny.", 2)
    ]
    
    for _ in range(80):
        t, r = random.choice(smartphone_templates)
        # Randomize a bit of noise
        if random.random() > 0.8: t += " " + "".join(random.choices("!@#$%^&*()_+", k=5))
        reviews.append({
            "product_category": "Smartphone",
            "text": t,
            "rating": r,
            "date": get_random_date(90, 1), # Last 90 days
            "source": "synthetic"
        })

    # --- Category: Headphones (Consistent positive trend for audio, mixed build) ---
    headphone_templates = [
        ("Bass is incredible! Better than my previous earphones.", 5),
        ("Audio quality is crisp, ANC works wonders.", 5),
        ("El sonido es muy bueno, pero los botones son de plástico barato.", 4),
        ("Left earbud stopped syncing after 1 month.", 1),
        ("Battery lasts literally forever. I charge it once a week.", 5),
        ("Connection drops constantly when I'm outdoors.", 2),
        ("Super comfortable for long listening sessions.", 5),
        ("Mic quality is garbage on Zoom calls.", 2)
    ]
    
    for _ in range(60):
        t, r = random.choice(headphone_templates)
        reviews.append({
            "product_category": "Headphones",
            "text": t,
            "rating": r,
            "date": get_random_date(90, 1),
            "source": "synthetic"
        })

    # --- Category: Smartwatch (THE ANOMALY SEEDING) ---
    # Historical (90 days ago to 15 days ago): Praise battery and screen.
    smartwatch_hist = [
        ("Battery easily lasts 3 days. Love not having to charge it daily.", 5),
        ("Display is vibrant even in direct sunlight.", 5),
        ("Fitness tracking is okay, heartbeat sensor is accurate.", 4),
        ("Step counter is entirely wrong. Compared it with another device.", 2),
        ("Fantastic smartwatch. The battery life is its best feature.", 5),
        ("Very slow UI. Swiping lags sometimes.", 3)
    ]
    
    for _ in range(40):
        t, r = random.choice(smartwatch_hist)
        reviews.append({
            "product_category": "Smartwatch",
            "text": t,
            "rating": r,
            "date": get_random_date(90, 15), # HISTORICAL
            "source": "synthetic"
        })
        
    # Recent (Last 14 days): Massive spike in "Battery" complaints (Defect Spike)
    smartwatch_recent_anomaly = [
        ("Ever since the last update, battery drains in 3 hours! Terrible.", 1),
        ("What happened to the battery life? It doesn't even last half a day now.", 1),
        ("Display is still nice, but the battery requires charging twice a day.", 2),
        ("Useless. Battery dies instantly after taking it off the charger.", 1),
        ("Amazing watch but the recent battery drain issue makes it a paperweight.", 2),
        ("Fitness tracking still works, but I can't track sleep because it dies overnight.", 2),
        ("Terrible battery. Don't buy right now.", 1)
    ]
    
    for _ in range(35):
        t, r = random.choice(smartwatch_recent_anomaly)
        reviews.append({
            "product_category": "Smartwatch",
            "text": t,
            "rating": r,
            "date": get_random_date(14, 0), # RECENT
            "source": "synthetic"
        })

    # Sort reviews by date descending
    reviews.sort(key=lambda x: x["date"], reverse=True)

    out_path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_reviews.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)
        
    print(f"Generated {len(reviews)} synthetic reviews with seeded anomalies to {out_path}.")

if __name__ == "__main__":
    generate_data()
