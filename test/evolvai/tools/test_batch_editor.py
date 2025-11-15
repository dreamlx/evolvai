"""
Story 2.2 - BatchEditor TDD测试套件
遵循TDD Red-Green-Refactor循环
"""

import tempfile
from pathlib import Path

import pytest


class TestBatchEditorCore:
    """BatchEditor核心功能测试 - Story 2.2"""

    def test_simple_rename_without_preview(self, tmp_path):
        """测试简单重命名（无预览模式）

        Story: 2.2 - Batch Edit System
        Scenario: Simple rename across multiple files
        DoD: F1 - Batch automation working

        Given 3 files with function "getUserData"
        When batch_edit(pattern="getUserData", replacement="fetchUserData")
        Then all 3 files updated
        And changes_count = 3
        And unified_diff shows changes
        And no preview step
        """
        from evolvai.tools.batch_editor import BatchEditor

        # Setup: Create 3 test files with "getUserData"
        file1 = tmp_path / "api.py"
        file1.write_text("def getUserData():\n    return data\n")

        file2 = tmp_path / "utils.py"
        file2.write_text("result = getUserData()\n")

        file3 = tmp_path / "models.py"
        file3.write_text("# Test getUserData function\n")

        # Execute: batch_edit without preview
        editor = BatchEditor(project_root=tmp_path)
        result = editor.batch_edit(
            pattern=r"getUserData",
            replacement="fetchUserData",
            scope="*.py",
            preview=False  # Apply directly
        )

        # Assert: All files updated
        assert result.success is True
        assert len(result.affected_files) == 3
        assert result.changes_count == 3
        assert result.unified_diff != ""
        assert result.rollback_id is not None  # Auto-rollback enabled

        # Verify actual file changes
        assert "fetchUserData" in file1.read_text()
        assert "fetchUserData" in file2.read_text()
        assert "fetchUserData" in file3.read_text()
        assert "getUserData" not in file1.read_text()

    def test_preview_mode_returns_diff_without_applying(self, tmp_path):
        """测试预览模式（不应用更改）

        Story: 2.2 - Batch Edit System
        Scenario: Preview complex refactoring
        DoD: F2 - Preview mode working

        Given 5 files to modify
        When batch_edit(preview=True)
        Then unified_diff returned
        And files NOT modified
        And affected_files list returned
        """
        from evolvai.tools.batch_editor import BatchEditor

        # Setup: Create 5 test files
        files = []
        for i in range(5):
            file = tmp_path / f"module{i}.py"
            file.write_text(f"class OldName{i}:\n    pass\n")
            files.append(file)

        # Execute: batch_edit with preview=True
        editor = BatchEditor(project_root=tmp_path)
        result = editor.batch_edit(
            pattern=r"OldName(\d+)",
            replacement=r"NewName\1",
            scope="*.py",
            preview=True  # Preview only
        )

        # Assert: Preview returned, no changes applied
        assert result.success is True
        assert len(result.affected_files) == 5
        assert result.changes_count == 5
        assert result.unified_diff != ""
        assert "OldName" in result.unified_diff
        assert "NewName" in result.unified_diff

        # Verify files NOT modified
        for i, file in enumerate(files):
            content = file.read_text()
            assert f"OldName{i}" in content
            assert f"NewName{i}" not in content

    def test_execution_plan_max_files_constraint(self, tmp_path):
        """测试ExecutionPlan max_files约束

        Story: 2.2 - Batch Edit System
        Scenario: Constraint violation handling
        DoD: Q1 - ExecutionPlan constraints enforced

        Given ExecutionPlan with max_files=3
        When batch_edit matches 5 files
        Then error raised
        And files NOT modified
        """
        from evolvai.core.execution_plan import ExecutionLimits, ExecutionPlan, RollbackStrategy, RollbackStrategyType
        from evolvai.tools.batch_editor import BatchEditor

        # Setup: Create 5 files
        for i in range(5):
            file = tmp_path / f"file{i}.py"
            file.write_text(f"value = {i}\n")

        # Execute: batch_edit with max_files=3 constraint
        editor = BatchEditor(project_root=tmp_path)
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.FILE_BACKUP),
            limits=ExecutionLimits(max_files=3, max_changes=100)
        )

        result = editor.batch_edit(
            pattern=r"value",
            replacement="result",
            scope="*.py",
            preview=False,
            execution_plan=plan
        )

        # Assert: Constraint violation
        assert result.success is False
        assert "max_files" in result.error_message.lower()
        assert len(result.affected_files) == 0
        assert result.changes_count == 0

    def test_execution_plan_max_changes_constraint(self, tmp_path):
        """测试ExecutionPlan max_changes约束

        Story: 2.2 - Batch Edit System
        Scenario: Constraint violation handling
        DoD: Q1 - ExecutionPlan constraints enforced

        Given ExecutionPlan with max_changes=2
        When batch_edit would make 5 changes
        Then error raised
        And files NOT modified
        """
        from evolvai.core.execution_plan import ExecutionLimits, ExecutionPlan, RollbackStrategy, RollbackStrategyType
        from evolvai.tools.batch_editor import BatchEditor

        # Setup: Create file with 5 occurrences
        file = tmp_path / "test.py"
        file.write_text("foo foo foo foo foo\n")

        # Execute: batch_edit with max_changes=2 constraint
        editor = BatchEditor(project_root=tmp_path)
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.FILE_BACKUP),
            limits=ExecutionLimits(max_files=10, max_changes=2)
        )

        result = editor.batch_edit(
            pattern=r"foo",
            replacement="bar",
            scope="*.py",
            preview=False,
            execution_plan=plan
        )

        # Assert: Constraint violation
        assert result.success is False
        assert "max_changes" in result.error_message.lower()
        assert result.changes_count == 0

        # Verify file NOT modified
        assert "foo" in file.read_text()
        assert "bar" not in file.read_text()

    def test_auto_rollback_on_partial_failure(self, tmp_path):
        """测试部分失败时的自动回滚

        Story: 2.2 - Batch Edit System
        Scenario: Auto-rollback on write failure
        DoD: Q2 - Rollback working on failure

        Given 3 files to modify
        When 2nd file write fails
        Then all changes rolled back
        And rollback_id provided
        And error_message explains failure
        """
        from unittest.mock import patch

        from evolvai.tools.batch_editor import BatchEditor

        # Setup: Create 3 files
        file1 = tmp_path / "file1.py"
        file1.write_text("old_value\n")
        file2 = tmp_path / "file2.py"
        file2.write_text("old_value\n")
        file3 = tmp_path / "file3.py"
        file3.write_text("old_value\n")

        # Execute: batch_edit with simulated write failure
        editor = BatchEditor(project_root=tmp_path)

        # Mock write to fail on 2nd file
        original_write = Path.write_text
        call_count = [0]

        def mock_write(self, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise PermissionError("Simulated write failure")
            return original_write(self, *args, **kwargs)

        with patch.object(Path, 'write_text', mock_write):
            result = editor.batch_edit(
                pattern=r"old_value",
                replacement="new_value",
                scope="*.py",
                preview=False
            )

        # Assert: Failure with rollback
        assert result.success is False
        assert result.rollback_id is not None
        assert "write failure" in result.error_message.lower()

        # Verify all files reverted (rollback worked)
        assert "old_value" in file1.read_text()
        assert "old_value" in file2.read_text()
        assert "old_value" in file3.read_text()

    def test_regex_pattern_with_capture_groups(self, tmp_path):
        """测试正则表达式捕获组

        Story: 2.2 - Batch Edit System
        Scenario: Complex regex refactoring
        DoD: F3 - Regex capture groups working

        Given files with pattern "function_name_v1"
        When batch_edit(pattern=r"(\w+)_v1", replacement=r"\1_v2")
        Then capture groups preserved in replacement
        And files updated correctly
        """
        from evolvai.tools.batch_editor import BatchEditor

        # Setup: Create files with versioned names
        file1 = tmp_path / "api.py"
        file1.write_text("def process_data_v1():\n    pass\n")

        file2 = tmp_path / "utils.py"
        file2.write_text("result = calculate_total_v1()\n")

        # Execute: batch_edit with capture group
        editor = BatchEditor(project_root=tmp_path)
        result = editor.batch_edit(
            pattern=r"(\w+)_v1",
            replacement=r"\1_v2",
            scope="*.py",
            preview=False
        )

        # Assert: Changes applied with capture groups
        assert result.success is True
        assert result.changes_count == 2

        # Verify capture groups worked
        content1 = file1.read_text()
        content2 = file2.read_text()
        assert "process_data_v2" in content1
        assert "calculate_total_v2" in content2
        assert "_v1" not in content1
        assert "_v1" not in content2


class TestBatchEditorEdgeCases:
    """BatchEditor边界情况测试"""

    def test_empty_result_when_no_matches(self, tmp_path):
        """测试无匹配时返回空结果

        Given files with no matching pattern
        When batch_edit()
        Then success=True but changes_count=0
        And affected_files=[]
        """
        from evolvai.tools.batch_editor import BatchEditor

        # Setup: Create file without matching pattern
        file = tmp_path / "test.py"
        file.write_text("def hello():\n    pass\n")

        # Execute: batch_edit with non-matching pattern
        editor = BatchEditor(project_root=tmp_path)
        result = editor.batch_edit(
            pattern=r"nonexistent_pattern",
            replacement="something",
            scope="*.py",
            preview=False
        )

        # Assert: Empty result
        assert result.success is True
        assert result.changes_count == 0
        assert len(result.affected_files) == 0
        assert result.unified_diff == ""

    def test_glob_scope_filtering(self, tmp_path):
        """测试glob scope过滤

        Given mix of .py and .js files
        When batch_edit(scope="*.py")
        Then only .py files modified
        """
        from evolvai.tools.batch_editor import BatchEditor

        # Setup: Create mix of file types
        py_file = tmp_path / "test.py"
        py_file.write_text("value = 1\n")

        js_file = tmp_path / "test.js"
        js_file.write_text("value = 1\n")

        # Execute: batch_edit with *.py scope
        editor = BatchEditor(project_root=tmp_path)
        result = editor.batch_edit(
            pattern=r"value",
            replacement="result",
            scope="*.py",
            preview=False
        )

        # Assert: Only .py file modified
        assert result.success is True
        assert len(result.affected_files) == 1
        assert result.affected_files[0].suffix == ".py"

        # Verify .js file unchanged
        assert "value" in js_file.read_text()
        assert "result" not in js_file.read_text()

    def test_invalid_regex_pattern_handling(self, tmp_path):
        """测试无效正则表达式处理

        Given invalid regex pattern
        When batch_edit()
        Then error raised with helpful message
        And success=False
        """
        from evolvai.tools.batch_editor import BatchEditor

        # Setup: Create test file
        file = tmp_path / "test.py"
        file.write_text("test content\n")

        # Execute: batch_edit with invalid regex
        editor = BatchEditor(project_root=tmp_path)
        result = editor.batch_edit(
            pattern=r"[invalid(regex",  # Invalid regex
            replacement="something",
            scope="*.py",
            preview=False
        )

        # Assert: Error handled
        assert result.success is False
        assert "regex" in result.error_message.lower() or "pattern" in result.error_message.lower()
        assert result.changes_count == 0
