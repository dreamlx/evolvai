"""Tests for ValidationResult data class."""

from evolvai.core.validation_result import (
    ValidationResult,
    ValidationViolation,
    ViolationSeverity,
)


class TestValidationViolation:
    """Test ValidationViolation data class."""

    def test_violation_creation(self):
        """Test creating a validation violation."""
        violation = ValidationViolation(
            field="limits.max_files",
            message="max_files must be between 1 and 100",
            severity=ViolationSeverity.ERROR,
            current_value=150,
            expected_range="1-100",
        )

        assert violation.field == "limits.max_files"
        assert violation.message == "max_files must be between 1 and 100"
        assert violation.severity == ViolationSeverity.ERROR
        assert violation.current_value == 150
        assert violation.expected_range == "1-100"

    def test_violation_severity_enum(self):
        """Test ViolationSeverity enum values."""
        assert ViolationSeverity.ERROR == "error"
        assert ViolationSeverity.WARNING == "warning"
        assert ViolationSeverity.INFO == "info"

    def test_violation_string_representation(self):
        """Test violation string representation."""
        violation = ValidationViolation(
            field="rollback.commands",
            message="Manual rollback requires commands",
            severity=ViolationSeverity.ERROR,
        )

        str_repr = str(violation)
        assert "rollback.commands" in str_repr
        assert "Manual rollback requires commands" in str_repr
        assert "ERROR" in str_repr


class TestValidationResult:
    """Test ValidationResult data class."""

    def test_valid_result(self):
        """Test creating a valid result with no violations."""
        result = ValidationResult(is_valid=True, violations=[])

        assert result.is_valid is True
        assert result.violations == []
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_invalid_result_with_violations(self):
        """Test creating an invalid result with violations."""
        violations = [
            ValidationViolation(
                field="limits.max_files",
                message="max_files exceeds limit",
                severity=ViolationSeverity.ERROR,
            ),
            ValidationViolation(
                field="limits.timeout_seconds",
                message="timeout too high",
                severity=ViolationSeverity.WARNING,
            ),
        ]

        result = ValidationResult(is_valid=False, violations=violations)

        assert result.is_valid is False
        assert len(result.violations) == 2
        assert result.error_count == 1
        assert result.warning_count == 1

    def test_get_violations_by_severity(self):
        """Test filtering violations by severity."""
        violations = [
            ValidationViolation(field="field1", message="error", severity=ViolationSeverity.ERROR),
            ValidationViolation(field="field2", message="warning", severity=ViolationSeverity.WARNING),
            ValidationViolation(field="field3", message="error2", severity=ViolationSeverity.ERROR),
        ]

        result = ValidationResult(is_valid=False, violations=violations)

        errors = result.get_violations_by_severity(ViolationSeverity.ERROR)
        warnings = result.get_violations_by_severity(ViolationSeverity.WARNING)

        assert len(errors) == 2
        assert len(warnings) == 1

    def test_summary_property(self):
        """Test summary property for user-facing messages."""
        violations = [
            ValidationViolation(
                field="limits.max_files",
                message="max_files exceeds limit",
                severity=ViolationSeverity.ERROR,
            ),
        ]

        result = ValidationResult(is_valid=False, violations=violations)
        summary = result.summary

        assert "1 error" in summary
        assert "max_files exceeds limit" in summary

    def test_to_dict_serialization(self):
        """Test dictionary serialization for audit log."""
        violations = [
            ValidationViolation(
                field="test_field",
                message="test message",
                severity=ViolationSeverity.ERROR,
            ),
        ]

        result = ValidationResult(is_valid=False, violations=violations)
        data = result.to_dict()

        assert data["is_valid"] is False
        assert "violations" in data
        assert len(data["violations"]) == 1
