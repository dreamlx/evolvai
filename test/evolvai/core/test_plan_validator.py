"""Tests for PlanValidator."""

import pytest

from evolvai.core.execution_plan import ExecutionLimits, ExecutionPlan, RollbackStrategy, RollbackStrategyType
from evolvai.core.plan_validator import PlanValidator


class TestPlanValidatorBasics:
    """Test PlanValidator basic functionality."""

    def test_validator_instantiation(self):
        """Test creating a PlanValidator instance."""
        validator = PlanValidator()
        assert validator is not None

    def test_validate_method_exists(self):
        """Test validate method exists and accepts ExecutionPlan."""
        validator = PlanValidator()
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
        )

        result = validator.validate(plan)
        assert result is not None

    def test_valid_simple_plan(self):
        """Test that a simple valid plan passes validation."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            limits=ExecutionLimits(max_files=10, max_changes=50, timeout_seconds=30),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True
        assert len(result.violations) == 0

    def test_pydantic_validates_boundaries(self):
        """Test that Pydantic catches boundary violations (not PlanValidator's job)."""
        from pydantic import ValidationError

        # Pydantic should catch this, not PlanValidator
        with pytest.raises(ValidationError) as exc_info:
            ExecutionPlan(
                rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
                limits=ExecutionLimits(max_files=0),  # Invalid boundary
            )

        # Confirm it's a Pydantic error
        assert "max_files" in str(exc_info.value).lower()

    def test_pydantic_validates_rollback_commands(self):
        """Test that Pydantic catches MANUAL strategy without commands."""
        from pydantic import ValidationError

        # Pydantic should catch this, not PlanValidator
        with pytest.raises(ValidationError) as exc_info:
            ExecutionPlan(
                rollback=RollbackStrategy(
                    strategy=RollbackStrategyType.MANUAL,
                    commands=[],  # Invalid: MANUAL requires commands
                ),
            )

        assert "manual" in str(exc_info.value).lower() or "commands" in str(exc_info.value).lower()
