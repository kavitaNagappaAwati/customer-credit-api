"""
utils/validators.py
───────────────────
Pure-function helpers for validating raw strings before they reach Pydantic.
These can also be called from service-layer code when you need programmatic
validation outside of a schema context.
"""

import re

# ── Compiled patterns (compile once, reuse many) ───────────────────────────────

_PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
_MOBILE_PATTERN = re.compile(r"^\d{10}$")


def is_valid_pan(pan: str) -> bool:
    """
    Validate an Indian Permanent Account Number (PAN).

    Format: AAAAA9999A
      - 5 uppercase letters
      - 4 digits
      - 1 uppercase letter

    Args:
        pan: The PAN string to validate.

    Returns:
        True if the PAN is structurally valid, False otherwise.
    """
    return bool(_PAN_PATTERN.match(pan))


def is_valid_mobile(mobile: str) -> bool:
    """
    Validate a 10-digit Indian mobile number (digits only, no country code).

    Args:
        mobile: The mobile string to validate.

    Returns:
        True if exactly 10 digits, False otherwise.
    """
    return bool(_MOBILE_PATTERN.match(mobile))
