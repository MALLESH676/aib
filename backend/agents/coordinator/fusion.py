from config import settings


def compute_fusion_score(
    risk_score: float,
    auth_score: float,
    review_score: float,
    risk_confidence: float,
    auth_confidence: float,
    review_confidence: float,
) -> dict:
    """
    Confidence-weighted fusion of agent scores.
    Returns fusion dict with weighted_score and component breakdown.
    """
    w_risk: float = settings.RISK_AGENT_WEIGHT
    w_auth: float = settings.AUTH_AGENT_WEIGHT
    w_review: float = settings.REVIEW_AGENT_WEIGHT

    # Confidence-adjust weights
    adjusted_risk = w_risk * (0.5 + risk_confidence * 0.5)
    adjusted_auth = w_auth * (0.5 + auth_confidence * 0.5)
    adjusted_review = w_review * (0.5 + review_confidence * 0.5)

    total_weight = adjusted_risk + adjusted_auth + adjusted_review
    if total_weight == 0:
        total_weight = 1.0

    weighted_score = (
        risk_score * adjusted_risk
        + auth_score * adjusted_auth
        + review_score * adjusted_review
    ) / total_weight

    return {
        "weighted_score": round(weighted_score, 2),
        "weights": {
            "risk": round(w_risk, 2),
            "authenticity": round(w_auth, 2),
            "review": round(w_review, 2),
        },
        "component_scores": {
            "risk": round(risk_score, 1),
            "authenticity": round(auth_score, 1),
            "review": round(review_score, 1),
        },
    }
