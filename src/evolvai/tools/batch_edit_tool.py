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
    
    TOOL SELECTION GUIDE
    ====================
    
    Understanding Tool Capability Levels
    -------------------------------------
    
    This guide helps you choose the right tool for your task. Tools are categorized
    by their capability level, which determines what kinds of operations they can handle.
    
    Level 1: Pattern-Based Text Operations (batch_edit, sed, awk)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    **What they can do:**
    - Match text patterns using regular expressions
    - Replace matched text with new text (including capture groups)
    - Process files as plain text without understanding code structure
    
    **What they CANNOT do:**
    - Understand code syntax or structure
    - Identify semantic boundaries (like "between import groups")
    - Analyze cross-file dependencies
    - Perform intelligent refactoring
    
    **Perfect for:**
    - Renaming variables/functions across files: getUserData → fetchUserData
    - Updating version strings: v1.0.0 → v2.0.0
    - Standardizing string formats: "error:" → "ERROR:"
    - Batch comment modifications: # TODO → # TODO(author)
    - Simple API migrations: oldAPI() → newAPI()
    
    **NOT suitable for:**
    - Import statement reorganization (use isort instead)
    - Code formatting (use black/ruff instead)
    - Adding missing docstrings (requires semantic understanding)
    - Complex refactoring (use LSP-based tools instead)
    
    Level 2: Syntax-Aware Structural Operations (isort, black, ruff)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    **What they can do:**
    - Parse code into Abstract Syntax Trees (AST)
    - Understand code structure (imports, functions, classes)
    - Perform syntax-aware transformations
    - Maintain code validity during modifications
    
    **Use these when:**
    - Sorting/organizing import statements → isort
    - Formatting code to standards → black
    - Fixing linting issues → ruff --fix
    - Adding/removing trailing commas → black
    
    Level 3: Semantic Refactoring Operations (LSP tools, IDE refactoring)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    **What they can do:**
    - Analyze code semantics and meaning
    - Track references across files
    - Understand type systems and interfaces
    - Perform complex refactoring operations
    
    **Use these when:**
    - Extracting methods/functions (IDE refactoring)
    - Renaming with cross-file reference updates (LSP rename)
    - Changing function signatures (IDE refactoring)
    - Interface/protocol modifications (requires semantic analysis)
    
    Decision Tree: Which Tool Should I Use?
    ----------------------------------------
    
    Q: Do I need to understand code structure?
       NO  → batch_edit (Level 1) ✅
       YES → Continue below
    
    Q: Do I need to understand code meaning/semantics?
       NO  → black/isort/ruff (Level 2) ✅
       YES → LSP tools/IDE (Level 3) ✅
    
    Q: Is this a simple text pattern replacement?
       YES → batch_edit (Level 1) ✅
       NO  → Continue below
    
    Q: Does it involve import statements or code formatting?
       YES → isort/black/ruff (Level 2) ✅
       NO  → Continue below
    
    Q: Does it require analyzing code logic or cross-file dependencies?
       YES → LSP tools/IDE (Level 3) ✅
       NO  → batch_edit might work (Level 1) ⚠️
    
    Common Mistakes and How to Avoid Them
    --------------------------------------
    
    ❌ MISTAKE: Using batch_edit to "add blank line between import groups"
    ✅ SOLUTION: Use isort - it understands import structure
    
    ❌ MISTAKE: Using batch_edit to "update all function signatures"
    ✅ SOLUTION: Use LSP rename or IDE refactoring - they track references
    
    ❌ MISTAKE: Using batch_edit to "format code consistently"
    ✅ SOLUTION: Use black/ruff - they understand Python syntax
    
    ❌ MISTAKE: Using batch_edit for "extracting common code to function"
    ✅ SOLUTION: Use IDE refactoring - requires semantic understanding
    
    When batch_edit Should Gracefully Decline
    ------------------------------------------
    
    If you encounter these error messages, it means you're trying to use
    a Level 1 tool for a Level 2/3 task:
    
    - "Cannot locate semantic boundary" → Need Level 2+ tool
    - "No matches found" (but you know the code exists) → Pattern too complex
    - "Would affect X files" (unexpectedly high) → Pattern too broad
    
    In these cases, batch_edit will provide suggestions for better tools.
    
    Real-World Examples from EvolvAI Dogfooding
    --------------------------------------------
    
    ✅ SUCCESS: Organizing imports with isort (not batch_edit)
       - Task: Sort imports according to PEP 8
       - Why batch_edit failed: Needs to understand stdlib vs third-party
       - Solution: Used isort with proper configuration
       - Result: All imports correctly organized
    
    ❌ ATTEMPTED: Standardizing test docstrings with batch_edit
       - Task: Convert triple-quoted Chinese descriptions to BDD format with Story/Scenario/DoD
       - Why batch_edit failed: Requires understanding test logic
       - Why it seemed possible: Looked like text transformation
       - Lesson: Adding semantic content requires Level 3 understanding
    
    ⚠️ DISCOVERED: Duplicate exception classes across modules
       - Task: Unify ConstraintViolationError imports
       - Why batch_edit failed: Exceptions have incompatible interfaces
       - Required solution: Manual refactoring (Level 3)
       - Lesson: Structural issues need architectural decisions
    
    Summary: Know Your Tool's Boundaries
    -------------------------------------
    
    batch_edit is a powerful Level 1 tool that excels at pattern-based text
    transformations across multiple files. It is NOT a universal refactoring
    tool. Understanding these boundaries helps you:
    
    1. Choose the right tool for the job
    2. Avoid wasting time on impossible tasks
    3. Achieve better results faster
    4. Maintain code quality and safety
    
    When in doubt, remember: Simple text patterns → batch_edit ✅
                            Everything else → Consider Level 2/3 tools
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
