"""
Seed database with pre-computed demo scenarios.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import uuid
from datetime import datetime
from models.database import AsyncSessionLocal, AnalysisCase, AuditLog
from agents.coordinator.coordinator import get_coordinator


async def seed_demo_cases():
    """Run all 3 demo scenarios and save to DB."""
    from data.synthetic.generator import DEMO_SCENARIOS

    coordinator = get_coordinator()

    async with AsyncSessionLocal() as session:
        for label, builder_fn in DEMO_SCENARIOS.items():
            request = builder_fn()
            try:
                result = await coordinator.analyze(request)

                case = AnalysisCase(
                    id=result["case_id"],
                    case_type=request.get("case_type", "transaction"),
                    entity_id=request["seller"]["id"],
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
                    scenario_label=label,
                )
                session.add(case)

                # Add audit logs
                for actor, agent_key in [
                    ("risk_agent", "risk"),
                    ("authenticity_agent", "authenticity"),
                    ("review_agent", "review"),
                ]:
                    agent_out = result["agent_outputs"][agent_key]
                    log = AuditLog(
                        case_id=result["case_id"],
                        timestamp=datetime.utcnow(),
                        actor=actor,
                        action=f"ANALYSIS_COMPLETE",
                        detail=json.dumps({
                            "risk_score": agent_out.get("risk_score", 0),
                            "recommendation": agent_out.get("recommendation", ""),
                            "confidence": agent_out.get("confidence", 0),
                        }),
                        model_version=agent_out.get("model_version", "v1"),
                        confidence=agent_out.get("confidence", 0),
                    )
                    session.add(log)

                policy_log = AuditLog(
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
                )
                session.add(policy_log)

                await session.commit()
                print(f"  Scenario {label} seeded: {result['policy_decision']['decision']} (score: {result['overall_risk_score']:.1f})")

            except Exception as e:
                print(f"  Scenario {label} seeding failed: {e}")
                await session.rollback()
