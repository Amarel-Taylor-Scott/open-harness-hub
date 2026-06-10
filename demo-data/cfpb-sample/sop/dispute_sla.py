"""CFPB-sample — dispute SLA constants (synthetic demo). Implements Reg E §1005.11."""
from __future__ import annotations

# Per Reg E §1005.11. The FAQ's "30" is stale; this is the implemented SLA.
ERROR_RESOLUTION_BUSINESS_DAYS = 10
EXTENDED_DAYS_WITH_PROVISIONAL_CREDIT = 45


def is_on_time(business_days_elapsed: int, provisional_credit: bool) -> bool:
    """True iff the investigation is still within the Reg E window."""
    limit = EXTENDED_DAYS_WITH_PROVISIONAL_CREDIT if provisional_credit else ERROR_RESOLUTION_BUSINESS_DAYS
    return business_days_elapsed <= limit
