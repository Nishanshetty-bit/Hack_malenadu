"""
InsightIQ 2.0 — Database Layer
SQLite database for storing reviews, clusters, and ingestion logs.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "insightiq.db")


def get_connection():
    """Get a new SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_review_id TEXT,
            user_id TEXT,
            original_text TEXT NOT NULL,
            cleaned_text TEXT,
            translated_text TEXT,
            source TEXT DEFAULT 'manual',
            rating REAL,
            detected_language TEXT DEFAULT 'en',
            is_duplicate INTEGER DEFAULT 0,
            cluster_id INTEGER,
            is_suspicious INTEGER DEFAULT 0,
            is_bot_user INTEGER DEFAULT 0,
            fake_score REAL DEFAULT 0.0,
            fake_flags TEXT DEFAULT '[]',
            preprocessing_notes TEXT DEFAULT '[]',
            sentiment_label TEXT,
            sentiment_score REAL,
            is_ambiguous INTEGER DEFAULT 0,
            ambiguity_flags TEXT DEFAULT '[]',
            product_category TEXT DEFAULT 'General',
            review_date TIMESTAMP,
            ingestion_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cluster_id) REFERENCES clusters(id),
            FOREIGN KEY (ingestion_id) REFERENCES ingestion_logs(id)
        );

        CREATE TABLE IF NOT EXISTS feature_sentiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            feature TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            confidence REAL DEFAULT 0.0,
            evidence TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            representative_text TEXT,
            review_count INTEGER DEFAULT 0,
            similarity_score REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ingestion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            file_name TEXT,
            total_count INTEGER DEFAULT 0,
            valid_count INTEGER DEFAULT 0,
            duplicate_count INTEGER DEFAULT 0,
            suspicious_count INTEGER DEFAULT 0,
            language_distribution TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Try to alter table for existing DBs
    try:
        cursor.execute("ALTER TABLE reviews ADD COLUMN original_review_id TEXT;")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE reviews ADD COLUMN user_id TEXT;")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE reviews ADD COLUMN is_bot_user INTEGER DEFAULT 0;")
    except sqlite3.OperationalError: pass

    try:
        cursor.execute("ALTER TABLE reviews ADD COLUMN is_ambiguous INTEGER DEFAULT 0;")
        cursor.execute("ALTER TABLE reviews ADD COLUMN ambiguity_flags TEXT DEFAULT '[]';")
    except sqlite3.OperationalError:
        pass  # Columns already exist
        
    try:
        cursor.execute("ALTER TABLE reviews ADD COLUMN product_category TEXT DEFAULT 'General';")
        cursor.execute("ALTER TABLE reviews ADD COLUMN review_date TIMESTAMP;")
    except sqlite3.OperationalError:
        pass  # Columns already exist

    conn.commit()
    conn.close()


# ─── Review Operations ────────────────────────────────────────────

def insert_reviews(reviews: List[Dict]) -> List[int]:
    """Insert multiple reviews, return their IDs."""
    conn = get_connection()
    cursor = conn.cursor()
    ids = []

    for r in reviews:
        cursor.execute("""
            INSERT INTO reviews (
                original_review_id, user_id, original_text, cleaned_text, 
                translated_text, source, rating, detected_language, 
                is_duplicate, cluster_id, is_suspicious, is_bot_user,
                fake_score, fake_flags, preprocessing_notes, sentiment_label,
                sentiment_score, is_ambiguous, ambiguity_flags, product_category,
                review_date, ingestion_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r.get("original_review_id"),
            r.get("user_id"),
            r.get("original_text", ""),
            r.get("cleaned_text"),
            r.get("translated_text"),
            r.get("source", "manual"),
            r.get("rating"),
            r.get("detected_language", "en"),
            r.get("is_duplicate", 0),
            r.get("cluster_id"),
            r.get("is_suspicious", 0),
            r.get("is_bot_user", 0),
            r.get("fake_score", 0.0),
            json.dumps(r.get("fake_flags", [])),
            json.dumps(r.get("preprocessing_notes", [])),
            r.get("sentiment_label"),
            r.get("sentiment_score"),
            r.get("is_ambiguous", 0),
            json.dumps(r.get("ambiguity_flags", [])),
            r.get("product_category", "General"),
            r.get("review_date") or datetime.now().isoformat(),
            r.get("ingestion_id"),
        ))
        ids.append(cursor.lastrowid)

    conn.commit()
    conn.close()
    return ids


def get_reviews(
    limit: int = 100,
    offset: int = 0,
    filter_suspicious: Optional[bool] = None,
    filter_duplicate: Optional[bool] = None,
    filter_language: Optional[str] = None,
    ingestion_id: Optional[int] = None,
) -> List[Dict]:
    """Fetch reviews with optional filters."""
    conn = get_connection()
    query = "SELECT * FROM reviews WHERE 1=1"
    params = []

    if filter_suspicious is not None:
        query += " AND is_suspicious = ?"
        params.append(1 if filter_suspicious else 0)
    if filter_duplicate is not None:
        query += " AND is_duplicate = ?"
        params.append(1 if filter_duplicate else 0)
    if filter_language:
        query += " AND detected_language = ?"
        params.append(filter_language)
    if ingestion_id:
        query += " AND ingestion_id = ?"
        params.append(ingestion_id)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        d["fake_flags"] = json.loads(d.get("fake_flags") or "[]")
        d["preprocessing_notes"] = json.loads(d.get("preprocessing_notes") or "[]")
        d["ambiguity_flags"] = json.loads(d.get("ambiguity_flags") or "[]")
        # Fetch features for this review
        d["features"] = get_feature_sentiments(d["id"])
        result.append(d)
    return result


def get_review_count(ingestion_id: Optional[int] = None) -> int:
    """Get total review count."""
    conn = get_connection()
    if ingestion_id:
        count = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE ingestion_id = ?", (ingestion_id,)
        ).fetchone()[0]
    else:
        count = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    conn.close()
    return count


def insert_feature_sentiments(review_id: int, features: List[Dict]):
    """Insert feature-level sentiments for a review."""
    if not features:
        return
    conn = get_connection()
    cursor = conn.cursor()
    for f in features:
        cursor.execute(
            "INSERT INTO feature_sentiments (review_id, feature, sentiment, confidence, evidence) VALUES (?, ?, ?, ?, ?)",
            (review_id, f.get("feature"), f.get("sentiment"), f.get("confidence"), f.get("evidence"))
        )
    conn.commit()
    conn.close()


def get_feature_sentiments(review_id: int) -> List[Dict]:
    """Get features extracted for a specific review."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT feature, sentiment, confidence, evidence FROM feature_sentiments WHERE review_id = ?",
        (review_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_feature_summary() -> List[Dict]:
    """Aggregate feature sentiment distribution."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT feature, sentiment, COUNT(*) as count, AVG(confidence) as avg_confidence
        FROM feature_sentiments
        GROUP BY feature, sentiment
        ORDER BY feature, count DESC
    """).fetchall()
    conn.close()
    
    # Restructure for easier frontend use
    summary = {}
    for r in rows:
        feat = r["feature"]
        if feat not in summary:
            summary[feat] = {"positive": 0, "negative": 0, "mixed": 0, "neutral": 0, "mentions": 0, "avg_confidence": 0}
        
        summary[feat][r["sentiment"]] = r["count"]
        summary[feat]["mentions"] += r["count"]
        # Running average weighting isn't perfect here but good enough for demo
        summary[feat]["avg_confidence"] = r["avg_confidence"]

    result = []
    for feat, stats in summary.items():
        result.append({"feature": feat, **stats})
    
    return sorted(result, key=lambda x: x["mentions"], reverse=True)


def get_ambiguous_reviews(limit: int = 50) -> List[Dict]:
    """Fetch reviews flagged as ambiguous or sarcastic."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reviews WHERE is_ambiguous = 1 ORDER BY created_at DESC LIMIT ?", 
        (limit,)
    ).fetchall()
    conn.close()
    
    result = []
    for row in rows:
        d = dict(row)
        d["fake_flags"] = json.loads(d.get("fake_flags") or "[]")
        d["preprocessing_notes"] = json.loads(d.get("preprocessing_notes") or "[]")
        d["ambiguity_flags"] = json.loads(d.get("ambiguity_flags") or "[]")
        d["features"] = get_feature_sentiments(d["id"])
        result.append(d)
    return result


# ─── Cluster Operations ───────────────────────────────────────────

def insert_cluster(representative_text: str, review_count: int, similarity: float) -> int:
    """Insert a deduplication cluster, return its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clusters (representative_text, review_count, similarity_score) VALUES (?, ?, ?)",
        (representative_text, review_count, similarity),
    )
    cluster_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return cluster_id


def get_clusters(limit: int = 50) -> List[Dict]:
    """Fetch deduplication clusters."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM clusters ORDER BY review_count DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cluster_reviews(cluster_id: int) -> List[Dict]:
    """Get all reviews in a specific cluster."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reviews WHERE cluster_id = ? ORDER BY created_at", (cluster_id,)
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["fake_flags"] = json.loads(d.get("fake_flags") or "[]")
        d["preprocessing_notes"] = json.loads(d.get("preprocessing_notes") or "[]")
        result.append(d)
    return result


# ─── Ingestion Log Operations ─────────────────────────────────────

def create_ingestion_log(source_type: str, file_name: Optional[str] = None) -> int:
    """Create an ingestion log entry, return its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ingestion_logs (source_type, file_name) VALUES (?, ?)",
        (source_type, file_name),
    )
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def update_ingestion_log(
    log_id: int,
    total_count: int = 0,
    valid_count: int = 0,
    duplicate_count: int = 0,
    suspicious_count: int = 0,
    language_distribution: Optional[Dict] = None,
):
    """Update an ingestion log with final stats."""
    conn = get_connection()
    conn.execute("""
        UPDATE ingestion_logs SET
            total_count = ?, valid_count = ?, duplicate_count = ?,
            suspicious_count = ?, language_distribution = ?
        WHERE id = ?
    """, (
        total_count, valid_count, duplicate_count, suspicious_count,
        json.dumps(language_distribution or {}), log_id,
    ))
    conn.commit()
    conn.close()


def get_ingestion_logs(limit: int = 20) -> List[Dict]:
    """Fetch recent ingestion logs."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM ingestion_logs ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["language_distribution"] = json.loads(d.get("language_distribution") or "{}")
        result.append(d)
    return result


# ─── Stats & Analytics ────────────────────────────────────────────

def get_dashboard_stats(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get aggregate statistics for the dashboard, optionally filtered by date."""
    conn = get_connection()
    
    date_filter = ""
    params = []
    
    if start_date and end_date:
        date_filter = "WHERE date(review_date) >= ? AND date(review_date) <= ?"
        params = [start_date, end_date]
    elif start_date:
        date_filter = "WHERE date(review_date) >= ?"
        params = [start_date]
    elif end_date:
        date_filter = "WHERE date(review_date) <= ?"
        params = [end_date]
        
    where_clause = date_filter
    and_clause = "AND " + date_filter[6:] if date_filter else ""

    total = conn.execute(f"SELECT COUNT(*) FROM reviews {where_clause}", params).fetchone()[0]
    suspicious = conn.execute(f"SELECT COUNT(*) FROM reviews WHERE is_suspicious = 1 {and_clause}", params).fetchone()[0]
    duplicates = conn.execute(f"SELECT COUNT(*) FROM reviews WHERE is_duplicate = 1 {and_clause}", params).fetchone()[0]
    ambiguous = conn.execute(f"SELECT COUNT(*) FROM reviews WHERE is_ambiguous = 1 {and_clause}", params).fetchone()[0]
    
    # We won't filter clusters by date for now, as clusters map to many reviews
    clusters = conn.execute("SELECT COUNT(*) FROM clusters").fetchone()[0]

    # Time series data
    ts_rows = conn.execute(
        f"SELECT date(review_date) as day, COUNT(*) as cnt FROM reviews {where_clause} GROUP BY day ORDER BY day",
        params
    ).fetchall()
    time_series = [{"date": row["day"], "reviews": row["cnt"]} for row in ts_rows]

    # Language distribution
    lang_rows = conn.execute(
        f"SELECT detected_language, COUNT(*) as cnt FROM reviews {where_clause} GROUP BY detected_language ORDER BY cnt DESC",
        params
    ).fetchall()
    language_distribution = {row["detected_language"]: row["cnt"] for row in lang_rows}

    # Source distribution
    source_rows = conn.execute(
        f"SELECT source, COUNT(*) as cnt FROM reviews {where_clause} GROUP BY source ORDER BY cnt DESC",
        params
    ).fetchall()
    source_distribution = {row["source"]: row["cnt"] for row in source_rows}

    # Recent ingestions
    recent_ingestions = get_ingestion_logs(5)

    # Average fake score
    avg_fake = conn.execute(f"SELECT AVG(fake_score) FROM reviews {where_clause}", params).fetchone()[0] or 0

    # Sentiment distribution
    sentiment_rows = conn.execute(
        f"SELECT sentiment_label, COUNT(*) as cnt FROM reviews WHERE sentiment_label IS NOT NULL {and_clause} GROUP BY sentiment_label",
        params
    ).fetchall()
    sentiment_distribution = {row["sentiment_label"]: row["cnt"] for row in sentiment_rows}
    
    # Category distribution
    cat_rows = conn.execute(
        f"SELECT product_category, COUNT(*) as cnt FROM reviews {where_clause} GROUP BY product_category ORDER BY cnt DESC",
        params
    ).fetchall()
    top_category = cat_rows[0]["product_category"] if cat_rows else "General"

    conn.close()

    clean_count = total - suspicious - duplicates
    quality_score = round((1 - (suspicious + duplicates) / max(total, 1)) * 100, 1)

    # Generate Dynamic Text Insights
    insights = []
    if total > 0:
        period_text = f"between {start_date} and {end_date}" if start_date and end_date else "in the dataset"
        insights.append(f"Analyzed {total} total reviews {period_text}.")
        insights.append(f"Your overall data quality score sits at {quality_score}%, with {clean_count} definitively clean and unique reviews.")
        if suspicious > 0:
            insights.append(f"We flagged {suspicious} reviews as highly suspicious or bot-generated (avg fake score: {round(avg_fake*100,0)}%), which were isolated from the clean pipeline.")
        else:
            insights.append(f"Excellent! 0 reviews were flagged as fake or bot-generated in this period.")
        insights.append(f"The most discussed product category during this timeframe was '{top_category}'.")
        
        pos = sentiment_distribution.get("positive", 0) + sentiment_distribution.get("very_positive", 0)
        neg = sentiment_distribution.get("negative", 0) + sentiment_distribution.get("very_negative", 0)
        if pos > neg:
            insights.append(f"The general tone leans positive, with {pos} positive reviews vs {neg} negative complaints.")
        elif neg > pos:
            insights.append(f"Sentiment is leaning significantly negative, with {neg} direct complaints dwarfing positive feedback.")
    else:
        insights.append("No reviews found for the selected date range.")

    return {
        "text_insights": insights,
        "time_series": time_series,
        "total_reviews": total,
        "suspicious_count": suspicious,
        "duplicate_count": duplicates,
        "ambiguous_count": ambiguous,
        "cluster_count": clusters,
        "clean_reviews": clean_count,
        "language_distribution": language_distribution,
        "source_distribution": source_distribution,
        "average_fake_score": round(avg_fake, 3),
        "sentiment_distribution": sentiment_distribution,
        "recent_ingestions": recent_ingestions,
        "quality_score": quality_score,
    }


# Initialize on import
init_db()
