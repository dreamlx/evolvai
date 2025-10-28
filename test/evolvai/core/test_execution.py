"""Tests for ToolExecutionEngine integration with PlanValidator."""

from unittest.mock import Mock, patch

import pytest

from evolvai.core.exceptions import ConstraintViolationError
from evolvai.core.execution import ToolExecutionEngine
from evolvai.core.execution_plan import (
    ExecutionPlan,
    RollbackStrategy,
    RollbackStrategyType,
    ValidationConfig,
)
from evolvai.core.validation_result import ValidationResult, ValidationViolation, ViolationSeverity


class TestToolExecutionEngineValidation:
    """Test PlanValidator integration with ToolExecutionEngine."""

    def test_validator_called_when_execution_plan_provided(self):
        """Test that PlanValidator is called when execution_plan is provided."""
        # Create a mock agent
        mock_agent = Mock()

        # Create a simple tool
        tool = Mock()
        tool.name = "test_tool"
        tool.apply = Mock(return_value="success")

        # Create an execution plan
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
        )

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock PlanValidator to track if it was called
        with patch("evolvai.core.execution.PlanValidator") as MockValidator:
            mock_validator_instance = MockValidator.return_value
            mock_validator_instance.validate.return_value = ValidationResult(is_valid=True, violations=[])

            # Execute with execution_plan
            engine.execute(tool, execution_plan=plan)

            # Verify validator was instantiated and called
            MockValidator.assert_called_once()
            mock_validator_instance.validate.assert_called_once_with(plan)

    def test_validator_not_called_when_no_execution_plan(self):
        """Test that PlanValidator is not called when execution_plan is None."""
        # Create a mock agent
        mock_agent = Mock()

        # Create a simple tool
        tool = Mock()
        tool.name = "test_tool"
        tool.apply = Mock(return_value="success")

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock PlanValidator to track if it was called
        with patch("evolvai.core.execution.PlanValidator") as MockValidator:
            # Execute without execution_plan
            engine.execute(tool)

            # Verify validator was NOT called
            MockValidator.assert_not_called()

    def test_valid_plan_passes_validation(self):
        """Test that valid ExecutionPlan passes validation and tool executes successfully."""
        # Create a mock agent
        mock_agent = Mock()
        mock_agent._active_project = Mock()  # Has active project
        mock_agent.is_using_language_server = Mock(return_value=False)

        # Create a simple tool with all required methods
        tool = Mock()
        tool.get_name = Mock(return_value="test_tool")
        tool.is_active = Mock(return_value=True)
        apply_fn = Mock(return_value="test_result")
        tool.get_apply_fn = Mock(return_value=apply_fn)

        # Create a valid execution plan
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
        )

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock PlanValidator to return valid result
        with patch("evolvai.core.execution.PlanValidator") as MockValidator:
            mock_validator_instance = MockValidator.return_value
            mock_validator_instance.validate.return_value = ValidationResult(is_valid=True, violations=[])

            # Execute with valid execution_plan
            result = engine.execute(tool, execution_plan=plan)

            # Verify tool was executed
            apply_fn.assert_called_once()
            # Verify result was returned
            assert result == "test_result"

    def test_valid_plan_recorded_in_audit_log(self):
        """Test that successful validation with valid plan is recorded in audit log."""
        # Create a mock agent
        mock_agent = Mock()
        mock_agent._active_project = Mock()  # Has active project
        mock_agent.is_using_language_server = Mock(return_value=False)

        # Create a simple tool with all required methods
        tool = Mock()
        tool.get_name = Mock(return_value="test_tool")
        tool.is_active = Mock(return_value=True)
        apply_fn = Mock(return_value="test_result")
        tool.get_apply_fn = Mock(return_value=apply_fn)

        # Create a valid execution plan
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
        )

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock PlanValidator to return valid result
        with patch("evolvai.core.execution.PlanValidator") as MockValidator:
            mock_validator_instance = MockValidator.return_value
            mock_validator_instance.validate.return_value = ValidationResult(is_valid=True, violations=[])

            # Execute with valid execution_plan
            engine.execute(tool, execution_plan=plan)

            # Verify audit log contains the execution
            audit_log = engine.get_audit_log()
            assert len(audit_log) == 1
            assert audit_log[0]["tool"] == "test_tool"
            assert audit_log[0]["success"] is True
            assert audit_log[0]["constraints"] == []  # No violations

    def test_invalid_plan_raises_exception(self):
        """Test that invalid ExecutionPlan raises ConstraintViolationError."""
        # Create a mock agent
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        # Create a simple tool
        tool = Mock()
        tool.get_name = Mock(return_value="test_tool")
        tool.is_active = Mock(return_value=True)
        apply_fn = Mock(return_value="test_result")
        tool.get_apply_fn = Mock(return_value=apply_fn)

        # Create an invalid execution plan (empty string in pre_conditions)
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            validation=ValidationConfig(
                pre_conditions=["git status clean", ""],  # Empty string invalid
                expected_outcomes=["file created"],
            ),
        )

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock PlanValidator to return invalid result
        with patch("evolvai.core.execution.PlanValidator") as MockValidator:
            mock_validator_instance = MockValidator.return_value
            violation = ValidationViolation(
                field="validation.pre_conditions",
                message="Empty strings are not allowed in pre_conditions",
                severity=ViolationSeverity.ERROR,
            )
            mock_validator_instance.validate.return_value = ValidationResult(is_valid=False, violations=[violation])

            # Execute with invalid execution_plan should raise ConstraintViolationError
            with pytest.raises(ConstraintViolationError):
                engine.execute(tool, execution_plan=plan)

    def test_exception_contains_validation_result(self):
        """Test that ConstraintViolationError contains ValidationResult with violations."""
        # Create a mock agent
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        # Create a simple tool
        tool = Mock()
        tool.get_name = Mock(return_value="test_tool")
        tool.is_active = Mock(return_value=True)
        apply_fn = Mock(return_value="test_result")
        tool.get_apply_fn = Mock(return_value=apply_fn)

        # Create an invalid execution plan
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            validation=ValidationConfig(
                pre_conditions=[""],  # Empty string invalid
                expected_outcomes=["file created"],
            ),
        )

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock PlanValidator to return invalid result with specific violation
        with patch("evolvai.core.execution.PlanValidator") as MockValidator:
            mock_validator_instance = MockValidator.return_value
            violation = ValidationViolation(
                field="validation.pre_conditions",
                message="Empty strings are not allowed",
                severity=ViolationSeverity.ERROR,
            )
            validation_result = ValidationResult(is_valid=False, violations=[violation])
            mock_validator_instance.validate.return_value = validation_result

            # Execute and catch exception
            with pytest.raises(ConstraintViolationError) as exc_info:
                engine.execute(tool, execution_plan=plan)

            # Verify exception contains validation result
            exception = exc_info.value
            assert exception.validation_result is not None
            assert exception.validation_result.is_valid is False
            assert len(exception.validation_result.violations) == 1
            assert exception.validation_result.violations[0].field == "validation.pre_conditions"
            assert exception.validation_result.violations[0].severity == ViolationSeverity.ERROR

    def test_invalid_plan_prevents_tool_execution(self):
        """Test that invalid ExecutionPlan prevents tool from executing."""
        # Create a mock agent
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        # Create a simple tool
        tool = Mock()
        tool.get_name = Mock(return_value="test_tool")
        tool.is_active = Mock(return_value=True)
        apply_fn = Mock(return_value="test_result")
        tool.get_apply_fn = Mock(return_value=apply_fn)

        # Create an invalid execution plan
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            validation=ValidationConfig(
                pre_conditions=[""],
                expected_outcomes=["file created"],
            ),
        )

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock PlanValidator to return invalid result
        with patch("evolvai.core.execution.PlanValidator") as MockValidator:
            mock_validator_instance = MockValidator.return_value
            violation = ValidationViolation(
                field="validation.pre_conditions",
                message="Empty strings are not allowed",
                severity=ViolationSeverity.ERROR,
            )
            mock_validator_instance.validate.return_value = ValidationResult(is_valid=False, violations=[violation])

            # Execute with invalid plan
            with pytest.raises(ConstraintViolationError):
                engine.execute(tool, execution_plan=plan)

            # Verify tool was NOT executed
            apply_fn.assert_not_called()

    def test_constraint_violations_recorded_in_audit_log(self):
        """Test that constraint violations are recorded in audit log with details."""
        # Create a mock agent
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        # Create a simple tool
        tool = Mock()
        tool.get_name = Mock(return_value="test_tool")
        tool.is_active = Mock(return_value=True)
        apply_fn = Mock(return_value="test_result")
        tool.get_apply_fn = Mock(return_value=apply_fn)

        # Create an invalid execution plan
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            validation=ValidationConfig(
                pre_conditions=[""],  # Empty string invalid
                expected_outcomes=["file created"],
            ),
        )

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock PlanValidator to return invalid result with specific violations
        with patch("evolvai.core.execution.PlanValidator") as MockValidator:
            mock_validator_instance = MockValidator.return_value
            violation1 = ValidationViolation(
                field="validation.pre_conditions",
                message="Empty strings not allowed",
                severity=ViolationSeverity.ERROR,
            )
            violation2 = ValidationViolation(
                field="validation.expected_outcomes",
                message="Missing timestamp",
                severity=ViolationSeverity.WARNING,
            )
            mock_validator_instance.validate.return_value = ValidationResult(is_valid=False, violations=[violation1, violation2])

            # Execute with invalid plan (will raise exception)
            try:
                engine.execute(tool, execution_plan=plan)
            except ConstraintViolationError:
                pass  # Expected

            # Verify audit log contains the violations
            audit_log = engine.get_audit_log()
            assert len(audit_log) == 1
            assert audit_log[0]["tool"] == "test_tool"
            assert audit_log[0]["success"] is False
            # Verify violations are recorded
            assert len(audit_log[0]["constraints"]) == 2
            assert audit_log[0]["constraints"][0]["field"] == "validation.pre_conditions"
            assert audit_log[0]["constraints"][0]["severity"] == "error"
            assert audit_log[0]["constraints"][1]["field"] == "validation.expected_outcomes"
            assert audit_log[0]["constraints"][1]["severity"] == "warning"

    def test_failed_validation_marked_as_failure(self):
        """Test that failed validation execution is marked as success=False in audit log."""
        # Create a mock agent
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        # Create a simple tool
        tool = Mock()
        tool.get_name = Mock(return_value="test_tool")
        tool.is_active = Mock(return_value=True)
        apply_fn = Mock(return_value="test_result")
        tool.get_apply_fn = Mock(return_value=apply_fn)

        # Create an invalid execution plan
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
            validation=ValidationConfig(pre_conditions=[""]),
        )

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock PlanValidator to return invalid result
        with patch("evolvai.core.execution.PlanValidator") as MockValidator:
            mock_validator_instance = MockValidator.return_value
            violation = ValidationViolation(
                field="validation.pre_conditions",
                message="Empty string",
                severity=ViolationSeverity.ERROR,
            )
            mock_validator_instance.validate.return_value = ValidationResult(is_valid=False, violations=[violation])

            # Execute with invalid plan
            try:
                engine.execute(tool, execution_plan=plan)
            except ConstraintViolationError:
                pass  # Expected

            # Verify audit log marks this as failure
            audit_log = engine.get_audit_log()
            assert len(audit_log) == 1
            assert audit_log[0]["success"] is False
            # Verify violation is recorded
            assert len(audit_log[0]["constraints"]) == 1
