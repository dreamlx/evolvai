"""
区域检测模块
"""

from .data_models import AppliedArea, ProjectArea, QueryRouting
from .detector import AreaDetector
from .feedback import ErrorResponse, ExecutionReport, FeedbackSystem, FixSuggestion
from .router import QueryRouter
from .wrapper import ConstraintViolationError, SafeSearchError, SafeSearchWrapper

__all__ = [
    "AppliedArea",
    "AreaDetector",
    "ConstraintViolationError",
    "ErrorResponse",
    "ExecutionReport",
    "FeedbackSystem",
    "FixSuggestion",
    "ProjectArea",
    "QueryRouter",
    "QueryRouting",
    "SafeSearchError",
    "SafeSearchWrapper",
]
