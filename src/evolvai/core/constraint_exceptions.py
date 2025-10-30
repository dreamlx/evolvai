"""Runtime constraint violation exceptions for Epic-001 Story 1.3.

These exceptions provide specific error types for different constraint violations,
enabling precise error handling and audit logging.
"""

from __future__ import annotations

from typing import Any


class FileLimitExceededError(Exception):
    """Raised when file processing exceeds execution plan limits."""

    def __init__(self, message: str, files_processed: int = 0, max_files: int = 0):
        super().__init__(message)
        self.message = message
        self.files_processed = files_processed
        self.max_files = max_files
        self.constraint_type = "file_limit"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for audit logging."""
        return {
            "constraint_type": self.constraint_type,
            "files_processed": self.files_processed,
            "max_files": self.max_files,
            "message": self.message,
        }


class ChangeLimitExceededError(Exception):
    """Raised when change count exceeds execution plan limits."""

    def __init__(self, message: str, changes_made: int = 0, max_changes: int = 0):
        super().__init__(message)
        self.message = message
        self.changes_made = changes_made
        self.max_changes = max_changes
        self.constraint_type = "change_limit"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for audit logging."""
        return {
            "constraint_type": self.constraint_type,
            "changes_made": self.changes_made,
            "max_changes": self.max_changes,
            "message": self.message,
        }


class TimeoutError(Exception):
    """Raised when execution exceeds timeout limit."""

    def __init__(self, message: str, elapsed_time: float = 0.0, timeout_seconds: float = 0.0):
        super().__init__(message)
        self.message = message
        self.elapsed_time = elapsed_time
        self.timeout_seconds = timeout_seconds
        self.constraint_type = "timeout"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for audit logging."""
        return {
            "constraint_type": self.constraint_type,
            "elapsed_time": self.elapsed_time,
            "timeout_seconds": self.timeout_seconds,
            "message": self.message,
        }
