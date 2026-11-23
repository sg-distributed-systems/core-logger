"""Standard-library log destinations and failure-isolated routing."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Protocol
import urllib.request

from .config import LoggerConfig
from .tiers import Tier


class LogHandler(Protocol):
    def emit(self, entry: dict) -> None:
        """Emit a structured log entry."""
        ...


class StdoutHandler:
    def __init__(self, pretty: bool = False) -> None:
        self.pretty = pretty

    def emit(self, entry: dict) -> None:
        if self.pretty:
            print(json.dumps(entry, indent=2, sort_keys=True))
        else:
            print(json.dumps(entry))


class FileHandler:
    def __init__(self, path) -> None:
        self.path = Path(path)

    def emit(self, entry: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry) + "\n")


class HttpHandler:
    def __init__(self, url: str, timeout: float = 2.0) -> None:
        self.url = url
        self.timeout = timeout

    def emit(self, entry: dict) -> None:
        request = urllib.request.Request(
            self.url,
            data=json.dumps(entry).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout):
            pass


class SafeHandler:
    def __init__(self, inner: LogHandler) -> None:
        self.inner = inner

    def emit(self, entry: dict) -> None:
        try:
            self.inner.emit(entry)
        except BaseException as error:
            # Even a broken stdout or an unserializable entry must not interrupt
            # the caller or prevent delivery to the remaining destinations.
            try:
                fallback = dict(entry)
                fallback["log_handler_error"] = f"{type(self.inner).__name__}: {error}"
                print(json.dumps(fallback, default=str))
            except BaseException:
                pass


def build_handlers(spec: str, pretty: bool) -> list:
    """Parse comma-separated destinations, warning about unknown entries."""
    handlers = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        if item == "stdout":
            handlers.append(StdoutHandler(pretty))
        elif item.startswith("file:") and item[5:]:
            handlers.append(FileHandler(item[5:]))
        elif item.startswith(("http://", "https://")):
            handlers.append(HttpHandler(item))
        elif item.startswith("http:") and item[5:]:
            handlers.append(HttpHandler(item[5:]))
        else:
            print(f"Warning: unknown log handler {item!r}; skipping", file=sys.stderr)
    return handlers


def default_handlers(tier: Tier, cfg: LoggerConfig) -> list:
    """Build safe tier destinations using the cached environment settings."""
    spec = getattr(cfg, f"handlers_{tier.value}")
    if spec is not None:
        handlers = build_handlers(spec, cfg.pretty)
    else:
        handlers = [StdoutHandler(cfg.pretty)]
        if tier == Tier.COMPLIANCE:
            handlers.append(FileHandler(cfg.compliance_file))
        elif tier == Tier.BUSINESS and cfg.business_http_url:
            handlers.append(HttpHandler(cfg.business_http_url))
    return [SafeHandler(handler) for handler in handlers]
