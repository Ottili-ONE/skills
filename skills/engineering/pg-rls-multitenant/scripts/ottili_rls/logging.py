"""Structured logging for the checkers.

Every run gets a run id and every log line is one JSON object with the same
keys, so a log stream can be read by a machine. The run id never enters the
result of a check: the result of a check is a function of its input alone.
"""
from __future__ import annotations

import json
import logging
import sys
import uuid
from typing import Any

LOGGER_NAME = "ottili.rls"
_RUN_ID_KEY = "run_id"
_FIELDS_KEY = "ottili_fields"


def new_run_id() -> str:
    """Return a fresh run id for one checker run."""
    return uuid.uuid4().hex


def configure_logging(level: str = "WARNING") -> logging.Logger:
    """Configure the checker logger to write one JSON object per line."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level.upper())
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
    return logger


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    run_id: str,
    **fields: Any,
) -> None:
    """Write one structured event."""
    logger.log(
        level,
        message,
        extra={_RUN_ID_KEY: run_id, _FIELDS_KEY: fields},
    )


class _JsonFormatter(logging.Formatter):
    """Render a log record as one JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        run_id = getattr(record, _RUN_ID_KEY, None)
        if run_id:
            payload[_RUN_ID_KEY] = run_id
        fields = getattr(record, _FIELDS_KEY, None)
        if isinstance(fields, dict):
            payload.update(fields)
        return json.dumps(payload, sort_keys=True, default=str)
