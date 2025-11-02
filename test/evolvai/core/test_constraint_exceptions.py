"""Tests for runtime constraint violation exceptions."""

from evolvai.core.constraint_exceptions import (
    ChangeLimitExceededError,
    FileLimitExceededError,
    TimeoutError,
)


class TestFileLimitExceededError:
    """Test FileLimitExceededError exception."""

    def test_file_limit_exceeded_error_creation(self):
        """Test FileLimitExceededError can be created with basic message."""
        error = FileLimitExceededError("File limit exceeded")

        assert str(error) == "File limit exceeded"
        assert error.message == "File limit exceeded"
        assert error.constraint_type == "file_limit"
        assert error.files_processed == 0
        assert error.max_files == 0

    def test_file_limit_exceeded_error_with_details(self):
        """Test FileLimitExceededError with detailed parameters."""
        error = FileLimitExceededError("File limit exceeded: 10 > 5", files_processed=10, max_files=5)

        assert str(error) == "File limit exceeded: 10 > 5"
        assert error.message == "File limit exceeded: 10 > 5"
        assert error.constraint_type == "file_limit"
        assert error.files_processed == 10
        assert error.max_files == 5

    def test_file_limit_exceeded_error_to_dict(self):
        """Test FileLimitExceededError to_dict method."""
        error = FileLimitExceededError("File limit exceeded: 10 > 5", files_processed=10, max_files=5)

        result = error.to_dict()
        expected = {
            "constraint_type": "file_limit",
            "files_processed": 10,
            "max_files": 5,
            "message": "File limit exceeded: 10 > 5",
        }

        assert result == expected

    def test_file_limit_exceeded_error_inheritance(self):
        """Test FileLimitExceededError inherits from Exception."""
        error = FileLimitExceededError("test message")

        assert isinstance(error, Exception)
        assert isinstance(error, FileLimitExceededError)

    def test_file_limit_exceeded_error_attributes_readonly(self):
        """Test that FileLimitExceededError attributes are properly set."""
        error = FileLimitExceededError("test message", files_processed=15, max_files=3)

        # Attributes should be accessible and have correct values
        assert hasattr(error, "message")
        assert hasattr(error, "files_processed")
        assert hasattr(error, "max_files")
        assert hasattr(error, "constraint_type")
        assert hasattr(error, "to_dict")

        # Values should match what was set
        assert error.message == "test message"
        assert error.files_processed == 15
        assert error.max_files == 3
        assert error.constraint_type == "file_limit"


class TestChangeLimitExceededError:
    """Test ChangeLimitExceededError exception."""

    def test_change_limit_exceeded_error_creation(self):
        """Test ChangeLimitExceededError can be created with basic message."""
        error = ChangeLimitExceededError("Change limit exceeded")

        assert str(error) == "Change limit exceeded"
        assert error.message == "Change limit exceeded"
        assert error.constraint_type == "change_limit"
        assert error.changes_made == 0
        assert error.max_changes == 0

    def test_change_limit_exceeded_error_with_details(self):
        """Test ChangeLimitExceededError with detailed parameters."""
        error = ChangeLimitExceededError("Change limit exceeded: 6 > 3", changes_made=6, max_changes=3)

        assert str(error) == "Change limit exceeded: 6 > 3"
        assert error.message == "Change limit exceeded: 6 > 3"
        assert error.constraint_type == "change_limit"
        assert error.changes_made == 6
        assert error.max_changes == 3

    def test_change_limit_exceeded_error_to_dict(self):
        """Test ChangeLimitExceededError to_dict method."""
        error = ChangeLimitExceededError("Change limit exceeded: 6 > 3", changes_made=6, max_changes=3)

        result = error.to_dict()
        expected = {
            "constraint_type": "change_limit",
            "changes_made": 6,
            "max_changes": 3,
            "message": "Change limit exceeded: 6 > 3",
        }

        assert result == expected


class TestTimeoutError:
    """Test TimeoutError exception."""

    def test_timeout_error_creation(self):
        """Test TimeoutError can be created with basic message."""
        error = TimeoutError("Execution timeout")

        assert str(error) == "Execution timeout"
        assert error.message == "Execution timeout"
        assert error.constraint_type == "timeout"
        assert error.elapsed_time == 0.0
        assert error.timeout_seconds == 0.0

    def test_timeout_error_with_details(self):
        """Test TimeoutError with detailed parameters."""
        error = TimeoutError("Execution timeout: 5.2s > 2.0s", elapsed_time=5.2, timeout_seconds=2.0)

        assert str(error) == "Execution timeout: 5.2s > 2.0s"
        assert error.message == "Execution timeout: 5.2s > 2.0s"
        assert error.constraint_type == "timeout"
        assert error.elapsed_time == 5.2
        assert error.timeout_seconds == 2.0

    def test_timeout_error_to_dict(self):
        """Test TimeoutError to_dict method."""
        error = TimeoutError("Execution timeout: 5.2s > 2.0s", elapsed_time=5.2, timeout_seconds=2.0)

        result = error.to_dict()
        expected = {
            "constraint_type": "timeout",
            "elapsed_time": 5.2,
            "timeout_seconds": 2.0,
            "message": "Execution timeout: 5.2s > 2.0s",
        }

        assert result == expected
