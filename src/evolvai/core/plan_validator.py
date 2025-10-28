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

        # Validate rollback strategy business rules
        violations.extend(self._validate_rollback_strategy(plan))

        # Validate validation config consistency
        violations.extend(self._validate_validation_config(plan))

        # Future cycles will add validation methods here:
        # violations.extend(self._validate_cross_field_rules(plan))

        # Determine if valid (no ERROR-level violations)
        is_valid = all(v.severity != ViolationSeverity.ERROR for v in violations)

        return ValidationResult(is_valid=is_valid, violations=violations)

    def _validate_rollback_strategy(self, plan: ExecutionPlan) -> list[ValidationViolation]:
        """Validate rollback strategy business rules.

        Note: Pydantic already validates that MANUAL requires commands.
        This adds optional safety warnings (INFO level).

        Args:
            plan: The ExecutionPlan to validate

        Returns:
            List of ValidationViolations (INFO level warnings only)

        """
        violations = []

        # Optional: Check for suspicious commands (INFO-level warnings only)
        # This is a "friendly reminder", not a security guarantee
        # Real security should be implemented through sandboxing/permissions
        suspicious_patterns = ["rm -rf /", "format c:", "del /f /s /q"]

        for cmd in plan.rollback.commands:
            for pattern in suspicious_patterns:
                if pattern in cmd.lower():
                    violations.append(
                        ValidationViolation(
                            field="rollback.commands",
                            message=f"Potentially destructive command: '{cmd}' contains '{pattern}'. "
                            f"This is a reminder, not a security check.",
                            severity=ViolationSeverity.INFO,  # INFO, not ERROR
                            current_value=cmd,
                        )
                    )

        return violations

    def _validate_validation_config(self, plan: ExecutionPlan) -> list[ValidationViolation]:
        """Validate validation config consistency.

        Checks for:
        - Empty strings in pre_conditions or expected_outcomes (ERROR)
        - Duplicate conditions (WARNING)

        Args:
            plan: The ExecutionPlan to validate

        Returns:
            List of ValidationViolations

        """
        violations = []

        # Check for empty strings in pre_conditions
        for i, condition in enumerate(plan.validation.pre_conditions):
            if not condition.strip():
                violations.append(
                    ValidationViolation(
                        field=f"validation.pre_conditions[{i}]",
                        message="Empty string in pre_conditions is not allowed",
                        severity=ViolationSeverity.ERROR,
                        current_value=condition,
                    )
                )

        # Check for empty strings in expected_outcomes
        for i, outcome in enumerate(plan.validation.expected_outcomes):
            if not outcome.strip():
                violations.append(
                    ValidationViolation(
                        field=f"validation.expected_outcomes[{i}]",
                        message="Empty string in expected_outcomes is not allowed",
                        severity=ViolationSeverity.ERROR,
                        current_value=outcome,
                    )
                )

        # Check for duplicates (warning only)
        if len(plan.validation.pre_conditions) != len(set(plan.validation.pre_conditions)):
            violations.append(
                ValidationViolation(
                    field="validation.pre_conditions",
                    message="Duplicate pre_conditions detected",
                    severity=ViolationSeverity.WARNING,
                )
            )

        if len(plan.validation.expected_outcomes) != len(set(plan.validation.expected_outcomes)):
            violations.append(
                ValidationViolation(
                    field="validation.expected_outcomes",
                    message="Duplicate expected_outcomes detected",
                    severity=ViolationSeverity.WARNING,
                )
            )

        return violations
