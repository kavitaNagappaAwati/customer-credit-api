"""
services/score_logic.py
────────────────────────
Business logic for:
  1. Score gating  — determining whether an offer is locked/unlocked.
  2. Status transitions — enforcing the pending → active → disbursed pipeline.
  3. Potential score — computing expected score after resolving all open gaps.
"""

from typing import List, Optional, Tuple

from app.models import CreditGap, GapStatus, Offer, OfferStatus


# ── Valid transition map ──────────────────────────────────────────────────────
# Only the pairs listed here are legal. Any other transition must be rejected.
VALID_TRANSITIONS = {
    OfferStatus.pending: OfferStatus.active,
    OfferStatus.active: OfferStatus.disbursed,
}


def is_offer_locked(customer_score: Optional[int], offer: Offer) -> bool:
    """
    Determine whether an offer is accessible to a customer.

    An offer is locked when:
      • The customer has no CIBIL score on record, OR
      • The customer's score is strictly below the offer's minimum requirement.

    Args:
        customer_score: The customer's current CIBIL score (may be None).
        offer:          The Offer ORM instance to check.

    Returns:
        True if the offer is locked (customer cannot proceed), False otherwise.
    """
    if customer_score is None:
        return True
    return customer_score < offer.min_score_required


def compute_score_gap(customer_score: Optional[int], offer: Offer) -> int:
    """
    Return the number of CIBIL points the customer needs to unlock an offer.

    If the offer is already unlocked, returns 0.

    Args:
        customer_score: The customer's current CIBIL score.
        offer:          The Offer ORM instance.

    Returns:
        Non-negative integer score gap.
    """
    if not is_offer_locked(customer_score, offer):
        return 0
    if customer_score is None:
        return offer.min_score_required  # Need the full minimum
    return offer.min_score_required - customer_score


def compute_potential_score(
    current_score: Optional[int],
    open_gaps: List[CreditGap],
) -> Optional[int]:
    """
    Estimate the customer's CIBIL score if all open credit gaps are resolved.

    Potential Score = Current Score + Σ(estimated_score_gain for each open gap)

    Args:
        current_score: The customer's current CIBIL score.
        open_gaps:     List of unresolved CreditGap ORM instances.

    Returns:
        The projected score (capped at 900), or None if no score exists yet.
    """
    if current_score is None:
        return None
    gain = sum(g.estimated_score_gain for g in open_gaps if g.status == GapStatus.open)
    return min(current_score + gain, 900)


def validate_status_transition(
    current_status: OfferStatus,
    requested_status: OfferStatus,
) -> Tuple[bool, Optional[str]]:
    """
    Check whether a status change from `current_status` to `requested_status`
    is a legal transition in the offer pipeline.

    Args:
        current_status:   The offer's existing status.
        requested_status: The status the caller wants to set.

    Returns:
        A tuple (is_valid: bool, error_message: Optional[str]).
        If valid, error_message is None.
    """
    if current_status == requested_status:
        return False, f"Offer is already in '{current_status.value}' status."

    expected_next = VALID_TRANSITIONS.get(current_status)
    if expected_next != requested_status:
        valid_str = expected_next.value if expected_next else "none (already final)"
        return (
            False,
            (
                f"Invalid transition: '{current_status.value}' → '{requested_status.value}'. "
                f"Only '{current_status.value}' → '{valid_str}' is allowed."
            ),
        )
    return True, None
