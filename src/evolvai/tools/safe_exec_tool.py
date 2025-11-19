"""SafeExecTool - MCP-exposed safe command execution tool.

Story 2.3 Day 3: MCP tool integration for safe command execution.
"""

from typing import Optional

from evolvai.core.execution_plan import ExecutionPlan
from evolvai.tools.safe_exec import SafeExecWrapper
from serena.tools.tools_base import Tool


class SafeExecTool(Tool):
    """Safe command execution with precondition checks and timeout management.
    
    Detects risky commands, validates availability, truncates output.
    See docs/guides/tool-usage.md for usage guidance.
    """

    def apply(
        self,
        command: str,
        timeout: int,
        working_dir: Optional[str] = None,
        execution_plan: Optional[ExecutionPlan] = None,
        confirmed: bool = False,
    ) -> str:
        """Execute shell command safely with precondition checks and timeout.
        
        Detects risky commands, validates availability, requires confirmation for dangerous operations.
        Returns JSON with exit_code, stdout, stderr, timeout info, and confirmation status.
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