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
    """Batch edit files using regex patterns with ExecutionPlan constraints.

    Supports preview mode, automatic rollback, and unified diff generation.
    Use for multi-file text pattern replacements (Level 1 operations).
    See docs/guides/tool-usage.md for tool selection guidance.
    """

    def apply(
        self,
        pattern: str,
        replacement: str,
        scope: str = "**/*",
        preview: bool = False,
        execution_plan: Optional[ExecutionPlan] = None,
    ) -> str:
        r"""Batch edit files using regex patterns with preview and rollback.

        Supports capture groups (\1, \2), glob filtering, and ExecutionPlan constraints.
        Returns JSON with affected_files, changes_count, unified_diff, and rollback_id.

        Note: This is a file-level editing tool. Use preview=True to verify changes
        before applying. Automatic rollback is available if edits fail.

        Args:
            pattern: Regular expression pattern to search for
            replacement: Replacement text (supports \1, \2 capture groups)
            scope: Glob pattern for file filtering (default: "**/*")
            preview: If True, show diff without applying changes
            execution_plan: Optional ExecutionPlan with constraints

        Returns:
            JSON string with success, affected_files, changes_count, unified_diff, rollback_id

        Examples:
            >>> # Rename function across codebase
            >>> batch_edit(pattern=r"oldFunc", replacement="newFunc", scope="**/*.py")
            >>> # Preview changes before applying
            >>> batch_edit(pattern=r"TODO", replacement="DONE", preview=True)

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
