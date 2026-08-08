import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coordinator.coordinator import get_coordinator
from data.synthetic.generator import build_scenario_a, build_scenario_b, build_scenario_c
from agents.risk_agent.model import get_risk_model
from data.synthetic.train_risk_model import train_risk_model


async def test_scenarios():
    print("[INFO] Pre-training risk model...")
    model = get_risk_model()
    train_risk_model(model)

    coordinator = get_coordinator()

    print("\n--- Scenario A (Legitimate Seller) ---")
    req_a = build_scenario_a()
    res_a = await coordinator.analyze(req_a)
    print(f"Decision: {res_a['policy_decision']['decision']}")
    print(f"Reason: {res_a['policy_decision']['reason']}")
    print(f"Overall Risk Score: {res_a['overall_risk_score']}/100")
    print(f"Overall Trust Score: {res_a['overall_trust_score']}/100")
    print(f"Agent scores: Risk={res_a['fusion']['component_scores']['risk']}, Auth={res_a['fusion']['component_scores']['authenticity']}, Review={res_a['fusion']['component_scores']['review']}")
    assert res_a['policy_decision']['decision'] == 'ALLOW', f"Expected ALLOW, got {res_a['policy_decision']['decision']}"

    print("\n--- Scenario B (Fraud Ring) ---")
    req_b = build_scenario_b()
    res_b = await coordinator.analyze(req_b)
    print(f"Decision: {res_b['policy_decision']['decision']}")
    print(f"Reason: {res_b['policy_decision']['reason']}")
    print(f"Overall Risk Score: {res_b['overall_risk_score']}/100")
    print(f"Overall Trust Score: {res_b['overall_trust_score']}/100")
    print(f"Agent scores: Risk={res_b['fusion']['component_scores']['risk']}, Auth={res_b['fusion']['component_scores']['authenticity']}, Review={res_b['fusion']['component_scores']['review']}")
    assert res_b['policy_decision']['decision'] == 'HOLD', f"Expected HOLD, got {res_b['policy_decision']['decision']}"

    print("\n--- Scenario C (Ambiguous Case) ---")
    req_c = build_scenario_c()
    res_c = await coordinator.analyze(req_c)
    print(f"Decision: {res_c['policy_decision']['decision']}")
    print(f"Reason: {res_c['policy_decision']['reason']}")
    print(f"Overall Risk Score: {res_c['overall_risk_score']}/100")
    print(f"Overall Trust Score: {res_c['overall_trust_score']}/100")
    print(f"Agent scores: Risk={res_c['fusion']['component_scores']['risk']}, Auth={res_c['fusion']['component_scores']['authenticity']}, Review={res_c['fusion']['component_scores']['review']}")
    assert res_c['policy_decision']['decision'] == 'REVIEW', f"Expected REVIEW, got {res_c['policy_decision']['decision']}"

    print("\n[SUCCESS] All E2E tests passed successfully!")

if __name__ == '__main__':
    asyncio.run(test_scenarios())
