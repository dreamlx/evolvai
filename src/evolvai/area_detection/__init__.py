"""
区域检测模块
"""

from .data_models import AppliedArea, EditValidationError, EditValidationResult, ProjectArea, QueryRouting, RollbackResult, RollbackStrategy
from .detector import AreaDetector
from .edit_validator import EditValidator
from .edit_wrapper import SafeEditWrapper
from .feedback import ErrorResponse, ExecutionReport, FeedbackSystem, FixSuggestion
from .rollback_manager import RollbackManager
from .router import QueryRouter
from .wrapper import ConstraintViolationError, SafeSearchError, SafeSearchWrapper

__all__ = [
    "AppliedArea",
    "AreaDetector",
    "ConstraintViolationError",
    "EditValidationError",
    "EditValidationResult",
    "EditValidator",
    "ErrorResponse",
    "ExecutionReport",
    "FeedbackSystem",
    "FixSuggestion",
    "ProjectArea",
    "QueryRouter",
    "QueryRouting",
    "RollbackManager",
    "RollbackResult",
    "RollbackStrategy",
    "SafeEditWrapper",
    "SafeSearchError",
    "SafeSearchWrapper",
]
