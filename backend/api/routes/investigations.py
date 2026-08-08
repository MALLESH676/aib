"""Human investigation actions route."""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import get_db, AnalysisCase, AuditLog

router = APIRouter()


@router.get("/queue")
async def get_review_queue(db: AsyncSession = Depends(get_db)):
    """Get human review queue (REVIEW + HOLD cases pending human action)."""
    result = await db.execute(
        select(AnalysisCase)
        .where(AnalysisCase.human_status == "pending")
        .order_by(AnalysisCase.fusion_score.desc())
    )
    cases = result.scalars().all()

    return [
        {
            "id": c.id,
            "case_type": c.case_type,
            "entity_id": c.entity_id,
            "decision": c.decision,
            "fusion_score": round(c.fusion_score, 1),
            "overall_risk_score": round(100 - c.overall_trust_score, 1),
            "created_at": c.created_at.isoformat() if c.created_at else "",
            "scenario_label": c.scenario_label,
            "summary": c.summary,
            "priority": "HIGH" if c.fusion_score >= 70 else "MEDIUM",
            "risk_agent_output": json.loads(c.risk_agent_output or "{}"),
            "auth_agent_output": json.loads(c.auth_agent_output or "{}"),
            "review_agent_output": json.loads(c.review_agent_output or "{}"),
            "latency_ms": c.latency_ms,
        }
        for c in cases
    ]


@router.post("/cases/{case_id}/action")
async def take_human_action(
    case_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Human investigator action.
    body: { action: 'approve'|'reject'|'escalate'|'request_more_evidence', notes: str, investigator: str }
    """
    result = await db.execute(select(AnalysisCase).where(AnalysisCase.id == case_id))
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    action = body.get("action", "").lower()
    valid_actions = ["approve", "reject", "escalate", "request_more_evidence"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")

    # Update case
    case.human_action = action
    case.human_notes = body.get("notes", "")
    case.human_investigator = body.get("investigator", "investigator_1")
    case.human_timestamp = datetime.utcnow()
    case.human_status = "escalated" if action == "escalate" else (
        "approved" if action == "approve" else (
            "rejected" if action == "reject" else "pending"
        )
    )

    # Audit log
    db.add(AuditLog(
        case_id=case_id,
        timestamp=datetime.utcnow(),
        actor="human",
        action=action.upper(),
        detail=json.dumps({
            "notes": body.get("notes", ""),
            "investigator": body.get("investigator", "investigator_1"),
            "previous_decision": case.decision,
        }),
        model_version="human-review-v1",
        confidence=1.0,
    ))

    await db.commit()

    return {
        "case_id": case_id,
        "action": action,
        "human_status": case.human_status,
        "timestamp": case.human_timestamp.isoformat(),
        "message": f"Case {action} successfully by {body.get('investigator', 'investigator_1')}",
    }
