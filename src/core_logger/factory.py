from core_logger.logger import Logger


def get_logger(service_name: str) -> Logger:
    """
    Create and return a Logger instance bound to a service name.
    """
    return Logger(service_name)
