# core-logger

A shared structured logging library used by all microservices. Provides a simple `Logger` class with `debug`, `info`, `warning`, and `error` methods that output JSON to stdout.

## Why this repo exists

Centralized logging ensures consistent log formats across all services, making it easier to aggregate, search, and analyze logs in production.

## Core Components

### `get_logger(service_name: str) -> Logger`
Factory function that creates a `Logger` instance bound to a service name. Each log entry includes the service name for filtering and routing.

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
Loads logger configuration from environment variables with sensible defaults.

### `serialize_exception(exc: BaseException) -> Dict`
Converts an exception to a dictionary with `exception_type` and `exception_message`.

### `serialize_exception_with_trace(exc: BaseException) -> Dict`
Converts an exception to a dictionary including the full stack trace.
