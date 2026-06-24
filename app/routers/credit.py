"""
routers/credit.py
─────────────────
Endpoints:
  POST   /customers/{id}/credit-gaps    — Create a credit gap
  PATCH  /credit-gaps/{id}/resolve      — Resolve an open credit gap
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import GapStatus
from app.schemas import CreditGapCreate, CreditGapResponse
from app.utils.responses import error_response

router = APIRouter(tags=["Credit Gaps"])


# ── POST /customers/{id}/credit-gaps ──────────────────────────────────────────

@router.post(
    "/customers/{customer_id}/credit-gaps",
    response_model=CreditGapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a credit gap for a customer",
)
def create_credit_gap(
    customer_id: int,
    payload: CreditGapCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new credit gap — a specific factor reducing the customer's
    CIBIL score — along with the recommended remediation action.

    The gap status defaults to `open`.
    """
    customer = crud.get_customer(db, customer_id)
    if not customer:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error=f"Customer with id {customer_id} not found.",
            code="CUSTOMER_NOT_FOUND",
        )

    gap = crud.create_credit_gap(db, customer_id, payload)
    return gap


# ── PATCH /credit-gaps/{id}/resolve ───────────────────────────────────────────

@router.patch(
    "/credit-gaps/{gap_id}/resolve",
    response_model=CreditGapResponse,
    summary="Mark a credit gap as resolved",
)
def resolve_credit_gap(
    gap_id: int,
    db: Session = Depends(get_db),
):
    """
    Transition a credit gap from `open` to `resolved` and record the
    resolution timestamp.

    Returns 404 if the gap does not exist.
    Returns 422 if the gap is already resolved.
    """
    gap = crud.get_credit_gap(db, gap_id)
    if not gap:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            error=f"Credit gap with id {gap_id} not found.",
            code="GAP_NOT_FOUND",
        )

    if gap.status == GapStatus.resolved:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error=f"Credit gap {gap_id} is already resolved.",
            code="GAP_ALREADY_RESOLVED",
        )

    resolved = crud.resolve_credit_gap(db, gap)
    return resolved
