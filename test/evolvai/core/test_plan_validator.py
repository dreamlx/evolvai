"""Tests for PlanValidator."""

import pytest

from evolvai.core.execution_plan import (
    ExecutionLimits,
    ExecutionPlan,
    RollbackStrategy,
    RollbackStrategyType,
    ValidationConfig,
)
from evolvai.core.plan_validator import PlanValidator
from evolvai.core.validation_result import ViolationSeverity


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


class TestPlanValidatorRollback:
    """Test rollback strategy validation (business rules only)."""

    def test_git_revert_strategy_valid(self):
        """Test git_revert strategy is valid."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT, commands=[]),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True

    def test_manual_strategy_with_commands_valid(self):
        """Test manual strategy with commands is valid."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.MANUAL,
                commands=["git revert HEAD", "git push"],
            ),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True

    def test_file_backup_strategy_valid(self):
        """Test file_backup strategy is valid."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.FILE_BACKUP),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True

    def test_suspicious_commands_warning_only(self):
        """Test suspicious commands generate INFO-level warnings (not errors)."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.MANUAL,
                commands=["rm -rf /"],  # Suspicious but not blocked
            ),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        # Still valid (not blocked), but with info-level violation
        assert result.is_valid is True
        assert len(result.violations) >= 1
        assert any("suspicious" in v.message.lower() or "destructive" in v.message.lower() for v in result.violations)
        # Should be INFO or WARNING, not ERROR
        assert all(v.severity != ViolationSeverity.ERROR for v in result.violations)


class TestPlanValidatorValidationConfig:
    """Test validation config consistency."""

    def test_empty_validation_config_valid(self):
        """Test empty pre_conditions and expected_outcomes is valid."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            validation=ValidationConfig(pre_conditions=[], expected_outcomes=[]),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True

    def test_non_empty_strings_valid(self):
        """Test non-empty strings in validation config are valid."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            validation=ValidationConfig(
                pre_conditions=["git status clean", "tests passing"],
                expected_outcomes=["file created", "no errors"],
            ),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True

    def test_empty_string_in_pre_conditions_invalid(self):
        """Test empty strings in pre_conditions are invalid."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            validation=ValidationConfig(
                pre_conditions=["git status clean", ""],  # Empty string
                expected_outcomes=["file created"],
            ),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is False
        assert result.error_count == 1
        assert any("empty string" in v.message.lower() for v in result.violations)

    def test_duplicate_conditions_warning(self):
        """Test duplicate conditions generate warnings."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            validation=ValidationConfig(
                pre_conditions=["tests pass", "tests pass"],  # Duplicate
                expected_outcomes=["success"],
            ),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True  # Valid but with warning
        assert result.warning_count > 0
        assert any("duplicate" in v.message.lower() for v in result.violations)
