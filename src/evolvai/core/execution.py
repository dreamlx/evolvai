"""Core execution engine components."""
import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from sensai.util import logging

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
    """Complete execution context with audit trail."""

    # Tool information
    tool_name: str
    kwargs: dict[str, Any]
    execution_plan: Any | None = None

    # Timing
    start_time: float = 0.0
    end_time: float = 0.0
    phase: ExecutionPhase = ExecutionPhase.PRE_VALIDATION

    # Constraint tracking (Epic-001)
    constraint_violations: list[str] | None = None
    should_batch: bool = False

    # Execution results
    result: str | None = None
    error: Exception | None = None

    # Token tracking (TPST core)
    estimated_tokens: int = 0
    actual_tokens: int = 0

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
                raise RuntimeError(
                    f"Error: Tool '{tool.get_name()}' is not active. "
                    f"Active tools: {active_tools}"
                )
        except Exception as e:
            raise RuntimeError(
                f"RuntimeError while checking if tool {tool.get_name()} is active: {e}"
            )

        # Check 2: Active project requirement
        if not isinstance(tool, ToolMarkerDoesNotRequireActiveProject):
            if self._agent._active_project is None:
                project_names = self._agent.serena_config.project_names
                raise RuntimeError(
                    "Error: No active project. Ask the user to provide the project path "
                    f"or to select a project from this list of known projects: {project_names}"
                )

            # Check 3: Language server status
            if (
                self._agent.is_using_language_server()
                and not self._agent.is_language_server_running()
            ):
                log.info("Language server is not running. Starting it ...")
                self._agent.reset_language_server()

    def _pre_execution_with_constraints(
        self, tool: "Tool", ctx: ExecutionContext
    ) -> None:
        """Phase 2: Pre-execution with constraints (Epic-001)."""
        # Placeholder for Epic-001 integration
        pass

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
                log.error(
                    f"Language server terminated while executing tool ({e}). "
                    "Restarting the language server and retrying ..."
                )
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
        """Phase 4: Post-execution cleanup."""
        # Will implement in Cycle 5
        pass
