"""ExecutionPlan validation logic.

Provides comprehensive validation for ExecutionPlan instances.

Important: This validator focuses on BUSINESS RULES that Pydantic cannot validate.
It does NOT duplicate Pydantic's boundary checking (max_files, timeout_seconds, etc.)
to avoid redundant overhead and support TPST optimization goals.
"""

from evolvai.core.execution_plan import ExecutionPlan
from evolvai.core.validation_result import ValidationResult, ValidationViolation, ViolationSeverity


class PlanValidator:
    """Validator for ExecutionPlan instances.

    Performs business rule validation for ExecutionPlan fields:
    - Rollback strategy consistency (beyond Pydantic checks)
    - Validation config consistency (semantic checks)
    - Cross-field validation rules (business logic)

    Does NOT validate:
    - Limits boundaries (already validated by Pydantic Field constraints)
    - Required fields (already validated by Pydantic)
    - Type checking (already validated by Pydantic)
    """

    def validate(self, plan: ExecutionPlan) -> ValidationResult:
        """Validate an ExecutionPlan.

        Args:
            plan: The ExecutionPlan to validate

        Returns:
            ValidationResult with violations (if any)

        """
        violations: list[ValidationViolation] = []

        # Future cycles will add validation methods here:
        # violations.extend(self._validate_rollback_strategy(plan))
        # violations.extend(self._validate_validation_config(plan))
        # violations.extend(self._validate_cross_field_rules(plan))

        # Determine if valid (no ERROR-level violations)
        is_valid = all(v.severity != ViolationSeverity.ERROR for v in violations)

        return ValidationResult(is_valid=is_valid, violations=violations)
