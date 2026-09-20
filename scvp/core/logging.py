"""
SCVP Structured Logging
=========================
A thin wrapper around the standard library `logging` module that
emits structured (JSON-capable) log records and carries a per-request
`request_id` through nested calls via a contextvar, so a single
agent run's logs can be correlated across core / model / tool calls
in later phases (see Phase 14 -- Observability).
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
import uuid
from typing import Any, Dict

_request_id_var: "contextvars.ContextVar[str]" = contextvars.ContextVar(
    "scvp_request_id", default="-"
)


def new_request_id() -> str:
    """Generate and set a new request id for the current execution context."""
    request_id = uuid.uuid4().hex[:12]
    _request_id_var.set(request_id)
    return request_id


def current_request_id() -> str:
    return _request_id_var.get()


class _RequestIdFilter(logging.Filter):
    """Injects the current request id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id()  # type: ignore[attr-defined]
        return True


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": round(time.time(), 3),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", current_request_id()),
        }
        extra = getattr(record, "scvp_extra", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_configured = False


def configure_logging(level: str = "INFO", json_format: bool = True) -> None:
    """Configure the root `scvp` logger. Safe to call multiple times."""
    global _configured
    root = logging.getLogger("scvp")
    root.setLevel(level.upper())

    if not root.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.addFilter(_RequestIdFilter())
        if json_format:
            handler.setFormatter(_JSONFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s (%(request_id)s): %(message)s"
                )
            )
        root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    if not _configured:
        configure_logging()
    return logging.getLogger(f"scvp.{name}")


def log_extra(**fields: Any) -> Dict[str, Any]:
    """Helper for attaching structured fields: logger.info('msg', extra=log_extra(tool='search'))."""
    return {"scvp_extra": fields}
