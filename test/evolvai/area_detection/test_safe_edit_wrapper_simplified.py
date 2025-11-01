"""
简化版SafeEditWrapper测试 - 遵循KISS原则
专注核心功能验证，避免过度复杂的mock
"""

from unittest.mock import Mock, patch

from evolvai.area_detection.edit_wrapper import SafeEditWrapper


class TestSafeEditWrapperSimplified:
    """简化版SafeEditWrapper测试 - 专注核心功能"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        assert wrapper.agent == mock_agent
        assert wrapper.project == mock_project
        assert wrapper.area_detector is not None

    def test_safe_edit_basic_success(self):
        """测试基本编辑成功流程"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        # 简化mock，只关注核心流程
        with patch.object(wrapper, '_get_project_areas') as mock_areas, \
             patch.object(wrapper, '_detect_language') as mock_lang, \
             patch.object(wrapper, '_read_file') as mock_read, \
             patch.object(wrapper, '_execute_validation_chain') as mock_validate, \
             patch.object(wrapper, '_create_rollback_point') as mock_backup:

            # 基本mock设置
            mock_areas.return_value = ([], [])
            mock_lang.return_value = "python"
            mock_read.return_value = "original content"
            mock_validate.return_value = {'is_valid': True, 'warnings': []}
            mock_backup.return_value = {
                'success': True,
                'backup_path': '/tmp/test-project/test.py.backup'
            }

            result = wrapper.safe_edit(
                file_path="test.py",
                content="print('hello')",
                mode="safe"
            )

            # 验证核心结果
            assert result["success"]
            assert result["file_path"] == "test.py"
            assert result["mode"] == "safe"
            assert result["rollback_info"]["backup_path"] == "/tmp/test-project/test.py.backup"

    def test_safe_edit_validation_failure(self):
        """测试编辑验证失败"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with patch.object(wrapper, '_get_project_areas') as mock_areas, \
             patch.object(wrapper, '_detect_language') as mock_lang, \
             patch.object(wrapper, '_read_file') as mock_read, \
             patch.object(wrapper, '_execute_validation_chain') as mock_validate:

            mock_areas.return_value = ([], [])
            mock_lang.return_value = "python"
            mock_read.return_value = "original content"

            # 验证失败
            mock_validate.return_value = {
                'is_valid': False,
                'error_message': 'Test validation error',
                'warnings': []
            }

            result = wrapper.safe_edit(
                file_path="test.py",
                content="invalid content",
                mode="safe"
            )

            # 验证失败结果
            assert not result["success"]
            assert "Test validation error" in result["error"]

    def test_edit_statistics_tracking(self):
        """测试编辑统计跟踪"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        # 初始统计
        stats = wrapper.get_edit_statistics()
        assert stats["total_edits"] == 0

        # 模拟成功编辑
        with patch.object(wrapper, '_get_project_areas') as mock_areas, \
             patch.object(wrapper, '_detect_language') as mock_lang, \
             patch.object(wrapper, '_read_file') as mock_read, \
             patch.object(wrapper, '_execute_validation_chain') as mock_validate, \
             patch.object(wrapper, '_create_rollback_point') as mock_backup:

            mock_areas.return_value = ([], [])
            mock_lang.return_value = "python"
            mock_read.return_value = "original content"
            mock_validate.return_value = {'is_valid': True, 'warnings': []}
            mock_backup.return_value = {'success': True, 'backup_path': '/tmp/backup'}

            wrapper.safe_edit("test.py", "print('hello')", "safe")

            # 验证统计更新
            stats = wrapper.get_edit_statistics()
            assert stats["total_edits"] == 1
            assert stats["successful_edits"] == 1

    def test_language_detection_integration(self):
        """测试语言检测集成"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with patch.object(wrapper, '_get_project_areas') as mock_areas, \
             patch.object(wrapper, '_detect_language') as mock_lang, \
             patch.object(wrapper, '_read_file') as mock_read, \
             patch.object(wrapper, '_execute_validation_chain') as mock_validate, \
             patch.object(wrapper, '_create_rollback_point') as mock_backup:

            mock_areas.return_value = ([], [])
            mock_lang.return_value = "javascript"  # 检测到JavaScript
            mock_read.return_value = "original content"
            mock_validate.return_value = {'is_valid': True, 'warnings': []}
            mock_backup.return_value = {'success': True, 'backup_path': '/tmp/backup'}

            wrapper.safe_edit(
                file_path="app.js",
                content="console.log('hello');",
                mode="safe"
            )

            # 验证语言检测被调用
            mock_lang.assert_called_once_with("app.js", "console.log('hello');")

    def test_error_handling(self):
        """测试错误处理"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        # 模拟读取文件异常
        with patch.object(wrapper, '_get_project_areas') as mock_areas, \
             patch.object(wrapper, '_detect_language') as mock_lang, \
             patch.object(wrapper, '_read_file') as mock_read:

            mock_areas.return_value = ([], [])
            mock_lang.return_value = "python"
            mock_read.side_effect = FileNotFoundError("File not found")

            result = wrapper.safe_edit(
                file_path="nonexistent.py",
                content="content",
                mode="safe"
            )

            # 验证错误处理
            assert not result["success"]
            assert "File not found" in result["error"]