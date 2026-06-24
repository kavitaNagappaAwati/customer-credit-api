"""
crud.py
───────
Repository layer — all raw database operations live here.
Routers and services never touch SQLAlchemy directly; they call these functions.

Follows the Repository Pattern:
  • One function per discrete DB operation.
  • Functions accept a `db: Session` as their first argument (injected by FastAPI).
  • Functions return ORM model instances or None — never raw dicts.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import CreditGap, Customer, GapStatus, Offer, OfferStatus
from app.schemas import (
    CreditGapCreate,
    CreditScoreUpdate,
    CustomerCreate,
    OfferCreate,
)


# ══════════════════════════════════════════════════════════════════════════════
# Customer CRUD
# ══════════════════════════════════════════════════════════════════════════════

def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    """Fetch a customer by primary key. Returns None if not found."""
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_customer_by_mobile(db: Session, mobile: str) -> Optional[Customer]:
    """Fetch a customer by mobile number (used for duplicate detection)."""
    return db.query(Customer).filter(Customer.mobile == mobile).first()


def create_customer(db: Session, payload: CustomerCreate) -> Customer:
    """
    Persist a new Customer record.

    Args:
        db:      Active database session.
        payload: Validated CustomerCreate schema.

    Returns:
        The newly created Customer ORM instance (with `id` populated).
    """
    customer = Customer(
        name=payload.name,
        mobile=payload.mobile,
        pan=payload.pan,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_credit_score(
    db: Session, customer: Customer, payload: CreditScoreUpdate
) -> Customer:
    """
    Update the customer's CIBIL score and record the fetch timestamp (UTC now).

    Args:
        db:       Active database session.
        customer: The ORM instance to mutate.
        payload:  Validated CreditScoreUpdate schema.

    Returns:
        The updated Customer ORM instance.
    """
    customer.cibil_score = payload.cibil_score
    customer.score_fetched_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(customer)
    return customer


# ══════════════════════════════════════════════════════════════════════════════
# Credit Gap CRUD
# ══════════════════════════════════════════════════════════════════════════════

def create_credit_gap(
    db: Session, customer_id: int, payload: CreditGapCreate
) -> CreditGap:
    """
    Persist a new CreditGap record for the given customer.

    Args:
        db:          Active database session.
        customer_id: FK to the parent Customer row.
        payload:     Validated CreditGapCreate schema.

    Returns:
        The newly created CreditGap ORM instance.
    """
    gap = CreditGap(
        customer_id=customer_id,
        factor=payload.factor,
        current_value=payload.current_value,
        ideal_value=payload.ideal_value,
        impact=payload.impact,
        estimated_score_gain=payload.estimated_score_gain,
        action_description=payload.action_description,
        status=GapStatus.open,
    )
    db.add(gap)
    db.commit()
    db.refresh(gap)
    return gap


def get_credit_gap(db: Session, gap_id: int) -> Optional[CreditGap]:
    """Fetch a credit gap by primary key. Returns None if not found."""
    return db.query(CreditGap).filter(CreditGap.id == gap_id).first()


def resolve_credit_gap(db: Session, gap: CreditGap) -> CreditGap:
    """
    Mark a credit gap as resolved and stamp the resolution timestamp.

    Args:
        db:  Active database session.
        gap: The ORM instance to mutate.

    Returns:
        The updated CreditGap ORM instance.
    """
    gap.status = GapStatus.resolved
    gap.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(gap)
    return gap


def get_gaps_by_customer(
    db: Session, customer_id: int
) -> List[CreditGap]:
    """Return all credit gaps (open + resolved) for a given customer."""
    return (
        db.query(CreditGap)
        .filter(CreditGap.customer_id == customer_id)
        .order_by(CreditGap.created_at.desc())
        .all()
    )


def get_open_gaps_by_customer(
    db: Session, customer_id: int
) -> List[CreditGap]:
    """Return only open credit gaps for a given customer."""
    return (
        db.query(CreditGap)
        .filter(
            CreditGap.customer_id == customer_id,
            CreditGap.status == GapStatus.open,
        )
        .all()
    )


def get_resolved_gaps_by_customer(
    db: Session, customer_id: int
) -> List[CreditGap]:
    """Return only resolved credit gaps for a given customer."""
    return (
        db.query(CreditGap)
        .filter(
            CreditGap.customer_id == customer_id,
            CreditGap.status == GapStatus.resolved,
        )
        .all()
    )


# ══════════════════════════════════════════════════════════════════════════════
# Offer CRUD
# ══════════════════════════════════════════════════════════════════════════════

def create_offer(
    db: Session, customer_id: int, payload: OfferCreate
) -> Offer:
    """
    Persist a new Offer record. Status is always initialised to `pending`.

    Args:
        db:          Active database session.
        customer_id: FK to the parent Customer row.
        payload:     Validated OfferCreate schema.

    Returns:
        The newly created Offer ORM instance.
    """
    offer = Offer(
        customer_id=customer_id,
        lender=payload.lender,
        amount=payload.amount,
        interest_rate=payload.interest_rate,
        tenure_months=payload.tenure_months,
        min_score_required=payload.min_score_required,
        status=OfferStatus.pending,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


def get_offer(db: Session, offer_id: int) -> Optional[Offer]:
    """Fetch an offer by primary key. Returns None if not found."""
    return db.query(Offer).filter(Offer.id == offer_id).first()


def get_offers_by_customer(
    db: Session, customer_id: int, locked: Optional[bool] = None
) -> List[Offer]:
    """
    Return all offers for a given customer, optionally filtered by lock status.

    Lock status is computed dynamically: an offer is locked if the customer's
    CIBIL score is below the offer's min_score_required.

    Note: because `locked` is a computed property, filtering happens in Python
    after the DB fetch rather than in SQL.

    Args:
        db:          Active database session.
        customer_id: The customer whose offers to retrieve.
        locked:      If True → return only locked offers;
                     If False → return only unlocked offers;
                     If None → return all offers.

    Returns:
        List of Offer ORM instances.
    """
    offers = (
        db.query(Offer)
        .filter(Offer.customer_id == customer_id)
        .order_by(Offer.created_at.desc())
        .all()
    )

    if locked is None:
        return offers

    # Requires the customer object to compute locked status — fetch it once
    customer = get_customer(db, customer_id)
    score = customer.cibil_score if customer else None

    def _is_locked(offer: Offer) -> bool:
        if score is None:
            return True
        return score < offer.min_score_required

    return [o for o in offers if _is_locked(o) == locked]


def update_offer_status(db: Session, offer: Offer, new_status: OfferStatus) -> Offer:
    """
    Transition an offer to the given status (caller must validate the transition).

    Args:
        db:         Active database session.
        offer:      The ORM instance to mutate.
        new_status: The target OfferStatus enum value.

    Returns:
        The updated Offer ORM instance.
    """
    offer.status = new_status
    db.commit()
    db.refresh(offer)
    return offer
