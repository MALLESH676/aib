"""
TrustShield – SQLAlchemy 2.0 async database models.
All tables use DeclarativeBase, Mapped, and mapped_column.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class Seller(Base):
    """Seller / merchant entity."""

    __tablename__ = "sellers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    account_age_days: Mapped[int] = mapped_column(Integer, default=0)
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    total_returns: Mapped[int] = mapped_column(Integer, default=0)
    dispute_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    is_new_seller: Mapped[bool] = mapped_column(Boolean, default=True)
    seller_tier: Mapped[str] = mapped_column(String, default="new")  # new, established, premium
    brand_authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    country: Mapped[str] = mapped_column(String, default="IN")


class Customer(Base):
    """Buyer / customer entity."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    account_age_days: Mapped[int] = mapped_column(Integer, default=0)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_returns: Mapped[int] = mapped_column(Integer, default=0)
    return_rate: Mapped[float] = mapped_column(Float, default=0.0)
    cod_refusal_rate: Mapped[float] = mapped_column(Float, default=0.0)
    linked_device_count: Mapped[int] = mapped_column(Integer, default=0)
    linked_account_count: Mapped[int] = mapped_column(Integer, default=0)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)


class Product(Base):
    """Product / listing entity."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    seller_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    brand: Mapped[str] = mapped_column(String, nullable=False, default="")
    category: Mapped[str] = mapped_column(String, nullable=False, default="")
    price: Mapped[float] = mapped_column(Float, nullable=False)
    msrp: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    image_url: Mapped[str] = mapped_column(String, default="")
    listing_age_days: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    """Individual purchase transaction."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, nullable=False)
    seller_id: Mapped[str] = mapped_column(String, nullable=False)
    product_id: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(String, nullable=False)  # COD, card, wallet
    status: Mapped[str] = mapped_column(String, nullable=False, default="completed")  # completed, returned, refunded
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    device_id: Mapped[str] = mapped_column(String, default="")
    ip_address: Mapped[str] = mapped_column(String, default="")
    is_first_time_buyer: Mapped[bool] = mapped_column(Boolean, default=False)
    orders_last_24h: Mapped[int] = mapped_column(Integer, default=1)
    orders_last_7d: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Review(Base):
    """Product review."""

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    product_id: Mapped[str] = mapped_column(String, nullable=False)
    customer_id: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False)
    helpful_votes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnalysisCase(Base):
    """
    Central record for every analysis run – stores all agent outputs, the
    fusion score, and the final policy decision.  Human-review workflow fields
    are also stored here.
    """

    __tablename__ = "analysis_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_type: Mapped[str] = mapped_column(String, nullable=False)  # transaction, product, seller
    entity_id: Mapped[str] = mapped_column(String, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Agent outputs stored as JSON strings
    risk_agent_output: Mapped[str] = mapped_column(Text, default="{}")
    auth_agent_output: Mapped[str] = mapped_column(Text, default="{}")
    review_agent_output: Mapped[str] = mapped_column(Text, default="{}")

    # Fusion & decision
    fusion_score: Mapped[float] = mapped_column(Float, default=0.0)
    decision: Mapped[str] = mapped_column(String, default="PENDING")  # ALLOW, REVIEW, HOLD, PENDING
    decision_reason: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    overall_trust_score: Mapped[float] = mapped_column(Float, default=100.0)
    summary: Mapped[str] = mapped_column(Text, default="")

    # Human-review workflow
    human_status: Mapped[str] = mapped_column(String, default="none")  # none, pending, approved, rejected, escalated
    human_action: Mapped[str] = mapped_column(String, default="")
    human_notes: Mapped[str] = mapped_column(Text, default="")
    human_investigator: Mapped[str] = mapped_column(String, default="")
    human_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Performance & labelling
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    scenario_label: Mapped[str] = mapped_column(String, default="")  # A, B, C or empty


class AuditLog(Base):
    """
    Append-only audit trail for every action taken by agents, the policy
    engine, or human investigators.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    actor: Mapped[str] = mapped_column(String, nullable=False)  # risk_agent, auth_agent, review_agent, coordinator, policy_engine, human
    action: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    model_version: Mapped[str] = mapped_column(String, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)


class DeviceAccountLink(Base):
    """
    Many-to-many mapping between device fingerprints and customer accounts,
    used for device-sharing fraud signals.
    """

    __tablename__ = "device_account_links"

    device_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, primary_key=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Async engine & session factory
# ---------------------------------------------------------------------------

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables on application startup (idempotent)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
