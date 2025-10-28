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


class TestPlanValidatorCrossField:
    """Test cross-field validation rules."""

    def test_batch_mode_with_sufficient_limits(self):
        """Test batch=True requires sufficient limits."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            limits=ExecutionLimits(max_files=10, max_changes=50),
            batch=True,
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True

    def test_batch_mode_with_low_limits_warning(self):
        """Test batch=True with low limits generates warning."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            limits=ExecutionLimits(max_files=1, max_changes=1),
            batch=True,
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True  # Valid but with warning
        assert result.warning_count > 0
        assert any("batch mode" in v.message.lower() and "low" in v.message.lower() for v in result.violations)

    def test_dry_run_false_requires_rollback(self):
        """Test dry_run=False requires explicit rollback strategy."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            dry_run=False,
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True  # Valid with git_revert

    def test_dry_run_true_allows_any_rollback(self):
        """Test dry_run=True allows any rollback strategy."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.MANUAL, commands=["echo test"]),
            dry_run=True,
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True

    def test_high_limits_with_short_timeout_warning(self):
        """Test high limits with short timeout generates warning."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            limits=ExecutionLimits(max_files=100, max_changes=1000, timeout_seconds=5),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True  # Valid but with warning
        assert result.warning_count > 0
        assert any("timeout" in v.message.lower() for v in result.violations)


class TestPlanValidatorPerformance:
    """Test PlanValidator performance."""

    def test_validation_performance(self):
        """Test that validation completes in <1ms."""
        import time

        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            limits=ExecutionLimits(max_files=50, max_changes=100, timeout_seconds=60),
            validation=ValidationConfig(
                pre_conditions=["test1", "test2", "test3"],
                expected_outcomes=["outcome1", "outcome2"],
            ),
            batch=True,
        )

        validator = PlanValidator()

        # Run 100 iterations to get average
        start = time.perf_counter()
        for _ in range(100):
            _ = validator.validate(plan)
        end = time.perf_counter()

        avg_time = (end - start) / 100
        assert avg_time < 0.001  # <1ms per validation

    def test_complex_plan_validation_performance(self):
        """Test performance with complex plan."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.MANUAL,
                commands=[f"command_{i}" for i in range(10)],
            ),
            limits=ExecutionLimits(max_files=100, max_changes=1000, timeout_seconds=300),
            validation=ValidationConfig(
                pre_conditions=[f"condition_{i}" for i in range(20)],
                expected_outcomes=[f"outcome_{i}" for i in range(20)],
            ),
            batch=True,
        )

        validator = PlanValidator()

        import time

        start = time.perf_counter()
        _ = validator.validate(plan)
        end = time.perf_counter()

        duration = end - start
        assert duration < 0.001  # Still <1ms even for complex plans


class TestPlanValidatorIntegration:
    """Integration tests with ExecutionPlan."""

    def test_typical_safe_plan(self):
        """Test validation of typical safe execution plan."""
        plan = ExecutionPlan(
            dry_run=True,
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            limits=ExecutionLimits(max_files=10, max_changes=50, timeout_seconds=30),
            validation=ValidationConfig(
                pre_conditions=["tests passing", "git status clean"],
                expected_outcomes=["changes applied", "no errors"],
            ),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_production_plan_with_rollback(self):
        """Test validation of production execution plan."""
        plan = ExecutionPlan(
            dry_run=False,
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.MANUAL,
                commands=["git revert HEAD", "git push origin main --force-with-lease"],
            ),
            limits=ExecutionLimits(max_files=5, max_changes=20, timeout_seconds=60),
            validation=ValidationConfig(
                pre_conditions=["tests pass", "code review approved", "CI green"],
                expected_outcomes=["deployment success", "health checks pass"],
            ),
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is True
        # May have warnings about force push, but should be valid

    def test_invalid_plan_comprehensive(self):
        """Test validation of plan with multiple violations."""
        plan = ExecutionPlan(
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.MANUAL,
                commands=["rm -rf /", "format c:"],  # Suspicious
            ),
            limits=ExecutionLimits(max_files=100, max_changes=1000, timeout_seconds=5),  # Short timeout
            validation=ValidationConfig(
                pre_conditions=["test", "", "test"],  # Empty + duplicate
                expected_outcomes=["outcome"],
            ),
            batch=True,  # High limits with batch is ok
        )

        validator = PlanValidator()
        result = validator.validate(plan)

        assert result.is_valid is False  # Has errors (empty string)
        assert result.error_count >= 1  # At least one error
        assert result.warning_count >= 2  # At least two warnings (suspicious + timeout)
