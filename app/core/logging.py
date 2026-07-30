import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for Silukman logs."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add custom fields if they exist
        custom_fields = [
            "run_id", "experiment_id", "image_id", "backend",
            "preset", "duration", "error_category"
        ]

        for field in custom_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logger(name: str, level: int = logging.INFO, as_json: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if as_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger.addHandler(handler)
    return logger


# Global instance for app
logger = setup_logger("silukman")
