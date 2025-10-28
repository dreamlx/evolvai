"""Custom exceptions for EvolvAI core."""

from evolvai.core.validation_result import ValidationResult


class ConstraintViolationError(Exception):
    """Raised when ExecutionPlan validation fails.

    Attributes:
        validation_result: The ValidationResult containing violations

    """

    def __init__(self, validation_result: ValidationResult):
        """Initialize with validation result.

        Args:
            validation_result: ValidationResult containing violations

        """
        self.validation_result: ValidationResult = validation_result

        # Use ValidationResult's summary for clear error message
        super().__init__(validation_result.summary)
