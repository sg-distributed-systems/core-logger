"""
Structured JSON logger with level filtering and exception handling.

Provides the Logger class that outputs JSON log entries to stdout with
configurable log levels, pretty printing, and automatic exception serialization.
"""

from __future__ import annotations

import json

from .formatter import format_log
from .config import load_logger_config
from .exceptions import serialize_exception_with_trace

_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}


class Logger:
    """A simple structured logger bound to a service name."""

    def __init__(self, service_name: str) -> None:
        self._service_name = service_name
        self._cfg = load_logger_config()

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

        if self._cfg.pretty:
            print(json.dumps(entry, indent=2, sort_keys=True))
        else:
            print(json.dumps(entry))

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
