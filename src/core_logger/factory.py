"""
Logger factory for creating service-bound logger instances.

Provides get_logger() as the primary entry point for obtaining a Logger
configured for a specific service name.
"""
from .logger import Logger


def get_logger(service_name: str) -> Logger:
    """
    Create and return a Logger instance bound to a service name.
    """
    return Logger(service_name)
