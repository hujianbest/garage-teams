"""Tests for ErrorHandler module."""

import pytest
from datetime import datetime

from garage_os.runtime.error_handler import ErrorHandler, RetryStrategy, ErrorLogEntry
from garage_os.types import ErrorCategory


class TestErrorClassification:
    """Test error classification logic."""

    def test_classify_connection_error(self):
        """ConnectionError should be classified as RETRYABLE."""
        error = ConnectionError("Connection failed")
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.RETRYABLE

    def test_classify_timeout_error(self):
        """TimeoutError should be classified as RETRYABLE."""
        error = TimeoutError("Operation timed out")
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.RETRYABLE

    def test_classify_os_error(self):
        """OSError should be classified as RETRYABLE."""
        error = OSError("System error")
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.RETRYABLE

    def test_classify_permission_error(self):
        """PermissionError should be classified as USER_INTERVENTION."""
        error = PermissionError("Access denied")
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.USER_INTERVENTION

    def test_classify_file_not_found(self):
        """FileNotFoundError should be classified as USER_INTERVENTION."""
        error = FileNotFoundError("File not found")
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.USER_INTERVENTION

    def test_classify_value_error(self):
        """ValueError should be classified as FATAL."""
        error = ValueError("Invalid value")
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.FATAL

    def test_classify_json_decode_error(self):
        """JSONDecodeError should be classified as FATAL."""
        # JSONDecodeError is a subclass of ValueError with 'JSON' in the name
        import json

        error = json.JSONDecodeError("Expecting value", "test", 0)
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.FATAL

    def test_classify_unicode_error(self):
        """UnicodeDecodeError should be classified as FATAL."""
        error = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        category = ErrorHandler.classify_error(error)
        assert category == ErrorCategory.FATAL


class TestRetryStrategy:
    """Test retry strategy generation."""

    def test_retry_strategy_retryable(self):
        """RETRYABLE category should return strategy with max_retries=3 and delays=[1,2,4]."""
        strategy = ErrorHandler.get_retry_strategy(ErrorCategory.RETRYABLE)
        assert strategy.max_retries == 3
        assert strategy.delays == [1.0, 2.0, 4.0]
        assert strategy.pause is False
        assert strategy.notify_user is False
        assert strategy.stop is False

    def test_retry_strategy_user_intervention(self):
        """USER_INTERVENTION category should return strategy with pause=True."""
        strategy = ErrorHandler.get_retry_strategy(ErrorCategory.USER_INTERVENTION)
        assert strategy.pause is True
        assert strategy.notify_user is True
        assert strategy.max_retries == 0
        assert strategy.delays == []

    def test_retry_strategy_fatal(self):
        """FATAL category should return strategy with stop=True."""
        strategy = ErrorHandler.get_retry_strategy(ErrorCategory.FATAL)
        assert strategy.stop is True
        assert strategy.log_fatal is True
        assert strategy.max_retries == 0

    def test_retry_strategy_ignorable(self):
        """IGNORABLE category should return strategy with continue_execution=True."""
        strategy = ErrorHandler.get_retry_strategy(ErrorCategory.IGNORABLE)
        assert strategy.continue_execution is True
        assert strategy.log is True
        assert strategy.max_retries == 0


class TestErrorLogging:
    """Test error logging functionality."""

    def test_log_error(self):
        """Error logging should create ErrorLogEntry with correct fields."""
        error = ValueError("Test error")
        category = ErrorCategory.FATAL
        session_id = "test-session-123"

        entry = ErrorHandler.log_error(error, category, session_id)

        assert isinstance(entry, ErrorLogEntry)
        assert entry.error_type == "ValueError"
        assert entry.message == "Test error"
        assert entry.category == ErrorCategory.FATAL
        assert entry.session_id == "test-session-123"
        assert entry.context is None
        assert isinstance(entry.timestamp, datetime)
        assert isinstance(entry.error_id, str)
        assert len(entry.error_id) > 0

    def test_log_error_with_context(self):
        """Error logging with context should record context information."""
        error = RuntimeError("Runtime failure")
        category = ErrorCategory.RETRYABLE
        session_id = "test-session-456"
        context = {"node_id": "node-1", "attempt": 2}

        entry = ErrorHandler.log_error(error, category, session_id, context)

        assert entry.context == context
        assert entry.context["node_id"] == "node-1"
        assert entry.context["attempt"] == 2

    def test_log_error_generates_unique_ids(self):
        """Each error log entry should have a unique error_id."""
        error = Exception("Test error")
        category = ErrorCategory.IGNORABLE

        entry1 = ErrorHandler.log_error(error, category)
        entry2 = ErrorHandler.log_error(error, category)

        assert entry1.error_id != entry2.error_id

    def test_log_error_strategy_matches_category(self):
        """Error log entry should have strategy matching its category."""
        error = ConnectionError("Connection failed")
        category = ErrorCategory.RETRYABLE

        entry = ErrorHandler.log_error(error, category)

        assert entry.strategy.max_retries == 3
        assert entry.strategy.delays == [1.0, 2.0, 4.0]
