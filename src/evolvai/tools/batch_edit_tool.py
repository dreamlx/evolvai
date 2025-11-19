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
        """Batch edit files using regex patterns with preview and rollback.
        
        Supports capture groups (\\1, \\2), glob filtering, and ExecutionPlan constraints.
        Returns JSON with affected_files, changes_count, unified_diff, and rollback_id.
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
