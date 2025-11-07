"""
Story 2.1: safe_search Wrapper - 智能搜索包装器

智能搜索包装器，通过scope限制和参数化约束防止搜索范围过大导致的性能问题。
集成AreaDetector、QueryRouter和FeedbackSystem，提供完整的智能搜索功能。
"""

import json
import time
from pathlib import Path
from typing import Any, Optional

from evolvai.area_detection.data_models import (
    AppliedArea,
    ProjectArea,
    QueryRouting,
)
from evolvai.area_detection.detector import AreaDetector
from evolvai.area_detection.feedback import (
    ErrorResponse,
    ExecutionReport,
    FeedbackSystem,
    FixSuggestion,
)
from evolvai.area_detection.router import QueryRouter
from evolvai.core.execution_plan import ExecutionPlan


class SafeSearchResult:
    """安全搜索结果"""

    def __init__(
        self,
        query: str,
        total_results: int,
        execution_report: ExecutionReport,
        raw_results: Optional[list[dict[str, Any]]] = None,
        error: Optional[ErrorResponse] = None,
    ):
        self.query = query
        self.total_results = total_results
        self.execution_report = execution_report
        self.raw_results = raw_results or []
        self.error = error
        self.success = error is None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式，便于JSON序列化"""
        result = {
            "success": self.success,
            "query": self.query,
            "total_results": self.total_results,
            "execution_report": {
                "detected_areas": self.execution_report.detected_areas,
                "applied_areas": self.execution_report.applied_areas,
                "applied_patterns": self.execution_report.applied_patterns,
                "total_results": self.execution_report.total_results,
                "execution_time_ms": self.execution_report.execution_time_ms,
                "coverage": self.execution_report.coverage,
                "performance": self.execution_report.performance,
            },
        }

        if self.raw_results:
            result["raw_results"] = self.raw_results

        if self.error:
            result["error"] = {
                "error_type": self.error.error_type,
                "summary": self.error.summary,
                "fix_suggestion": {
                    "summary": self.error.fix_suggestion.summary,
                    "code_example": self.error.fix_suggestion.code_example,
                    "alternative_approaches": self.error.fix_suggestion.alternative_approaches,
                },
            }

        return result

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2)


class SafeSearchWrapper:
    """智能搜索包装器

    集成AreaDetector、QueryRouter和FeedbackSystem，提供完整的智能搜索功能。
    支持区域检测、查询路由、预算分配和执行约束。
    """

    def __init__(self, project_root: str, agent=None):
        self.project_root = Path(project_root)
        self.agent = agent

        # 初始化核心组件
        self.area_detector = AreaDetector(str(self.project_root))
        self.query_router = QueryRouter()
        self.feedback_system = FeedbackSystem()

    def search(
        self,
        query: str,
        scope: str = "**/*",
        max_files: int = 50,
        max_results: int = 100,
        timeout_seconds: int = 30,
        execution_plan: Optional[ExecutionPlan] = None,
        area_selector: str = "auto",
        include_areas: Optional[list[dict[str, Any]]] = None,
        mode: str = "balanced",
    ) -> SafeSearchResult:
        """执行智能搜索

        Args:
            query: 搜索查询或模式
            scope: 搜索范围模式
            max_files: 最大搜索文件数
            max_results: 最大结果数
            timeout_seconds: 超时时间（秒）
            execution_plan: 执行计划（包含约束）
            area_selector: 区域选择策略 ("auto", "backend-go", "frontend-ts", 等)
            include_areas: 显式定义的区域列表
            mode: 搜索模式 ("conservative", "balanced", "broad")

        Returns:
            SafeSearchResult: 搜索结果，包含执行报告和详细信息

        """
        start_time = time.time()

        try:
            # 0. 验证查询
            validation = self.validate_query(query)
            if validation.error_type != "validation_passed":
                return SafeSearchResult(
                    query=query,
                    total_results=0,
                    execution_report=ExecutionReport(
                        detected_areas=[],
                        applied_areas=[],
                        applied_patterns=[],
                        total_results=0,
                        execution_time_ms=0,
                        coverage={},
                        performance={},
                    ),
                    error=validation,
                )

            # 1. 区域检测
            if include_areas:
                # 使用显式定义的区域
                areas = self._create_areas_from_config(include_areas)
            else:
                # 自动检测区域
                areas = self.area_detector.detect_areas()

            if not areas:
                return self._create_error_result(
                    query,
                    "no_areas_detected",
                    "No project areas could be detected",
                    {"suggestion": "Check if project contains recognizable source files"},
                )

            # 2. 区域过滤（如果指定了area_selector）
            if area_selector != "auto":
                areas = [area for area in areas if area_selector in area.name.lower()]

            if not areas:
                return self._create_error_result(
                    query,
                    "no_matching_areas",
                    f"No areas matching selector '{area_selector}' found",
                    {"suggestion": "Try different area_selector or use 'auto'"},
                )

            # 3. 查询路由和预算分配
            total_budget = self._get_budget_for_mode(mode, max_files)
            routing = self.query_router.route_query(query, areas, total_budget)

            # 4. 执行搜索
            search_results = self._execute_search(query, routing, max_results, timeout_seconds, execution_plan)

            # 5. 创建执行报告
            execution_time_ms = (time.time() - start_time) * 1000
            execution_report = self.feedback_system.create_execution_report(routing, search_results)
            execution_report.execution_time_ms = execution_time_ms

            # 6. 返回结果
            return SafeSearchResult(
                query=query,
                total_results=len(search_results),
                execution_report=execution_report,
                raw_results=search_results,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            # 处理约束违规
            if hasattr(e, "constraint_type"):
                error_response = self.feedback_system.create_constraint_violation_response(e)
            else:
                error_response = self.feedback_system.create_error_response("search_error", str(e), {"query": query})

            return SafeSearchResult(
                query=query,
                total_results=0,
                execution_report=ExecutionReport(
                    detected_areas=[],
                    applied_areas=[],
                    applied_patterns=[],
                    total_results=0,
                    execution_time_ms=execution_time_ms,
                    coverage={},
                    performance={"error": str(e)},
                ),
                error=error_response,
            )

    def _create_areas_from_config(self, area_configs: list[dict[str, Any]]) -> list[ProjectArea]:
        """从配置创建区域列表"""
        areas = []
        for config in area_configs:
            areas.append(
                ProjectArea(
                    name=config["name"],
                    language=config.get("language", "unknown"),
                    confidence="Configured",
                    evidence=["explicit configuration"],
                    file_patterns=config.get("include_globs", ["*"]),
                    root_path=config.get("root", str(self.project_root)),
                )
            )
        return areas

    def _get_budget_for_mode(self, mode: str, max_files: int) -> int:
        """根据模式获取预算"""
        mode_multipliers = {
            "conservative": 0.6,
            "balanced": 1.0,
            "broad": 1.5,
        }
        multiplier = mode_multipliers.get(mode, 1.0)
        return int(max_files * multiplier)

    def _execute_search(
        self,
        query: str,
        routing: QueryRouting,
        max_results: int,
        timeout_seconds: int,
        execution_plan: Optional[ExecutionPlan],
    ) -> list[dict[str, Any]]:
        """执行实际的搜索操作"""
        results = []

        for applied_area in routing.applied_areas:
            try:
                # 构建搜索模式
                patterns = routing.final_patterns

                # 执行搜索（这里简化实现，实际应该使用具体的搜索工具）
                area_results = self._search_in_area(query, applied_area, patterns, max_results, timeout_seconds, execution_plan)

                results.extend(area_results)

                # 更新区域统计信息
                applied_area.scanned_files = len(area_results)  # 简化统计
                applied_area.match_count = len(area_results)
                applied_area.duration_ms = 10.0  # 简化计时

            except Exception as e:
                # 记录单个区域的错误，但继续处理其他区域
                applied_area.scanned_files = 0
                applied_area.match_count = 0
                applied_area.duration_ms = 0.0
                continue

        return results[:max_results]

    def _search_in_area(
        self,
        query: str,
        area: AppliedArea,
        patterns: list[str],
        max_results: int,
        timeout_seconds: int,
        execution_plan: Optional[ExecutionPlan],
    ) -> list[dict[str, Any]]:
        """在特定区域内执行搜索

        简化实现：这里应该集成实际的搜索工具（ripgrep、ugrep、grep等）
        """
        # 简化的搜索实现，实际应该调用具体的搜索工具
        # 这里返回模拟结果，实际实现需要：
        # 1. 根据patterns构建搜索命令
        # 2. 调用ripgrep/ugrep/grep等工具
        # 3. 解析结果并返回结构化数据

        mock_results = []
        area_root = area.name.split("-")[0] if "-" in area.name else "root"

        # 模拟搜索结果（实际实现时删除）
        for i in range(min(3, max_results)):
            mock_results.append(
                {
                    "file": f"{area_root}/example_file.py",
                    "line": i + 1,
                    "content": f"// Line containing: {query}",
                    "match": query,
                    "area": area.name,
                }
            )

        return mock_results

    def _create_error_result(self, query: str, error_type: str, message: str, context: dict[str, Any]) -> SafeSearchResult:
        """创建错误结果"""
        error_response = self.feedback_system.create_error_response(error_type, message, context)

        return SafeSearchResult(
            query=query,
            total_results=0,
            execution_report=ExecutionReport(
                detected_areas=[],
                applied_areas=[],
                applied_patterns=[],
                total_results=0,
                execution_time_ms=0.0,
                coverage={},
                performance={"error": message},
            ),
            error=error_response,
        )

    def get_project_areas(self, sample_limit: int = 200) -> list[ProjectArea]:
        """获取项目区域信息（用于MCP工具get_language_hint）"""
        return self.area_detector.detect_areas(sample_limit)

    def validate_query(self, query: str) -> ErrorResponse:
        """验证查询是否安全

        检查过于宽泛或危险的查询模式
        """
        # 检查过于宽泛的模式
        dangerous_patterns = [".*", ".*$", "^.*$", ".*.$", "find everything", "all files"]

        query_lower = query.lower().strip()
        for pattern in dangerous_patterns:
            if pattern in query_lower or query_lower == pattern:
                return self.feedback_system.create_error_response(
                    "business_conflict",
                    f"Query pattern '{query}' is too broad",
                    {
                        "suggestion": "Use more specific search pattern",
                        "broad_pattern": pattern,
                    },
                )

        # 检查空查询
        if not query or len(query.strip()) < 2:
            return self.feedback_system.create_error_response(
                "invalid_query",
                "Query is too short or empty",
                {"suggestion": "Use at least 2 characters for search"},
            )

        # 查询有效
        return ErrorResponse(
            error_type="validation_passed",
            summary="Query validation passed",
            fix_suggestion=FixSuggestion(
                summary="Query is safe to execute",
                code_example=f"safe_search('{query}')",
                alternative_approaches=[],
            ),
        )
