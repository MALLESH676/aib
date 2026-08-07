"""Train risk model on synthetic data."""
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.synthetic.generator import generate_legitimate_customer, generate_fraudulent_customer, generate_legitimate_seller, generate_fraudulent_seller


def generate_training_data(n_samples: int = 2000):
    """Generate synthetic training data for the risk model."""
    X_list = []
    y_list = []

    # Legitimate samples (70%)
    n_legit = int(n_samples * 0.70)
    for _ in range(n_legit):
        cust = generate_legitimate_customer()
        seller = generate_legitimate_seller()
        transaction = {
            "amount": np.random.uniform(200, 5000),
            "payment_method": np.random.choice(["card", "wallet", "COD"], p=[0.5, 0.3, 0.2]),
            "is_first_time_buyer": np.random.random() < 0.15,
            "orders_last_24h": int(np.random.poisson(1.2)),
            "orders_last_7d": int(np.random.poisson(3)),
        }
        device = {"linked_accounts": 1, "vpn_detected": False, "emulator_detected": False}

        features = _extract_features(cust, transaction, seller, device)
        X_list.append(features)
        y_list.append(0)  # legitimate

    # Fraudulent samples (30%)
    n_fraud = n_samples - n_legit
    for _ in range(n_fraud):
        cust = generate_fraudulent_customer()
        seller = generate_fraudulent_seller()
        transaction = {
            "amount": np.random.uniform(800, 8000),
            "payment_method": np.random.choice(["COD", "card", "wallet"], p=[0.65, 0.25, 0.10]),
            "is_first_time_buyer": np.random.random() < 0.6,
            "orders_last_24h": int(np.random.poisson(4)),
            "orders_last_7d": int(np.random.poisson(9)),
        }
        device = {
            "linked_accounts": np.random.randint(2, 6),
            "vpn_detected": np.random.random() < 0.3,
            "emulator_detected": np.random.random() < 0.4,
        }

        features = _extract_features(cust, transaction, seller, device)
        X_list.append(features)
        y_list.append(1)  # fraudulent

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.int32)


def _extract_features(customer, transaction, seller, device):
    account_age = customer.get("account_age_days", 365)
    amount = transaction.get("amount", 1000)
    return [
        customer.get("return_rate", 0.0),
        customer.get("cod_refusal_rate", 0.0),
        float(customer.get("linked_device_count", 1)),
        float(customer.get("linked_account_count", 1)),
        min(account_age / 365.0, 1.0),
        float(transaction.get("orders_last_24h", 1)),
        float(transaction.get("orders_last_7d", 1)),
        min(amount / 10000.0, 1.0),
        float(account_age <= 7),
        float(transaction.get("payment_method", "") == "COD"),
        seller.get("dispute_rate", 0.0),
        float(device.get("vpn_detected", False)),
        float(device.get("emulator_detected", False)),
        float(transaction.get("is_first_time_buyer", False)),
        float(transaction.get("orders_last_24h", 1)) / max(float(transaction.get("orders_last_7d", 1)), 1.0),
    ]


def train_risk_model(model_instance):
    """Train the risk model in-place."""
    try:
        X, y = generate_training_data(2000)
        model_instance.train(X, y)
        print(f"  Risk model trained on {len(X)} samples ({sum(y)} fraud, {len(y)-sum(y)} legitimate)")
    except Exception as e:
        print(f"  Risk model training failed: {e}")


if __name__ == "__main__":
    from agents.risk_agent.model import get_risk_model
    model = get_risk_model()
    train_risk_model(model)
    print("Training complete.")
