"""Tool Template - READ THIS FIRST when creating new MCP tools.

⚠️ CRITICAL: MCP Tool Docstring Rule
====================================

Class docstring MUST be ≤ 10 lines.

Reason: Transmitted on EVERY MCP connection (~1 token/word)
Impact: 160-line docstring = 1.5k wasted tokens per session
Guide: See docs/guides/tool-usage.md for detailed documentation

Example Structure:
    \"\"\"[Verb] [object] [with key constraint].

    [1-2 sentences describing key features or use cases]
    See docs/guides/tool-usage.md for detailed usage.
    \"\"\"

✅ Good Examples:
-----------------
- "Batch edit files using regex patterns with ExecutionPlan constraints."
- "Safe command execution with precondition checks and timeout management."
- "Search codebase with area detection and budget limits."

❌ Bad Examples (TOO VERBOSE):
-------------------------------
- Multi-paragraph tool philosophy
- Level 1/2/3 classification explanations
- Detailed usage scenarios and examples
- Decision trees and selection guides
- Real-world case studies

Where to put detailed content:
-------------------------------
- Tool selection frameworks → docs/guides/tool-usage.md
- Usage examples → docs/guides/tool-usage.md
- Design rationale → docs/development/architecture/adrs/
- API reference → Method docstrings (can be longer)

"""

from typing import Optional

from evolvai.core.execution_plan import ExecutionPlan
from serena.tools.tools_base import Tool


class YourToolTemplate(Tool):
    """[Verb] [object] [with constraint].

    [1-2 sentences about key features or constraints]
    See docs/guides/tool-usage.md for usage guidance.
    """

    def apply(
        self,
        # Your parameters here
        param1: str,
        param2: int = 10,
        execution_plan: Optional[ExecutionPlan] = None,
    ) -> str:
        """[Brief one-line description of what this method does].

        This method docstring CAN be longer (not transmitted by MCP).
        You can provide detailed Args/Returns/Raises here.

        Args:
            param1: Description with example (e.g., "pattern like r'\\w+'")
            param2: Description with default explanation
            execution_plan: Optional ExecutionPlan for constraint validation

        Returns:
            JSON string with results containing:
            - success: bool
            - data: dict
            - error_message: Optional[str]

        Raises:
            ConstraintViolationError: If ExecutionPlan constraints violated
            ValueError: If parameters invalid

        Example:
            >>> your_tool(param1="value", param2=20)
            '{"success": true, "data": {...}}'

        """
        # Implementation here
        import json

        # Your logic
        result = {"success": True, "data": {}, "error_message": None}

        return json.dumps(result, indent=2)


# Quick Checklist Before Committing:
# ===================================
#
# ✅ Class docstring ≤ 10 lines?
# ✅ Educational content moved to docs/guides/?
# ✅ apply() method has detailed documentation?
# ✅ Parameters have clear types and descriptions?
# ✅ Returns JSON with consistent structure?
# ✅ ExecutionPlan support (if applicable)?
# ✅ Tests written following TDD plan?
# ✅ pre-commit hook passed?
#
# If any ❌, fix before committing!
