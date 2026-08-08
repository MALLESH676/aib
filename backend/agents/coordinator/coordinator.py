import asyncio
import time
import uuid
from typing import Optional

from agents.risk_agent.agent import RiskAgent
from agents.authenticity_agent.agent import AuthenticityAgent
from agents.review_agent.agent import ReviewAgent
from .fusion import compute_fusion_score
from .policy import apply_policy


class TrustCoordinator:
    """Orchestrates all agents and produces the final trust & safety decision."""

    def __init__(self) -> None:
        self.risk_agent = RiskAgent()
        self.auth_agent = AuthenticityAgent()
        self.review_agent = ReviewAgent()

    async def analyze(self, request: dict) -> dict:
        start_time = time.time()

        event_id: str = request.get("event_id", str(uuid.uuid4()))
        customer: dict = request.get("customer") or {}
        transaction: dict = request.get("transaction") or {}
        seller: dict = request.get("seller") or {}
        product: dict = request.get("product") or {}
        reviews: list = request.get("reviews") or []
        device: dict = request.get("device") or {}
        review_window_hours: int = request.get("review_window_hours", 24)
        product_age_days: int = product.get("listing_age_days", 30)

        # Default device if not provided
        if not device:
            device = {
                "id": "unknown",
                "linked_accounts": 1,
                "vpn_detected": False,
                "emulator_detected": False,
            }

        # Default customer if not provided
        if not customer:
            customer = {
                "id": "unknown",
                "account_age_days": 365,
                "total_orders": 1,
                "total_returns": 0,
                "return_rate": 0.0,
                "cod_refusal_rate": 0.0,
                "linked_device_count": 1,
                "linked_account_count": 1,
            }

        # Default transaction if not provided
        if not transaction:
            transaction = {
                "id": "unknown",
                "amount": product.get("price", 1000),
                "payment_method": "card",
                "is_first_time_buyer": False,
                "orders_last_24h": 1,
                "orders_last_7d": 1,
            }

        # --- Run all agents in parallel ---
        risk_task = self.risk_agent.analyze(event_id, customer, transaction, seller, device)
        auth_task = self.auth_agent.analyze(event_id, product, seller)
        review_task = self.review_agent.analyze(
            event_id,
            product.get("id", ""),
            seller.get("id", ""),
            reviews,
            review_window_hours,
            product_age_days,
        )

        risk_output, auth_output, review_output = await asyncio.gather(
            risk_task,
            auth_task,
            review_task,
            return_exceptions=True,
        )

        # Handle individual agent failures gracefully
        if isinstance(risk_output, Exception):
            print(f"Risk agent failed: {risk_output}")
            risk_output = self._fallback_risk_output(event_id)
        if isinstance(auth_output, Exception):
            print(f"Auth agent failed: {auth_output}")
            auth_output = self._fallback_auth_output(event_id)
        if isinstance(review_output, Exception):
            print(f"Review agent failed: {review_output}")
            review_output = self._fallback_review_output(event_id)

        # --- Fusion ---
        fusion = compute_fusion_score(
            risk_score=risk_output["risk_score"],
            auth_score=auth_output["risk_score"],
            review_score=review_output["risk_score"],
            risk_confidence=risk_output["confidence"],
            auth_confidence=auth_output["confidence"],
            review_confidence=review_output["confidence"],
        )

        # --- Policy ---
        policy_decision = apply_policy(
            fusion["weighted_score"], risk_output, auth_output, review_output
        )

        # --- Overall scores ---
        overall_risk: float = fusion["weighted_score"]
        overall_trust: float = max(0.0, 100.0 - overall_risk)

        # --- Summary ---
        summary = self._generate_summary(risk_output, auth_output, review_output, policy_decision)

        total_latency = int((time.time() - start_time) * 1000)
        case_id = str(uuid.uuid4())

        return {
            "case_id": case_id,
            "event_id": event_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agent_outputs": {
                "risk": risk_output,
                "authenticity": auth_output,
                "review": review_output,
            },
            "fusion": fusion,
            "policy_decision": policy_decision,
            "overall_trust_score": round(overall_trust, 1),
            "overall_risk_score": round(overall_risk, 1),
            "summary": summary,
            "latency_ms": total_latency,
        }

    def _generate_summary(
        self,
        risk: dict,
        auth: dict,
        review: dict,
        policy: dict,
    ) -> str:
        decision: str = policy["decision"]
        parts = []
        if risk["risk_score"] >= 60:
            parts.append(f"high transaction risk ({risk['risk_score']:.0f}/100)")
        if auth["risk_score"] >= 60:
            parts.append(f"possible counterfeit product ({auth['risk_score']:.0f}/100)")
        if review["risk_score"] >= 60:
            parts.append(f"review manipulation detected ({review['risk_score']:.0f}/100)")

        if not parts:
            return "No significant fraud signals detected. All agents report normal activity."

        return f"Decision: {decision}. Signals detected: {'; '.join(parts)}."

    def _fallback_risk_output(self, event_id: str) -> dict:
        return {
            "agent": "risk_agent",
            "version": "1.0.0",
            "event_id": event_id,
            "risk_score": 50.0,
            "risk_category": "MEDIUM",
            "signals": [],
            "recommendation": "REVIEW",
            "confidence": 0.3,
            "explanation": "Risk agent unavailable. Routing to human review.",
            "model_version": "fallback",
            "latency_ms": 0,
        }

    def _fallback_auth_output(self, event_id: str) -> dict:
        return {
            "agent": "authenticity_agent",
            "version": "1.0.0",
            "event_id": event_id,
            "counterfeit_probability": 0.5,
            "risk_score": 50.0,
            "suspicious_attributes": [],
            "image_analysis": {
                "logo_consistency": "UNKNOWN",
                "image_quality_score": 0.5,
                "similar_known_counterfeits": 0,
                "notes": "Analysis unavailable",
            },
            "recommendation": "REVIEW",
            "confidence": 0.3,
            "explanation": "Authenticity agent unavailable. Routing to human review.",
            "model_version": "fallback",
            "latency_ms": 0,
        }

    def _fallback_review_output(self, event_id: str) -> dict:
        return {
            "agent": "review_agent",
            "version": "1.0.0",
            "event_id": event_id,
            "manipulation_probability": 0.5,
            "risk_score": 50.0,
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
            "recommendation": "REVIEW",
            "confidence": 0.3,
            "explanation": "Review agent unavailable. Routing to human review.",
            "model_version": "fallback",
            "latency_ms": 0,
        }


# Global singleton instance
_coordinator: Optional[TrustCoordinator] = None


def get_coordinator() -> TrustCoordinator:
    """Return the global TrustCoordinator singleton, creating it if necessary."""
    global _coordinator
    if _coordinator is None:
        _coordinator = TrustCoordinator()
    return _coordinator
