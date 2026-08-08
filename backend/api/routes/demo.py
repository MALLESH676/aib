"""
Demo scenarios route — triggers pre-built scenarios for live demo.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import get_db, AnalysisCase
from agents.coordinator.coordinator import get_coordinator
from data.synthetic.generator import DEMO_SCENARIOS

router = APIRouter()


@router.post("/demo/{scenario}")
async def run_demo_scenario(scenario: str, db: AsyncSession = Depends(get_db)):
    """
    Trigger a pre-built demo scenario.
    scenario: A (Legitimate/ALLOW), B (Fraud Ring/HOLD), C (Ambiguous/REVIEW)
    """
    scenario = scenario.upper()
    if scenario not in DEMO_SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario '{scenario}'. Valid: A, B, C")

    builder_fn = DEMO_SCENARIOS[scenario]
    request = builder_fn()

    coordinator = get_coordinator()
    result = await coordinator.analyze(request)

    # Persist
    case = AnalysisCase(
        id=result["case_id"],
        case_type=request.get("case_type", "transaction"),
        entity_id=request["seller"]["id"],
        created_at=__import__("datetime").datetime.utcnow(),
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
        scenario_label=scenario,
    )
    db.add(case)
    await db.commit()

    return {**result, "scenario": scenario, "scenario_description": {
        "A": "Legitimate seller — Expected: ALLOW",
        "B": "Fraud ring with counterfeit product and fake reviews — Expected: HOLD",
        "C": "Ambiguous case requiring human judgment — Expected: REVIEW",
    }[scenario]}


@router.get("/demo/scenarios")
async def list_demo_scenarios():
    """List available demo scenarios."""
    return {
        "scenarios": [
            {"id": "A", "name": "Legitimate Seller", "expected_decision": "ALLOW",
             "description": "Clean transaction from established seller. Demonstrates no false positives."},
            {"id": "B", "name": "Fraud Ring", "expected_decision": "HOLD",
             "description": "Return fraud + counterfeit product + coordinated fake reviews. Primary demo scenario."},
            {"id": "C", "name": "Ambiguous Case", "expected_decision": "REVIEW",
             "description": "Mixed signals requiring human judgment. Demonstrates responsible AI."},
        ]
    }
