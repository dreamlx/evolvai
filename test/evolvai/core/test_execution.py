"""Tests for ToolExecutionEngine integration with PlanValidator."""

from unittest.mock import Mock, patch

from evolvai.core.execution import ToolExecutionEngine
from evolvai.core.execution_plan import (
    ExecutionPlan,
    RollbackStrategy,
    RollbackStrategyType,
)
from evolvai.core.validation_result import ValidationResult


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
