"""
Log entry formatting with configurable fields.

Builds JSON-serializable log entries with level, service, message, optional
correlation ID, timestamp, and process ID based on LoggerConfig settings.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os

from .context import get_correlation_id
from .config import load_logger_config


def format_log(level: str, service: str, message: str, fields: dict) -> dict:
    cfg = load_logger_config()

    entry = {
        "level": level,
        "service": service,
        "message": message,
        **(fields or {}),
    }

    cid = get_correlation_id()
    if cid:
        entry[cfg.correlation_id_key] = cid

    if cfg.include_timestamp:
        entry[cfg.timestamp_key] = datetime.now(timezone.utc).isoformat()

    if cfg.include_pid:
        entry["pid"] = os.getpid()

    return entry


_SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "api_key"}


def redact_sensitive_fields(fields: dict) -> dict:
    """Return a copy of fields with sensitive values masked for safe logging."""
    redacted = {}
    for key, value in (fields or {}).items():
        if key.lower() in _SENSITIVE_KEYS:
            redacted[key] = "***redacted***"
        else:
            redacted[key] = value
    return redacted
