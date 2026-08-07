"""
TrustShield – Pydantic v2 schemas for request/response validation.
All schemas use model_config = ConfigDict(extra="ignore") for forward-compatibility.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared config mixin
# ---------------------------------------------------------------------------

class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore")


# ===========================================================================
# 1. INPUT SCHEMAS
# ===========================================================================

class CustomerInput(_Base):
    """Buyer profile snapshot included in an analysis request."""

    id: str
    account_age_days: int
    total_orders: int
    total_returns: int
    return_rate: float
    cod_refusal_rate: float
    linked_device_count: int
    linked_account_count: int


class TransactionInput(_Base):
    """Single transaction being evaluated."""

    id: str
    amount: float
    payment_method: str  # COD, card, wallet
    is_first_time_buyer: bool
    orders_last_24h: int
    orders_last_7d: int
    status: str = "completed"


class SellerInput(_Base):
    """Seller profile snapshot included in an analysis request."""

    id: str
    name: str = ""
    account_age_days: int
    total_sales: int
    avg_rating: float
    dispute_rate: float
    is_new_seller: bool
    brand_authorized: bool = False


class ProductInput(_Base):
    """Product / listing being evaluated."""

    id: str
    title: str
    description: str
    brand: str
    category: str
    price: float
    msrp: float
    image_url: str = ""
    listing_age_days: int


class ReviewInput(_Base):
    """A single product review included for manipulation analysis."""

    id: str
    customer_id: str
    rating: int
    text: str
    timestamp: str  # ISO-8601 format
    verified_purchase: bool = False


class DeviceInput(_Base):
    """Device / session signals."""

    id: str
    linked_accounts: int
    vpn_detected: bool = False
    emulator_detected: bool = False


class AnalysisRequest(_Base):
    """
    Top-level payload sent to the /analyze endpoint.
    case_type determines which agents are invoked.
    """

    event_id: str
    case_type: str = "transaction"  # transaction, product, seller
    customer: Optional[CustomerInput] = None
    transaction: Optional[TransactionInput] = None
    seller: SellerInput
    product: ProductInput
    reviews: List[ReviewInput] = Field(default_factory=list)
    device: Optional[DeviceInput] = None
    review_window_hours: int = 24


# ===========================================================================
# 2. AGENT OUTPUT SCHEMAS
# ===========================================================================

class SignalItem(_Base):
    """A single scored feature / signal produced by an agent."""

    signal: str
    value: Any
    weight: float = 0.0
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    detail: str = ""


# ---------------------------------------------------------------------------
# Risk Agent
# ---------------------------------------------------------------------------

class RiskAgentOutput(_Base):
    """Output from the transaction-risk scoring agent."""

    agent: str = "risk_agent"
    version: str = "1.0.0"
    event_id: str
    risk_score: float          # 0-100
    risk_category: str         # LOW, MEDIUM, HIGH, CRITICAL
    signals: List[SignalItem]
    recommendation: str        # ALLOW, REVIEW, HOLD
    confidence: float          # 0-1
    explanation: str
    model_version: str
    latency_ms: int


# ---------------------------------------------------------------------------
# Authenticity Agent
# ---------------------------------------------------------------------------

class SuspiciousAttribute(_Base):
    """A potentially counterfeit attribute flagged by the authenticity agent."""

    attribute: str
    detail: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


class ImageAnalysis(_Base):
    """Structured results from image / logo analysis."""

    logo_consistency: str
    image_quality_score: float
    similar_known_counterfeits: int
    notes: str


class AuthenticityAgentOutput(_Base):
    """Output from the product-authenticity / counterfeit-detection agent."""

    agent: str = "authenticity_agent"
    version: str = "1.0.0"
    event_id: str
    counterfeit_probability: float   # 0-1
    risk_score: float                # 0-100
    suspicious_attributes: List[SuspiciousAttribute]
    image_analysis: ImageAnalysis
    recommendation: str              # ALLOW, REVIEW, HOLD
    confidence: float                # 0-1
    explanation: str
    model_version: str
    latency_ms: int


# ---------------------------------------------------------------------------
# Review-Manipulation Agent
# ---------------------------------------------------------------------------

class ClusterAnalysis(_Base):
    """Network / cluster metrics for coordinated review detection."""

    suspicious_clusters: int
    cluster_size: int
    network_density: float
    linked_accounts: List[str]


class RatingStats(_Base):
    """Aggregated statistics over the review window."""

    avg_rating: float
    five_star_rate: float
    review_velocity: int          # reviews per window
    velocity_window_minutes: float


class ReviewAgentOutput(_Base):
    """Output from the review-manipulation detection agent."""

    agent: str = "review_agent"
    version: str = "1.0.0"
    event_id: str
    manipulation_probability: float  # 0-1
    risk_score: float                # 0-100
    signals: List[SignalItem]
    cluster_analysis: ClusterAnalysis
    rating_stats: RatingStats
    recommendation: str              # ALLOW, FLAG, HOLD
    confidence: float                # 0-1
    explanation: str
    model_version: str
    latency_ms: int


# ---------------------------------------------------------------------------
# Fusion & final decision
# ---------------------------------------------------------------------------

class FusionOutput(_Base):
    """Weighted fusion of all agent scores."""

    weighted_score: float
    weights: Dict[str, float]
    component_scores: Dict[str, float]


class PolicyDecision(_Base):
    """Output of the policy engine after consulting fusion results."""

    decision: str                # ALLOW, REVIEW, HOLD
    reason: str
    threshold_used: float
    requires_human_approval: bool
    action_taken: str


class AnalysisResponse(_Base):
    """Full response returned from the /analyze endpoint."""

    case_id: str
    event_id: str
    timestamp: str               # ISO-8601
    agent_outputs: Dict[str, Any]
    fusion: FusionOutput
    policy_decision: PolicyDecision
    overall_trust_score: float   # 0-100  (100 = fully trusted)
    overall_risk_score: float    # 0-100
    summary: str
    latency_ms: int


# ===========================================================================
# 3. DASHBOARD / API SCHEMAS
# ===========================================================================

class DashboardStats(_Base):
    """Aggregate metrics shown on the operations dashboard."""

    total_cases: int
    allowed: int
    under_review: int
    held: int
    human_review_queue: int
    avg_risk_score: float
    avg_latency_ms: float
    detection_rate: float  # (held + review) / total


class CaseSummary(_Base):
    """Lightweight case record for list / table views."""

    id: str
    case_type: str
    entity_id: str
    decision: str
    fusion_score: float
    overall_trust_score: float
    created_at: str          # ISO-8601
    human_status: str
    scenario_label: str


class HumanActionRequest(_Base):
    """Payload posted by a human investigator to act on a case."""

    action: str              # approve, reject, escalate, request_more_evidence
    notes: str = ""
    investigator: str = "investigator_1"


class AuditLogEntry(_Base):
    """Single entry from the audit log, returned by the audit API."""

    id: int
    case_id: str
    timestamp: str           # ISO-8601
    actor: str
    action: str
    detail: Dict[str, Any]
    model_version: str
    confidence: float
