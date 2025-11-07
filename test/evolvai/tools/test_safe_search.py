"""
Story 2.1: safe_search - Complete Integration Tests

BDD-driven TDD implementation for safe_search wrapper.
Tests SafeSearchWrapper and MCP tools with full integration.
"""

import json
from unittest.mock import Mock, patch

from evolvai.area_detection.data_models import ProjectArea
from evolvai.tools.safe_search import SafeSearchWrapper
from serena.tools.safe_search_tool import GetLanguageHintTool, SafeSearchTool


class TestSafeSearchWrapper:
    """SafeSearchWrapper 集成测试套件"""

    def test_basic_search_with_auto_detection(self, tmp_path):
        """测试基本搜索与自动区域检测

        Story: story-2.1-tdd-plan.md
        Scenario: "自动检测项目区域并执行搜索"
        DoD: F1 - 基础搜索功能

        Given 项目包含Go和TypeScript代码
        When 调用search()进行查询
        Then 应该自动检测区域
        And 返回搜索结果
        """
        wrapper = SafeSearchWrapper(str(tmp_path))

        with patch.object(wrapper.area_detector, "detect_areas") as mock_detect:
            mock_detect.return_value = [
                ProjectArea(
                    name="go-backend",
                    language="go",
                    confidence="High",
                    evidence=["go.mod"],
                    file_patterns=["*.go"],
                    root_path=str(tmp_path / "backend"),
                )
            ]

            result = wrapper.search(query="find handler", max_files=50)

            assert result.success
            assert result.query == "find handler"
            assert len(result.execution_report.detected_areas) > 0

    def test_search_with_area_selector(self, tmp_path):
        """测试使用区域选择器搜索

        Story: story-2.1-tdd-plan.md
        Scenario: "使用area_selector指定搜索区域"
        DoD: F2 - 区域选择功能

        Given 项目有多个区域
        When 使用area_selector="backend-go"
        Then 只搜索Go后端区域
        """
        wrapper = SafeSearchWrapper(str(tmp_path))

        with patch.object(wrapper.area_detector, "detect_areas") as mock_detect:
            mock_detect.return_value = [
                ProjectArea(
                    name="backend-go",
                    language="go",
                    confidence="High",
                    evidence=["go.mod"],
                    file_patterns=["*.go"],
                    root_path=str(tmp_path / "backend"),
                ),
                ProjectArea(
                    name="frontend-ts",
                    language="typescript",
                    confidence="High",
                    evidence=["package.json"],
                    file_patterns=["*.ts"],
                    root_path=str(tmp_path / "frontend"),
                ),
            ]

            result = wrapper.search(query="find JWT handler", area_selector="backend-go", max_files=30)

            assert result.success
            # 验证只使用了backend-go区域
            applied_area_names = [area["name"] for area in result.execution_report.applied_areas]
            assert "backend-go" in applied_area_names
            assert "frontend-ts" not in applied_area_names

    def test_query_validation_broad_pattern(self, tmp_path):
        """测试查询验证 - 过于宽泛的模式

        Story: story-2.1-tdd-plan.md
        Scenario: "拒绝过于宽泛的查询模式"
        DoD: Q1 - 查询验证

        Given 用户输入过于宽泛的查询
        When 调用search()
        Then 应该返回验证错误
        And 提供修复建议
        """
        wrapper = SafeSearchWrapper(str(tmp_path))

        result = wrapper.search(query=".*", max_files=50)

        assert not result.success
        assert result.error is not None
        assert "too broad" in result.error.summary.lower()
        assert result.error.fix_suggestion is not None

    def test_query_validation_empty_query(self, tmp_path):
        """测试查询验证 - 空查询

        Story: story-2.1-tdd-plan.md
        Scenario: "拒绝空或过短的查询"
        DoD: Q1 - 查询验证

        Given 用户输入空查询
        When 调用search()
        Then 应该返回验证错误
        """
        wrapper = SafeSearchWrapper(str(tmp_path))

        result = wrapper.search(query="", max_files=50)

        assert not result.success
        assert result.error is not None
        assert "too short or empty" in result.error.summary.lower()

    def test_search_with_budget_allocation(self, tmp_path):
        """测试预算分配策略

        Story: story-2.1-tdd-plan.md
        Scenario: "根据查询内容智能分配预算"
        DoD: F3 - 智能预算分配

        Given 混合项目包含Go和TS区域
        When 查询包含"React component"关键词
        Then 应该给前端区域分配更多预算
        """
        wrapper = SafeSearchWrapper(str(tmp_path))

        with patch.object(wrapper.area_detector, "detect_areas") as mock_detect:
            mock_detect.return_value = [
                ProjectArea(
                    name="backend-go",
                    language="go",
                    confidence="High",
                    evidence=["go.mod"],
                    file_patterns=["*.go"],
                    root_path=str(tmp_path / "backend"),
                ),
                ProjectArea(
                    name="frontend-ts",
                    language="typescript",
                    confidence="High",
                    evidence=["package.json"],
                    file_patterns=["*.ts"],
                    root_path=str(tmp_path / "frontend"),
                ),
            ]

            result = wrapper.search(query="find React login component", max_files=50)

            assert result.success
            applied_areas = result.execution_report.applied_areas

            # 找到前端和后端区域的预算
            frontend_budget = next((area["budget_files"] for area in applied_areas if "frontend" in area["name"]), 0)
            backend_budget = next((area["budget_files"] for area in applied_areas if "backend" in area["name"]), 0)

            # 前端应该获得更多预算
            assert frontend_budget > backend_budget

    def test_search_modes(self, tmp_path):
        """测试搜索模式

        Story: story-2.1-tdd-plan.md
        Scenario: "支持conservative/balanced/broad三种模式"
        DoD: F4 - 搜索模式支持

        Given 项目有多个区域
        When 使用不同mode参数
        Then 预算分配应该不同
        """
        wrapper = SafeSearchWrapper(str(tmp_path))

        with patch.object(wrapper.area_detector, "detect_areas") as mock_detect:
            mock_detect.return_value = [
                ProjectArea(
                    name="backend-go",
                    language="go",
                    confidence="High",
                    evidence=["go.mod"],
                    file_patterns=["*.go"],
                    root_path=str(tmp_path),
                )
            ]

            # Conservative模式
            result_conservative = wrapper.search(query="find handler", mode="conservative", max_files=50)

            # Broad模式
            result_broad = wrapper.search(query="find handler", mode="broad", max_files=50)

            # Broad模式应该有更大的总预算
            conservative_total = sum(area["budget_files"] for area in result_conservative.execution_report.applied_areas)
            broad_total = sum(area["budget_files"] for area in result_broad.execution_report.applied_areas)

            assert broad_total > conservative_total

    def test_explicit_area_configuration(self, tmp_path):
        """测试显式区域配置

        Story: story-2.1-tdd-plan.md
        Scenario: "支持显式定义搜索区域"
        DoD: F5 - 显式区域配置

        Given 用户提供显式区域配置
        When 调用search()
        Then 应该使用用户配置而非自动检测
        """
        wrapper = SafeSearchWrapper(str(tmp_path))

        include_areas = [
            {
                "name": "custom-backend",
                "root": "backend",
                "language": "go",
                "include_globs": ["backend/**/*.go"],
                "exclude_globs": ["backend/vendor/**"],
            }
        ]

        result = wrapper.search(query="find handler", include_areas=include_areas, max_files=30)

        assert result.success
        detected_area_names = [area["name"] for area in result.execution_report.detected_areas]
        assert "custom-backend" in detected_area_names

    def test_get_project_areas(self, tmp_path):
        """测试获取项目区域信息

        Story: story-2.1-tdd-plan.md
        Scenario: "支持查询项目区域信息"
        DoD: F6 - 区域查询功能

        Given 项目包含多个区域
        When 调用get_project_areas()
        Then 返回所有检测到的区域信息
        """
        wrapper = SafeSearchWrapper(str(tmp_path))

        with patch.object(wrapper.area_detector, "detect_areas") as mock_detect:
            mock_detect.return_value = [
                ProjectArea(
                    name="backend-go",
                    language="go",
                    confidence="High",
                    evidence=["go.mod"],
                    file_patterns=["*.go"],
                    root_path=str(tmp_path / "backend"),
                )
            ]

            areas = wrapper.get_project_areas()

            assert len(areas) == 1
            assert areas[0].language == "go"
            assert areas[0].confidence == "High"


class TestSafeSearchTool:
    """SafeSearchTool MCP工具测试套件"""

    def test_mcp_tool_basic_search(self, tmp_path):
        """测试MCP工具基本搜索

        Story: story-2.1-tdd-plan.md
        Scenario: "通过MCP接口执行搜索"
        DoD: F8 - MCP接口功能

        Given AI助手调用safe_search工具
        When 传入查询参数
        Then 返回JSON格式的搜索结果
        """
        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        tool = SafeSearchTool(mock_agent)

        with patch("evolvai.area_detection.detector.AreaDetector.detect_areas") as mock_detect:
            mock_detect.return_value = [
                ProjectArea(
                    name="test-area",
                    language="python",
                    confidence="High",
                    evidence=["pyproject.toml"],
                    file_patterns=["*.py"],
                    root_path=str(tmp_path),
                )
            ]

            result_json = tool.apply(query="find test function", max_files=30)

            result = json.loads(result_json)
            assert "success" in result
            assert "execution_report" in result

    def test_mcp_tool_query_validation(self, tmp_path):
        """测试MCP工具查询验证

        Story: story-2.1-tdd-plan.md
        Scenario: "MCP工具正确验证查询"
        DoD: Q2 - MCP查询验证

        Given AI助手传入无效查询
        When 调用safe_search
        Then 返回错误信息和修复建议
        """
        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        tool = SafeSearchTool(mock_agent)

        result_json = tool.apply(query=".*", max_files=30)
        result = json.loads(result_json)

        assert result["success"] is False
        assert "error" in result
        assert "too broad" in result["error"]["message"].lower()

    def test_mcp_tool_with_area_selector(self, tmp_path):
        """测试MCP工具使用区域选择器

        Story: story-2.1-tdd-plan.md
        Scenario: "MCP工具支持area_selector参数"
        DoD: F9 - 区域选择器支持

        Given 混合项目
        When AI助手指定area_selector
        Then 只搜索指定区域
        """
        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        tool = SafeSearchTool(mock_agent)

        with patch("evolvai.area_detection.detector.AreaDetector.detect_areas") as mock_detect:
            mock_detect.return_value = [
                ProjectArea(
                    name="backend-go",
                    language="go",
                    confidence="High",
                    evidence=["go.mod"],
                    file_patterns=["*.go"],
                    root_path=str(tmp_path / "backend"),
                ),
                ProjectArea(
                    name="frontend-ts",
                    language="typescript",
                    confidence="High",
                    evidence=["package.json"],
                    file_patterns=["*.ts"],
                    root_path=str(tmp_path / "frontend"),
                ),
            ]

            result_json = tool.apply(query="find component", area_selector="frontend-ts", max_files=30)

            result = json.loads(result_json)
            assert result["success"]

            applied_areas = result["execution_report"]["applied_areas"]
            area_names = [area["name"] for area in applied_areas]
            assert any("frontend" in name for name in area_names)


class TestGetLanguageHintTool:
    """GetLanguageHintTool 测试套件"""

    def test_language_hint_detection(self, tmp_path):
        """测试语言检测工具

        Story: story-2.1-tdd-plan.md
        Scenario: "get_language_hint检测项目语言"
        DoD: F10 - 语言检测工具

        Given 项目包含多种语言
        When AI助手调用get_language_hint
        Then 返回检测到的语言和区域信息
        """
        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        tool = GetLanguageHintTool(mock_agent)

        with patch("evolvai.area_detection.detector.AreaDetector.detect_areas") as mock_detect:
            mock_detect.return_value = [
                ProjectArea(
                    name="backend-go",
                    language="go",
                    confidence="High",
                    evidence=["go.mod", "cmd/"],
                    file_patterns=["*.go"],
                    root_path=str(tmp_path / "backend"),
                )
            ]

            result_json = tool.apply(sample_limit=200)
            result = json.loads(result_json)

            assert "areas" in result
            assert len(result["areas"]) > 0
            assert result["areas"][0]["language"] == "go"
            assert "cache_status" in result


class TestEndToEndWorkflow:
    """端到端工作流测试"""

    def test_complete_search_workflow(self, tmp_path):
        """测试完整搜索工作流

        Story: story-2.1-tdd-plan.md
        Scenario: "完整的搜索工作流"
        DoD: Integration - 端到端集成

        Given 混合项目包含Go后端和TS前端
        When AI助手执行搜索查询
        Then 自动检测区域
        And 智能路由查询
        And 返回完整执行报告
        """
        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        # 1. 首先获取语言提示
        hint_tool = GetLanguageHintTool(mock_agent)

        with patch("evolvai.area_detection.detector.AreaDetector.detect_areas") as mock_detect:
            mock_detect.return_value = [
                ProjectArea(
                    name="backend-go",
                    language="go",
                    confidence="High",
                    evidence=["go.mod"],
                    file_patterns=["*.go"],
                    root_path=str(tmp_path / "backend"),
                ),
                ProjectArea(
                    name="frontend-ts",
                    language="typescript",
                    confidence="High",
                    evidence=["package.json", "tsconfig.json"],
                    file_patterns=["*.ts", "*.tsx"],
                    root_path=str(tmp_path / "frontend"),
                ),
            ]

            hint_result = hint_tool.apply(sample_limit=200)
            hint_data = json.loads(hint_result)

            assert len(hint_data["areas"]) == 2

            # 2. 然后执行搜索
            search_tool = SafeSearchTool(mock_agent)

            search_result = search_tool.apply(query="find authentication handler", area_selector="auto", mode="balanced", max_files=50)

            search_data = json.loads(search_result)

            assert search_data["success"]
            assert "execution_report" in search_data
            assert len(search_data["execution_report"]["detected_areas"]) == 2
            assert "performance" in search_data["execution_report"]
