import time
import math
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict


class ReviewAgent:
    NAME = "review_agent"
    VERSION = "1.0.0"

    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self._embedder = None  # lazy loaded

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                print(f"Warning: sentence-transformers not available: {e}")
                self._embedder = None
        return self._embedder

    def _compute_text_similarity(self, texts: List[str]) -> float:
        """Returns average pairwise cosine similarity"""
        if len(texts) < 2:
            return 0.0
        embedder = self._get_embedder()
        if embedder is None:
            # Fallback: simple overlap-based similarity
            return self._simple_similarity(texts)
        try:
            import numpy as np
            embeddings = embedder.encode(texts, show_progress_bar=False)
            # Normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norms + 1e-8)
            # Pairwise similarity
            sims = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = float(np.dot(embeddings[i], embeddings[j]))
                    sims.append(sim)
            return float(sum(sims) / len(sims)) if sims else 0.0
        except Exception as e:
            print(f"Embedding computation failed: {e}")
            return self._simple_similarity(texts)

    def _simple_similarity(self, texts: List[str]) -> float:
        """Word overlap similarity fallback"""
        if len(texts) < 2:
            return 0.0
        word_sets = [set(t.lower().split()) for t in texts]
        sims = []
        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                intersection = word_sets[i] & word_sets[j]
                union = word_sets[i] | word_sets[j]
                sims.append(len(intersection) / len(union) if union else 0.0)
        return float(sum(sims) / len(sims)) if sims else 0.0

    def _detect_review_burst(self, reviews: List[dict]) -> Dict:
        """Detect review burst activity"""
        if len(reviews) < 2:
            return {"has_burst": False, "burst_count": len(reviews), "window_minutes": 0}

        # Parse timestamps
        timestamps = []
        for r in reviews:
            ts = r.get("timestamp", "")
            if isinstance(ts, str):
                try:
                    timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                except Exception:
                    timestamps.append(datetime.utcnow())
            else:
                timestamps.append(datetime.utcnow())

        timestamps.sort()

        if len(timestamps) < 2:
            return {"has_burst": False, "burst_count": 1, "window_minutes": 0}

        # Find tightest window containing all reviews
        window_minutes = (timestamps[-1] - timestamps[0]).total_seconds() / 60

        # Find burst: max reviews in any 60-minute window
        max_burst = 0
        min_burst_window = float("inf")
        for i in range(len(timestamps)):
            count = 1
            for j in range(i + 1, len(timestamps)):
                if (timestamps[j] - timestamps[i]).total_seconds() <= 3600:
                    count += 1
                else:
                    break
            if count > max_burst:
                max_burst = count
                if count >= 2:
                    w = (timestamps[i + count - 1] - timestamps[i]).total_seconds() / 60
                    min_burst_window = w

        has_burst = max_burst >= 5 or (max_burst >= 3 and min_burst_window <= 30)

        return {
            "has_burst": has_burst,
            "burst_count": max_burst,
            "window_minutes": round(min_burst_window if min_burst_window < float("inf") else window_minutes, 1),
        }

    def _analyze_graph(self, reviews: List[dict]) -> Dict:
        """NetworkX graph analysis of reviewer relationships"""
        try:
            import networkx as nx

            G = nx.Graph()
            # Add nodes for each reviewer
            reviewers = [r.get("customer_id", f"r_{i}") for i, r in enumerate(reviews)]
            G.add_nodes_from(reviewers)

            # Add edges where reviewers posted within 5 minutes of each other
            timestamps: Dict[str, datetime] = {}
            for r in reviews:
                cid = r.get("customer_id", "")
                ts = r.get("timestamp", "")
                if isinstance(ts, str):
                    try:
                        timestamps[cid] = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except Exception:
                        timestamps[cid] = datetime.utcnow()

            for i, r1 in enumerate(reviews):
                for j, r2 in enumerate(reviews):
                    if i >= j:
                        continue
                    c1 = r1.get("customer_id", f"r_{i}")
                    c2 = r2.get("customer_id", f"r_{j}")
                    if c1 in timestamps and c2 in timestamps:
                        diff = abs((timestamps[c1] - timestamps[c2]).total_seconds())
                        if diff <= 300:  # 5 minutes
                            G.add_edge(c1, c2)

            # Get largest connected component
            if len(G.nodes) == 0:
                return {
                    "suspicious_clusters": 0,
                    "cluster_size": 0,
                    "network_density": 0.0,
                    "linked_accounts": [],
                }

            components = list(nx.connected_components(G))
            largest = max(components, key=len)
            density = nx.density(G)

            return {
                "suspicious_clusters": sum(1 for c in components if len(c) >= 3),
                "cluster_size": len(largest),
                "network_density": round(density, 3),
                "linked_accounts": list(largest)[:10],
            }
        except Exception as e:
            print(f"Graph analysis failed: {e}")
            return {"suspicious_clusters": 0, "cluster_size": 1, "network_density": 0.0, "linked_accounts": []}

    async def analyze(
        self,
        event_id: str,
        product_id: str,
        seller_id: str,
        reviews: List[dict],
        review_window_hours: int = 24,
        product_age_days: int = 30,
    ) -> dict:
        start_time = time.time()

        signals: List[Dict[str, Any]] = []
        total_score = 0.0

        if not reviews:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "agent": self.NAME,
                "version": self.VERSION,
                "event_id": event_id,
                "manipulation_probability": 0.0,
                "risk_score": 0.0,
                "signals": [],
                "cluster_analysis": {
                    "suspicious_clusters": 0,
                    "cluster_size": 0,
                    "network_density": 0.0,
                    "linked_accounts": [],
                },
                "rating_stats": {
                    "avg_rating": 0.0,
                    "five_star_rate": 0.0,
                    "review_velocity": 0,
                    "velocity_window_minutes": 0,
                },
                "recommendation": "ALLOW",
                "confidence": 0.5,
                "explanation": "No reviews to analyze.",
                "model_version": "sentence-transformers-v1+networkx",
                "latency_ms": latency_ms,
            }

        # --- 1. Burst detection ---
        burst = self._detect_review_burst(reviews)
        burst_count = burst["burst_count"]
        burst_window = burst["window_minutes"]

        if burst["has_burst"] and burst_count >= 10:
            signals.append({
                "signal": "critical_review_burst",
                "value": float(burst_count),
                "weight": 0.25,
                "severity": "CRITICAL",
                "detail": f"{burst_count} reviews posted in {burst_window:.0f} minutes",
            })
            total_score += 30.0
        elif burst["has_burst"] and burst_count >= 5:
            signals.append({
                "signal": "review_burst",
                "value": float(burst_count),
                "weight": 0.20,
                "severity": "HIGH",
                "detail": f"{burst_count} reviews in {burst_window:.0f} minutes",
            })
            total_score += 20.0
        elif len(reviews) >= 3:
            # check velocity relative to product age
            if product_age_days <= 7 and len(reviews) >= 8:
                signals.append({
                    "signal": "high_review_velocity",
                    "value": float(len(reviews)),
                    "weight": 0.12,
                    "severity": "MEDIUM",
                    "detail": f"{len(reviews)} reviews on {product_age_days}-day-old product",
                })
                total_score += 12.0

        # --- 2. Text similarity ---
        texts = [r.get("text", "") for r in reviews if r.get("text", "").strip()]
        avg_similarity = self._compute_text_similarity(texts) if len(texts) >= 2 else 0.0

        if avg_similarity >= 0.85:
            signals.append({
                "signal": "high_text_similarity",
                "value": round(avg_similarity, 3),
                "weight": 0.25,
                "severity": "CRITICAL",
                "detail": f"Average review similarity {avg_similarity:.2f} (threshold: 0.85)",
            })
            total_score += 28.0
        elif avg_similarity >= 0.65:
            signals.append({
                "signal": "elevated_text_similarity",
                "value": round(avg_similarity, 3),
                "weight": 0.15,
                "severity": "HIGH",
                "detail": f"Average review similarity {avg_similarity:.2f} — possibly templated",
            })
            total_score += 18.0
        elif avg_similarity >= 0.45:
            signals.append({
                "signal": "moderate_text_similarity",
                "value": round(avg_similarity, 3),
                "weight": 0.08,
                "severity": "MEDIUM",
                "detail": f"Average review similarity {avg_similarity:.2f}",
            })
            total_score += 8.0

        # --- 3. Unverified purchase rate ---
        verified = sum(1 for r in reviews if r.get("verified_purchase", False))
        unverified_rate = 1.0 - (verified / len(reviews))
        if unverified_rate >= 0.85 and len(reviews) >= 5:
            signals.append({
                "signal": "high_unverified_rate",
                "value": round(unverified_rate, 2),
                "weight": 0.15,
                "severity": "HIGH",
                "detail": f"{int(unverified_rate * len(reviews))} of {len(reviews)} reviews from non-purchasers",
            })
            total_score += 15.0
        elif unverified_rate >= 0.60 and len(reviews) >= 3:
            signals.append({
                "signal": "elevated_unverified_rate",
                "value": round(unverified_rate, 2),
                "weight": 0.08,
                "severity": "MEDIUM",
                "detail": f"{int(unverified_rate * 100):.0f}% reviews from non-purchasers",
            })
            total_score += 8.0

        # --- 4. Rating distribution anomaly ---
        ratings = [r.get("rating", 3) for r in reviews]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        five_star_rate = sum(1 for r in ratings if r == 5) / len(ratings) if ratings else 0.0

        if five_star_rate >= 0.95 and len(reviews) >= 5:
            signals.append({
                "signal": "rating_distribution_anomaly",
                "value": round(five_star_rate, 2),
                "weight": 0.10,
                "severity": "MEDIUM",
                "detail": f"{five_star_rate:.0%} five-star ratings on {len(reviews)} reviews",
            })
            total_score += 10.0

        # --- 5. Graph / coordinated account analysis ---
        graph_result = self._analyze_graph(reviews)
        cluster_density = graph_result["network_density"]
        cluster_size = graph_result["cluster_size"]

        if cluster_density >= 0.7 and cluster_size >= 4:
            signals.append({
                "signal": "coordinated_accounts",
                "value": round(cluster_density, 3),
                "weight": 0.20,
                "severity": "CRITICAL",
                "detail": f"{cluster_size} reviewers in coordinated cluster (density: {cluster_density:.2f})",
            })
            total_score += 22.0
        elif cluster_density >= 0.4 and cluster_size >= 3:
            signals.append({
                "signal": "suspicious_reviewer_cluster",
                "value": round(cluster_density, 3),
                "weight": 0.12,
                "severity": "HIGH",
                "detail": f"{cluster_size} reviewers showing coordinated behavior",
            })
            total_score += 12.0

        # --- 6. Finalize ---
        risk_score = min(total_score, 100.0)
        manipulation_probability = risk_score / 100.0

        if risk_score >= 70:
            recommendation = "HOLD"
        elif risk_score >= 35:
            recommendation = "FLAG"
        else:
            recommendation = "ALLOW"

        critical_signals = sum(1 for s in signals if s["severity"] in ["CRITICAL", "HIGH"])
        confidence = min(0.50 + (critical_signals * 0.10) + (len(signals) * 0.04), 0.98)

        explanation = self._generate_explanation(signals, risk_score, len(reviews))

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "agent": self.NAME,
            "version": self.VERSION,
            "event_id": event_id,
            "manipulation_probability": round(manipulation_probability, 3),
            "risk_score": round(risk_score, 1),
            "signals": signals,
            "cluster_analysis": graph_result,
            "rating_stats": {
                "avg_rating": round(avg_rating, 2),
                "five_star_rate": round(five_star_rate, 3),
                "review_velocity": len(reviews),
                "velocity_window_minutes": burst_window,
            },
            "recommendation": recommendation,
            "confidence": round(confidence, 3),
            "explanation": explanation,
            "model_version": "sentence-transformers-v1+networkx",
            "latency_ms": latency_ms,
        }

    def _generate_explanation(self, signals: List[dict], score: float, review_count: int) -> str:
        if not signals:
            return f"No significant manipulation signals detected across {review_count} reviews."

        critical = [s for s in signals if s["severity"] == "CRITICAL"]
        high = [s for s in signals if s["severity"] == "HIGH"]

        parts = [s["detail"] for s in (critical + high)[:3]]

        if score >= 70:
            return f"Strong evidence of review manipulation across {review_count} reviews: {'; '.join(parts)}."
        elif score >= 35:
            return f"Suspicious review patterns detected: {'; '.join(parts)}."
        else:
            return f"Minor review anomalies: {'; '.join(parts)}."
