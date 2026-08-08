from config import settings


def apply_policy(
    fusion_score: float,
    risk_output: dict,
    auth_output: dict,
    review_output: dict,
) -> dict:
    """
    DETERMINISTIC policy engine. No LLM involved.

    Evaluates the fused risk score and individual agent outputs to produce a
    final decision of ALLOW, REVIEW, or HOLD with a human-readable reason.
    """
    allow_threshold: float = settings.RISK_ALLOW_THRESHOLD
    review_threshold: float = settings.RISK_REVIEW_THRESHOLD
    high_confidence_threshold: float = settings.HIGH_CONFIDENCE_THRESHOLD

    risk_confidence: float = risk_output.get("confidence", 0.5)
    auth_confidence: float = auth_output.get("confidence", 0.5)
    review_confidence: float = review_output.get("confidence", 0.5)
    avg_confidence: float = (risk_confidence + auth_confidence + review_confidence) / 3

    # --- Hard rules (override everything) ---
    # If any agent is CRITICAL with high confidence → HOLD immediately
    risk_signals: list = risk_output.get("signals", [])
    review_signals: list = review_output.get("signals", [])
    has_critical_signal: bool = any(
        s.get("severity") == "CRITICAL" for s in risk_signals + review_signals
    )

    # Low confidence override → REVIEW always
    if avg_confidence < 0.45:
        return {
            "decision": "REVIEW",
            "reason": (
                f"Average agent confidence ({avg_confidence:.2f}) below threshold. "
                "Routing to human review for low-confidence cases."
            ),
            "threshold_used": allow_threshold,
            "requires_human_approval": True,
            "action_taken": "REVIEW_QUEUED",
        }

    # HOLD conditions
    if fusion_score >= review_threshold and avg_confidence >= high_confidence_threshold:
        reason_parts = []
        if risk_output.get("risk_score", 0) >= 70:
            reason_parts.append(f"Risk Agent: {risk_output['risk_score']:.0f}/100")
        if auth_output.get("risk_score", 0) >= 70:
            reason_parts.append(f"Authenticity Agent: {auth_output['risk_score']:.0f}/100")
        if review_output.get("risk_score", 0) >= 70:
            reason_parts.append(f"Review Agent: {review_output['risk_score']:.0f}/100")

        agents_str = (
            ", ".join(reason_parts) if reason_parts else "multiple agents"
        )
        reason = (
            f"Fusion score {fusion_score:.1f} exceeds HOLD threshold ({review_threshold}). "
            f"High-risk signals from: {agents_str}. Confidence: {avg_confidence:.2f}."
        )

        return {
            "decision": "HOLD",
            "reason": reason,
            "threshold_used": review_threshold,
            "requires_human_approval": True,
            "action_taken": "HOLD_PENDING_REVIEW",
        }

    # HOLD even at lower fusion score if critical signal detected
    if has_critical_signal and fusion_score >= 55 and avg_confidence >= 0.70:
        return {
            "decision": "HOLD",
            "reason": (
                f"Critical fraud signal detected with high confidence ({avg_confidence:.2f}). "
                f"Fusion score: {fusion_score:.1f}. Precautionary hold applied."
            ),
            "threshold_used": 55.0,
            "requires_human_approval": True,
            "action_taken": "HOLD_CRITICAL_SIGNAL",
        }

    # REVIEW conditions
    if fusion_score >= allow_threshold:
        reason = (
            f"Fusion score {fusion_score:.1f} is in REVIEW range "
            f"({allow_threshold}–{review_threshold}). Case routed for human review."
        )
        if avg_confidence < high_confidence_threshold:
            reason += (
                f" Note: confidence ({avg_confidence:.2f}) below high-confidence "
                "threshold — human judgment required."
            )
        return {
            "decision": "REVIEW",
            "reason": reason,
            "threshold_used": allow_threshold,
            "requires_human_approval": True,
            "action_taken": "REVIEW_QUEUED",
        }

    # ALLOW
    return {
        "decision": "ALLOW",
        "reason": (
            f"Fusion score {fusion_score:.1f} is below ALLOW threshold ({allow_threshold}). "
            f"No significant fraud signals detected. Confidence: {avg_confidence:.2f}."
        ),
        "threshold_used": allow_threshold,
        "requires_human_approval": False,
        "action_taken": "TRANSACTION_ALLOWED",
    }
