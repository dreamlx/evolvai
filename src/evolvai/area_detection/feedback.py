"""
LLM可观测的反馈系统
"""

from dataclasses import dataclass
from typing import Any, Optional

from .data_models import QueryRouting


@dataclass
class ErrorResponse:
    """LLM友好的错误响应"""

    error_type: str
    summary: str
    fix_suggestion: "FixSuggestion"
    violation_details: Optional[dict[str, Any]] = None


@dataclass
class FixSuggestion:
    """修复建议"""

    summary: str
    code_example: str
    alternative_approaches: list[str]


@dataclass
class ExecutionReport:
    """执行报告"""

    detected_areas: list[dict[str, Any]]
    applied_areas: list[dict[str, Any]]
    applied_patterns: list[str]
    total_results: int
    execution_time_ms: float
    coverage: dict[str, dict[str, Any]]
    performance: dict[str, Any]


class FeedbackSystem:
    """LLM可观测的反馈系统"""

    def create_execution_report(self, routing: QueryRouting, results: Any) -> ExecutionReport:
        """创建执行报告"""
        # 检测到的区域信息
        detected_areas = [
            {"name": area.name, "language": area.language, "root": area.root_path, "confidence": area.confidence, "evidence": area.evidence}
            for area in routing.areas
        ]

        # 应用的区域配置
        applied_areas = [
            {
                "name": area.name,
                "budget_files": area.budget_files,
                "scanned_files": area.scanned_files,
                "found_matches": area.match_count,
                "duration_ms": area.duration_ms,
                "score": area.score,
            }
            for area in routing.applied_areas
        ]

        # 覆盖率信息
        coverage = {
            area.name: {"scanned": area.scanned_files, "found": area.match_count, "duration_ms": area.duration_ms}
            for area in routing.applied_areas
        }

        # 性能指标
        total_scanned = sum(area.scanned_files for area in routing.applied_areas)
        total_matches = sum(area.match_count for area in routing.applied_areas)
        total_duration = sum(area.duration_ms for area in routing.applied_areas)
        efficiency_score = (total_matches / total_scanned * 100) if total_scanned > 0 else 0

        performance = {
            "total_files_scanned": total_scanned,
            "total_matches_found": total_matches,
            "total_duration_ms": total_duration,
            "efficiency_score": efficiency_score,
            "areas_processed": len(routing.applied_areas),
        }

        return ExecutionReport(
            detected_areas=detected_areas,
            applied_areas=applied_areas,
            applied_patterns=routing.final_patterns,
            total_results=total_matches,
            execution_time_ms=total_duration,
            coverage=coverage,
            performance=performance,
        )

    def create_error_response(self, error_type: str, message: str, context: dict[str, Any] | None = None) -> ErrorResponse:
        """创建LLM友好的错误响应"""
        context = context or {}

        if error_type == "business_conflict":
            return ErrorResponse(
                error_type=error_type,
                summary=f"Business rule violation: {message}",
                fix_suggestion=FixSuggestion(
                    summary=context.get("suggestion", "Adjust your query to comply with business rules"),
                    code_example=self._get_business_conflict_example(context),
                    alternative_approaches=[
                        "Use more specific search patterns",
                        "Restrict search scope with file patterns",
                        "Use area_selector to target specific project areas",
                    ],
                ),
            )
        else:
            return ErrorResponse(
                error_type=error_type,
                summary=f"Error: {message}",
                fix_suggestion=FixSuggestion(
                    summary="Review and adjust your search parameters",
                    code_example="# Example: safe_search('specific pattern', max_files=30)",
                    alternative_approaches=["Check query syntax", "Verify file permissions"],
                ),
            )

    def create_constraint_violation_response(self, constraint_exception: Exception) -> ErrorResponse:
        """创建约束违规响应"""
        if hasattr(constraint_exception, "constraint_type"):
            constraint_type = constraint_exception.constraint_type
            details = {}

            if constraint_type == "file_limit":
                details = {
                    "files_processed": getattr(constraint_exception, "files_processed", 0),
                    "max_files": getattr(constraint_exception, "max_files", 0),
                }
                suggestion = f"Reduce search scope from {details['files_processed']} to ≤{details['max_files']} files"
                example = "# Reduce max_files parameter\nsafe_search('pattern', max_files=25)"

            elif constraint_type == "change_limit":
                details = {
                    "changes_made": getattr(constraint_exception, "changes_made", 0),
                    "max_changes": getattr(constraint_exception, "max_changes", 0),
                }
                suggestion = f"Limit changes to ≤{details['max_changes']} operations"
                example = "# Use read-only operations or limit scope\nsafe_search('pattern', read_only=True)"

            elif constraint_type == "timeout":
                details = {
                    "elapsed_time": getattr(constraint_exception, "elapsed_time", 0),
                    "timeout_seconds": getattr(constraint_exception, "timeout_seconds", 0),
                }
                suggestion = "Reduce search complexity or increase timeout"
                example = "# Increase timeout or simplify query\nsafe_search('pattern', timeout_seconds=60)"

            else:
                suggestion = "Review constraint parameters"
                example = "# Check execution limits\nsafe_search('pattern', max_files=50, timeout_seconds=30)"

            return ErrorResponse(
                error_type=f"constraint_{constraint_type}",
                summary=f"Constraint violation: {constraint_exception!s}",
                fix_suggestion=FixSuggestion(
                    summary=suggestion,
                    code_example=example,
                    alternative_approaches=[
                        "Use area_selector to focus search",
                        "Apply more specific file patterns",
                        "Break complex queries into smaller parts",
                    ],
                ),
                violation_details=details,
            )
        else:
            return self.create_error_response("unknown_constraint", str(constraint_exception))

    def _get_business_conflict_example(self, context: dict[str, Any]) -> str:
        """获取业务冲突的代码示例"""
        if "broad_pattern" in str(context):
            return """# Too broad pattern - AVOID
safe_search('.*')

# Better approach - USE SPECIFIC PATTERNS
safe_search('authentication', area_selector='backend-go')
safe_search('Component', area_selector='frontend-ts')"""
        else:
            return """# Follow business rules for search patterns
safe_search('specific_function_name', max_files=30)
safe_search('ClassName', area_selector='auto')"""
