"""
Logger configuration loaded from environment variables.

Provides LoggerConfig dataclass with settings for log level, timestamp inclusion,
correlation ID key names, and output formatting. All settings have sensible defaults
and can be overridden via environment variables (see load_logger_config()).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class LoggerConfig:
    level: str = "INFO"
    include_timestamp: bool = True
    timestamp_key: str = "timestamp"
    correlation_id_key: str = "correlation_id"
    include_pid: bool = False
    pretty: bool = False
    service_tier: str = "infrastructure"
    handlers_compliance: str | None = None
    handlers_business: str | None = None
    handlers_infrastructure: str | None = None
    compliance_file: str = "/var/log/compliance/audit.log"
    business_http_url: str | None = None


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
        service_tier=os.getenv("LOG_SERVICE_TIER", "infrastructure"),
        handlers_compliance=os.getenv("LOG_HANDLERS_COMPLIANCE"),
        handlers_business=os.getenv("LOG_HANDLERS_BUSINESS"),
        handlers_infrastructure=os.getenv("LOG_HANDLERS_INFRASTRUCTURE"),
        compliance_file=os.getenv("LOG_COMPLIANCE_FILE", "/var/log/compliance/audit.log"),
        business_http_url=os.getenv("LOG_BUSINESS_HTTP_URL"),
    )


@lru_cache(maxsize=1)
def get_logger_config() -> LoggerConfig:
    """Return the cached environment configuration."""
    return load_logger_config()


def reload_logger_config() -> None:
    """Clear the configuration cache; subsequent calls load the environment."""
    get_logger_config.cache_clear()
