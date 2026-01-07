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
