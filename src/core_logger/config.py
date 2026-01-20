"""
Logger configuration loaded from environment variables.

Provides LoggerConfig dataclass with settings for log level, timestamp inclusion,
correlation ID key names, and output formatting. All settings have sensible defaults
and can be overridden via environment variables (see load_logger_config()).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LoggerConfig:
    level: str = "INFO"
    include_timestamp: bool = True
    timestamp_key: str = "timestamp"
    correlation_id_key: str = "correlation_id"
    include_pid: bool = False
    pretty: bool = False


def load_logger_config() -> LoggerConfig:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    include_timestamp = os.getenv("LOG_INCLUDE_TIMESTAMP", "true").lower() in ("1", "true", "yes", "on")
    include_pid = os.getenv("LOG_INCLUDE_PID", "false").lower() in ("1", "true", "yes", "on")
    pretty = os.getenv("LOG_PRETTY", "false").lower() in ("1", "true", "yes", "on")
    correlation_id_key = os.getenv("LOG_CORRELATION_ID_KEY", "correlation_id")
    timestamp_key = os.getenv("LOG_TIMESTAMP_KEY", "timestamp")

    return LoggerConfig(
        level=level,
        include_timestamp=include_timestamp,
        include_pid=include_pid,
        pretty=pretty,
        correlation_id_key=correlation_id_key,
        timestamp_key=timestamp_key,
    )
