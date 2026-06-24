"""
services/emi.py
───────────────
Pure-function EMI calculation service.

Formula (standard reducing-balance EMI):
    EMI = [P × r × (1 + r)^n] / [(1 + r)^n − 1]

Where:
    P = Principal (loan amount)
    r = Monthly interest rate  = annual_rate / 12 / 100
    n = Tenure in months
"""

import math

from app.models import Offer
from app.schemas import EMIResponse


def calculate_emi(offer: Offer) -> EMIResponse:
    """
    Calculate the fixed monthly EMI for a given loan offer.

    The calculation is done entirely in memory — no database writes occur.

    Args:
        offer: An ORM Offer instance containing principal, rate, and tenure.

    Returns:
        An EMIResponse schema with all relevant fields populated.

    Raises:
        ValueError: If the interest rate is zero (edge-case handled gracefully
                    by returning a simple division result).
    """
    principal: float = offer.amount
    annual_rate: float = offer.interest_rate
    tenure_months: int = offer.tenure_months

    if annual_rate == 0:
        # Zero-interest loan — divide principal evenly across tenure
        monthly_emi = round(principal / tenure_months, 2)
    else:
        monthly_rate: float = annual_rate / 12 / 100  # r
        compound_factor: float = math.pow(1 + monthly_rate, tenure_months)  # (1+r)^n
        monthly_emi = round(
            (principal * monthly_rate * compound_factor) / (compound_factor - 1), 2
        )

    return EMIResponse(
        offer_id=offer.id,
        principal=principal,
        interest_rate=annual_rate,
        tenure_months=tenure_months,
        monthly_emi=monthly_emi,
    )
