"""
Structured logging configuration. JSON format when LOG_FORMAT=json.
"""
import logging
import os
import sys

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog with structured logging. JSON output when LOG_FORMAT=json."""
    use_json = os.environ.get("LOG_FORMAT", "").lower() == "json"
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if use_json else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level.upper(), logging.INFO)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
