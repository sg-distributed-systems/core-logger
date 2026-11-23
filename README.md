# core-logger

A shared structured logging library used by all microservices. Provides a simple `Logger` class with `debug`, `info`, `warning`, and `error` methods that output JSON to stdout.

## Why this repo exists

Centralized logging ensures consistent log formats across all services, making it easier to aggregate, search, and analyze logs in production.

## Core Components

### `get_logger(service_name: str, tier=None, log_handlers=None) -> Logger`
Factory function that creates a `Logger` instance bound to a service name. Each log entry includes the service name and tier for filtering and routing. An explicit tier overrides `LOG_SERVICE_TIER`; `log_handlers` replaces the default destinations (an empty list disables output).

### `Logger`
Provides `debug()`, `info()`, `warning()`, and `error()` methods. Each method accepts a message string and optional keyword arguments that become structured fields in the log output.

### `format_log()`
Formats log entries as JSON dictionaries with timestamp, level, service, message, and any additional fields passed by the caller.

### `set_correlation_id(value: str)`
Sets the correlation ID for the current execution context. The ID will be automatically included in all subsequent log entries.

### `get_correlation_id() -> Optional[str]`
Returns the current correlation ID, or None if not set.

### `clear_correlation_id()`
Clears the correlation ID from the current context.

### `LoggerConfig`
Dataclass holding logger configuration loaded from environment variables. Supports settings for log level, timestamp inclusion, correlation ID key, and pretty printing.

### `load_logger_config() -> LoggerConfig`
Loads logger configuration from environment variables with sensible defaults, without caching. Logging uses `get_logger_config()` from `core_logger.config`, which caches configuration. After changing environment settings at runtime, call `reload_logger_config()` from that module and create new logger instances to refresh their settings and destinations.

### `serialize_exception(exc: BaseException) -> Dict`
Converts an exception to a dictionary with `exception_type` and `exception_message`.

### `serialize_exception_with_trace(exc: BaseException) -> Dict`
Converts an exception to a dictionary including the full stack trace.

## Tier-based routing

```python
from core_logger import Tier, FileHandler, get_logger

logger = get_logger("payments", tier=Tier.COMPLIANCE)
logger.info("payment approved", payment_id="123", token="hidden")

# Custom destinations replace the tier defaults and remain failure-isolated.
custom = get_logger("worker", log_handlers=[FileHandler("./logs/worker.jsonl")])
```

Every entry includes a `tier` field. Select a tier with a `Tier` member or a
case-insensitive string. Precedence is an explicit `tier` argument, then the
case-insensitive `LOG_SERVICE_TIER` environment variable, then `infrastructure`.
Invalid environment values fall back to infrastructure; invalid explicit values
raise `ValueError`.

Default destinations:

| Tier | Destinations |
| --- | --- |
| `infrastructure` | stdout only (the backward-compatible default) |
| `business` | stdout, plus HTTP POST if `LOG_BUSINESS_HTTP_URL` is set |
| `compliance` | stdout and an append-only JSON-lines file at `LOG_COMPLIANCE_FILE` (default `/var/log/compliance/audit.log`) |

Override a tier's destinations with `LOG_HANDLERS_COMPLIANCE`,
`LOG_HANDLERS_BUSINESS`, or `LOG_HANDLERS_INFRASTRUCTURE`. Each takes a
comma-separated list containing:

- `stdout` — JSON stdout output; respects `LOG_PRETTY`.
- `file:<path>` — append one JSON line per entry, creating parent directories.
- `http:<url>` — POST JSON using a two-second timeout. Bare `http://` and
  `https://` URLs also work.

For example:

```sh
export LOG_SERVICE_TIER=business
export LOG_HANDLERS_BUSINESS='stdout,file:./logs/business.jsonl,http:https://logs.example.com/ingest'
```

An explicitly empty handler spec disables that tier's output. Unknown entries
are skipped with a warning on stderr. All destinations, including custom
handlers implementing `emit(entry: dict) -> None`, are wrapped in `SafeHandler`:
if a destination fails, the entry falls back to stdout with a `log_handler_error`
field, and other destinations are still attempted. Ensure the compliance file
location is writable in your deployment. File and HTTP handlers always use
compact JSON, regardless of `LOG_PRETTY`.

**Behavior change for compliance-tier logs:** before any destination receives an
entry, top-level fields named `password`, `token`, `secret`, `authorization`, or
`api_key` (case-insensitive) are replaced with `***redacted***`. This also applies
to custom handlers and failure fallback output. Redaction is not recursive and
does not sanitize message text. Other tiers retain their existing behavior.
With no new environment variables, `get_logger("x")` still writes the same JSON
to stdout, with only the additional `tier` field.

## Tests

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
