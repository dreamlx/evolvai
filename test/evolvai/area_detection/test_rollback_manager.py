"""
测试RollbackManager的回滚管理功能
"""

from unittest.mock import patch

from evolvai.area_detection.rollback_manager import RollbackManager, RollbackResult, RollbackStrategy


class TestRollbackManager:
    """测试RollbackManager的核心功能"""

    def test_git_rollback_success(self):
        """测试Git回滚成功"""
        manager = RollbackManager()

        with patch('subprocess.run') as mock_subprocess:
            # 模拟git命令成功执行
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = "HEAD is now at abc123"

            result = manager.git_rollback(
                commit_hash="abc123",
                message="Test rollback"
            )

            assert result.success
            assert result.strategy == RollbackStrategy.GIT
            assert "abc123" in result.message
            assert result.rollback_hash == "abc123"

    def test_git_rollback_failure(self):
        """测试Git回滚失败"""
        manager = RollbackManager()

        with patch('subprocess.run') as mock_subprocess:
            # 模拟git命令失败
            mock_subprocess.return_value.returncode = 1
            mock_subprocess.return_value.stderr = "fatal: not a git repository"

            result = manager.git_rollback(
                commit_hash="abc123",
                message="Test rollback"
            )

            assert not result.success
            assert result.strategy == RollbackStrategy.GIT
            assert "not a git repository" in result.error_message

    def test_file_backup_rollback_success(self):
        """测试文件备份回滚成功"""
        manager = RollbackManager()

        with patch('os.path.exists') as mock_exists, \
             patch('shutil.copy2') as mock_copy, \
             patch('os.remove') as mock_remove:

            # 模拟备份文件存在
            mock_exists.return_value = True

            result = manager.file_backup_rollback(
                file_path="/test/file.py",
                backup_path="/test/file.py.backup"
            )

            assert result.success
            assert result.strategy == RollbackStrategy.FILE_BACKUP
            assert mock_copy.called
            assert mock_remove.called

    def test_file_backup_rollback_no_backup_file(self):
        """测试文件备份回滚 - 备份文件不存在"""
        manager = RollbackManager()

        with patch('os.path.exists') as mock_exists:
            # 模拟备份文件不存在
            mock_exists.return_value = False

            result = manager.file_backup_rollback(
                file_path="/test/file.py",
                backup_path="/test/file.py.backup"
            )

            assert not result.success
            assert result.strategy == RollbackStrategy.FILE_BACKUP
            assert "backup file not found" in result.error_message.lower()

    def test_create_backup_before_edit(self):
        """测试编辑前创建备份"""
        manager = RollbackManager()

        with patch('os.path.exists') as mock_exists, \
             patch('shutil.copy2') as mock_copy, \
             patch('os.makedirs') as mock_makedirs:

            mock_exists.return_value = True

            backup_path = manager.create_backup(
                file_path="/test/project/src/main.py"
            )

            assert backup_path.endswith(".backup")
            assert "main.py.backup" in backup_path
            assert mock_copy.called
            assert mock_makedirs.called

    def test_create_backup_directory_creation(self):
        """测试创建备份时的目录创建"""
        manager = RollbackManager()

        with patch('os.path.exists') as mock_exists, \
             patch('shutil.copy2') as mock_copy, \
             patch('os.makedirs') as mock_makedirs:

            # 模拟目录不存在
            def exists_side_effect(path):
                if ".backup" in path:
                    return False
                return True

            mock_exists.side_effect = exists_side_effect

            backup_path = manager.create_backup(
                file_path="/test/project/src/main.py"
            )

            assert backup_path.endswith(".backup")
            assert mock_makedirs.called

    def test_multiple_file_rollback_success(self):
        """测试多文件回滚成功"""
        manager = RollbackManager()

        files_to_rollback = [
            {"file": "/test/file1.py", "backup": "/test/file1.py.backup"},
            {"file": "/test/file2.py", "backup": "/test/file2.py.backup"}
        ]

        with patch.object(manager, 'file_backup_rollback') as mock_rollback:
            # 模拟所有回滚都成功
            mock_rollback.side_effect = [
                RollbackResult(success=True, strategy=RollbackStrategy.FILE_BACKUP),
                RollbackResult(success=True, strategy=RollbackStrategy.FILE_BACKUP)
            ]

            results = manager.multiple_file_rollback(files_to_rollback)

            assert len(results) == 2
            assert all(result.success for result in results)
            assert mock_rollback.call_count == 2

    def test_multiple_file_rollback_partial_failure(self):
        """测试多文件回滚部分失败"""
        manager = RollbackManager()

        files_to_rollback = [
            {"file": "/test/file1.py", "backup": "/test/file1.py.backup"},
            {"file": "/test/file2.py", "backup": "/test/file2.py.backup"}
        ]

        with patch.object(manager, 'file_backup_rollback') as mock_rollback:
            # 模拟第一个成功，第二个失败
            mock_rollback.side_effect = [
                RollbackResult(success=True, strategy=RollbackStrategy.FILE_BACKUP),
                RollbackResult(success=False, strategy=RollbackStrategy.FILE_BACKUP,
                             error_message="Backup not found")
            ]

            results = manager.multiple_file_rollback(files_to_rollback)

            assert len(results) == 2
            assert results[0].success
            assert not results[1].success
            assert "Backup not found" in results[1].error_message

    def test_smart_rollback_strategy_selection(self):
        """测试智能回滚策略选择"""
        manager = RollbackManager()

        # 测试Git仓库环境选择Git策略
        with patch.object(manager, '_is_git_repo') as mock_git_check, \
             patch.object(manager, 'git_rollback') as mock_git_rollback:

            mock_git_check.return_value = True
            mock_git_rollback.return_value = RollbackResult(success=True, strategy=RollbackStrategy.GIT)

            result = manager.smart_rollback(
                file_path="/test/file.py"
            )

            assert result.success
            mock_git_check.assert_called_once()
            mock_git_rollback.assert_called_once()

    def test_cleanup_old_backups(self):
        """测试清理旧备份文件"""
        manager = RollbackManager()

        with patch('glob.glob') as mock_glob, \
             patch('os.path.getmtime') as mock_getmtime, \
             patch('os.remove') as mock_remove:

            # 模拟找到多个备份文件
            backup_files = [
                "/test/file1.py.backup",
                "/test/file2.py.backup",
                "/test/file3.py.backup"
            ]
            mock_glob.return_value = backup_files

            # 模拟文件时间，file3.py.backup是最旧的
            mock_getmtime.side_effect = [1000, 2000, 500]

            manager.cleanup_old_backups(
                backup_dir="/test",
                max_backups=2
            )

            # 应该删除最旧的文件
            mock_remove.assert_called_once_with("/test/file3.py.backup")
