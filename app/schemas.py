"""
schemas.py
──────────
Pydantic v2 schemas for request validation and response serialisation.

Naming convention:
  <Model>Create   — inbound payload for POST
  <Model>Update   — inbound payload for PATCH
  <Model>Response — outbound representation sent to clients
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator, model_validator

from app.models import GapStatus, OfferStatus


# ── Shared helpers ─────────────────────────────────────────────────────────────

PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
MOBILE_REGEX = re.compile(r"^\d{10}$")


# ══════════════════════════════════════════════════════════════════════════════
# Customer schemas
# ══════════════════════════════════════════════════════════════════════════════

class CustomerCreate(BaseModel):
    """Payload required to register a new customer."""

    name: str
    mobile: str
    pan: str

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        if not MOBILE_REGEX.match(v):
            raise ValueError("Mobile number must be exactly 10 digits.")
        return v

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        if not PAN_REGEX.match(v):
            raise ValueError("PAN must match format AAAAA9999A (e.g. ABCDE1234F).")
        return v


class CustomerResponse(BaseModel):
    """Full customer representation returned from the API."""

    id: int
    name: str
    mobile: str
    pan: str
    cibil_score: Optional[int]
    score_fetched_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Credit Score schemas
# ══════════════════════════════════════════════════════════════════════════════

class CreditScoreUpdate(BaseModel):
    """Payload to update a customer's CIBIL score."""

    cibil_score: int

    @field_validator("cibil_score")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        if not (300 <= v <= 900):
            raise ValueError("CIBIL score must be between 300 and 900.")
        return v


# ══════════════════════════════════════════════════════════════════════════════
# Credit Gap schemas
# ══════════════════════════════════════════════════════════════════════════════

class CreditGapCreate(BaseModel):
    """Payload to register a new credit gap for a customer."""

    factor: str
    current_value: str
    ideal_value: str
    impact: Literal["high", "medium", "low"]
    estimated_score_gain: int
    action_description: str

    @field_validator("estimated_score_gain")
    @classmethod
    def non_negative_gain(cls, v: int) -> int:
        if v < 0:
            raise ValueError("estimated_score_gain cannot be negative.")
        return v


class CreditGapResponse(BaseModel):
    """Full credit gap representation returned from the API."""

    id: int
    customer_id: int
    factor: str
    current_value: str
    ideal_value: str
    impact: str
    estimated_score_gain: int
    action_description: str
    status: GapStatus
    resolved_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Credit Profile schema
# ══════════════════════════════════════════════════════════════════════════════

class CreditProfileResponse(BaseModel):
    """
    Aggregated view of a customer's credit health:
    includes their score, potential score, and all gaps broken down by status.
    """

    customer: CustomerResponse
    current_score: Optional[int]
    potential_score: Optional[int]
    open_gaps: List[CreditGapResponse]
    resolved_gaps: List[CreditGapResponse]

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Improvement Summary schema
# ══════════════════════════════════════════════════════════════════════════════

class ImprovementSummaryResponse(BaseModel):
    """
    Bonus endpoint — summarises the score improvement journey for a customer.
    """

    customer_id: int
    resolved_gaps: List[CreditGapResponse]
    recovered_score: int          # Sum of estimated_score_gain from resolved gaps
    remaining_score_gain: int     # Sum of estimated_score_gain from open gaps

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Offer schemas
# ══════════════════════════════════════════════════════════════════════════════

class OfferCreate(BaseModel):
    """Payload to create a new loan offer for a customer."""

    lender: str
    amount: float
    interest_rate: float
    tenure_months: int
    min_score_required: int

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Loan amount must be positive.")
        return v

    @field_validator("interest_rate")
    @classmethod
    def valid_rate(cls, v: float) -> float:
        if not (0 < v <= 100):
            raise ValueError("Interest rate must be between 0 and 100.")
        return v

    @field_validator("tenure_months")
    @classmethod
    def positive_tenure(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Tenure must be at least 1 month.")
        return v

    @field_validator("min_score_required")
    @classmethod
    def valid_min_score(cls, v: int) -> int:
        if not (300 <= v <= 900):
            raise ValueError("min_score_required must be between 300 and 900.")
        return v


class OfferResponse(BaseModel):
    """
    Full offer representation including the dynamic `locked` flag and `score_gap`.
    These are computed at query time and not persisted to the database.
    """

    id: int
    customer_id: int
    lender: str
    amount: float
    interest_rate: float
    tenure_months: int
    min_score_required: int
    status: OfferStatus
    created_at: datetime
    locked: bool
    score_gap: int       # 0 if unlocked; (min_score_required - cibil_score) if locked

    model_config = {"from_attributes": True}


class OfferStatusUpdate(BaseModel):
    """Payload to transition an offer's status."""

    status: OfferStatus


# ══════════════════════════════════════════════════════════════════════════════
# EMI Calculator schema
# ══════════════════════════════════════════════════════════════════════════════

class EMIResponse(BaseModel):
    """Result of the EMI calculation — never persisted."""

    offer_id: int
    principal: float
    interest_rate: float
    tenure_months: int
    monthly_emi: float


# ══════════════════════════════════════════════════════════════════════════════
# Standard error schema
# ══════════════════════════════════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    """Uniform error envelope returned for all 4xx / 5xx responses."""

    error: str
    code: str
