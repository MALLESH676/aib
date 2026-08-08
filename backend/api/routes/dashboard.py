"""Dashboard stats route."""
import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from models.database import get_db, AnalysisCase, AuditLog

router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregated dashboard metrics."""
    result = await db.execute(select(AnalysisCase))
    cases = result.scalars().all()

    total = len(cases)
    if total == 0:
        return {
            "total_cases": 0,
            "allowed": 0,
            "under_review": 0,
            "held": 0,
            "human_review_queue": 0,
            "avg_risk_score": 0.0,
            "avg_latency_ms": 0.0,
            "detection_rate": 0.0,
            "automation_rate": 0.0,
        }

    allowed = sum(1 for c in cases if c.decision == "ALLOW")
    under_review = sum(1 for c in cases if c.decision == "REVIEW")
    held = sum(1 for c in cases if c.decision == "HOLD")
    queue = sum(1 for c in cases if c.human_status == "pending")
    avg_risk = sum(100 - c.overall_trust_score for c in cases) / total
    avg_latency = sum(c.latency_ms for c in cases) / total
    detection_rate = (under_review + held) / total if total > 0 else 0
    automation_rate = allowed / total if total > 0 else 0

    # Recent cases for sparkline
    recent = sorted(cases, key=lambda c: c.created_at, reverse=True)[:20]
    recent_decisions = [{"decision": c.decision, "score": 100 - c.overall_trust_score, "label": c.scenario_label} for c in recent]

    return {
        "total_cases": total,
        "allowed": allowed,
        "under_review": under_review,
        "held": held,
        "human_review_queue": queue,
        "avg_risk_score": round(avg_risk, 1),
        "avg_latency_ms": round(avg_latency, 0),
        "detection_rate": round(detection_rate * 100, 1),
        "automation_rate": round(automation_rate * 100, 1),
        "recent_decisions": recent_decisions,
    }


@router.get("/cases")
async def list_cases(
    skip: int = 0,
    limit: int = 50,
    decision: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all analysis cases."""
    query = select(AnalysisCase).order_by(AnalysisCase.created_at.desc())
    if decision:
        query = query.where(AnalysisCase.decision == decision.upper())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    cases = result.scalars().all()

    return [
        {
            "id": c.id,
            "case_type": c.case_type,
            "entity_id": c.entity_id,
            "decision": c.decision,
            "fusion_score": round(c.fusion_score, 1),
            "overall_trust_score": round(c.overall_trust_score, 1),
            "overall_risk_score": round(100 - c.overall_trust_score, 1),
            "created_at": c.created_at.isoformat() if c.created_at else "",
            "human_status": c.human_status,
            "scenario_label": c.scenario_label,
            "latency_ms": c.latency_ms,
            "summary": c.summary,
        }
        for c in cases
    ]


@router.get("/cases/{case_id}")
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
    """Get full case detail with all agent outputs."""
    result = await db.execute(select(AnalysisCase).where(AnalysisCase.id == case_id))
    case = result.scalar_one_or_none()

    if not case:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Case not found")

    # Get audit logs for this case
    audit_result = await db.execute(
        select(AuditLog).where(AuditLog.case_id == case_id).order_by(AuditLog.timestamp)
    )
    logs = audit_result.scalars().all()

    return {
        "id": case.id,
        "case_type": case.case_type,
        "entity_id": case.entity_id,
        "created_at": case.created_at.isoformat() if case.created_at else "",
        "risk_agent_output": json.loads(case.risk_agent_output or "{}"),
        "auth_agent_output": json.loads(case.auth_agent_output or "{}"),
        "review_agent_output": json.loads(case.review_agent_output or "{}"),
        "fusion_score": round(case.fusion_score, 1),
        "decision": case.decision,
        "decision_reason": case.decision_reason,
        "confidence": round(case.confidence, 3),
        "overall_trust_score": round(case.overall_trust_score, 1),
        "overall_risk_score": round(100 - case.overall_trust_score, 1),
        "summary": case.summary,
        "human_status": case.human_status,
        "human_action": case.human_action,
        "human_notes": case.human_notes,
        "human_investigator": case.human_investigator,
        "human_timestamp": case.human_timestamp.isoformat() if case.human_timestamp else None,
        "latency_ms": case.latency_ms,
        "scenario_label": case.scenario_label,
        "audit_log": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                "actor": log.actor,
                "action": log.action,
                "detail": json.loads(log.detail or "{}"),
                "model_version": log.model_version,
                "confidence": log.confidence,
            }
            for log in logs
        ],
    }
