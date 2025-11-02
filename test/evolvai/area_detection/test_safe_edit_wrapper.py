"""
测试SafeEditWrapper的安全编辑功能
"""

from unittest.mock import Mock, patch

import pytest

from evolvai.area_detection.data_models import ProjectArea


class TestSafeEditWrapper:
    """测试SafeEditWrapper的核心功能"""

    def test_safe_edit_execution_success(self):
        """测试安全编辑执行成功"""
        from evolvai.area_detection.edit_wrapper import SafeEditWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        # 模拟编辑成功的场景
        with patch.object(wrapper, '_get_project_areas') as mock_areas, \
             patch.object(wrapper, '_detect_language') as mock_lang, \
             patch.object(wrapper, '_read_file') as mock_read, \
             patch.object(wrapper, '_execute_validation_chain') as mock_validate, \
             patch.object(wrapper, '_create_rollback_point') as mock_backup, \
             patch.object(wrapper.agent, 'execution_engine') as mock_engine:

            # Mock项目区域检测
            mock_areas.return_value = ([], [])
            mock_lang.return_value = "go"
            mock_read.return_value = "original content"

            # 所有验证都通过
            mock_validate.return_value = {
                'is_valid': True,
                'validation_result': Mock(is_valid=True),
                'warnings': []
            }

            # Mock回滚点创建
            mock_backup.return_value = {
                'success': True,
                'backup_path': '/tmp/test-project/file.py.backup'
            }

            mock_engine.execute.return_value = Mock(
                success=True,
                message="Edit successful",
                modified_files=1
            )

            result = wrapper.safe_edit(
                file_path="backend/user.go",
                content="package main\n\nfunc getUserData() string {\n    return \"user\"\n}",
                mode="safe"
            )

            assert result["success"]
            assert result["file_path"] == "backend/user.go"
            assert result["mode"] == "safe"
            assert result["rollback_info"]["backup_path"] == "/tmp/test-project/file.py.backup"

    def test_safe_edit_pre_validation_failure(self):
        """测试编辑前验证失败"""
        from evolvai.area_detection.edit_validator import EditValidationError
        from evolvai.area_detection.edit_wrapper import SafeEditWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with patch.object(wrapper, '_validate_edit') as mock_validate:
            # 验证失败
            mock_validate.side_effect = EditValidationError(
                error_type="syntax_error",
                message="Invalid Go syntax",
                file_path="bad.go"
            )

            with pytest.raises(EditValidationError) as exc_info:
                wrapper.safe_edit(
                    file_path="bad.go",
                    content="invalid go code",
                    mode="safe"
                )

            assert exc_info.value.error_type == "syntax_error"
            assert "Invalid Go syntax" in str(exc_info.value)

    def test_safe_edit_constraint_violation_handling(self):
        """测试编辑约束违规处理"""
        from evolvai.area_detection.edit_wrapper import SafeEditWrapper
        from evolvai.core.constraint_exceptions import ChangeLimitExceededError

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with patch.object(wrapper, '_validate_edit') as mock_validate, \
             patch.object(wrapper, '_create_backup') as mock_backup, \
             patch.object(wrapper.agent, 'execution_engine') as mock_engine:

            # 前期验证通过，但执行时遇到约束违规
            mock_validate.return_value = Mock(is_valid=True)
            mock_backup.return_value = "/tmp/test-project/file.py.backup"
            mock_engine.execute.side_effect = ChangeLimitExceededError(
                "Too many changes",
                changes_made=150,
                max_changes=100
            )

            with pytest.raises(ChangeLimitExceededError):
                wrapper.safe_edit(
                    file_path="large_file.py",
                    content="large edit content",
                    mode="safe",
                    max_changes=100
                )

    def test_safe_edit_post_validation_rollback(self):
        """测试编辑后验证失败触发回滚"""
        from evolvai.area_detection.edit_validator import EditValidationError
        from evolvai.area_detection.edit_wrapper import SafeEditWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with patch.object(wrapper, '_validate_edit') as mock_pre_validate, \
             patch.object(wrapper, '_create_backup') as mock_backup, \
             patch.object(wrapper.agent, 'execution_engine') as mock_engine, \
             patch.object(wrapper, '_validate_edit_result') as mock_post_validate, \
             patch.object(wrapper.rollback_manager, 'file_backup_rollback') as mock_rollback:

            # 前期验证和执行都成功，但后验证失败
            mock_pre_validate.return_value = Mock(is_valid=True)
            mock_backup.return_value = "/tmp/test-project/file.py.backup"
            mock_engine.execute.return_value = "Edit completed"
            mock_post_validate.side_effect = EditValidationError(
                error_type="logic_error",
                message="Edit broke existing functionality"
            )
            mock_rollback.return_value = Mock(success=True)

            with pytest.raises(EditValidationError) as exc_info:
                wrapper.safe_edit(
                    file_path="test.py",
                    content="broken edit",
                    mode="safe"
                )

            assert exc_info.value.error_type == "logic_error"
            # 验证回滚被调用
            mock_rollback.assert_called_once()

    def test_safe_edit_area_aware_execution(self):
        """测试区域感知编辑执行"""
        from evolvai.area_detection.edit_wrapper import SafeEditWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with patch.object(wrapper.area_detector, 'detect_areas') as mock_detect, \
             patch.object(wrapper, '_validate_edit') as mock_validate, \
             patch.object(wrapper.agent, 'execution_engine') as mock_engine, \
             patch.object(wrapper, '_validate_edit_result') as mock_post_validate:

            # 模拟检测到backend-go区域
            areas = [
                ProjectArea(
                    name="backend-go",
                    language="go",
                    confidence="High",
                    evidence=["go.mod"],
                    file_patterns=["*.go"],
                    root_path="/tmp/test-project"
                )
            ]
            mock_detect.return_value = areas
            mock_validate.return_value = Mock(is_valid=True, affected_areas=["backend-go"])
            mock_engine.execute.return_value = "Edit successful"
            mock_post_validate.return_value = Mock(is_valid=True)

            result = wrapper.safe_edit(
                file_path="backend/auth.go",
                content="package main\n\nfunc authenticate() bool { return true }",
                area_selector="backend-go",
                mode="safe"
            )

            assert result["success"]
            assert "backend-go" in result["affected_areas"]
            assert result["area_selector"] == "backend-go"

    def test_safe_edit_mode_validation(self):
        """测试编辑模式验证"""
        from evolvai.area_detection.edit_wrapper import SafeEditWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with patch.object(wrapper, '_validate_edit') as mock_validate, \
             patch.object(wrapper, '_create_backup') as mock_backup, \
             patch.object(wrapper.agent, 'execution_engine') as mock_engine, \
             patch.object(wrapper, '_validate_edit_result') as mock_post_validate:

            mock_validate.return_value = Mock(is_valid=True)
            mock_backup.return_value = "/tmp/test-project/file.py.backup"
            mock_engine.execute.return_value = "Edit successful"
            mock_post_validate.return_value = Mock(is_valid=True)

            # 测试conservative模式（最严格）
            result = wrapper.safe_edit(
                file_path="file.py",
                content="conservative edit",
                mode="conservative",
                max_changes=5,
                max_lines_added=10
            )

            assert result["success"]
            assert result["mode"] == "conservative"
            assert result["constraints"]["max_changes"] == 5

            # 测试aggressive模式（较宽松）
            result = wrapper.safe_edit(
                file_path="file.py",
                content="aggressive edit",
                mode="aggressive"
            )

            assert result["success"]
            assert result["mode"] == "aggressive"

    def test_safe_edit_batch_operations(self):
        """测试批量编辑操作"""
        from evolvai.area_detection.edit_wrapper import SafeEditWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        batch_edits = [
            {
                "file_path": "file1.py",
                "content": "edit 1",
                "mode": "safe"
            },
            {
                "file_path": "file2.py",
                "content": "edit 2",
                "mode": "safe"
            }
        ]

        with patch.object(wrapper, 'safe_edit') as mock_safe_edit:
            # 模拟所有编辑都成功
            mock_safe_edit.side_effect = [
                {"success": True, "message": "Edit 1 successful"},
                {"success": True, "message": "Edit 2 successful"}
            ]

            results = wrapper.safe_edit_batch(batch_edits)

            assert len(results) == 2
            assert all(result["success"] for result in results)
            assert mock_safe_edit.call_count == 2

    def test_safe_edit_execution_plan_integration(self):
        """测试与Story 1.3 ExecutionPlan集成"""
        from evolvai.area_detection.edit_wrapper import SafeEditWrapper
        from evolvai.core.execution_plan import ExecutionLimits, ExecutionPlan, RollbackStrategy, RollbackStrategyType

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        execution_plan = ExecutionPlan(
            description="Test edit with constraints",
            tool_name="safe_edit",
            limits=ExecutionLimits(max_changes=50, max_files=10, timeout_seconds=60),
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT)
        )

        with patch.object(wrapper, '_validate_edit') as mock_validate, \
             patch.object(wrapper, '_create_backup') as mock_backup, \
             patch.object(wrapper.agent, 'execution_engine') as mock_engine, \
             patch.object(wrapper, '_validate_edit_result') as mock_post_validate:

            mock_validate.return_value = Mock(is_valid=True)
            mock_backup.return_value = "/tmp/test-project/file.py.backup"
            mock_engine.execute.return_value = "Edit successful"
            mock_post_validate.return_value = Mock(is_valid=True)

            result = wrapper.safe_edit(
                file_path="test.py",
                content="test edit with execution plan",
                execution_plan=execution_plan
            )

            assert result["success"]
            assert "execution_plan" in result
            assert result["execution_plan"]["description"] == "Test edit with constraints"

            # 验证ExecutionPlan被传递给执行引擎
            mock_engine.execute.assert_called_once()
            call_kwargs = mock_engine.execute.call_args[1]
            assert "execution_plan" in call_kwargs
            assert call_kwargs["execution_plan"] == execution_plan

    def test_safe_edit_mcp_interface(self):
        """测试MCP接口兼容性"""
        from evolvai.area_detection.edit_wrapper import SafeEditWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with patch.object(wrapper, 'safe_edit') as mock_safe_edit:
            mock_safe_edit.return_value = {
                "success": True,
                "message": "Edit completed",
                "affected_areas": ["backend-go"],
                "backup_path": "/tmp/test-project/file.py.backup"
            }

            # 测试MCP标准的参数格式
            result = wrapper.safe_edit_mcp(
                file_path="backend/user.go",
                content="package main\n\nfunc getUserData() string { return \"user\" }",
                mode="safe",
                area_selector="backend-go",
                max_changes=20,
                timeout_seconds=30,
                create_backup=True,
                validate_result=True
            )

            assert result["success"]
            assert "affected_areas" in result
            assert "backup_path" in result

            # 验证参数正确传递
            mock_safe_edit.assert_called_once()
            call_args = mock_safe_edit.call_args[1]
            assert call_args["mode"] == "safe"
            assert call_args["area_selector"] == "backend-go"
            assert call_args["max_changes"] == 20
            assert call_args["create_backup"] is True
