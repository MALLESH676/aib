from dataclasses import dataclass
from typing import List


@dataclass
class RuleSignal:
    signal: str
    value: float
    weight: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    detail: str
    score_contribution: float  # 0-100


def evaluate_risk_rules(customer: dict, transaction: dict, seller: dict, device: dict) -> tuple[float, List[RuleSignal]]:
    """
    Evaluate deterministic fraud rules.
    Returns (rule_score: float 0-100, signals: List[RuleSignal])
    """
    signals = []
    total_score = 0.0

    # --- Customer return rate rules ---
    return_rate = customer.get("return_rate", 0.0)
    if return_rate >= 0.6:
        sig = RuleSignal("high_return_rate", return_rate, 0.25, "HIGH", f"Return rate {return_rate:.0%} (threshold: 60%)", 25.0)
        signals.append(sig); total_score += sig.score_contribution
    elif return_rate >= 0.4:
        sig = RuleSignal("elevated_return_rate", return_rate, 0.15, "MEDIUM", f"Return rate {return_rate:.0%} (threshold: 40%)", 15.0)
        signals.append(sig); total_score += sig.score_contribution

    # --- COD refusal rate ---
    cod_rate = customer.get("cod_refusal_rate", 0.0)
    if cod_rate >= 0.4:
        sig = RuleSignal("cod_refusal_abuse", cod_rate, 0.20, "HIGH", f"COD refusal rate {cod_rate:.0%} (threshold: 40%)", 20.0)
        signals.append(sig); total_score += sig.score_contribution
    elif cod_rate >= 0.25:
        sig = RuleSignal("elevated_cod_refusal", cod_rate, 0.10, "MEDIUM", f"COD refusal rate {cod_rate:.0%}", 10.0)
        signals.append(sig); total_score += sig.score_contribution

    # --- Multi-account device ---
    linked_accounts = customer.get("linked_account_count", 1)
    if linked_accounts >= 3:
        sig = RuleSignal("multi_account_device", float(linked_accounts), 0.15, "HIGH", f"{linked_accounts} accounts on same device", 20.0)
        signals.append(sig); total_score += sig.score_contribution
    elif linked_accounts == 2:
        sig = RuleSignal("shared_device_account", float(linked_accounts), 0.08, "MEDIUM", "2 accounts on same device", 8.0)
        signals.append(sig); total_score += sig.score_contribution

    # --- New account high value ---
    account_age = customer.get("account_age_days", 999)
    amount = transaction.get("amount", 0)
    if account_age <= 7 and amount >= 3000:
        sig = RuleSignal("new_account_high_value", amount, 0.12, "HIGH", f"Account {account_age} days old, transaction \u20b9{amount:,.0f}", 18.0)
        signals.append(sig); total_score += sig.score_contribution
    elif account_age <= 3:
        sig = RuleSignal("very_new_account", float(account_age), 0.08, "MEDIUM", f"Account only {account_age} days old", 8.0)
        signals.append(sig); total_score += sig.score_contribution

    # --- Unusual order frequency ---
    orders_24h = transaction.get("orders_last_24h", 1)
    if orders_24h >= 5:
        sig = RuleSignal("unusual_order_frequency", float(orders_24h), 0.10, "HIGH", f"{orders_24h} orders in last 24 hours", 15.0)
        signals.append(sig); total_score += sig.score_contribution
    elif orders_24h >= 3:
        sig = RuleSignal("elevated_order_frequency", float(orders_24h), 0.06, "MEDIUM", f"{orders_24h} orders in 24 hours", 6.0)
        signals.append(sig); total_score += sig.score_contribution

    # --- COD payment method with high amount ---
    if transaction.get("payment_method") == "COD" and amount >= 2000:
        sig = RuleSignal("high_value_cod", amount, 0.08, "MEDIUM", f"COD payment for \u20b9{amount:,.0f}", 8.0)
        signals.append(sig); total_score += sig.score_contribution

    # --- Device signals ---
    if device.get("vpn_detected"):
        sig = RuleSignal("vpn_detected", 1.0, 0.06, "MEDIUM", "VPN/proxy detected on transaction", 8.0)
        signals.append(sig); total_score += sig.score_contribution

    if device.get("emulator_detected"):
        sig = RuleSignal("emulator_detected", 1.0, 0.08, "HIGH", "Device emulator detected", 12.0)
        signals.append(sig); total_score += sig.score_contribution

    # --- Seller signals ---
    dispute_rate = seller.get("dispute_rate", 0.0)
    if dispute_rate >= 0.15:
        sig = RuleSignal("high_seller_dispute_rate", dispute_rate, 0.10, "MEDIUM", f"Seller dispute rate {dispute_rate:.0%}", 10.0)
        signals.append(sig); total_score += sig.score_contribution

    # Cap at 100
    return min(total_score, 100.0), signals
