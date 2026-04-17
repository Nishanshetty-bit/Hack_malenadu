"""Quick check of fake scores in the database."""
import json
import urllib.request

data = json.loads(urllib.request.urlopen("http://localhost:8000/reviews?limit=50").read())
reviews = data["reviews"]

# Sort by fake_score descending
reviews.sort(key=lambda r: r.get("fake_score", 0), reverse=True)

print(f"Total reviews: {len(reviews)}")
print(f"{'#':>3} {'Score':>6} {'Sus':>4} {'Text':<65} Flags")
print("-" * 120)
for i, r in enumerate(reviews[:20]):
    text = r["original_text"][:62].replace("\n", " ")
    score = r.get("fake_score", 0)
    sus = "YES" if r.get("is_suspicious") else "no"
    flags = r.get("fake_flags", [])
    flag_str = "; ".join(flags[:2]) if flags else ""
    print(f"{i+1:>3} {score:>6.3f} {sus:>4} {text:<65} {flag_str}")
