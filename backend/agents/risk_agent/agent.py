import time
import asyncio
from typing import Dict, Any

from .rules import evaluate_risk_rules
from .model import get_risk_model


class RiskAgent:
    NAME = "risk_agent"
    VERSION = "1.0.0"

    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self.model = get_risk_model()

    async def analyze(self, event_id: str, customer: dict, transaction: dict, seller: dict, device: dict) -> dict:
        start_time = time.time()

        # 1. Deterministic rules
        rule_score, signals = evaluate_risk_rules(customer, transaction, seller, device)

        # 2. ML model score (if trained, blend with rule score)
        ml_prob = self.model.predict_proba(customer, transaction, seller, device)
        if self.model.is_trained and ml_prob > 0:
            # Blend: 60% ML, 40% rules
            risk_score = ml_prob * 100 * 0.60 + rule_score * 0.40
        else:
            risk_score = rule_score

        risk_score = min(max(risk_score, 0.0), 100.0)

        # 3. Categorize
        if risk_score >= 70:
            risk_category = "HIGH"
            recommendation = "HOLD"
        elif risk_score >= 40:
            risk_category = "MEDIUM"
            recommendation = "REVIEW"
        else:
            risk_category = "LOW"
            recommendation = "ALLOW"

        # 4. Confidence (based on number of signals and their severity)
        high_signals = sum(1 for s in signals if s.severity in ["HIGH", "CRITICAL"])
        confidence = min(0.50 + (high_signals * 0.10) + (len(signals) * 0.03), 0.99)

        # 5. Convert signals to dicts
        signal_dicts = [
            {"signal": s.signal, "value": s.value, "weight": s.weight,
             "severity": s.severity, "detail": s.detail}
            for s in signals
        ]

        # 6. Generate explanation
        explanation = self._generate_explanation(signal_dicts, risk_score)

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "agent": self.NAME,
            "version": self.VERSION,
            "event_id": event_id,
            "risk_score": round(risk_score, 1),
            "risk_category": risk_category,
            "signals": signal_dicts,
            "recommendation": recommendation,
            "confidence": round(confidence, 3),
            "explanation": explanation,
            "model_version": "xgboost-v1" if self.model.is_trained else "rules-v1",
            "latency_ms": latency_ms,
        }

    def _generate_explanation(self, signals: list, score: float) -> str:
        if not signals:
            return "No significant risk signals detected. Transaction appears normal."

        high_signals = [s for s in signals if s["severity"] in ["HIGH", "CRITICAL"]]
        medium_signals = [s for s in signals if s["severity"] == "MEDIUM"]

        parts = []
        for s in high_signals[:3]:
            parts.append(s["detail"])
        for s in medium_signals[:2]:
            parts.append(s["detail"])

        if score >= 70:
            prefix = "Multiple strong fraud indicators detected: "
        elif score >= 40:
            prefix = "Moderate risk signals detected: "
        else:
            prefix = "Minor risk signals noted: "

        return prefix + "; ".join(parts) + "."
