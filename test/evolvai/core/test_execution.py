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
