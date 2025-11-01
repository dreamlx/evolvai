"""
Safe Search包装器 - 整合所有组件的完整包装器
"""

from typing import Any, Optional

from .detector import AreaDetector
from .feedback import ExecutionReport, FeedbackSystem
from .router import QueryRouter


class SafeSearchWrapper:
    """Safe Search包装器 - 整合AreaDetector + QueryRouter + Story 1.3"""

    def __init__(self, agent: Any, project: Any):
        """
        初始化SafeSearch包装器

        Args:
            agent: SerenaAgent实例
            project: 项目对象，需要包含root_path属性

        """
        self.agent = agent
        self.project = project
        self.area_detector = AreaDetector(project.root_path)
        self.query_router = QueryRouter()
        self.feedback_system = FeedbackSystem()

    def execute(self, query: str, execution_plan: Optional[Any] = None, **kwargs) -> str:
        """
        执行安全搜索

        Args:
            query: 搜索查询
            execution_plan: Story 1.3的执行计划（可选）
            **kwargs: 其他搜索参数

        Returns:
            搜索结果字符串

        """
        # 1. 检测项目区域
        areas = self.area_detector.detect_areas()

        # 2. 路由查询
        routing = self.query_router.route_query(query, areas)

        # 3. 构建搜索参数
        search_params = self._build_search_params(routing, **kwargs)

        # 4. 通过Story 1.3的执行引擎执行
        try:
            # 获取搜索工具
            search_tool = self._get_search_tool()

            # Execute search, passing ExecutionPlan if provided
            if execution_plan:
                result = self.agent.execution_engine.execute(search_tool, execution_plan=execution_plan, **search_params)
            else:
                result = self.agent.execution_engine.execute(search_tool, **search_params)

            # 5. 生成执行报告
            report = self.feedback_system.create_execution_report(routing, result)
            return self._format_report(report)

        except Exception as e:
            # 6. 处理异常并提供LLM友好的反馈
            from evolvai.core.constraint_exceptions import ChangeLimitExceededError, FileLimitExceededError

            if isinstance(e, (FileLimitExceededError, ChangeLimitExceededError)):
                # Story 1.3约束违规
                feedback = self.feedback_system.create_constraint_violation_response(e)
                raise ConstraintViolationError(feedback) from e
            # 其他错误
            feedback = self.feedback_system.create_error_response("execution_error", str(e))
            raise SafeSearchError(feedback) from e

    def safe_search(
        self,
        query: str,
        area_selector: str = "auto",
        mode: str = "balanced",
        max_files: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        MCP接口的安全搜索方法

        Args:
            query: 搜索查询
            area_selector: 区域选择策略 ("auto", "backend-go", "frontend-ts", etc.)
            mode: 搜索模式 ("conservative", "balanced", "broad")
            max_files: 最大文件数限制
            timeout_seconds: 超时时间限制
            **kwargs: 其他参数

        Returns:
            格式化的搜索结果

        """
        # 1. 检测项目区域
        areas = self.area_detector.detect_areas()

        # 2. 根据area_selector过滤区域
        if area_selector != "auto":
            areas = [area for area in areas if area.name == area_selector or area.language == area_selector]

        if not areas:
            return {
                "error": f"No areas found for selector: {area_selector}",
                "suggestion": "Try 'auto' selector or check project structure",
            }

        # 3. 根据模式调整总预算
        total_budget = self._get_budget_for_mode(mode, max_files)

        # 4. 路由查询
        routing = self.query_router.route_query(query, areas, total_budget=total_budget)

        # 5. Create ExecutionPlan (Story 1.3 integration)
        from evolvai.core.execution_plan import ExecutionLimits, ExecutionPlan, RollbackStrategy, RollbackStrategyType

        execution_plan = ExecutionPlan(
            description=f"Safe search: {query}",
            tool_name="safe_search",
            limits=ExecutionLimits(max_files=total_budget, timeout_seconds=timeout_seconds or 30),
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
        )

        # 6. 执行搜索
        try:
            result = self.execute(query, execution_plan=execution_plan, **kwargs)

            # 7. 生成并返回格式化报告
            if isinstance(result, str):
                # Parse result, assume JSON format
                import json

                try:
                    result_data = json.loads(result)
                except json.JSONDecodeError:
                    result_data = {"raw_result": result}
            else:
                result_data = result

            # 生成执行报告
            report = self.feedback_system.create_execution_report(routing, result_data)

            return {
                "detected_areas": report.detected_areas,
                "applied_areas": report.applied_areas,
                "applied_patterns": report.applied_patterns,
                "total_results": report.total_results,
                "execution_time_ms": report.execution_time_ms,
                "coverage": report.coverage,
                "performance": report.performance,
                "query": query,
                "area_selector": area_selector,
                "mode": mode,
                "results": result_data,
            }

        except Exception as e:
            # 处理异常并返回错误信息
            if hasattr(e, "error_type"):
                # 这是我们的自定义错误
                return {
                    "error": e.error_type,
                    "summary": e.summary,
                    "fix_suggestion": {
                        "summary": e.fix_suggestion.summary,
                        "code_example": e.fix_suggestion.code_example,
                        "alternative_approaches": e.fix_suggestion.alternative_approaches,
                    },
                }
            else:
                # 标准异常
                return {"error": "execution_failed", "summary": str(e), "suggestion": "Check query syntax and project structure"}

    def _get_search_tool(self) -> Any:
        """获取搜索工具"""
        # 这里应该返回实际的搜索工具
        # 暂时返回一个mock对象
        from unittest.mock import Mock

        tool = Mock()
        tool.get_name.return_value = "safe_search"
        tool.is_active.return_value = True
        tool.get_apply_fn.return_value = Mock(return_value="mock search result")
        return tool

    def _build_search_params(self, routing: Any, **kwargs) -> dict[str, Any]:
        """构建搜索参数"""
        params = {
            "patterns": routing.final_patterns,
            "areas": [{"name": area.name, "budget": area.budget_files} for area in routing.applied_areas],
        }
        params.update(kwargs)
        return params

    def _get_budget_for_mode(self, mode: str, max_files: Optional[int]) -> int:
        """根据模式获取预算"""
        mode_budgets = {"conservative": 20, "balanced": 50, "broad": 100}

        if max_files:
            return min(max_files, mode_budgets.get(mode, 50))
        return mode_budgets.get(mode, 50)

    def _format_report(self, report: ExecutionReport) -> str:
        """格式化执行报告为字符串"""
        import json

        return json.dumps(
            {
                "detected_areas": report.detected_areas,
                "applied_areas": report.applied_areas,
                "applied_patterns": report.applied_patterns,
                "total_results": report.total_results,
                "execution_time_ms": report.execution_time_ms,
                "coverage": report.coverage,
                "performance": report.performance,
            },
            indent=2,
        )


class ConstraintViolationError(Exception):
    """约束违规错误"""

    def __init__(self, error_response):
        self.error_type = error_response.error_type
        self.summary = error_response.summary
        self.fix_suggestion = error_response.fix_suggestion
        self.violation_details = error_response.violation_details
        super().__init__(error_response.summary)


class SafeSearchError(Exception):
    """Safe搜索通用错误"""

    def __init__(self, error_response):
        self.error_type = error_response.error_type
        self.summary = error_response.summary
        self.fix_suggestion = error_response.fix_suggestion
        super().__init__(error_response.summary)
