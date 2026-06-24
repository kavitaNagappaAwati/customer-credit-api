from typing import Optional, List

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import EMIResponse, OfferCreate, OfferResponse, OfferStatusUpdate
from app.services.emi import calculate_emi
from app.services.score_logic import (
    compute_score_gap,
    is_offer_locked,
    validate_status_transition,
)

router = APIRouter(tags=["Offers"])


# ───────── Helper ─────────

def enrich_offer(offer, customer_score: Optional[int]) -> OfferResponse:
    locked = is_offer_locked(customer_score, offer)
    gap = compute_score_gap(customer_score, offer)

    return OfferResponse(
        id=offer.id,
        customer_id=offer.customer_id,
        lender=offer.lender,
        amount=offer.amount,
        interest_rate=offer.interest_rate,
        tenure_months=offer.tenure_months,
        min_score_required=offer.min_score_required,
        status=offer.status,
        created_at=offer.created_at,
        locked=locked,
        score_gap=gap,
    )


# ───────── CREATE OFFER ─────────

@router.post(
    "/customers/{customer_id}/offers",
    response_model=OfferResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_offer(customer_id: int, payload: OfferCreate, db: Session = Depends(get_db)):

    customer = crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="CUSTOMER_NOT_FOUND")

    offer = crud.create_offer(db, customer_id, payload)

    return enrich_offer(offer, customer.cibil_score)


# ───────── LIST OFFERS ─────────

@router.get(
    "/customers/{customer_id}/offers",
    response_model=List[OfferResponse],
)
def list_offers(
    customer_id: int,
    locked: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):

    customer = crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="CUSTOMER_NOT_FOUND")

    offers = crud.get_offers_by_customer(db, customer_id)

    enriched = [
        enrich_offer(o, customer.cibil_score)
        for o in offers
    ]

    if locked is not None:
        enriched = [o for o in enriched if o.locked == locked]

    return enriched


# ───────── UPDATE STATUS ─────────

@router.patch("/offers/{offer_id}/status", response_model=OfferResponse)
def update_offer_status(
    offer_id: int,
    payload: OfferStatusUpdate,
    db: Session = Depends(get_db),
):

    offer = crud.get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="OFFER_NOT_FOUND")

    ok, msg = validate_status_transition(offer.status, payload.status)
    if not ok:
        raise HTTPException(
            status_code=422,
            detail=msg,
        )

    customer = crud.get_customer(db, offer.customer_id)

    if is_offer_locked(customer.cibil_score if customer else None, offer):
        raise HTTPException(
            status_code=422,
            detail=f"Offer locked: score too low",
        )

    updated = crud.update_offer_status(db, offer, payload.status)

    return enrich_offer(updated, customer.cibil_score if customer else None)


# ───────── EMI ─────────

@router.get("/offers/{offer_id}/emi", response_model=EMIResponse)
def get_emi(offer_id: int, db: Session = Depends(get_db)):

    offer = crud.get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="OFFER_NOT_FOUND")

    return calculate_emi(offer)