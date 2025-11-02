"""
测试FeedbackSystem的LLM可观测反馈功能
"""

from unittest.mock import Mock, patch

import pytest

from evolvai.area_detection.data_models import AppliedArea, ProjectArea, QueryRouting

# 导入我们要测试的类
from evolvai.area_detection.feedback import FeedbackSystem
from evolvai.core.constraint_exceptions import FileLimitExceededError


class TestFeedbackSystem:
    """测试FeedbackSystem的核心功能"""

    def test_execution_report_generation(self):
        """测试执行报告生成"""
        feedback = FeedbackSystem()

        routing = QueryRouting(
            areas=[
                ProjectArea(name="backend-go", language="go", confidence="High", evidence=["go.mod"], file_patterns=["*.go"]),
                ProjectArea(
                    name="frontend-ts", language="typescript", confidence="High", evidence=["package.json"], file_patterns=["*.ts"]
                ),
            ],
            applied_areas=[
                AppliedArea(name="backend-go", budget_files=35, scanned_files=35, match_count=8, duration_ms=45.0, score=3),
                AppliedArea(name="frontend-ts", budget_files=15, scanned_files=15, match_count=2, duration_ms=12.0, score=1),
            ],
            final_patterns=["backend/**/*.go", "frontend/**/*.ts"],
            query="find JWT authentication handler",
        )

        report = feedback.create_execution_report(routing, Mock())

        # 验证检测到的区域信息
        detected_languages = [area["language"] for area in report.detected_areas]
        assert "go" in detected_languages
        assert "typescript" in detected_languages

        # 验证应用的区域预算
        backend_applied = next(area for area in report.applied_areas if area["name"] == "backend-go")
        assert backend_applied["budget_files"] == 35

        # 验证覆盖率信息
        assert hasattr(report, "coverage")
        assert report.coverage["backend-go"]["scanned"] == 35
        assert report.coverage["backend-go"]["found"] == 8

    def test_llm_friendly_error_messages(self):
        """测试LLM友好的错误消息"""
        feedback = FeedbackSystem()

        # 测试业务冲突错误
        business_error = feedback.create_error_response(
            "business_conflict", "Query pattern '.*' is too broad", {"suggestion": "Use more specific search pattern"}
        )

        assert business_error.error_type == "business_conflict"
        assert "specific search pattern" in business_error.fix_suggestion.summary
        assert "safe_search" in business_error.fix_suggestion.code_example

    def test_constraint_violation_feedback(self):
        """测试约束违规的反馈"""
        feedback = FeedbackSystem()

        # 模拟FileLimitExceededError
        constraint_error = feedback.create_constraint_violation_response(
            FileLimitExceededError("File limit exceeded: 60 > 50", files_processed=60, max_files=50)
        )

        assert constraint_error.error_type == "constraint_file_limit"
        assert constraint_error.violation_details["files_processed"] == 60
        assert constraint_error.violation_details["max_files"] == 50
        assert "Reduce search scope" in constraint_error.fix_suggestion.summary

    def test_performance_metrics_collection(self):
        """测试性能指标收集"""
        feedback = FeedbackSystem()

        routing = QueryRouting(
            areas=[],
            applied_areas=[AppliedArea(name="test-area", budget_files=30, scanned_files=30, match_count=5, duration_ms=25.5, score=2)],
            final_patterns=["**/*.py"],
            query="test query",
        )

        report = feedback.create_execution_report(routing, Mock())

        # 验证性能指标
        assert hasattr(report, "performance")
        assert report.performance["total_files_scanned"] == 30
        assert report.performance["total_matches_found"] == 5
        assert report.performance["total_duration_ms"] == 25.5
        assert report.performance["efficiency_score"] > 0

    def test_mcp_schema_compliance(self):
        """测试MCP Schema合规性"""
        feedback = FeedbackSystem()

        routing = QueryRouting(
            areas=[],
            applied_areas=[AppliedArea(name="test-area", budget_files=20, scanned_files=20, match_count=3, duration_ms=15.0, score=1)],
            final_patterns=["**/*.go"],
            query="test query",
        )

        report = feedback.create_execution_report(routing, Mock())

        # 验证MCP响应格式
        required_fields = ["detected_areas", "applied_areas", "applied_patterns", "total_results", "execution_time_ms"]
        for field in required_fields:
            assert hasattr(report, field)

        assert isinstance(report.total_results, int)
        assert isinstance(report.execution_time_ms, (int, float))


class TestSafeSearchWrapper:
    """测试SafeSearchWrapper的完整集成功能"""

    def test_story13_integration(self):
        """测试Story 1.3集成"""
        from evolvai.area_detection.wrapper import SafeSearchWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeSearchWrapper(mock_agent, mock_project)

        # 创建带约束的ExecutionPlan
        from evolvai.core.execution_plan import ExecutionLimits, ExecutionPlan, RollbackStrategy, RollbackStrategyType

        limits = ExecutionLimits(max_files=50, timeout_seconds=20)
        rollback = RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT)
        execution_plan = ExecutionPlan(
            description="Test safe search with constraints", tool_name="safe_search", limits=limits, rollback=rollback
        )

        # 模拟执行引擎
        with patch.object(mock_agent, "execution_engine") as mock_engine:
            mock_engine.execute.return_value = "Found 3 matches"

            wrapper.execute("find getUserData", execution_plan=execution_plan)

            # 验证ExecutionPlan被传递给执行引擎
            mock_engine.execute.assert_called_once()
            call_kwargs = mock_engine.execute.call_args[1]
            assert "execution_plan" in call_kwargs

    def test_constraint_violation_handling(self):
        """测试约束违规处理"""
        from evolvai.area_detection.wrapper import ConstraintViolationError, SafeSearchWrapper
        from evolvai.core.constraint_exceptions import FileLimitExceededError

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeSearchWrapper(mock_agent, mock_project)

        # 模拟约束违规
        with patch.object(mock_agent, "execution_engine") as mock_engine:
            mock_engine.execute.side_effect = FileLimitExceededError("Too many files", files_processed=60, max_files=50)

            with pytest.raises(ConstraintViolationError) as exc_info:
                wrapper.execute("find .*", max_files=50)

            # 验证包装后的错误包含原始约束违规信息
            error_message = str(exc_info.value)
            assert "Too many files" in error_message
            assert "constraint violation" in error_message.lower()

    def test_mcp_interface_with_area_support(self):
        """测试支持区域的MCP接口"""
        from evolvai.area_detection.wrapper import SafeSearchWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeSearchWrapper(mock_agent, mock_project)

        # 测试area_selector参数
        with patch.object(wrapper, "execute") as mock_execute:
            mock_execute.return_value = {"results": []}

            # 测试auto模式
            wrapper.safe_search("find handler", area_selector="auto")
            mock_execute.assert_called_once()
            # Verify execute method is called with execution_plan parameter
            call_args = mock_execute.call_args[1]
            assert "execution_plan" in call_args

    def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        from evolvai.area_detection.wrapper import SafeSearchWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeSearchWrapper(mock_agent, mock_project)

        # 模拟完整工作流程
        with patch.object(wrapper, "execute") as mock_execute:
            mock_execute.return_value = "Found 5 matches"  # Return string for feedback system processing

            result = wrapper.safe_search("find authentication handler", mode="balanced")

            # 验证返回结果包含所有必要字段
            assert "detected_areas" in result
            assert "applied_areas" in result
            assert "total_results" in result
            # total_results is calculated from routing.applied_areas, should match sum of match_count
            assert result["total_results"] >= 0
