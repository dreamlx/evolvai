"""SafeExecTool - MCP-exposed safe command execution tool.

Story 2.3 Day 3: MCP tool integration for safe command execution.
"""

from typing import Optional

from evolvai.core.execution_plan import ExecutionPlan
from evolvai.tools.safe_exec import SafeExecWrapper
from serena.tools.tools_base import Tool


class SafeExecTool(Tool):
    """Safe command execution tool exposed via MCP.

    Provides safe command execution with:
    - Fast-fail precondition checking
    - Timeout management with AI feedback
    - Interactive command detection
    - Output truncation to reduce token waste
    - Optional ExecutionPlan constraint validation
    """

    def apply(
        self,
        command: str,
        timeout: int,
        working_dir: Optional[str] = None,
        execution_plan: Optional[ExecutionPlan] = None,
        confirmed: bool = False,
    ) -> str:
        """Execute a shell command safely with precondition checks and optional confirmation.

        Two-phase execution (Story 2.4):
        1. First call (confirmed=False): Returns confirmation_required=True if risky
        2. Second call (confirmed=True): Executes after user confirmation

        This tool provides safe command execution with multiple layers of validation:
        - Detects absurd commands (rm -rf /, mkfs, fork bombs)
        - Detects interactive commands (vim, ssh, sudo without -n)
        - Detects high-risk operations requiring confirmation (wildcards, current dir deletes)
        - Validates command availability (prevents "command not found")
        - Enforces timeout limits (max 300s)
        - Truncates long output (head 50 + tail 50 lines)
        - Optionally validates against ExecutionPlan constraints

        Args:
            command: The shell command to execute
            timeout: Execution timeout in seconds (1-300s)
            working_dir: Working directory for command execution (defaults to project root)
            execution_plan: Optional ExecutionPlan for constraint validation
            confirmed: Skip confirmation check if True (Story 2.4)

        Returns:
            JSON string with execution results containing:
            - success: bool
            - exit_code: int
            - stdout: str (truncated if > 100 lines)
            - stderr: str (truncated if > 100 lines)
            - duration_ms: float
            - timeout_occurred: bool
            - suggested_timeout: Optional[int] (AI learning feedback)
            - confirmation_required: bool (Story 2.4)
            - confirmation_message: Optional[str] (Story 2.4)
            - risk_level: str (Story 2.4)

        Raises:
            ConstraintViolationError: If preconditions fail (absurd command, missing command, etc.)

        Example:
            >>> safe_exec(command="echo hello", timeout=5)
            '{"success": true, "exit_code": 0, "stdout": "hello\\n", ...}'

            >>> safe_exec(command="rm -rf ./tmp_*", timeout=5)
            '{"confirmation_required": true, "risk_level": "high", ...}'

            >>> safe_exec(command="rm -rf ./tmp_*", timeout=5, confirmed=True)
            '{"success": true, "confirmation_required": false, ...}'

        """
        import json

        # Determine working directory
        if working_dir is None:
            working_dir = self.get_project_root()

        # Create wrapper and execute
        wrapper = SafeExecWrapper(working_dir=working_dir)
        result = wrapper.execute(
            command=command,
            timeout=timeout,
            execution_plan=execution_plan,
            confirmed=confirmed,  # Story 2.4: Pass confirmed parameter
        )

        # Convert result to JSON
        result_dict = {
            "success": result.success,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": result.duration_ms,
            "precondition_passed": result.precondition_passed,
            "error_message": result.error_message,
            # Day 2: Timeout feedback fields
            "timeout_occurred": result.timeout_occurred,
            "actual_duration_seconds": result.actual_duration_seconds,
            "suggested_timeout": result.suggested_timeout,
            # Story 2.4: Confirmation fields
            "confirmation_required": result.confirmation_required,
            "confirmation_message": result.confirmation_message,
            "risk_level": result.risk_level,
        }

        return json.dumps(result_dict, indent=2)
