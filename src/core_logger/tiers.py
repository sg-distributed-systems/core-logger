"""Service tiers and their environment-based resolution."""
from __future__ import annotations

import os
from enum import Enum


class Tier(str, Enum):
    COMPLIANCE = "compliance"
    BUSINESS = "business"
    INFRASTRUCTURE = "infrastructure"


def resolve_tier(explicit=None) -> Tier:
    """Resolve an explicit tier, the environment tier, or infrastructure."""
    if explicit is not None:
        if isinstance(explicit, Tier):
            return explicit
        if isinstance(explicit, str):
            return Tier(explicit.lower())
        raise ValueError("Tier must be a Tier or string")

    try:
        return Tier(os.getenv("LOG_SERVICE_TIER", "infrastructure").lower())
    except ValueError:
        return Tier.INFRASTRUCTURE
