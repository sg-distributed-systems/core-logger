import datetime


def format_log(
    *,
    level: str,
    service: str,
    message: str,
    fields: dict
) -> dict:
    """
    Return a JSON-serializable dict representing a log entry.
    """
    return {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "level": level,
        "service": service,
        "message": message,
        **fields
    }
