"""BatchEditTool - MCP-exposed batch editing tool.

Story 2.2 Day 5: MCP tool integration for batch file editing.
"""

import json
from pathlib import Path
from typing import Optional

from evolvai.core.execution_plan import ExecutionPlan
from evolvai.tools.batch_editor import BatchEditor
from serena.tools.tools_base import Tool


class BatchEditTool(Tool):
    """Batch file editing tool exposed via MCP.

    Provides batch editing with:
    - Regex pattern search and replace
    - Preview mode (diff without apply)
    - ExecutionPlan constraint validation
    - Automatic rollback on failure
    - Unified diff generation
    """

    def apply(
        self,
        pattern: str,
        replacement: str,
        scope: str = "**/*",
        preview: bool = False,
        execution_plan: Optional[ExecutionPlan] = None,
    ) -> str:
        """Batch edit files using regex pattern search and replace.

        This tool enables safe batch editing across multiple files with:
        - Regex pattern matching with capture group support (\\1, \\2, etc.)
        - Glob-based file scope filtering (*.py, **/*.ts, etc.)
        - Preview mode to review changes before applying
        - ExecutionPlan constraints to prevent unintended large-scale changes
        - Automatic file-level rollback on failure
        - Unified diff output for change review

        Two-phase workflow:
        1. Preview phase (preview=True): Returns unified diff without modifying files
        2. Apply phase (preview=False): Applies changes with automatic rollback safety

        Args:
            pattern: Regular expression pattern to search for.
                    Supports full Python regex syntax including capture groups.
                    Example: r"(\\w+)_v1" to match versioned names
            replacement: Replacement text. Supports capture group references (\\1, \\2, etc.).
                        Example: r"\\1_v2" to preserve captured name and change version
            scope: Glob pattern to filter files (default: "**/*" for all files).

        Examples:
                   - "*.py" - All Python files in project root
                   - "**/*.ts" - All TypeScript files recursively
                   - "src/**/*.js" - JavaScript files under src/
            preview: If True, returns diff without modifying files (default: False).
                    Use preview mode to review changes before applying.
            execution_plan: Optional ExecutionPlan for constraint validation.
                           Prevents accidental large-scale modifications.
                           Example constraints:
                           - max_files: Maximum number of files to modify
                           - max_changes: Maximum number of pattern matches across all files

        Returns:
            JSON string with editing results containing:
            - success: bool - Whether operation succeeded
            - affected_files: list[str] - Paths of files that were/would be modified
            - changes_count: int - Total number of pattern matches replaced
            - unified_diff: str - Git-style unified diff showing changes
            - rollback_id: str|None - Rollback ID for recovery (if applied)
            - error_message: str|None - Error description if operation failed
            - duration_ms: float - Operation duration in milliseconds

        Raises:
            ConstraintViolationError: If ExecutionPlan constraints are violated
            RuntimeError: If backup creation or file writing fails

        Examples:
            >>> # Preview changes before applying
            >>> batch_edit(
            ...     pattern=r"getUserData",
            ...     replacement="fetchUserData",
            ...     scope="**/*.py",
            ...     preview=True
            ... )
            '{"success": true, "affected_files": ["api.py", "utils.py"], ...}'

            >>> # Apply changes with ExecutionPlan constraints
            >>> batch_edit(
            ...     pattern=r"(\\w+)_v1",
            ...     replacement=r"\\1_v2",
            ...     scope="src/**/*.ts",
            ...     preview=False,
            ...     execution_plan=ExecutionPlan(limits={"max_files": 10})
            ... )
            '{"success": true, "rollback_id": "abc123", ...}'

        Safety Features:
            - File-level rollback: Each file gets independent backup ID
            - Only modified files are restored on failure
            - User's other uncommitted work remains untouched
            - Atomic file writes using temp file + replace pattern
            - No dependency on git or external version control

        Design Principle (ADR-004):
            Tool-level rollback > System-level rollback
            - Development tools must only rollback their own changes
            - Never use git reset/hard reset (destroys user's uncommitted work)
            - File-level precision prevents collateral damage

        """
        # Get project root for BatchEditor
        project_root = Path(self.get_project_root())

        # Create editor and execute
        editor = BatchEditor(project_root=project_root)
        result = editor.batch_edit(
            pattern=pattern,
            replacement=replacement,
            scope=scope,
            preview=preview,
            execution_plan=execution_plan,
        )

        # Convert result to JSON
        result_dict = {
            "success": result.success,
            "affected_files": [str(f) for f in result.affected_files],
            "changes_count": result.changes_count,
            "unified_diff": result.unified_diff,
            "rollback_id": result.rollback_id,
            "error_message": result.error_message,
            "duration_ms": result.duration_ms,
        }

        return json.dumps(result_dict, indent=2)
