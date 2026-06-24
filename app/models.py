"""
models.py
─────────
SQLAlchemy ORM models representing:
  • customers
  • credit_gaps
  • offers
"""

import enum
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class GapStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"


class OfferStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    disbursed = "disbursed"


# ─────────────────────────────────────────────
# CUSTOMER TABLE
# ─────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String(255), nullable=False)
    mobile = Column(String(10), nullable=False, unique=True, index=True)
    pan = Column(String(10), nullable=False, unique=True, index=True)

    cibil_score = Column(Integer, nullable=True)
    score_fetched_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    credit_gaps = relationship(
        "CreditGap",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    offers = relationship(
        "Offer",
        back_populates="customer",
        cascade="all, delete-orphan",
    )


# ─────────────────────────────────────────────
# CREDIT GAP TABLE
# ─────────────────────────────────────────────

class CreditGap(Base):
    __tablename__ = "credit_gaps"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    factor = Column(String(255), nullable=False)
    current_value = Column(String(255), nullable=False)
    ideal_value = Column(String(255), nullable=False)

    impact = Column(
        Enum("high", "medium", "low", name="gap_impact_enum"),
        nullable=False,
    )

    estimated_score_gain = Column(Integer, default=0, nullable=False)

    action_description = Column(Text, nullable=False)

    status = Column(
        Enum(GapStatus, name="gap_status_enum"),
        default=GapStatus.open,
        nullable=False,
        index=True,
    )

    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationship
    customer = relationship("Customer", back_populates="credit_gaps")


# ─────────────────────────────────────────────
# OFFER TABLE
# ─────────────────────────────────────────────

class Offer(Base):
    __tablename__ = "offers"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    lender = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    tenure_months = Column(Integer, nullable=False)

    min_score_required = Column(Integer, nullable=False)

    status = Column(
        Enum(OfferStatus, name="offer_status_enum"),
        default=OfferStatus.pending,
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationship
    customer = relationship("Customer", back_populates="offers")