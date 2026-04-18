"""
InsightIQ 2.0 — FastAPI Backend
Customer Review Intelligence Platform - Data Ingestion & Preprocessing API
"""

import os
import io
import csv
import json
import traceback
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import database as db
from models.preprocessor import TextPreprocessor
from models.fake_review_detector import FakeReviewDetector
from models.deduplicator import ReviewDeduplicator
from models.language_processor import LanguageProcessor
from models.sentiment_analyzer import SentimentAnalyzer
from models.trend_analyzer import TrendAnalyzer

# ─── App Setup ────────────────────────────────────────────────────

app = FastAPI(
    title="InsightIQ 2.0",
    description="AI-Powered Customer Review Intelligence Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Initialize ML Models ────────────────────────────────────────

preprocessor = TextPreprocessor()
fake_detector = FakeReviewDetector()
deduplicator = ReviewDeduplicator(similarity_threshold=0.85)
language_processor = LanguageProcessor()
sentiment_analyzer = SentimentAnalyzer()
trend_analyzer = TrendAnalyzer()

print("[InsightIQ] All models initialized.")


# ─── Pydantic Models ─────────────────────────────────────────────

class PasteRequest(BaseModel):
    text: str
    source: str = "manual_paste"

class APIFeedRequest(BaseModel):
    reviews: List[Dict[str, Any]]
    source: str = "api_feed"

class AnalyzeRequest(BaseModel):
    ingestion_id: Optional[int] = None
    reviews: Optional[List[Dict[str, Any]]] = None


# ─── Helper: Process Review Pipeline ─────────────────────────────

def run_pipeline(raw_reviews: List[Dict], ingestion_id: int) -> Dict:
    """
    Run the full preprocessing pipeline on a batch of reviews:
    1. Text preprocessing (clean noisy input)
    2. Language detection & translation
    3. Deduplication (exact + near-duplicate clustering)
    4. Bot/fake review detection
    5. Granular sentiment extraction & ambiguity detection
    6. Store results in database
    """
    processed = []
    language_counts = {}

    # ── Step 1 & 2: Preprocess + Language Detection ──────────
    for raw in raw_reviews:
        # Support the new data format provided by user
        text = raw.get("review", raw.get("text", raw.get("content", raw.get("original_text", ""))))
        rating = raw.get("rating", raw.get("score", raw.get("stars")))
        original_id = str(raw.get("id", ""))
        user_id = str(raw.get("user_id", ""))

        if rating is not None:
            try:
                rating = float(rating)
            except (ValueError, TypeError):
                rating = None

        # Preprocess (now includes Slang Expansion and Emoji Cleaning)
        prep_result = preprocessor.preprocess(text)

        # Language detection (now includes Hinglish/Kanglish) & translation
        lang_result = language_processor.process_review(prep_result["cleaned_text"])

        # Use translated text for downstream analysis if available
        analysis_text = lang_result.get("translated_text", prep_result["cleaned_text"])

        lang_code = lang_result.get("language_code", "en")
        language_counts[lang_code] = language_counts.get(lang_code, 0) + 1

        processed.append({
            "original_review_id": original_id,
            "user_id": user_id,
            "original_text": text,
            "cleaned_text": prep_result["cleaned_text"],
            "translated_text": analysis_text if lang_result.get("was_translated") else None,
            "detected_language": lang_code,
            "rating": rating,
            "product_category": raw.get("product_category", raw.get("product", raw.get("category", "General"))),
            "review_date": raw.get("date", raw.get("review_date")),
            "preprocessing_notes": prep_result["notes"],
            "emoji_extracted": prep_result.get("emoji_extracted", []),
            "source": raw.get("source", "upload"),
            "ingestion_id": ingestion_id,
        })

    # ── Step 3: Deduplication ────────────────────────────────
    texts_for_dedup = [
        r.get("translated_text") or r["cleaned_text"]
        for r in processed
    ]
    dedup_result = deduplicator.deduplicate(texts_for_dedup)

    # Create clusters in database and mark duplicates
    cluster_id_map = {}  # cluster index → db cluster id
    for i, cluster in enumerate(dedup_result["near_duplicate_clusters"]):
        db_cluster_id = db.insert_cluster(
            representative_text=cluster["representative_text"],
            review_count=cluster["review_count"],
            similarity=cluster["average_similarity"],
        )
        cluster_id_map[i] = db_cluster_id
        # Mark reviews with their cluster
        for idx in cluster["indices"]:
            processed[idx]["cluster_id"] = db_cluster_id
            if idx != cluster["representative_idx"]:
                processed[idx]["is_duplicate"] = 1

    # Also mark exact duplicates
    for h, indices in dedup_result["exact_duplicates"].items():
        for idx in indices[1:]:
            processed[idx]["is_duplicate"] = 1

    # ── Step 4: Fake/Bot Review Detection ────────────────────
    fake_results = fake_detector.batch_analyze([
        {
            "text": r.get("translated_text") or r["cleaned_text"],
            "rating": r.get("rating"),
            "original_text": r["original_text"],
            "user_id": r.get("user_id"),
        }
        for r in processed
    ])

    for i, fake_r in enumerate(fake_results):
        processed[i]["fake_score"] = fake_r["fake_score"]
        processed[i]["is_suspicious"] = 1 if fake_r["is_suspicious"] else 0
        processed[i]["is_bot_user"] = fake_r.get("is_bot_user", 0)
        processed[i]["fake_flags"] = fake_r["flags"]

    # ── Step 5: Granular Sentiment Analysis ──────────────────
    for i, r in enumerate(processed):
        text = r.get("translated_text") or r["cleaned_text"]
        rating = r.get("rating")
        
        sent_result = sentiment_analyzer.analyze(text, rating)
        
        processed[i]["sentiment_label"] = sent_result["overall_sentiment"]
        processed[i]["sentiment_score"] = sent_result["overall_sentiment_score"]
        processed[i]["features"] = sent_result["features"]
        processed[i]["is_ambiguous"] = 1 if sent_result["is_ambiguous"] else 0
        processed[i]["ambiguity_flags"] = sent_result["ambiguity_flags"]

    # ── Step 6: Store in Database ────────────────────────────
    review_ids = db.insert_reviews(processed)

    # Insert feature sentiments
    for i, review_id in enumerate(review_ids):
        db.insert_feature_sentiments(review_id, processed[i].get("features", []))

    # Update ingestion log
    suspicious_count = sum(1 for r in processed if r.get("is_suspicious"))
    duplicate_count = sum(1 for r in processed if r.get("is_duplicate"))
    ambiguous_count = sum(1 for r in processed if r.get("is_ambiguous"))

    db.update_ingestion_log(
        log_id=ingestion_id,
        total_count=len(raw_reviews),
        valid_count=len(raw_reviews) - suspicious_count,
        duplicate_count=duplicate_count,
        suspicious_count=suspicious_count,
        language_distribution=language_counts,
    )

    return {
        "ingestion_id": ingestion_id,
        "total_processed": len(processed),
        "duplicates_found": duplicate_count,
        "suspicious_flagged": suspicious_count,
        "ambiguous_flagged": ambiguous_count,
        "clusters_created": len(dedup_result["near_duplicate_clusters"]),
        "language_distribution": language_counts,
        "dedup_stats": dedup_result["stats"],
        "reviews": [
            {
                "id": review_ids[i],
                "original_text": r["original_text"][:200],
                "cleaned_text": r["cleaned_text"][:200],
                "translated_text": (r.get("translated_text") or "")[:200],
                "detected_language": r["detected_language"],
                "is_duplicate": r.get("is_duplicate", 0),
                "is_suspicious": r.get("is_suspicious", 0),
                "is_ambiguous": r.get("is_ambiguous", 0),
                "fake_score": r.get("fake_score", 0),
                "fake_flags": r.get("fake_flags", []),
                "preprocessing_notes": r.get("preprocessing_notes", []),
                "sentiment_label": r.get("sentiment_label"),
                "sentiment_score": r.get("sentiment_score"),
                "rating": r.get("rating"),
            }
            for i, r in enumerate(processed)
        ],
    }


# ─── Endpoints ────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "InsightIQ 2.0 — Customer Review Intelligence Platform", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ── File Upload (CSV / JSON) ─────────────────────────────────────

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or JSON file containing reviews."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = file.filename.lower().split(".")[-1]
    if ext not in ("csv", "json"):
        raise HTTPException(400, f"Unsupported file type: .{ext}. Use CSV or JSON.")

    content = await file.read()

    try:
        if ext == "csv":
            reviews = _parse_csv(content.decode("utf-8", errors="replace"))
        else:
            reviews = _parse_json(content.decode("utf-8", errors="replace"))
    except Exception as e:
        raise HTTPException(400, f"Failed to parse file: {str(e)}")

    if not reviews:
        raise HTTPException(400, "No reviews found in file")

    # Create ingestion log
    ingestion_id = db.create_ingestion_log("file_upload", file.filename)

    # Run pipeline
    result = run_pipeline(reviews, ingestion_id)

    return JSONResponse(content={
        "success": True,
        "message": f"Processed {len(reviews)} reviews from {file.filename}",
        **result,
    })


def _parse_csv(content: str) -> List[Dict]:
    """Parse CSV content into review dicts. Flexible column detection."""
    reader = csv.DictReader(io.StringIO(content))
    reviews = []

    # Possible column names for review text
    text_columns = ["review", "text", "content", "comment", "feedback", "review_text",
                     "review_body", "body", "message", "description", "Review", "Text"]
    rating_columns = ["rating", "score", "stars", "Rating", "Score", "Stars",
                       "star_rating", "review_rating"]

    for row in reader:
        # Find text column
        text = ""
        for col in text_columns:
            if col in row and row[col]:
                text = row[col]
                break
        if not text:
            # Try first non-empty value
            for v in row.values():
                if v and len(str(v)) > 10:
                    text = str(v)
                    break

        if not text:
            continue

        # Find rating column
        rating = None
        for col in rating_columns:
            if col in row and row[col]:
                try:
                    rating = float(row[col])
                except (ValueError, TypeError):
                    pass
                break

        reviews.append({
            "text": text,
            "rating": rating,
            "source": "csv_upload",
        })

    return reviews


def _parse_json(content: str) -> List[Dict]:
    """Parse JSON content into review dicts. Handles array or object with reviews key."""
    data = json.loads(content)

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Look for common keys containing review arrays
        for key in ["reviews", "data", "items", "results", "feedback"]:
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
        else:
            items = [data]
    else:
        return []

    reviews = []
    for item in items:
        if isinstance(item, str):
            reviews.append({"text": item, "source": "json_upload"})
        elif isinstance(item, dict):
            text = ""
            for key in ["review", "text", "content", "comment", "feedback",
                         "review_text", "body", "message"]:
                if key in item and item[key]:
                    text = str(item[key])
                    break
            if not text:
                continue

            rating = None
            for key in ["rating", "score", "stars"]:
                if key in item:
                    try:
                        rating = float(item[key])
                    except (ValueError, TypeError):
                        pass
                    break

            reviews.append({
                "text": text,
                "rating": rating,
                "source": "json_upload",
                **{k: v for k, v in item.items() if k not in ("text", "review", "content", "rating", "score")},
            })

    return reviews


# ── Manual Paste ──────────────────────────────────────────────────

@app.post("/paste")
async def paste_reviews(req: PasteRequest):
    """Accept manually pasted reviews (JSON or one per line/paragraph)."""
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "No text provided")

    reviews = []
    
    # Try parsing as JSON first
    if (text.startswith("[") and text.endswith("]")) or (text.startswith("{") and text.endswith("}")):
        try:
            reviews = _parse_json(text)
        except Exception:
            # Fall back to line-by-line if JSON parsing fails
            pass

    # Fall back to line-by-line if JSON failed or produced nothing
    if not reviews:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            raise HTTPException(400, "No reviews found in pasted text")
        reviews = [{"text": line, "source": req.source} for line in lines]

    ingestion_id = db.create_ingestion_log("manual_paste")
    result = run_pipeline(reviews, ingestion_id)

    return JSONResponse(content={
        "success": True,
        "message": f"Processed {len(reviews)} pasted reviews",
        **result,
    })


# ── Simulated API Feed ───────────────────────────────────────────

@app.post("/api-feed")
async def api_feed(req: APIFeedRequest):
    """Simulate receiving reviews from an external API feed."""
    if not req.reviews:
        raise HTTPException(400, "No reviews in feed")

    ingestion_id = db.create_ingestion_log("api_feed")
    result = run_pipeline(req.reviews, ingestion_id)

    return JSONResponse(content={
        "success": True,
        "message": f"Processed {len(req.reviews)} reviews from API feed",
        **result,
    })


# ── Load Sample Data ─────────────────────────────────────────────

@app.post("/load-samples")
async def load_samples():
    """Load built-in sample reviews for demo purposes."""
    sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_reviews.json")

    if not os.path.exists(sample_path):
        raise HTTPException(404, "Sample data file not found")

    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    reviews = data if isinstance(data, list) else data.get("reviews", [])

    ingestion_id = db.create_ingestion_log("sample_data", "sample_reviews.json")
    result = run_pipeline(reviews, ingestion_id)

    return JSONResponse(content={
        "success": True,
        "message": f"Loaded {len(reviews)} sample reviews",
        **result,
    })


# ── Query Endpoints ──────────────────────────────────────────────

@app.get("/reviews")
async def get_reviews(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    suspicious: Optional[bool] = None,
    duplicate: Optional[bool] = None,
    language: Optional[str] = None,
    ingestion_id: Optional[int] = None,
):
    """Fetch processed reviews with optional filters."""
    reviews = db.get_reviews(
        limit=limit,
        offset=offset,
        filter_suspicious=suspicious,
        filter_duplicate=duplicate,
        filter_language=language,
        ingestion_id=ingestion_id,
    )
    total = db.get_review_count(ingestion_id)

    return {
        "reviews": reviews,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/stats")
async def get_stats(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get aggregate statistics for the dashboard."""
    return db.get_dashboard_stats(start_date, end_date)


@app.get("/clusters")
async def get_clusters(limit: int = Query(50, ge=1, le=200)):
    """Get deduplication clusters."""
    clusters = db.get_clusters(limit)
    result = []
    for cluster in clusters:
        reviews = db.get_cluster_reviews(cluster["id"])
        result.append({
            **cluster,
            "reviews": reviews,
        })
    return {"clusters": result}


@app.get("/ingestion-logs")
async def get_ingestion_logs(limit: int = Query(20, ge=1, le=100)):
    """Get recent ingestion history."""
    logs = db.get_ingestion_logs(limit)
    return {"logs": logs}


@app.get("/feature-insights")
async def get_feature_insights():
    """Get aggregated feature sentiments."""
    return {"features": db.get_feature_summary()}


@app.get("/ambiguous-reviews")
async def get_ambiguous_reviews(limit: int = Query(50, ge=1, le=200)):
    """Get reviews flagged as ambiguous or sarcastic."""
    return {"reviews": db.get_ambiguous_reviews(limit)}


@app.get("/reviews/{review_id}/features")
async def get_review_features(review_id: int):
    """Get feature sentiments for a specific review."""
    return {"features": db.get_feature_sentiments(review_id)}


@app.get("/trends")
async def get_trends(
    category: str = Query("General"), 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
):
    """Get temporal trends and anomalies for a specific product category."""
    return trend_analyzer.get_trends(category, start_date, end_date)


@app.get("/alerts")
async def get_alerts(
    status: Optional[str] = Query(None),
    team: Optional[str] = Query(None)
):
    """Fetch all active or resolved anomalies."""
    return {"alerts": db.get_alerts(status, team)}


@app.post("/alerts/resolve/{alert_id}")
async def resolve_alert(alert_id: int):
    """Mark an alert as resolved."""
    db.resolve_alert(alert_id)
    return {"success": True, "message": f"Alert {alert_id} resolved"}



# ── Standalone Analysis Endpoints ─────────────────────────────────

@app.post("/detect-fake")
async def detect_fake(review: Dict[str, Any]):
    """Standalone fake review detection."""
    text = review.get("text", "")
    rating = review.get("rating")
    result = fake_detector.analyze(text, rating)
    return result


@app.post("/detect-language")
async def detect_language(review: Dict[str, Any]):
    """Standalone language detection + translation."""
    text = review.get("text", "")
    result = language_processor.process_review(text)
    return result


@app.post("/preprocess")
async def preprocess_text(review: Dict[str, Any]):
    """Standalone text preprocessing."""
    text = review.get("text", "")
    result = preprocessor.preprocess(text)
    return result


@app.post("/analyze-sentiment")
async def analyze_sentiment(review: Dict[str, Any]):
    """Standalone sentiment analysis."""
    text = review.get("text", "")
    rating = review.get("rating")
    return sentiment_analyzer.analyze(text, rating)


# ── Category Cross-Comparison ─────────────────────────────────────

@app.get("/category-comparison")
async def category_comparison():
    """Get per-category aggregated stats for cross-comparison."""
    return {"categories": db.get_category_comparison()}


# ── Downloadable Report ──────────────────────────────────────────

@app.get("/export-report")
async def export_report(format: str = Query("json")):
    """Export comprehensive analytics report as JSON or CSV."""
    report = db.get_report_data()

    if format == "csv":
        # Generate CSV content for reviews
        output = io.StringIO()
        if report["reviews"]:
            fieldnames = [
                "id", "original_text", "detected_language", "rating",
                "sentiment_label", "sentiment_score", "fake_score",
                "is_suspicious", "is_duplicate", "is_ambiguous",
                "product_category", "review_date", "features"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for rev in report["reviews"]:
                row = {**rev}
                row["features"] = "; ".join(
                    f"{f['feature']}({f['sentiment']},{f.get('confidence', 0):.0%})"
                    for f in rev.get("features", [])
                )
                writer.writerow(row)

        return JSONResponse(content={
            "format": "csv",
            "filename": f"insightiq_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "content": output.getvalue(),
            "summary": report["summary"],
            "feature_insights": report["feature_insights"],
            "category_comparison": report["category_comparison"],
        })

    return JSONResponse(content={
        "format": "json",
        "filename": f"insightiq_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        **report,
    })


# ── Reset (for testing) ──────────────────────────────────────────

@app.post("/reset")
async def reset_database():
    """Reset the database (for demo/testing purposes)."""
    conn = db.get_connection()
    conn.execute("DELETE FROM feature_sentiments")
    conn.execute("DELETE FROM reviews")
    conn.execute("DELETE FROM clusters")
    conn.execute("DELETE FROM ingestion_logs")
    conn.commit()
    conn.close()
    return {"success": True, "message": "Database reset successfully"}


# ─── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
