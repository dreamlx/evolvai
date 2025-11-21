"""
简化版SafeEditWrapper测试 - Story 2.2版本
专注核心功能：原子性写入 + 自动回滚安全网
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
        """测试基本编辑成功流程 - Story 2.2简化版"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        # 简化mock - 只mock核心IO操作
        with (
            patch.object(wrapper, "_read_file") as mock_read,
            patch.object(wrapper, "_write_file") as mock_write,
            patch.object(wrapper, "_create_rollback_point") as mock_backup,
        ):

            # 基本mock设置
            mock_read.return_value = "original content"
            mock_write.return_value = {"success": True}
            mock_backup.return_value = {
                "success": True,
                "strategy": "file_backup",
                "rollback_hash": "abc123",
                "message": "Backup created",
                "error": None,
                "duration_ms": 5.0,
            }

            result = wrapper.safe_edit(file_path="test.py", content="print('hello')", auto_rollback=True)

            # 验证核心结果
            assert result["success"]
            assert result["file_path"] == "test.py"
            assert result["rollback_id"] == "abc123"
            assert result["duration_ms"] > 0

    def test_safe_edit_write_failure_triggers_rollback(self):
        """测试写入失败时触发自动回滚"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with (
            patch.object(wrapper, "_read_file") as mock_read,
            patch.object(wrapper, "_write_file") as mock_write,
            patch.object(wrapper, "_create_rollback_point") as mock_backup,
            patch.object(wrapper, "_execute_rollback") as mock_rollback,
        ):

            mock_read.return_value = "original content"
            mock_write.return_value = {"success": False, "error": "Write failed: Permission denied"}
            mock_backup.return_value = {
                "success": True,
                "strategy": "file_backup",
                "rollback_hash": "abc123",
                "message": "Backup created",
                "error": None,
                "duration_ms": 5.0,
            }

            result = wrapper.safe_edit(file_path="test.py", content="invalid content", auto_rollback=True)

            # 验证失败结果
            assert not result["success"]
            assert "Write failed" in result["error"]

            # 验证自动回滚被调用
            mock_rollback.assert_called_once()

    def test_safe_edit_without_auto_rollback(self):
        """测试禁用自动回滚的编辑"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with (
            patch.object(wrapper, "_read_file") as mock_read,
            patch.object(wrapper, "_write_file") as mock_write,
            patch.object(wrapper, "_create_rollback_point") as mock_backup,
        ):

            mock_read.return_value = "original content"
            mock_write.return_value = {"success": True}

            result = wrapper.safe_edit(file_path="test.py", content="print('hello')", auto_rollback=False)  # 禁用回滚

            # 验证成功
            assert result["success"]
            assert result["rollback_id"] is None  # 没有创建回滚点

            # 验证没有调用创建回滚点
            mock_backup.assert_not_called()

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
        with (
            patch.object(wrapper, "_read_file") as mock_read,
            patch.object(wrapper, "_write_file") as mock_write,
            patch.object(wrapper, "_create_rollback_point") as mock_backup,
        ):

            mock_read.return_value = "original content"
            mock_write.return_value = {"success": True}
            mock_backup.return_value = {
                "success": True,
                "strategy": "file_backup",
                "rollback_hash": "abc123",
                "message": "Backup created",
                "error": None,
                "duration_ms": 5.0,
            }

            wrapper.safe_edit("test.py", "print('hello')", auto_rollback=True)

            # 验证统计更新
            stats = wrapper.get_edit_statistics()
            assert stats["total_edits"] == 1
            assert stats["successful_edits"] == 1
            assert stats["success_rate"] == 1.0

    def test_safe_edit_batch(self):
        """测试批量编辑功能"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        with (
            patch.object(wrapper, "_read_file") as mock_read,
            patch.object(wrapper, "_write_file") as mock_write,
            patch.object(wrapper, "_create_rollback_point") as mock_backup,
        ):

            mock_read.return_value = "original content"
            mock_write.return_value = {"success": True}
            mock_backup.return_value = {
                "success": True,
                "strategy": "file_backup",
                "rollback_hash": "abc123",
                "message": "Backup created",
                "error": None,
                "duration_ms": 5.0,
            }

            edits = [
                {"file_path": "test1.py", "content": "print('1')"},
                {"file_path": "test2.py", "content": "print('2')"},
            ]

            result = wrapper.safe_edit_batch(edits, stop_on_error=True)

            # 验证批量结果
            assert result["success"]
            assert result["total_edits"] == 2
            assert result["successful_edits"] == 2
            assert len(result["results"]) == 2

    def test_error_handling(self):
        """测试错误处理"""
        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeEditWrapper(mock_agent, mock_project)

        # 模拟读取文件异常
        with patch.object(wrapper, "_read_file") as mock_read:
            mock_read.side_effect = Exception("File read error")

            result = wrapper.safe_edit(file_path="nonexistent.py", content="content", auto_rollback=True)

            # 验证错误处理
            assert not result["success"]
            assert "File read error" in result["error"]
            assert result["duration_ms"] > 0
