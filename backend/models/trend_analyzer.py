"""
InsightIQ 2.0 — Trend Analyzer
Detects temporal shifts and emerging issues in feature sentiment.
"""
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import database as db

class TrendAnalyzer:
    def __init__(self):
        pass

    def get_trends(self, category: str = "Smartwatch", start_date: str = None, end_date: str = None, persist: bool = True) -> Dict:
        """
        Calculates sentiment distribution shifts comparing the 'recent' 
        window to the 'historical' window for a given category.
        Uses date windowing if start_date and end_date are provided.
        
        Key logic:
        - Negative/positive RATES are calculated as: 
          (neg_mentions_for_feature / total_mentions_for_feature) within each bucket.
        - This gives a true per-feature sentiment ratio, not diluted by total reviews.
        - Alerts fire when the recent feature-negative-ratio significantly exceeds historical.
        """
        conn = db.get_connection()
        
        query = "SELECT id, review_date FROM reviews"
        params = []
        if category != "General":
            query += " WHERE product_category = ?"
            params.append(category)
        query += " ORDER BY review_date DESC"
        
        reviews = conn.execute(query, tuple(params)).fetchall()
        
        if len(reviews) < 15:
            conn.close()
            return {"status": "insufficient_data", "alerts": [], "features": {}}

        recent_ids = []
        hist_ids = []
        recent_range = None

        if start_date and end_date:
            for r in reviews:
                r_date_str = r["review_date"]
                if not r_date_str:
                    continue
                if start_date <= r_date_str[:10] <= end_date:
                    recent_ids.append(r["id"])
                elif r_date_str[:10] < start_date:
                    hist_ids.append(r["id"])
            recent_range = {"start": start_date, "end": end_date}
        else:
            # DYNAMIC DATE DETECTION
            valid_dates = [r["review_date"][:10] for r in reviews if r["review_date"]]
            if not valid_dates:
                num_recent = max(5, len(reviews) // 5)
                recent_ids = [r["id"] for r in reviews[:num_recent]]
                hist_ids = [r["id"] for r in reviews[num_recent:]]
                recent_range = {"start": "Index-Split", "end": "Index-Split"}
            else:
                max_date_str = max(valid_dates)
                max_dt = datetime.strptime(max_date_str, "%Y-%m-%d")
                
                lookback_days = 7
                min_recent_threshold = 10
                
                while lookback_days < 90:
                    cut_off_dt = max_dt - timedelta(days=lookback_days)
                    cut_off_str = cut_off_dt.strftime("%Y-%m-%d")
                    
                    temp_recent = [r["id"] for r in reviews if r["review_date"] and r["review_date"][:10] >= cut_off_str]
                    
                    if len(temp_recent) >= min_recent_threshold or lookback_days >= 30:
                        recent_ids = temp_recent
                        recent_id_set = set(recent_ids)
                        hist_ids = [r["id"] for r in reviews if r["id"] not in recent_id_set]
                        recent_range = {"start": cut_off_str, "end": max_date_str}
                        break
                    lookback_days += 7
                
                if not recent_ids:
                    num_recent = max(5, len(reviews) // 5)
                    recent_ids = [r["id"] for r in reviews[:num_recent]]
                    hist_ids = [r["id"] for r in reviews[num_recent:]]
                    recent_range = {"start": "Fallback", "end": max_date_str}

        # Fetch feature sentiments per bucket
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

        if persist:
            db.clear_stale_alerts()

        all_features = set(list(recent_stats.keys()) + list(hist_stats.keys()))

        for feat in all_features:
            r_stat = recent_stats.get(feat, {"negative": 0, "positive": 0, "neutral": 0, "mixed": 0, "total": 0})
            h_stat = hist_stats.get(feat, {"negative": 0, "positive": 0, "neutral": 0, "mixed": 0, "total": 0})

            r_total = max(r_stat["total"], 1)
            h_total = max(h_stat["total"], 1)

            # Calculate rates relative to the feature's own mention count in each bucket
            # This gives the TRUE sentiment ratio for each feature
            r_neg_rate = r_stat["negative"] / r_total
            h_neg_rate = h_stat["negative"] / h_total
            r_pos_rate = r_stat["positive"] / r_total
            h_pos_rate = h_stat["positive"] / h_total

            # Also compute volume change to detect emerging vs vanishing features
            volume_change = r_stat["total"] - h_stat["total"]

            feature_trends[feat] = {
                "recent_mentions": r_stat["total"],
                "hist_mentions": h_stat["total"],
                "recent_negative_pct": round(r_neg_rate * 100, 1),
                "hist_negative_pct": round(h_neg_rate * 100, 1),
                "recent_positive_pct": round(r_pos_rate * 100, 1),
                "hist_positive_pct": round(h_pos_rate * 100, 1),
                "volume_change": volume_change,
            }

            # Skip features with too few recent mentions (noise filtering)
            if r_stat["total"] < 3 and h_stat["total"] < 3:
                continue

            # Team Mapping Logic
            feature_lower = feat.lower()
            if any(w in feature_lower for w in ["delivery", "packaging", "shipping", "arrive", "box"]):
                assigned_team = "Logistics Team"
            elif any(w in feature_lower for w in ["battery", "screen", "software", "mic", "display", "audio", "gps", "camera", "sensor", "hardware"]):
                assigned_team = "Engineering Team"
            elif any(w in feature_lower for w in ["price", "subscription", "refund", "cost", "value", "deal"]):
                assigned_team = "Management Team"
            else:
                assigned_team = "Customer Support"

            time_range_msg = f"between {start_date} and {end_date}" if (start_date and end_date) else "recently"

            # Anomaly Rules (now based on per-feature ratios)
            alert = None
            neg_delta = r_neg_rate - h_neg_rate
            pos_delta = r_pos_rate - h_pos_rate
            
            # 1. Defect Spike: feature negative ratio jumped significantly
            #    e.g. battery went from 19% negative to 82% negative
            if r_neg_rate > 0.30 and neg_delta > 0.15:
                alert = {
                    "severity": "critical",
                    "feature": feat,
                    "type": "Defect Spike",
                    "assigned_team": assigned_team,
                    "message": f"CRITICAL: '{feat}' negative ratio surged to {r_neg_rate*100:.0f}% (was {h_neg_rate*100:.0f}%) {time_range_msg}. {r_stat['negative']} complaints in {r_stat['total']} mentions. Routing to {assigned_team}.",
                    "recent_pct": round(r_neg_rate * 100, 1),
                    "hist_pct": round(h_neg_rate * 100, 1),
                }
            
            # 2. Emerging Concern: moderate negative jump
            elif r_neg_rate > 0.20 and neg_delta > 0.10:
                alert = {
                    "severity": "warning",
                    "feature": feat,
                    "type": "Emerging Concern",
                    "assigned_team": assigned_team,
                    "message": f"WARNING: '{feat}' negativity rose to {r_neg_rate*100:.0f}% (was {h_neg_rate*100:.0f}% historic). Monitor {assigned_team}.",
                    "recent_pct": round(r_neg_rate * 100, 1),
                    "hist_pct": round(h_neg_rate * 100, 1),
                }

            # 3. Praise Trend: significant positive jump
            elif r_pos_rate > 0.40 and pos_delta > 0.15:
                alert = {
                    "severity": "success",
                    "feature": feat,
                    "type": "Praise Trend",
                    "assigned_team": assigned_team,
                    "message": f"EXCELLENT: Users are loving '{feat}'! Positive ratio grew to {r_pos_rate*100:.0f}% (was {h_pos_rate*100:.0f}%) {time_range_msg}.",
                    "recent_pct": round(r_pos_rate * 100, 1),
                    "hist_pct": round(h_pos_rate * 100, 1),
                }

            if alert:
                alerts.append(alert)
                if persist:
                    db.insert_alert(alert)

        # Sort alerts by severity
        severity_order = {"critical": 0, "warning": 1, "success": 2}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))

        return {
            "status": "success",
            "category": category,
            "recent_bucket_size": len(recent_ids),
            "hist_bucket_size": len(hist_ids),
            "alerts": alerts,
            "trends": feature_trends,
            "recent_range": recent_range
        }
