import numpy as np
from typing import Optional
import pickle
import os


class RiskModel:
    """
    XGBoost risk scoring model with fallback to rule-based scoring.
    Trained on synthetic data during startup.
    """

    def __init__(self):
        self.model = None
        self.is_trained = False
        self.feature_names = [
            "return_rate", "cod_refusal_rate", "linked_device_count",
            "linked_account_count", "account_age_days_norm", "orders_last_24h",
            "orders_last_7d", "amount_norm", "is_new_account", "payment_method_cod",
            "dispute_rate", "vpn_detected", "emulator_detected",
            "is_first_time_buyer", "order_frequency_ratio"
        ]

    def _extract_features(self, customer: dict, transaction: dict, seller: dict, device: dict) -> np.ndarray:
        account_age = customer.get("account_age_days", 365)
        amount = transaction.get("amount", 1000)
        features = [
            customer.get("return_rate", 0.0),
            customer.get("cod_refusal_rate", 0.0),
            float(customer.get("linked_device_count", 1)),
            float(customer.get("linked_account_count", 1)),
            min(account_age / 365.0, 1.0),  # normalized to 0-1
            float(transaction.get("orders_last_24h", 1)),
            float(transaction.get("orders_last_7d", 1)),
            min(amount / 10000.0, 1.0),  # normalized
            float(account_age <= 7),
            float(transaction.get("payment_method", "") == "COD"),
            seller.get("dispute_rate", 0.0),
            float(device.get("vpn_detected", False)),
            float(device.get("emulator_detected", False)),
            float(transaction.get("is_first_time_buyer", False)),
            float(transaction.get("orders_last_24h", 1)) / max(float(transaction.get("orders_last_7d", 1)), 1.0),
        ]
        return np.array(features, dtype=np.float32).reshape(1, -1)

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        try:
            from xgboost import XGBClassifier
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                use_label_encoder=False,
                eval_metric="logloss",
                random_state=42,
                verbosity=0
            )
            self.model.fit(X, y)
            self.is_trained = True
        except Exception as e:
            print(f"XGBoost training failed: {e}. Using rule-based fallback.")
            self.is_trained = False

    def predict_proba(self, customer: dict, transaction: dict, seller: dict, device: dict) -> float:
        """Returns fraud probability 0.0 - 1.0"""
        if self.model is None or not self.is_trained:
            return 0.0  # Caller should use rule score as fallback
        try:
            features = self._extract_features(customer, transaction, seller, device)
            prob = self.model.predict_proba(features)[0][1]
            return float(prob)
        except Exception as e:
            print(f"Model prediction failed: {e}")
            return 0.0


# Global model instance
_risk_model: Optional[RiskModel] = None


def get_risk_model() -> RiskModel:
    global _risk_model
    if _risk_model is None:
        _risk_model = RiskModel()
    return _risk_model
