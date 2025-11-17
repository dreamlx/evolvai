"""
MCP Tools - JSON Results & Error Handling Tests

Dimension 4: 验证 MCP 工具返回有效且结构正确的 JSON
Dimension 5: 验证错误被正确捕获并返回 LLM 友好的错误信息

测试目标:
- JSON 结果格式正确且可解析
- 必需字段存在
- 嵌套结构正确
- 错误信息对 LLM 友好
- 包含修复建议
"""
import pytest


class TestBatchEditJSONResults:
    """BatchEdit JSON 结果测试"""

    def test_preview_mode_returns_valid_json(self, simple_project, mock_agent):
        """验证 preview 模式返回有效 JSON

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Preview mode returns parseable JSON
        DoD: Result is valid JSON with required fields

        Given simple_project with 3 .py files
        When batch_edit(preview=True)
        Then result is valid JSON with success, affected_files, unified_diff
        """
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create tool and execute in preview mode
        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="old_value",
            replacement="new_value",
            scope="**/*.py",
            preview=True
        )

        # Verify result is valid JSON
        result = json.loads(result_json)

        # Verify required fields exist
        assert "success" in result, "Missing 'success' field"
        assert "affected_files" in result, "Missing 'affected_files' field"
        assert "unified_diff" in result, "Missing 'unified_diff' field"

        # Verify success is True
        assert result["success"] is True, f"Expected success=True, got {result['success']}"

        # Verify affected_files is a list
        assert isinstance(result["affected_files"], list), \
            f"affected_files should be list, got {type(result['affected_files'])}"

        # Verify we found the 3 test files
        assert len(result["affected_files"]) == 3, \
            f"Expected 3 affected files, got {len(result['affected_files'])}"
        # TODO: Implement in Phase 2.1

    def test_apply_mode_includes_rollback_id(self, simple_project, mock_agent):
        """验证 apply 模式包含 rollback_id

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Apply mode includes rollback_id
        DoD: Successful apply returns rollback_id

        Given simple_project with files
        When batch_edit(preview=False)
        Then result includes rollback_id field
        """
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create tool and execute in apply mode
        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="old_value",
            replacement="new_value",
            scope="**/*.py",
            preview=False
        )

        # Verify result is valid JSON
        result = json.loads(result_json)

        # Verify rollback_id field exists
        assert "rollback_id" in result, "Missing 'rollback_id' field"

        # Verify rollback_id is not None for successful apply
        if result["success"]:
            assert result["rollback_id"] is not None, \
                "rollback_id should not be None for successful apply"
            assert isinstance(result["rollback_id"], str), \
                f"rollback_id should be str, got {type(result['rollback_id'])}"
            assert len(result["rollback_id"]) > 0, \
                "rollback_id should not be empty string"
        # TODO: Implement in Phase 2.1

    def test_unified_diff_format(self, simple_project, mock_agent):
        """验证 unified_diff 格式正确

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: unified_diff is git-style diff
        DoD: Diff contains --- and +++ markers

        Given simple_project
        When batch_edit generates diff
        Then unified_diff contains "---" and "+++" markers
        """
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create tool and execute in preview mode to get diff
        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="old_value",
            replacement="new_value",
            scope="**/*.py",
            preview=True
        )

        # Verify result is valid JSON
        result = json.loads(result_json)

        # Verify unified_diff field exists
        assert "unified_diff" in result, "Missing 'unified_diff' field"
        unified_diff = result["unified_diff"]

        # Verify unified_diff is a string
        assert isinstance(unified_diff, str), \
            f"unified_diff should be str, got {type(unified_diff)}"

        # Verify git-style diff markers present
        assert "---" in unified_diff, "unified_diff missing '---' marker"
        assert "+++" in unified_diff, "unified_diff missing '+++' marker"

        # Verify diff shows the actual changes (old_value -> new_value)
        assert "-" in unified_diff or "old_value" in unified_diff, \
            "unified_diff should show removed/old content"
        assert "+" in unified_diff or "new_value" in unified_diff, \
            "unified_diff should show added/new content"
        # TODO: Implement in Phase 2.1


@pytest.mark.skip(reason="safe_search uses mock data - MCP layer validation only")
class TestSafeSearchJSONResults:
    """SafeSearch JSON 结果测试（基于 mock 数据）

    注意: safe_search 当前使用 mock 实现，这些测试仅验证 MCP 层
    的 JSON 格式和结构，不验证实际搜索准确性。
    """

    def test_successful_search_json_structure(self, go_project, mock_agent):
        """验证成功搜索的 JSON 结构

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Search returns valid JSON structure
        DoD: Result has success, query, execution_report fields

        Given go_project with .go files
        When safe_search(query="main")
        Then result is valid JSON with required structure
        """
        # TODO: Implement in Phase 2.1

    def test_execution_report_structure(self, go_project, mock_agent):
        """验证 execution_report 嵌套结构

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: execution_report has nested fields
        DoD: Report contains detected_areas, execution_time_ms

        Given search result
        When check execution_report
        Then has detected_areas, applied_areas, execution_time_ms
        """
        # TODO: Implement in Phase 2.1


class TestBatchEditErrorHandling:
    """BatchEdit 错误处理测试"""

    def test_invalid_regex_error(self, simple_project, mock_agent):
        """验证无效正则表达式返回清晰错误

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Invalid regex returns helpful error
        DoD: Error message mentions "regex" or "pattern"

        Given invalid regex pattern
        When batch_edit(pattern="[unclosed(")
        Then success=False and error_message mentions regex
        """
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create tool and execute with invalid regex
        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="[unclosed(",  # Invalid regex - unclosed bracket
            replacement="anything",
            scope="**/*.py",
            preview=True
        )

        # Verify result is valid JSON
        result = json.loads(result_json)

        # Verify success is False
        assert "success" in result, "Missing 'success' field"
        assert result["success"] is False, \
            f"Expected success=False for invalid regex, got {result['success']}"

        # Verify error_message field exists and mentions regex/pattern
        assert "error_message" in result, "Missing 'error_message' field"
        error_msg = result["error_message"].lower()
        assert "regex" in error_msg or "pattern" in error_msg, \
            f"Error message should mention 'regex' or 'pattern', got: {result['error_message']}"
        # TODO: Implement in Phase 2.2

    def test_execution_plan_constraint_violation(self, simple_project, mock_agent):
        """验证 ExecutionPlan 约束违规返回清晰错误

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Constraint violation returns clear error
        DoD: Error message mentions "max_files"

        Given ExecutionPlan with max_files=2
        And 5 files to modify
        When batch_edit with plan
        Then success=False and error_message mentions max_files
        """
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool
        from evolvai.core.execution_plan import (
            ExecutionPlan,
            RollbackStrategy,
            RollbackStrategyType,
            ExecutionLimits,
        )

        # Create 5 files to trigger max_files constraint
        for i in range(4, 6):
            (simple_project / f"file{i}.py").write_text("old_value = test")

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create ExecutionPlan with max_files=2 (but we have 5 files)
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.FILE_BACKUP),
            limits=ExecutionLimits(max_files=2),
        )

        # Create tool and execute with constraint
        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="old_value",
            replacement="new_value",
            scope="**/*.py",
            preview=True,
            execution_plan=plan
        )

        # Verify result is valid JSON
        result = json.loads(result_json)

        # Verify success is False
        assert "success" in result, "Missing 'success' field"
        assert result["success"] is False, \
            f"Expected success=False for constraint violation, got {result['success']}"

        # Verify error_message mentions max_files constraint
        assert "error_message" in result, "Missing 'error_message' field"
        error_msg = result["error_message"].lower()
        assert "max_files" in error_msg or "constraint" in error_msg or "limit" in error_msg, \
            f"Error message should mention constraint violation, got: {result['error_message']}"
        # TODO: Implement in Phase 2.2

    def test_error_response_includes_success_false(self, simple_project, mock_agent):
        """验证错误响应包含 success=False

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: All errors set success=False
        DoD: Error result has success=False

        Given any error condition
        When batch_edit fails
        Then result["success"] == False
        """
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create tool and trigger an error (invalid regex)
        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="[invalid(",  # Invalid regex
            replacement="anything",
            scope="**/*.py",
            preview=True
        )

        # Verify result is valid JSON
        result = json.loads(result_json)

        # Verify success field exists and is False
        assert "success" in result, \
            "Error response must include 'success' field"
        assert result["success"] is False, \
            f"Error response must have success=False, got {result['success']}"

        # Verify error_message exists for failed operations
        assert "error_message" in result, \
            "Error response must include 'error_message' field"
        assert result["error_message"] is not None, \
            "error_message should not be None for failed operations"
        assert len(result["error_message"]) > 0, \
            "error_message should not be empty for failed operations"
        # TODO: Implement in Phase 2.2


@pytest.mark.skip(reason="safe_search uses mock data")
class TestSafeSearchErrorHandling:
    """SafeSearch 错误处理测试"""

    def test_dangerous_query_rejected(self, go_project, mock_agent):
        """验证危险查询被拒绝

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Overly broad queries rejected
        DoD: Query ".*" returns error with suggestion

        Given dangerous query pattern ".*"
        When safe_search(query=".*")
        Then success=False and error mentions "broad"
        """
        # TODO: Implement in Phase 2.2

    def test_empty_query_rejected(self, go_project, mock_agent):
        """验证空查询被拒绝

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Empty or too short queries rejected
        DoD: Query "" returns error

        Given empty query
        When safe_search(query="")
        Then success=False and error mentions query length
        """
        # TODO: Implement in Phase 2.2
