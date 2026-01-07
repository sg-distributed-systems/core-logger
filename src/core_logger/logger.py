import json

from core_logger.formatter import format_log


class Logger:
    """A simple structured logger bound to a service name."""

    def __init__(self, service_name: str) -> None:
        self._service_name = service_name

    def _log(self, level: str, msg: str, **fields) -> None:
        entry = format_log(
            level=level,
            service=self._service_name,
            message=msg,
            fields=fields
        )
        print(json.dumps(entry))

    def debug(self, msg: str, **fields) -> None:
        self._log("DEBUG", msg, **fields)

    def info(self, msg: str, **fields) -> None:
        self._log("INFO", msg, **fields)

    def warning(self, msg: str, **fields) -> None:
        self._log("WARNING", msg, **fields)

    def error(self, msg: str, **fields) -> None:
        self._log("ERROR", msg, **fields)
