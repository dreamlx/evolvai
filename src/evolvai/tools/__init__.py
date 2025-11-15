"""
EvolvAI Safe Tools
提供安全的操作包装器
"""

from .patch_editor import (
    ApplyResult,
    ConstraintViolationError,
    PatchEditor,
    ProposalResult,
)
from .safe_search import (
    SafeSearchResult,
    SafeSearchWrapper,
)

# Note: MCP tool wrappers (SafeExecTool, BatchEditTool) are imported
# in serena.tools.__init__.py to avoid circular import issues

__all__ = [
    "ApplyResult",
    "ConstraintViolationError",
    "PatchEditor",
    "ProposalResult",
    "SafeSearchResult",
    "SafeSearchWrapper",
]
