"""Validation result data structures.

Provides data classes for representing ExecutionPlan validation results.
"""

from dataclasses import dataclass, field
from enum import Enum


class ViolationSeverity(str, Enum):
    """Severity levels for validation violations."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationViolation:
    """A single validation violation.

    Attributes:
        field: The field that failed validation
        message: Human-readable error message
        severity: Violation severity level
        current_value: The actual value that failed (optional)
        expected_range: The expected value or range (optional)

    """

    field: str
    message: str
    severity: ViolationSeverity
    current_value: object = None
    expected_range: str | None = None

    def __str__(self) -> str:
        """String representation for logging."""
        return f"[{self.severity.value.upper()}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    """Result of ExecutionPlan validation.

    Attributes:
        is_valid: Whether the plan passed validation
        violations: List of validation violations

    """

    is_valid: bool
    violations: list[ValidationViolation] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Count of error-level violations."""
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level violations."""
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.WARNING)

    def get_violations_by_severity(self, severity: ViolationSeverity) -> list[ValidationViolation]:
        """Get violations filtered by severity level."""
        return [v for v in self.violations if v.severity == severity]

    @property
    def summary(self) -> str:
        """User-facing summary of validation result."""
        if self.is_valid:
            return "Validation passed"

        error_msg = f"{self.error_count} error{'s' if self.error_count != 1 else ''}"
        warning_msg = f"{self.warning_count} warning{'s' if self.warning_count != 1 else ''}"

        summary_parts = []
        if self.error_count > 0:
            summary_parts.append(error_msg)
        if self.warning_count > 0:
            summary_parts.append(warning_msg)

        summary = f"Validation failed: {', '.join(summary_parts)}\n"

        # Add first few violation messages
        for violation in self.violations[:5]:
            summary += f"  - {violation}\n"

        if len(self.violations) > 5:
            summary += f"  ... and {len(self.violations) - 5} more\n"

        return summary

    def to_dict(self) -> dict:
        """Convert to dictionary for audit log."""
        return {
            "is_valid": self.is_valid,
            "violations": [
                {
                    "field": v.field,
                    "message": v.message,
                    "severity": v.severity.value,
                    "current_value": v.current_value,
                    "expected_range": v.expected_range,
                }
                for v in self.violations
            ],
        }
