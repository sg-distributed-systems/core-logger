"""
Exception serialization utilities for structured logging.

Converts exceptions into dictionaries suitable for JSON logging, including
exception type, message, and optionally the full stack trace. Used by
Logger.exception() to produce machine-readable error logs.
"""
from __future__ import annotations

import traceback
from typing import Any, Dict


def serialize_exception(exc: BaseException) -> Dict[str, Any]:
    return {
        "exception_type": exc.__class__.__name__,
        "exception_message": str(exc),
    }


def serialize_exception_with_trace(exc: BaseException) -> Dict[str, Any]:
    return {
        **serialize_exception(exc),
        "stacktrace": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    }
