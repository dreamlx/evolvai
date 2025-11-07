"""
MCP tool wrappers for PatchEditor (safe_edit Patch-First architecture)
"""

from pathlib import Path
from typing import Any, Optional

from evolvai.core.execution_plan import ExecutionPlan
from evolvai.tools import ApplyResult, PatchEditor, ProposalResult
from serena.tools.tools_base import Tool, ToolMarkerCanEdit

__all__ = [
    "ApplyEditTool",
    "ProposeEditTool",
]


class ProposeEditTool(Tool):
    """
    Generate an edit proposal (unified diff) without modifying files.
    Uses safe_edit Patch-First architecture for preview-before-apply workflow.
    """

    def apply(
        self,
        pattern: str,
        replacement: str,
        scope: str = "**/*",
        language: Optional[str] = None,
    ) -> str:
        """
        Propose code edits by generating a unified diff without modifying files.

        This tool implements the Patch-First architecture's "propose" phase,
        allowing AI assistants to preview changes before applying them.

        Args:
            pattern: Search pattern (regular expression or string)
            replacement: Replacement content
            scope: File scope (glob pattern), default: "**/*"
            language: Optional language filter (e.g., "python", "go")

        Returns:
            JSON string containing:
            - patch_id: Unique identifier for the patch
            - unified_diff: Complete diff in unified format
            - affected_files: List of files that would be modified
            - statistics: Metadata (files_modified, lines_changed, etc.)

        Example:
            ```python
            propose_edit(
                pattern="getUserData",
                replacement="fetchUserData",
                scope="backend/**/*.go"
            )
            ```

        """
        project_root = self.agent.get_project_root()
        if not project_root:
            return "Error: No active project. Please activate a project first."

        editor = PatchEditor(project_root=Path(project_root))

        try:
            result: ProposalResult = editor.propose_edit(
                pattern=pattern,
                replacement=replacement,
                scope=scope,
                language=language,
            )

            # Return JSON-formatted result
            return self._format_proposal_result(result)

        except FileNotFoundError as e:
            return f"Error: {e}"
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

    def _format_proposal_result(self, result: ProposalResult) -> str:
        """Format ProposalResult as JSON string"""
        import json

        return json.dumps(
            {
                "success": True,
                "patch_id": result.patch_id,
                "affected_files": result.affected_files,
                "unified_diff": result.unified_diff,
                "statistics": result.statistics,
                "created_at": result.created_at.isoformat(),
            },
            indent=2,
        )


class ApplyEditTool(Tool, ToolMarkerCanEdit):
    """
    Apply a validated patch to modify files.
    Uses safe_edit Patch-First architecture with ExecutionPlan constraints.
    """

    def apply(
        self,
        patch_id: str,
        max_files: int = 10,
        max_changes: int = 50,
        timeout_seconds: int = 30,
    ) -> str:
        """
        Apply a previously proposed patch with behavioral constraints.

        This tool implements the Patch-First architecture's "apply" phase,
        with ExecutionPlan constraints for safety:
        - max_files: Maximum number of files to modify
        - max_changes: Maximum number of line changes
        - timeout_seconds: Maximum execution time

        Args:
            patch_id: The patch ID from propose_edit result
            max_files: Maximum files to modify (default: 10)
            max_changes: Maximum line changes (default: 50)
            timeout_seconds: Maximum execution time in seconds (default: 30)

        Returns:
            JSON string containing:
            - success: Whether application succeeded
            - modified_files: List of files that were modified
            - error_message: Error details if failed

        Raises:
            PatchNotFoundError: If patch_id doesn't exist
            ConstraintViolationError: If ExecutionPlan constraints violated
            TimeoutError: If execution exceeds timeout

        Example:
            ```python
            apply_edit(
                patch_id="patch_1234_abc",
                max_files=5,
                max_changes=20,
                timeout_seconds=15
            )
            ```

        """
        from evolvai.core.execution_plan import (
            ExecutionLimits,
            RollbackStrategy,
            RollbackStrategyType,
            ValidationConfig,
        )
        from evolvai.tools import ConstraintViolationError, PatchEditor

        project_root = self.agent.get_project_root()
        if not project_root:
            return "Error: No active project. Please activate a project first."

        editor = PatchEditor(project_root=Path(project_root))

        # Create ExecutionPlan with constraints
        execution_plan = ExecutionPlan(
            dry_run=False,
            validation=ValidationConfig(),
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.FILE_BACKUP,
                commands=[],
            ),
            limits=ExecutionLimits(
                max_files=max_files,
                max_changes=max_changes,
                timeout_seconds=timeout_seconds,
            ),
        )

        try:
            result: ApplyResult = editor.apply_edit(
                patch_id=patch_id, execution_plan=execution_plan
            )

            return self._format_apply_result(result)

        except ConstraintViolationError as e:
            return self._format_constraint_error(e)
        except TimeoutError as e:
            return f"Error: Operation timed out - {e}"
        except Exception as e:
            return f"Error applying patch: {e}"

    def _format_apply_result(self, result: ApplyResult) -> str:
        """Format ApplyResult as JSON string"""
        import json

        return json.dumps(
            {
                "success": result.success,
                "modified_files": result.modified_files,
                "worktree_path": result.worktree_path,
                "audit_log_id": result.audit_log_id,
                "error_message": result.error_message,
            },
            indent=2,
        )

    def _format_constraint_error(self, error: Any) -> str:
        """Format ConstraintViolationError as JSON string"""
        import json

        return json.dumps(
            {
                "success": False,
                "error_type": "ConstraintViolationError",
                "constraint_type": error.constraint_type,
                "limit": error.limit,
                "actual": error.actual,
                "message": str(error),
            },
            indent=2,
        )
