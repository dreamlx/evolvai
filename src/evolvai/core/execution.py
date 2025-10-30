"""Core execution engine components."""

import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from sensai.util import logging

from evolvai.core.exceptions import ConstraintViolationError
from evolvai.core.plan_validator import PlanValidator

if TYPE_CHECKING:
    from serena.agent import SerenaAgent
    from serena.tools.tools_base import Tool

log = logging.getLogger(__name__)


class ExecutionPhase(Enum):
    """Execution phases for tool execution."""

    PRE_VALIDATION = "pre_validation"
    PRE_EXECUTION = "pre_execution"
    EXECUTION = "execution"
    POST_EXECUTION = "post_execution"


@dataclass
class ExecutionContext:
    """Execution context for tool execution tracking."""

    # Tool information
    tool_name: str
    kwargs: dict[str, Any]
    execution_plan: Any | None = None

    # Timing
    start_time: float = 0.0
    end_time: float = 0.0
    phase: ExecutionPhase = ExecutionPhase.PRE_VALIDATION

    # Constraint tracking (Epic-001)
    constraint_violations: list[dict[str, Any]] | None = None
    should_batch: bool = False

    # Runtime tracking (Story 1.3)
    files_processed: int = 0
    changes_made: int = 0

    # Execution results
    result: str | None = None
    error: Exception | None = None

    # Token tracking (TPST core)
    estimated_tokens: int = 0
    actual_tokens: int = 0

    def check_limits(self) -> None:
        """Check runtime constraints against execution plan limits.

        Raises:
            Exception: When any constraint is violated

        """
        # Skip validation if no execution_plan provided (backward compatibility)
        if self.execution_plan is None:
            return

        # Skip validation if no limits defined (graceful handling)
        if self.execution_plan.limits is None:
            return

        limits = self.execution_plan.limits

        # Check file count constraint
        if hasattr(limits, "max_files") and self.files_processed > limits.max_files:
            raise Exception(f"File limit exceeded: {self.files_processed} > {limits.max_files}")

        # Check change count constraint
        if hasattr(limits, "max_changes") and self.changes_made > limits.max_changes:
            raise Exception(f"Change limit exceeded: {self.changes_made} > {limits.max_changes}")

        # Check timeout constraint
        if hasattr(limits, "timeout_seconds"):
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            if elapsed_time > limits.timeout_seconds:
                raise Exception(f"Execution timeout: {elapsed_time:.1f}s > {limits.timeout_seconds}s")

    def to_audit_record(self) -> dict[str, Any]:
        """Convert to audit record for TPST analysis."""
        return {
            "tool": self.tool_name,
            "phase": self.phase.value,
            "duration": self.end_time - self.start_time,
            "tokens": self.actual_tokens,
            "success": self.error is None,
            "constraints": self.constraint_violations or [],
            "batched": self.should_batch,
        }


class ToolExecutionEngine:
    """Unified tool execution engine.

    Provides:
    1. 4-phase execution flow
    2. Complete audit trail
    3. Epic-001 constraint integration point
    4. TPST analysis support
    """

    def __init__(self, agent: "SerenaAgent", enable_constraints: bool = False):
        """Initialize execution engine.

        :param agent: SerenaAgent instance
        :param enable_constraints: Enable Epic-001 constraints
        """
        self._agent = agent
        self._constraints_enabled = enable_constraints
        self._audit_log: list[dict[str, Any]] = []

    def execute(self, tool: "Tool", **kwargs: Any) -> str:
        """Execute tool with full 4-phase flow.

        :param tool: Tool to execute
        :param kwargs: Tool arguments
        :return: Tool execution result
        """
        # Extract execution_plan if present
        execution_plan = kwargs.pop("execution_plan", None)

        # Create execution context
        ctx = ExecutionContext(
            tool_name=tool.get_name(),
            kwargs=kwargs.copy(),
            execution_plan=execution_plan,
            start_time=time.time(),
        )

        try:
            # Phase 1: Pre-validation
            ctx.phase = ExecutionPhase.PRE_VALIDATION
            self._pre_validation(tool, ctx)

            # Phase 2: Pre-execution (Epic-001)
            if self._constraints_enabled:
                ctx.phase = ExecutionPhase.PRE_EXECUTION
                self._pre_execution_with_constraints(tool, ctx)

            # Phase 3: Execution
            ctx.phase = ExecutionPhase.EXECUTION
            ctx.result = self._execute_tool(tool, ctx)

            # Phase 4: Post-execution
            ctx.phase = ExecutionPhase.POST_EXECUTION
            self._post_execution(tool, ctx)

            return ctx.result

        except ConstraintViolationError as e:
            # Record error and violations in context before re-raising
            ctx.error = e
            # Violations are already in ctx.constraint_violations from _pre_execution_with_constraints
            # Re-raise constraint violations for special handling by caller
            raise
        except Exception as e:
            ctx.error = e
            log.error(f"Error executing tool {tool.get_name()}: {e}", exc_info=e)
            return f"Error executing tool: {e}"

        finally:
            ctx.end_time = time.time()
            self._audit_log.append(ctx.to_audit_record())

    def _pre_validation(self, tool: "Tool", ctx: ExecutionContext) -> None:
        """Phase 1: Pre-validation checks.

        Checks:
        1. Tool activation status
        2. Active project requirement
        3. Language server status
        """
        # Import here to avoid circular dependency
        from serena.tools.tools_base import ToolMarkerDoesNotRequireActiveProject

        # Check 1: Tool activation
        try:
            if not tool.is_active():
                active_tools = self._agent.get_active_tool_names()
                raise RuntimeError(f"Error: Tool '{tool.get_name()}' is not active. Active tools: {active_tools}")
        except Exception as e:
            raise RuntimeError(f"RuntimeError while checking if tool {tool.get_name()} is active: {e}")

        # Check 2: Active project requirement
        if not isinstance(tool, ToolMarkerDoesNotRequireActiveProject):
            if self._agent._active_project is None:
                project_names = self._agent.serena_config.project_names
                raise RuntimeError(
                    "Error: No active project. Ask the user to provide the project path "
                    f"or to select a project from this list of known projects: {project_names}"
                )

            # Check 3: Language server status
            if self._agent.is_using_language_server() and not self._agent.is_language_server_running():
                log.info("Language server is not running. Starting it ...")
                self._agent.reset_language_server()

    def _pre_execution_with_constraints(self, tool: "Tool", ctx: ExecutionContext) -> None:
        """Phase 2: Pre-execution with constraints (Epic-001).

        Validates ExecutionPlan if provided, otherwise skips validation
        for backward compatibility.

        Args:
            tool: The tool to execute
            ctx: Execution context containing execution_plan (if any)

        Raises:
            ConstraintViolationError: If execution_plan validation fails

        """
        # Skip validation if no execution_plan provided (backward compatibility)
        if ctx.execution_plan is None:
            return

        # Validate execution plan
        validator = PlanValidator()
        result = validator.validate(ctx.execution_plan)

        # If validation failed, raise error
        if not result.is_valid:
            ctx.constraint_violations = [
                {
                    "field": violation.field,
                    "message": violation.message,
                    "severity": violation.severity.value,
                }
                for violation in result.violations
            ]
            raise ConstraintViolationError(result)

    def _execute_tool(self, tool: "Tool", ctx: ExecutionContext) -> str:
        """Phase 3: Actual tool execution.

        Features:
        - LSP exception handling with retry
        - Token estimation (basic)
        """
        from solidlsp.ls_exceptions import SolidLSPException

        apply_fn = tool.get_apply_fn()

        # Basic token estimation (improve in future)
        ctx.estimated_tokens = len(str(ctx.kwargs)) // 4  # Rough estimate

        try:
            result = apply_fn(**ctx.kwargs)
        except SolidLSPException as e:
            # Handle LSP termination with retry
            if e.is_language_server_terminated():
                log.error(f"Language server terminated while executing tool ({e}). Restarting the language server and retrying ...")
                self._agent.reset_language_server()
                # Retry execution
                result = apply_fn(**ctx.kwargs)
            else:
                # Re-raise non-terminated LSP exceptions
                raise

        # Rough actual token tracking (improve in future)
        ctx.actual_tokens = len(str(result)) // 4

        return result

    def _post_execution(self, tool: "Tool", ctx: ExecutionContext) -> None:
        """Phase 4: Post-execution cleanup.

        Features:
        - Record tool usage statistics
        - Save LSP cache if available
        """
        # Record tool usage for statistics
        if hasattr(self._agent, "record_tool_usage_if_enabled") and ctx.result is not None:
            self._agent.record_tool_usage_if_enabled(ctx.kwargs, ctx.result, tool)

        # Save language server cache
        if self._agent.language_server is not None:
            try:
                self._agent.language_server.save_cache()
            except Exception as e:
                log.error(f"Error saving language server cache: {e}")

    # Audit Log Interface (Cycle 6)

    def get_audit_log(self, tool_name: str | None = None) -> list[dict[str, Any]]:
        """Get audit log with optional filtering.

        :param tool_name: Optional tool name to filter by
        :return: List of audit records
        """
        if tool_name is None:
            return self._audit_log.copy()
        return [record for record in self._audit_log if record["tool"] == tool_name]

    def clear_audit_log(self) -> None:
        """Clear the audit log."""
        self._audit_log.clear()

    # TPST Analysis Interface (Cycle 7)

    def analyze_tpst(self) -> dict[str, Any]:
        """Analyze TPST (Tokens Per Solved Task) metrics.

        :return: Dictionary with token statistics
        """
        if not self._audit_log:
            return {
                "total_executions": 0,
                "total_tokens": 0,
                "average_tokens": 0,
                "successful_executions": 0,
                "failed_executions": 0,
            }

        total_tokens = sum(record["tokens"] for record in self._audit_log)
        successful = [record for record in self._audit_log if record["success"]]
        failed = [record for record in self._audit_log if not record["success"]]

        return {
            "total_executions": len(self._audit_log),
            "total_tokens": total_tokens,
            "average_tokens": (total_tokens / len(self._audit_log) if self._audit_log else 0),
            "successful_executions": len(successful),
            "failed_executions": len(failed),
            "success_rate": (len(successful) / len(self._audit_log) if self._audit_log else 0),
        }

    def get_slow_tools(self, threshold_seconds: float = 1.0) -> list[dict[str, Any]]:
        """Get tools that exceeded duration threshold.

        :param threshold_seconds: Duration threshold in seconds
        :return: List of slow tool executions
        """
        slow_tools = [record for record in self._audit_log if record["duration"] > threshold_seconds]
        # Sort by duration (slowest first)
        slow_tools.sort(key=lambda x: x["duration"], reverse=True)
        return slow_tools
