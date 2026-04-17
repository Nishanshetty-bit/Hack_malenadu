"""
InsightIQ 2.0 — Trend Analyzer
Detects temporal shifts and emerging issues in feature sentiment.
"""
from typing import List, Dict, Tuple
from datetime import datetime
import database as db

class TrendAnalyzer:
    def __init__(self):
        pass

    def get_trends(self, category: str = "Smartwatch") -> Dict:
        """
        Calculates sentiment distribution shifts comparing the 'recent' 
        window to the 'historical' window for a given category.
        Uses simplistic ID bucketing (or date parsing) to proxy time.
        """
        conn = db.get_connection()
        # Fetch reviews for category
        reviews = conn.execute(
            "SELECT id, review_date FROM reviews WHERE product_category = ? ORDER BY review_date DESC", 
            (category,)
        ).fetchall()
        
        if len(reviews) < 20: # Not enough data
            conn.close()
            return {"status": "insufficient_data", "alerts": [], "features": {}}

        # Define 'recent' as the most recent 20% of reviews or up to 50
        num_recent = min(len(reviews) // 5 + 10, 50)
        recent_ids = [r["id"] for r in reviews[:num_recent]]
        hist_ids = [r["id"] for r in reviews[num_recent:]]

        # Fetch feature sentiments
        def fetch_bucket_features(ids: List[int]) -> Dict:
            if not ids: return {}
            placeholders = ",".join("?" * len(ids))
            query = f"""
                SELECT feature, sentiment, COUNT(*) as count 
                FROM feature_sentiments 
                WHERE review_id IN ({placeholders})
                GROUP BY feature, sentiment
            """
            rows = conn.execute(query, ids).fetchall()
            
            stats = {}
            for r in rows:
                feat = r["feature"]
                sent = r["sentiment"]
                if feat not in stats:
                    stats[feat] = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0, "total": 0}
                stats[feat][sent] = r["count"]
                stats[feat]["total"] += r["count"]
            return stats

        recent_stats = fetch_bucket_features(recent_ids)
        hist_stats = fetch_bucket_features(hist_ids)
        conn.close()

        # Compare and generate alerts
        alerts = []
        feature_trends = {}

        for feat in set(list(recent_stats.keys()) + list(hist_stats.keys())):
            r_stat = recent_stats.get(feat, {"negative": 0, "positive": 0, "total": 0})
            h_stat = hist_stats.get(feat, {"negative": 0, "positive": 0, "total": 0})

            # Calculate rates
            r_total_reviews = max(len(recent_ids), 1)
            h_total_reviews = max(len(hist_ids), 1)

            # Feature mention rate
            r_mention_rate = r_stat["total"] / r_total_reviews
            h_mention_rate = h_stat["total"] / h_total_reviews

            # Negative rate (complaints)
            r_neg_rate = r_stat["negative"] / r_total_reviews
            h_neg_rate = h_stat["negative"] / h_total_reviews

            # Positive rate (praise)
            r_pos_rate = r_stat["positive"] / r_total_reviews
            h_pos_rate = h_stat["positive"] / h_total_reviews

            feature_trends[feat] = {
                "recent_mentions": r_stat["total"],
                "hist_mentions": h_stat["total"],
                "recent_negative_pct": round(r_neg_rate * 100, 1),
                "hist_negative_pct": round(h_neg_rate * 100, 1),
                "recent_positive_pct": round(r_pos_rate * 100, 1),
                "hist_positive_pct": round(h_pos_rate * 100, 1)
            }

            # Anomaly rules (Systemic Issue Detection)
            # Defect Spike
            if r_neg_rate > 0.15 and (r_neg_rate - h_neg_rate) > 0.20:
                alerts.append({
                    "severity": "critical",
                    "feature": feat,
                    "type": "Defect Spike",
                    "message": f"'{feat.capitalize()}' complaints have appeared in {r_neg_rate*100:.0f}% of recent reviews, up from {h_neg_rate*100:.0f}% historically. This indicates a systemic issue."
                })
            
            # Approaching Warning
            elif r_neg_rate > 0.10 and (r_neg_rate - h_neg_rate) > 0.10:
                alerts.append({
                    "severity": "warning",
                    "feature": feat,
                    "type": "Emerging Concern",
                    "message": f"Negative sentiment for '{feat}' is trending upward ({r_neg_rate*100:.0f}% recent vs {h_neg_rate*100:.0f}% historic)."
                })

            # Praise Trend
            elif r_pos_rate > 0.20 and (r_pos_rate - h_pos_rate) > 0.15:
                alerts.append({
                    "severity": "success",
                    "feature": feat,
                    "type": "Praise Trend",
                    "message": f"Customers are increasingly loving the '{feat}'! Mentions spiked to {r_pos_rate*100:.0f}%, up from {h_pos_rate*100:.0f}%."
                })

        # Sort alerts by severity
        severity_order = {"critical": 0, "warning": 1, "success": 2}
        alerts.sort(key=lambda x: severity_order[x["severity"]])

        return {
            "status": "success",
            "category": category,
            "recent_bucket_size": len(recent_ids),
            "hist_bucket_size": len(hist_ids),
            "alerts": alerts,
            "trends": feature_trends
        }

