"""
POST /api/v1/analyze — Full analysis endpoint
"""
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db, AnalysisCase, AuditLog
from agents.coordinator.coordinator import get_coordinator

router = APIRouter()


@router.post("/analyze")
async def analyze(request: dict, db: AsyncSession = Depends(get_db)):
    """
    Run all three agents in parallel and return final trust decision.
    """
    coordinator = get_coordinator()
    result = await coordinator.analyze(request)

    # Save to DB
    case = AnalysisCase(
        id=result["case_id"],
        case_type=request.get("case_type", "transaction"),
        entity_id=request.get("seller", {}).get("id", str(uuid.uuid4())),
        created_at=datetime.utcnow(),
        risk_agent_output=json.dumps(result["agent_outputs"]["risk"]),
        auth_agent_output=json.dumps(result["agent_outputs"]["authenticity"]),
        review_agent_output=json.dumps(result["agent_outputs"]["review"]),
        fusion_score=result["fusion"]["weighted_score"],
        decision=result["policy_decision"]["decision"],
        decision_reason=result["policy_decision"]["reason"],
        confidence=(
            result["agent_outputs"]["risk"]["confidence"] +
            result["agent_outputs"]["authenticity"]["confidence"] +
            result["agent_outputs"]["review"]["confidence"]
        ) / 3,
        overall_trust_score=result["overall_trust_score"],
        summary=result["summary"],
        human_status="pending" if result["policy_decision"]["decision"] in ["REVIEW", "HOLD"] else "none",
        latency_ms=result["latency_ms"],
        scenario_label=request.get("scenario_label", ""),
    )
    db.add(case)

    # Audit logs
    for actor, agent_key in [
        ("risk_agent", "risk"),
        ("authenticity_agent", "authenticity"),
        ("review_agent", "review"),
    ]:
        agent_out = result["agent_outputs"][agent_key]
        db.add(AuditLog(
            case_id=result["case_id"],
            timestamp=datetime.utcnow(),
            actor=actor,
            action="ANALYSIS_COMPLETE",
            detail=json.dumps({
                "risk_score": agent_out.get("risk_score", 0),
                "recommendation": agent_out.get("recommendation", ""),
                "confidence": agent_out.get("confidence", 0),
                "signals_count": len(agent_out.get("signals", agent_out.get("suspicious_attributes", []))),
            }),
            model_version=agent_out.get("model_version", "v1"),
            confidence=agent_out.get("confidence", 0),
        ))

    db.add(AuditLog(
        case_id=result["case_id"],
        timestamp=datetime.utcnow(),
        actor="policy_engine",
        action=result["policy_decision"]["decision"],
        detail=json.dumps({
            "reason": result["policy_decision"]["reason"],
            "fusion_score": result["fusion"]["weighted_score"],
            "threshold_used": result["policy_decision"]["threshold_used"],
        }),
        model_version="policy-v1",
        confidence=1.0,
    ))

    await db.commit()
    return result
