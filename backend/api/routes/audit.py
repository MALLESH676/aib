"""Audit log route."""
import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import get_db, AuditLog

router = APIRouter()


@router.get("/audit-log")
async def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    case_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Get audit log entries."""
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())
    if case_id:
        query = query.where(AuditLog.case_id == case_id)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "case_id": log.case_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
            "actor": log.actor,
            "action": log.action,
            "detail": json.loads(log.detail or "{}"),
            "model_version": log.model_version,
            "confidence": round(log.confidence, 3),
        }
        for log in logs
    ]
