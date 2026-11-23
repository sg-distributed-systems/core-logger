"""
Structured JSON logger with level filtering and exception handling.

Provides the Logger class that outputs JSON log entries to stdout with
configurable log levels, pretty printing, and automatic exception serialization.
"""

from __future__ import annotations

from .formatter import format_log, redact_sensitive_fields
from .config import get_logger_config
from .handlers import LogHandler, SafeHandler, default_handlers
from .tiers import Tier, resolve_tier
from .exceptions import serialize_exception_with_trace

_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}


class Logger:
    """A simple structured logger bound to a service name."""

    def __init__(
        self,
        service_name: str,
        tier: Tier | str | None = None,
        handlers: list[LogHandler] | None = None,
    ) -> None:
        self._service_name = service_name
        self._cfg = get_logger_config()
        self.tier = resolve_tier(tier)
        self._handlers = (
            default_handlers(self.tier, self._cfg)
            if handlers is None
            else [SafeHandler(handler) for handler in handlers]
        )

    def _log(self, level: str, msg: str, **fields) -> None:
        configured = _LEVELS.get(self._cfg.level, 20)
        current = _LEVELS.get(level, 20)
        if current < configured:
            return

        entry = format_log(
            level=level,
            service=self._service_name,
            message=msg,
            fields=fields
        )

        entry["tier"] = self.tier.value
        if self.tier == Tier.COMPLIANCE:
            entry = redact_sensitive_fields(entry)
        for handler in self._handlers:
            handler.emit(entry)

    def debug(self, msg: str, **fields) -> None:
        self._log("DEBUG", msg, **fields)

    def info(self, msg: str, **fields) -> None:
        self._log("INFO", msg, **fields)

    def warning(self, msg: str, **fields) -> None:
        self._log("WARNING", msg, **fields)

    def error(self, msg: str, **fields) -> None:
        self._log("ERROR", msg, **fields)

    def exception(self, msg: str, exc: BaseException, **fields) -> None:
        error_fields = serialize_exception_with_trace(exc)
        self._log("ERROR", msg, **error_fields, **fields)
