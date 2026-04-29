"""Error Handler module for garage-agent.

This module provides error classification, retry strategies, and logging
capabilities for handling errors during session execution.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from garage_os.types import ErrorCategory


@dataclass
class RetryStrategy:
    """Retry strategy configuration based on error category."""

    max_retries: int = 0
    delays: list[float] = field(default_factory=list)
    pause: bool = False
    notify_user: bool = False
    stop: bool = False
    log_fatal: bool = False
    continue_execution: bool = False
    log: bool = False


@dataclass
class ErrorLogEntry:
    """Log entry for an error that occurred during execution."""

    error_id: str
    error_type: str
    message: str
    category: ErrorCategory
    strategy: RetryStrategy
    session_id: str | None
    context: dict[str, Any] | None
    timestamp: datetime


class ErrorHandler:
    """Error classification, retry strategy, and logging."""

    MAX_RETRIES = 3
    RETRY_DELAYS = [1.0, 2.0, 4.0]  # exponential backoff in seconds

    @staticmethod
    def classify_error(error: Exception) -> ErrorCategory:
        """Classify error into category.

        Categories:
        - OSError/ConnectionError/TimeoutError → RETRYABLE
        - PermissionError/FileNotFoundError → USER_INTERVENTION
        - ValueError/json.JSONDecodeError/UnicodeDecodeError → FATAL (data corruption)
        - Other known non-critical exceptions → IGNORABLE

        Args:
            error: The exception to classify

        Returns:
            ErrorCategory: The category of the error
        """
        error_type = type(error)
        error_name = error_type.__name__

        # RETRYABLE errors
        if error_type in (OSError, ConnectionError, TimeoutError):
            return ErrorCategory.RETRYABLE

        # USER_INTERVENTION errors
        if error_type in (PermissionError, FileNotFoundError):
            return ErrorCategory.USER_INTERVENTION

        # FATAL errors (data corruption)
        # Check for JSON decode error
        if error_name == "JSONDecodeError":
            return ErrorCategory.FATAL

        # Check for Unicode decode error
        if error_name == "UnicodeDecodeError":
            return ErrorCategory.FATAL

        # Other ValueErrors could be ignorable, but we'll treat as fatal by default
        if error_type == ValueError:
            return ErrorCategory.FATAL

        # IGNORABLE errors
        return ErrorCategory.IGNORABLE

    @staticmethod
    def get_retry_strategy(category: ErrorCategory) -> RetryStrategy:
        """Get retry strategy based on error category.

        Args:
            category: The error category

        Returns:
            RetryStrategy: The retry strategy for this category
        """
        if category == ErrorCategory.RETRYABLE:
            return RetryStrategy(
                max_retries=ErrorHandler.MAX_RETRIES,
                delays=ErrorHandler.RETRY_DELAYS,
            )
        elif category == ErrorCategory.USER_INTERVENTION:
            return RetryStrategy(
                pause=True,
                notify_user=True,
            )
        elif category == ErrorCategory.FATAL:
            return RetryStrategy(
                stop=True,
                log_fatal=True,
            )
        else:  # IGNORABLE
            return RetryStrategy(
                continue_execution=True,
                log=True,
            )

    @staticmethod
    def log_error(
        error: Exception,
        category: ErrorCategory,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ErrorLogEntry:
        """Log an error and return the log entry.

        Args:
            error: The exception that occurred
            category: The category of the error
            session_id: Optional session identifier
            context: Optional context information

        Returns:
            ErrorLogEntry: The log entry for this error
        """
        strategy = ErrorHandler.get_retry_strategy(category)

        return ErrorLogEntry(
            error_id=str(uuid.uuid4()),
            error_type=type(error).__name__,
            message=str(error),
            category=category,
            strategy=strategy,
            session_id=session_id,
            context=context,
            timestamp=datetime.now(),
        )

    @staticmethod
    def execute_with_retry(
        operation: Callable,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[Any, ErrorLogEntry | None]:
        """Execute an operation with retry logic based on error classification.

        Args:
            operation: Callable to execute
            session_id: Optional session identifier
            context: Optional context information

        Returns:
            Tuple of (result, error_entry). error_entry is None if operation succeeds.
        """
        last_error = None
        attempt = 0

        while attempt <= ErrorHandler.MAX_RETRIES:
            try:
                result = operation()
                return result, None
            except Exception as e:
                last_error = e
                category = ErrorHandler.classify_error(e)

                # Only retry RETRYABLE errors
                if category != ErrorCategory.RETRYABLE:
                    entry = ErrorHandler.log_error(e, category, session_id, context)
                    return None, entry

                # Check if we've exhausted retries
                if attempt >= ErrorHandler.MAX_RETRIES:
                    # Upgrade to FATAL and log
                    fatal_entry = ErrorHandler.log_error(
                        e, ErrorCategory.FATAL, session_id, context
                    )
                    return None, fatal_entry

                # Wait before retrying
                delay_index = min(attempt, len(ErrorHandler.RETRY_DELAYS) - 1)
                delay = ErrorHandler.RETRY_DELAYS[delay_index]
                time.sleep(delay)
                attempt += 1

        # Should never reach here, but handle edge case
        return None, ErrorHandler.log_error(
            last_error, ErrorCategory.FATAL, session_id, context
        )
