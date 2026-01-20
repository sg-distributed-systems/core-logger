"""
Correlation ID context management using contextvars.

Provides thread-safe storage and retrieval of correlation IDs that automatically
propagate across async boundaries. Use set_correlation_id() at the start of a
request/job and the ID will be included in all subsequent log entries.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> Optional[str]:
    return _correlation_id.get()


def clear_correlation_id() -> None:
    _correlation_id.set(None)
