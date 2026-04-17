"""
InsightIQ 2.0 — Review Deduplicator
Uses TF-IDF vectorization + cosine similarity for near-duplicate detection,
with exact-match deduplication as a fast first pass.
"""

import hashlib
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class ReviewDeduplicator:
    """
    Detect exact and near-duplicate reviews using:
    1. Exact hash matching (fast first pass)
    2. TF-IDF + cosine similarity (near-duplicate clustering)
    """

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: Cosine similarity threshold for near-duplicates (0-1).
                                  Higher = stricter matching. Default 0.85.
        """
        self.similarity_threshold = similarity_threshold

    def _normalize_for_hash(self, text: str) -> str:
        """Normalize text for exact-match comparison."""
        import re
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def _hash_text(self, text: str) -> str:
        """Generate MD5 hash for normalized text."""
        normalized = self._normalize_for_hash(text)
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def find_exact_duplicates(self, texts: List[str]) -> Dict:
        """
        Find exact duplicates using hash matching.
        Returns dict mapping hash → list of indices.
        """
        hash_groups = defaultdict(list)
        for i, text in enumerate(texts):
            h = self._hash_text(text)
            hash_groups[h].append(i)

        # Only return groups with duplicates
        return {h: indices for h, indices in hash_groups.items() if len(indices) > 1}

    def find_near_duplicates(self, texts: List[str]) -> List[Dict]:
        """
        Find near-duplicate clusters using TF-IDF + cosine similarity.
        Returns list of cluster dicts, each with:
        - indices: list of review indices in the cluster
        - representative_idx: index of the representative review
        - similarity_scores: pairwise similarities
        """
        if not SKLEARN_AVAILABLE:
            # Fallback: use simple character-level Jaccard similarity
            return self._jaccard_fallback(texts)

        if len(texts) < 2:
            return []

        # Build TF-IDF matrix
        try:
            vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
        except ValueError:
            # All texts might be empty or too short
            return []

        # Compute pairwise cosine similarity
        sim_matrix = cosine_similarity(tfidf_matrix)

        # Find clusters using union-find
        n = len(texts)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Build edges for similar pairs
        for i in range(n):
            for j in range(i + 1, n):
                if sim_matrix[i][j] >= self.similarity_threshold:
                    union(i, j)

        # Group by cluster
        cluster_map = defaultdict(list)
        for i in range(n):
            cluster_map[find(i)].append(i)

        # Build cluster results (only groups with >1 member)
        clusters = []
        for root, indices in cluster_map.items():
            if len(indices) > 1:
                # Find representative (longest text in cluster)
                representative_idx = max(indices, key=lambda i: len(texts[i]))

                # Compute average similarity within cluster
                sims = []
                for i_idx in range(len(indices)):
                    for j_idx in range(i_idx + 1, len(indices)):
                        sims.append(sim_matrix[indices[i_idx]][indices[j_idx]])

                avg_sim = sum(sims) / len(sims) if sims else 1.0

                clusters.append({
                    "indices": indices,
                    "representative_idx": representative_idx,
                    "representative_text": texts[representative_idx],
                    "review_count": len(indices),
                    "average_similarity": round(avg_sim, 3),
                })

        return clusters

    def _jaccard_fallback(self, texts: List[str]) -> List[Dict]:
        """Fallback near-duplicate detection using character-level Jaccard similarity."""
        n = len(texts)
        if n < 2:
            return []

        # Compute shingles (character n-grams)
        def get_shingles(text, k=3):
            text = text.lower().strip()
            return set(text[i:i+k] for i in range(len(text) - k + 1))

        shingles = [get_shingles(t) for t in texts]

        # Union-find
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Compare pairs
        for i in range(n):
            for j in range(i + 1, n):
                if not shingles[i] or not shingles[j]:
                    continue
                intersection = len(shingles[i] & shingles[j])
                union_size = len(shingles[i] | shingles[j])
                jaccard = intersection / union_size if union_size > 0 else 0
                if jaccard >= self.similarity_threshold:
                    union(i, j)

        # Group clusters
        cluster_map = defaultdict(list)
        for i in range(n):
            cluster_map[find(i)].append(i)

        clusters = []
        for root, indices in cluster_map.items():
            if len(indices) > 1:
                representative_idx = max(indices, key=lambda i: len(texts[i]))
                clusters.append({
                    "indices": indices,
                    "representative_idx": representative_idx,
                    "representative_text": texts[representative_idx],
                    "review_count": len(indices),
                    "average_similarity": self.similarity_threshold,
                })

        return clusters

    def deduplicate(self, texts: List[str]) -> Dict:
        """
        Full deduplication pipeline.
        Returns:
        - exact_duplicates: dict of hash → indices
        - near_duplicate_clusters: list of cluster dicts
        - duplicate_indices: set of all indices that are duplicates
        - unique_indices: set of indices that are unique
        - stats: summary statistics
        """
        exact = self.find_exact_duplicates(texts)
        near = self.find_near_duplicates(texts)

        # Collect all duplicate indices
        duplicate_indices = set()

        # From exact duplicates: keep first, mark rest as duplicates
        for h, indices in exact.items():
            for idx in indices[1:]:  # Keep first, mark rest
                duplicate_indices.add(idx)

        # From near duplicates: keep representative, mark rest
        for cluster in near:
            rep = cluster["representative_idx"]
            for idx in cluster["indices"]:
                if idx != rep:
                    duplicate_indices.add(idx)

        unique_indices = set(range(len(texts))) - duplicate_indices

        return {
            "exact_duplicates": exact,
            "near_duplicate_clusters": near,
            "duplicate_indices": list(duplicate_indices),
            "unique_indices": list(unique_indices),
            "stats": {
                "total_reviews": len(texts),
                "exact_duplicate_groups": len(exact),
                "near_duplicate_clusters": len(near),
                "total_duplicates": len(duplicate_indices),
                "unique_reviews": len(unique_indices),
                "dedup_rate": round(len(duplicate_indices) / max(len(texts), 1) * 100, 1),
            },
        }
