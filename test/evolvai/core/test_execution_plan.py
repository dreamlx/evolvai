"""Tests for ExecutionPlan schema and related data structures."""

import pytest
from pydantic import ValidationError

# Test imports - will fail initially (Red phase)
from evolvai.core.execution_plan import (
    ExecutionLimits,
    ExecutionPlan,
    RollbackStrategy,
    RollbackStrategyType,
    ValidationConfig,
)


class TestRollbackStrategyType:
    """Test RollbackStrategyType enum."""

    def test_enum_values_exist(self):
        """Test that all required rollback strategy types exist."""
        assert RollbackStrategyType.GIT_REVERT == "git_revert"
        assert RollbackStrategyType.FILE_BACKUP == "file_backup"
        assert RollbackStrategyType.MANUAL == "manual"

    def test_enum_is_string_enum(self):
        """Test that enum values are strings."""
        assert isinstance(RollbackStrategyType.GIT_REVERT.value, str)


class TestExecutionLimits:
    """Test ExecutionLimits data class."""

    def test_default_values(self):
        """Test ExecutionLimits default values."""
        limits = ExecutionLimits()

        assert limits.max_files == 10
        assert limits.max_changes == 50
        assert limits.timeout_seconds == 30

    def test_custom_values(self):
        """Test ExecutionLimits with custom values."""
        limits = ExecutionLimits(max_files=20, max_changes=100, timeout_seconds=60)

        assert limits.max_files == 20
        assert limits.max_changes == 100
        assert limits.timeout_seconds == 60

    def test_max_files_boundary_validation(self):
        """Test max_files must be between 1 and 100."""
        # Valid boundaries
        ExecutionLimits(max_files=1)  # Min
        ExecutionLimits(max_files=100)  # Max

        # Invalid: 0
        with pytest.raises(ValidationError) as exc_info:
            ExecutionLimits(max_files=0)
        assert "max_files" in str(exc_info.value)

        # Invalid: 101
        with pytest.raises(ValidationError) as exc_info:
            ExecutionLimits(max_files=101)
        assert "max_files" in str(exc_info.value)

    def test_max_changes_boundary_validation(self):
        """Test max_changes must be between 1 and 1000."""
        # Valid boundaries
        ExecutionLimits(max_changes=1)
        ExecutionLimits(max_changes=1000)

        # Invalid: 0
        with pytest.raises(ValidationError):
            ExecutionLimits(max_changes=0)

        # Invalid: 1001
        with pytest.raises(ValidationError):
            ExecutionLimits(max_changes=1001)

    def test_timeout_boundary_validation(self):
        """Test timeout_seconds must be between 1 and 300."""
        # Valid boundaries
        ExecutionLimits(timeout_seconds=1)
        ExecutionLimits(timeout_seconds=300)

        # Invalid: 0
        with pytest.raises(ValidationError):
            ExecutionLimits(timeout_seconds=0)

        # Invalid: 301
        with pytest.raises(ValidationError):
            ExecutionLimits(timeout_seconds=301)

    def test_negative_values_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            ExecutionLimits(max_files=-1)

        with pytest.raises(ValidationError):
            ExecutionLimits(timeout_seconds=-1)


class TestValidationConfig:
    """Test ValidationConfig data class."""

    def test_default_values(self):
        """Test ValidationConfig default values."""
        config = ValidationConfig()

        assert config.pre_conditions == []
        assert config.expected_outcomes == []

    def test_custom_values(self):
        """Test ValidationConfig with custom values."""
        config = ValidationConfig(
            pre_conditions=["git status clean", "tests pass"],
            expected_outcomes=["file created", "no errors"],
        )

        assert config.pre_conditions == ["git status clean", "tests pass"]
        assert config.expected_outcomes == ["file created", "no errors"]

    def test_empty_lists_allowed(self):
        """Test that empty lists are valid."""
        config = ValidationConfig(pre_conditions=[], expected_outcomes=[])

        assert config.pre_conditions == []
        assert config.expected_outcomes == []


class TestRollbackStrategy:
    """Test RollbackStrategy data class."""

    def test_required_strategy_field(self):
        """Test that strategy field is required."""
        with pytest.raises(ValidationError) as exc_info:
            RollbackStrategy()
        assert "strategy" in str(exc_info.value)

    def test_default_commands_list(self):
        """Test that commands defaults to empty list."""
        strategy = RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT)

        assert strategy.commands == []

    def test_custom_commands(self):
        """Test RollbackStrategy with custom commands."""
        strategy = RollbackStrategy(
            strategy=RollbackStrategyType.MANUAL,
            commands=["git revert HEAD", "git push"],
        )

        assert strategy.strategy == RollbackStrategyType.MANUAL
        assert strategy.commands == ["git revert HEAD", "git push"]

    def test_manual_strategy_requires_commands(self):
        """Test that manual strategy requires commands."""
        # Manual without commands should fail validation
        with pytest.raises(ValidationError) as exc_info:
            RollbackStrategy(strategy=RollbackStrategyType.MANUAL, commands=[])
        assert "Manual rollback" in str(exc_info.value) or "commands" in str(exc_info.value)

    def test_git_revert_allows_empty_commands(self):
        """Test that git_revert strategy allows empty commands."""
        strategy = RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT, commands=[])

        assert strategy.strategy == RollbackStrategyType.GIT_REVERT
        assert strategy.commands == []


class TestExecutionPlan:
    """Test ExecutionPlan main class."""

    def test_rollback_field_required(self):
        """Test that rollback field is required."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionPlan()
        assert "rollback" in str(exc_info.value)

    def test_default_values(self):
        """Test ExecutionPlan default values."""
        plan = ExecutionPlan(rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT))

        assert plan.dry_run is True
        assert plan.batch is False
        assert isinstance(plan.validation, ValidationConfig)
        assert isinstance(plan.limits, ExecutionLimits)
        assert plan.limits.max_files == 10

    def test_custom_values(self):
        """Test ExecutionPlan with custom values."""
        plan = ExecutionPlan(
            dry_run=False,
            validation=ValidationConfig(pre_conditions=["test1"]),
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.FILE_BACKUP,
                commands=["backup.sh"],
            ),
            limits=ExecutionLimits(max_files=5),
            batch=True,
        )

        assert plan.dry_run is False
        assert plan.batch is True
        assert plan.validation.pre_conditions == ["test1"]
        assert plan.rollback.strategy == RollbackStrategyType.FILE_BACKUP
        assert plan.limits.max_files == 5

    def test_json_serialization(self):
        """Test ExecutionPlan JSON serialization."""
        plan = ExecutionPlan(
            dry_run=False,
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.GIT_REVERT,
                commands=["git revert HEAD"],
            ),
            limits=ExecutionLimits(max_files=5, timeout_seconds=60),
        )

        # Serialize to JSON
        json_data = plan.model_dump_json()
        assert isinstance(json_data, str)

        # Deserialize back
        restored_plan = ExecutionPlan.model_validate_json(json_data)
        assert restored_plan == plan
        assert restored_plan.limits.max_files == 5
        assert restored_plan.rollback.commands == ["git revert HEAD"]

    def test_model_dump_dict(self):
        """Test ExecutionPlan dict conversion."""
        plan = ExecutionPlan(
            dry_run=False,
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
        )

        data = plan.model_dump()
        assert isinstance(data, dict)
        assert data["dry_run"] is False
        assert data["rollback"]["strategy"] == "git_revert"


# Performance tests (Story requirement)
class TestPerformanceRequirements:
    """Test performance requirements for schema operations."""

    def test_instantiation_performance(self):
        """Test that schema instantiation is fast (<1ms)."""
        import time

        start = time.perf_counter()
        for _ in range(100):
            ExecutionPlan(rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT))
        end = time.perf_counter()

        avg_time = (end - start) / 100
        # Should be much faster than 1ms
        assert avg_time < 0.001, f"Average instantiation time: {avg_time:.6f}s"

    def test_validation_performance(self):
        """Test that field validation is fast (<10ms)."""
        import time

        start = time.perf_counter()
        for _ in range(100):
            plan = ExecutionPlan(rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT))
            # Trigger validation by accessing fields
            _ = plan.dry_run
            _ = plan.limits.max_files
        end = time.perf_counter()

        avg_time = (end - start) / 100
        # Should be much faster than 10ms
        assert avg_time < 0.01, f"Average validation time: {avg_time:.6f}s"
