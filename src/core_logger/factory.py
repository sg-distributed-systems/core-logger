"""
Logger factory for creating service-bound logger instances.

Provides get_logger() as the primary entry point for obtaining a Logger
configured for a specific service name and routing tier.
"""
from __future__ import annotations

from .handlers import LogHandler
from .logger import Logger
from .tiers import Tier


def get_logger(
    service_name: str,
    tier: Tier | str | None = None,
    log_handlers: list[LogHandler] | None = None,
) -> Logger:
    """Create a Logger bound to service_name.

    tier overrides LOG_SERVICE_TIER (default: infrastructure).
    log_handlers replaces tier defaults, including when empty. Each handler
    is wrapped for failure isolation and stdout fallback.
    """
    return Logger(service_name, tier=tier, handlers=log_handlers)
