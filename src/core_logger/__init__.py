"""
Core logger package for structured JSON logging across microservices.

Exports get_logger() for creating service-bound loggers, and correlation ID
management functions for request tracing across service boundaries.
"""
from .factory import get_logger
from .context import set_correlation_id, get_correlation_id, clear_correlation_id

__all__ = [
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "clear_correlation_id",
]
