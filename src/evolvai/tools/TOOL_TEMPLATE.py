"""Tool Template - READ THIS FIRST when creating new MCP tools.

⚠️ CRITICAL: MCP Tool Docstring Rules
=====================================

**What MCP transmits**: apply() method docstring (NOT class docstring!)

Source: mcp.py line 177: func_doc = tool.get_apply_docstring()
        tools_base.py line 166: docstring = apply_fn.__doc__

**apply() docstring MUST be ≤ 10 lines**

Reason: Transmitted on EVERY MCP connection (~1 token/word)
Impact: 89-line docstring = 1.3k wasted tokens per session
Guide: See docs/guides/tool-usage.md for detailed documentation

Class vs Method Docstrings:
----------------------------
- Class docstring: For human developers (can be longer, not transmitted)
- apply() docstring: For MCP/LLM (≤10 lines, transmitted every connection)

Example Structure:
    def apply(self, ...) -> str:
        \"\"\"[One-line capability statement].
        
        [1-2 lines key constraints/features]
        [Optional: Returns/output format]
        \"\"\"

✅ Good Examples (apply() docstring):
-------------------------------------
- "Batch edit files using regex patterns with preview and rollback."
- "Execute shell command safely with precondition checks and timeout."
- "Search codebase with area detection and budget limits."

❌ Bad Examples (TOO VERBOSE in apply()):
-----------------------------------------
- Multi-paragraph detailed explanations
- Full Args/Returns/Raises sections
- Usage examples and code snippets
- Design principles and rationale

Where to put detailed content:
-------------------------------
- Class docstring: Brief tool description (for developers)
- apply() docstring: ≤10 lines capability statement (for MCP)
- docs/guides/: Educational content, examples, patterns
- Method parameters: Use type hints + brief inline comments

"""

from typing import Optional

from evolvai.core.execution_plan import ExecutionPlan
from serena.tools.tools_base import Tool


class YourToolTemplate(Tool):
    """[Brief tool description for developers].
    
    This class docstring is NOT transmitted by MCP.
    You can be more descriptive here if needed for human developers.
    See docs/guides/tool-usage.md for usage guidance.
    """

    def apply(
        self,
        # Your parameters here
        param1: str,
        param2: int = 10,
        execution_plan: Optional[ExecutionPlan] = None,
    ) -> str:
        """[One-line capability statement with key constraint].
        
        [Optional: 1-2 lines about returns or critical behavior]
        """
        # Implementation here


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