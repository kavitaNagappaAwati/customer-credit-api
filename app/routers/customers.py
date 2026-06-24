"""
routers/customers.py
────────────────────
Endpoints:
  POST   /customers                       — Register a new customer
  POST   /customers/{id}/credit-score     — Update CIBIL score
  GET    /customers/{id}/credit-profile   — Full credit profile view
  GET    /customers/{id}/improvement-summary (bonus)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import (
    CreditProfileResponse,
    CreditScoreUpdate,
    CustomerCreate,
    CustomerResponse,
    ImprovementSummaryResponse,
)
from app.services.score_logic import compute_potential_score
from app.utils.responses import error_response

router = APIRouter(prefix="/customers", tags=["Customers"])


# ── POST /customers ────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer",
)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new customer record.

    Validates:
      • PAN format  (AAAAA9999A)
      • Mobile is exactly 10 digits
      • Mobile is not already registered (returns 409 on duplicate)
    """
    # Duplicate mobile check
    existing = crud.get_customer_by_mobile(db, payload.mobile)
    if existing:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            error=f"A customer with mobile '{payload.mobile}' already exists.",
            code="DUPLICATE_MOBILE",
        )

    customer = crud.create_customer(db, payload)
    return customer


# ── POST /customers/{id}/credit-score ─────────────────────────────────────────

@router.post(
    "/{customer_id}/credit-score",
    response_model=CustomerResponse,
    summary="Update a customer's CIBIL score",
)
def update_credit_score(
    customer_id: int,
    payload: CreditScoreUpdate,
    db: Session = Depends(get_db),
):
    """
    Record the latest CIBIL score for a customer and update `score_fetched_at`
    to the current UTC timestamp.

    Score must be in the range [300, 900].
    """
    customer = crud.get_customer(db, customer_id)
    if not customer:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error=f"Customer with id {customer_id} not found.",
            code="CUSTOMER_NOT_FOUND",
        )

    updated = crud.update_credit_score(db, customer, payload)
    return updated


# ── GET /customers/{id}/credit-profile ────────────────────────────────────────

@router.get(
    "/{customer_id}/credit-profile",
    response_model=CreditProfileResponse,
    summary="Get the full credit profile for a customer",
)
def get_credit_profile(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns a consolidated view of the customer's credit health:

      • Customer details
      • Current CIBIL score
      • Potential score (current + sum of open gap gains)
      • Open credit gaps (actionable items)
      • Resolved credit gaps (historical)
    """
    customer = crud.get_customer(db, customer_id)
    if not customer:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error=f"Customer with id {customer_id} not found.",
            code="CUSTOMER_NOT_FOUND",
        )

    open_gaps = crud.get_open_gaps_by_customer(db, customer_id)
    resolved_gaps = crud.get_resolved_gaps_by_customer(db, customer_id)
    potential_score = compute_potential_score(customer.cibil_score, open_gaps)

    return CreditProfileResponse(
        customer=customer,
        current_score=customer.cibil_score,
        potential_score=potential_score,
        open_gaps=open_gaps,
        resolved_gaps=resolved_gaps,
    )


# ── GET /customers/{id}/improvement-summary (bonus) ───────────────────────────

@router.get(
    "/{customer_id}/improvement-summary",
    response_model=ImprovementSummaryResponse,
    summary="[Bonus] Score improvement journey summary",
)
def improvement_summary(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns a summary of the customer's score improvement journey:

      • resolved_gaps      — gaps that have been actioned
      • recovered_score    — total CIBIL points already regained
      • remaining_score_gain — potential points still available from open gaps
    """
    customer = crud.get_customer(db, customer_id)
    if not customer:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error=f"Customer with id {customer_id} not found.",
            code="CUSTOMER_NOT_FOUND",
        )

    resolved_gaps = crud.get_resolved_gaps_by_customer(db, customer_id)
    open_gaps = crud.get_open_gaps_by_customer(db, customer_id)

    recovered_score = sum(g.estimated_score_gain for g in resolved_gaps)
    remaining_score_gain = sum(g.estimated_score_gain for g in open_gaps)

    return ImprovementSummaryResponse(
        customer_id=customer_id,
        resolved_gaps=resolved_gaps,
        recovered_score=recovered_score,
        remaining_score_gain=remaining_score_gain,
    )
