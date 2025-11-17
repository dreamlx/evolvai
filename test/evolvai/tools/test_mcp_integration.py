"""
MCP Tools - ExecutionPlan Integration Tests

Dimension 6: 验证 ExecutionPlan 约束在 MCP 层正确传递和执行

测试目标:
- ExecutionPlan 参数正确传递到核心层
- 约束验证在核心层执行
- 违规时返回明确错误
"""
from unittest.mock import patch


class TestBatchEditExecutionPlan:
    """BatchEdit ExecutionPlan 集成测试"""

    def test_execution_plan_passed_to_core(self, simple_project, mock_agent):
        """验证 ExecutionPlan 被传递到 BatchEditor

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: ExecutionPlan propagates to core layer
        DoD: BatchEditor.batch_edit receives execution_plan parameter

        Given BatchEditTool with ExecutionPlan
        When tool.apply(execution_plan=plan)
        Then BatchEditor.batch_edit called with execution_plan=plan
        """
        from evolvai.core.execution_plan import (
            ExecutionLimits,
            ExecutionPlan,
            RollbackStrategy,
            RollbackStrategyType,
        )
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create ExecutionPlan with constraints
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.FILE_BACKUP),
            limits=ExecutionLimits(max_files=10, max_changes=100),
        )

        # Patch BatchEditor to verify it receives the execution_plan
        with patch("evolvai.tools.batch_edit_tool.BatchEditor") as MockBatchEditor:
            mock_editor_instance = MockBatchEditor.return_value
            # Configure mock to return a valid result
            from evolvai.tools.batch_editor import BatchEditResult
            mock_editor_instance.batch_edit.return_value = BatchEditResult(
                success=True,
                affected_files=[],
                changes_count=0,
                unified_diff="",
                rollback_id=None,
                error_message=None,
                duration_ms=0.0
            )

            # Create tool and execute with ExecutionPlan
            tool = BatchEditTool(mock_agent)
            tool.apply(
                pattern="old_value",
                replacement="new_value",
                scope="**/*.py",
                preview=True,
                execution_plan=plan
            )

            # Verify BatchEditor.batch_edit was called with execution_plan
            mock_editor_instance.batch_edit.assert_called_once()
            call_kwargs = mock_editor_instance.batch_edit.call_args.kwargs
            assert "execution_plan" in call_kwargs, \
                "batch_edit should receive execution_plan parameter"
            assert call_kwargs["execution_plan"] is plan, \
                "execution_plan should be passed unchanged to BatchEditor"
        # TODO: Implement in Phase 2.3

    def test_max_files_constraint_enforced(self, simple_project, mock_agent):
        """验证 max_files 约束在核心层执行

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: max_files constraint prevents over-modification
        DoD: Modifying > max_files returns constraint error

        Given ExecutionPlan with max_files=2
        And 5 files matching pattern
        When batch_edit executes
        Then constraint violation error returned
        """
        import json

        from evolvai.core.execution_plan import (
            ExecutionLimits,
            ExecutionPlan,
            RollbackStrategy,
            RollbackStrategyType,
        )
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Create 5 files total (3 from simple_project + 2 more)
        for i in range(4, 6):
            (simple_project / f"file{i}.py").write_text("old_value = test")

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create ExecutionPlan with max_files=2 (we have 5 files)
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

        # Verify constraint violation
        assert result["success"] is False, \
            "Should fail when exceeding max_files constraint"
        assert "error_message" in result, "Should include error message"
        error_msg = result["error_message"].lower()
        assert "max_files" in error_msg or "constraint" in error_msg or "limit" in error_msg, \
            f"Error should mention max_files constraint, got: {result['error_message']}"
        # TODO: Implement in Phase 2.3

    def test_max_changes_constraint_enforced(self, simple_project, mock_agent):
        """验证 max_changes 约束在核心层执行

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: max_changes constraint prevents excessive replacements
        DoD: Exceeding max_changes returns constraint error

        Given ExecutionPlan with max_changes=2
        And file with 5 pattern matches
        When batch_edit executes
        Then constraint violation error returned
        """
        import json

        from evolvai.core.execution_plan import (
            ExecutionLimits,
            ExecutionPlan,
            RollbackStrategy,
            RollbackStrategyType,
        )
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Create a file with 5 occurrences of the pattern
        test_file = simple_project / "many_matches.py"
        test_file.write_text("""
old_value = 1
old_value = 2
old_value = 3
old_value = 4
old_value = 5
""")

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create ExecutionPlan with max_changes=2 (file has 5 matches)
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.FILE_BACKUP),
            limits=ExecutionLimits(max_changes=2),
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

        # Verify constraint violation
        assert result["success"] is False, \
            "Should fail when exceeding max_changes constraint"
        assert "error_message" in result, "Should include error message"
        error_msg = result["error_message"].lower()
        assert "max_changes" in error_msg or "constraint" in error_msg or "limit" in error_msg, \
            f"Error should mention max_changes constraint, got: {result['error_message']}"
        # TODO: Implement in Phase 2.3

    def test_execution_plan_optional(self, simple_project, mock_agent):
        """验证 ExecutionPlan 参数可选

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: batch_edit works without ExecutionPlan
        DoD: Omitting execution_plan succeeds

        Given BatchEditTool
        When batch_edit without execution_plan
        Then operation succeeds normally
        """
        import json

        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Update mock_agent to return simple_project path
        mock_agent.get_project_root.return_value = str(simple_project)

        # Create tool and execute WITHOUT execution_plan
        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="old_value",
            replacement="new_value",
            scope="**/*.py",
            preview=True
            # Note: No execution_plan parameter
        )

        # Verify result is valid JSON
        result = json.loads(result_json)

        # Verify operation succeeded without execution_plan
        assert "success" in result, "Missing 'success' field"
        assert result["success"] is True, \
            f"Should succeed without execution_plan, got: {result.get('error_message', 'N/A')}"

        # Verify normal operation - affected files found
        assert "affected_files" in result, "Missing 'affected_files' field"
        assert len(result["affected_files"]) > 0, \
            "Should find affected files when execution_plan is omitted"
        # TODO: Implement in Phase 2.3
