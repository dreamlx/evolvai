"""
测试SafeExecWrapper的安全执行功能
遵循KISS原则：专注行为验证，避免过度设计
"""

from unittest.mock import Mock, patch

from evolvai.area_detection.data_models import ExecutionPrecondition, ExecutionResult, ExecutionRiskLevel


class TestPreconditionChecker:
    """测试前置条件检查器 - 专注业务逻辑验证"""

    def test_safe_command_passes_check(self):
        """测试安全命令通过前置检查"""
        # 用户故事：用户可以执行安全的系统命令

        from evolvai.area_detection.exec_validator import PreconditionChecker

        checker = PreconditionChecker()

        # 模拟安全命令
        with patch('os.access', return_value=True), \
             patch('shutil.which', return_value='/bin/ls'), \
             patch('os.path.exists', return_value=True):

            precondition = ExecutionPrecondition(
                command="ls -la",
                working_directory="/tmp",
                timeout_seconds=30,
                required_permissions=["read"],
                system_dependencies=["ls"],
                environment_variables={},
                risk_level=ExecutionRiskLevel.LOW
            )

            result = checker.validate(precondition)

            assert result.is_valid
            assert len(result.errors) == 0

    def test_dangerous_command_blocked(self):
        """测试危险命令被阻止"""
        # 用户故事：系统阻止删除重要文件的命令

        from evolvai.area_detection.exec_validator import PreconditionChecker

        checker = PreconditionChecker()

        # 模拟危险命令
        precondition = ExecutionPrecondition(
            command="rm -rf /",
            working_directory="/",
            timeout_seconds=60,
            required_permissions=["write"],
            system_dependencies=["rm"],
            environment_variables={},
            risk_level=ExecutionRiskLevel.CRITICAL
        )

        result = checker.validate(precondition)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("dangerous" in error.lower() for error in result.errors)

    def test_missing_dependency_detected(self):
        """测试依赖缺失被检测"""
        # 用户故事：系统检测到命令依赖不存在时给出明确错误

        from evolvai.area_detection.exec_validator import PreconditionChecker

        checker = PreconditionChecker()

        # 模拟依赖缺失
        with patch('shutil.which', return_value=None):
            precondition = ExecutionPrecondition(
                command="nonexistent-command",
                working_directory="/tmp",
                timeout_seconds=30,
                required_permissions=[],
                system_dependencies=["nonexistent-command"],
                environment_variables={},
                risk_level=ExecutionRiskLevel.MEDIUM
            )

            result = checker.validate(precondition)

            assert not result.is_valid
            assert any("dependency" in error.lower() for error in result.errors)

    def test_permission_denied_handled_gracefully(self):
        """测试权限不足被优雅处理"""
        from evolvai.area_detection.exec_validator import PreconditionChecker

        checker = PreconditionChecker()

        # 模拟权限不足
        with patch('os.access', return_value=False):
            precondition = ExecutionPrecondition(
                command="cat /etc/shadow",
                working_directory="/",
                timeout_seconds=30,
                required_permissions=["read"],
                system_dependencies=["cat"],
                environment_variables={},
                risk_level=ExecutionRiskLevel.HIGH
            )

            result = checker.validate(precondition)

            assert not result.is_valid
            assert any("permission" in error.lower() for error in result.errors)


class TestProcessManager:
    """测试进程管理器 - 专注进程生命周期管理"""

    def test_process_group_management(self):
        """测试进程组管理"""
        # 用户故事：系统能够正确管理进程组

        from evolvai.area_detection.exec_manager import ProcessManager

        manager = ProcessManager()

        # 模拟成功的进程创建
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None

        with patch('subprocess.Popen', return_value=mock_process), \
             patch('os.getpgid', return_value=12345):

            process_info = manager.create_process(
                command="echo hello",
                working_directory="/tmp"
            )

            # 验证进程信息正确设置
            assert process_info.pid == 12345
            assert process_info.pgid == 12345
            assert process_info.command == "echo hello"
            assert process_info.is_running is True
            assert process_info.start_time > 0

    def test_timeout_kills_all_children(self):
        """测试超时时杀死所有子进程"""
        # 用户故事：超时时系统能够清理所有相关进程

        from evolvai.area_detection.exec_manager import ProcessManager

        manager = ProcessManager()

        # 模拟超时场景
        with patch('subprocess.TimeoutExpired'), \
             patch('os.killpg') as mock_killpg, \
             patch('time.sleep'):

            result = manager.wait_with_timeout(
                process_info=Mock(pgid=12345),
                timeout_seconds=0.001  # 强制超时
            )

            # 验证超时结果
            assert result.timeout_occurred is True
            assert result.success is False
            assert "timed out" in result.stderr  # 验证包含超时信息
            # 验证尝试了杀死进程组（不管具体调用次数）
            assert mock_killpg.call_count > 0

    def test_cleanup_on_failure(self):
        """测试失败时的清理"""
        # 用户故事：进程异常时系统能够清理资源

        from evolvai.area_detection.exec_manager import ProcessManager

        manager = ProcessManager()

        # 模拟进程异常退出
        with patch('os.killpg') as mock_killpg:
            process_info = Mock(pgid=12345, is_running=True)
            manager.cleanup_process(process_info)

            # 验证尝试了清理（不管具体调用次数）
            assert mock_killpg.call_count > 0


class TestSafeExecWrapper:
    """测试SafeExecWrapper集成功能"""

    def test_safe_exec_success_flow(self):
        """测试安全执行成功流程"""
        # 用户故事：用户可以通过safe_exec安全执行命令

        from evolvai.area_detection.exec_wrapper import SafeExecWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeExecWrapper(mock_agent, mock_project)

        # 模拟成功的执行流程
        with patch.object(wrapper, '_check_preconditions') as mock_check, \
             patch.object(wrapper, '_execute_command') as mock_exec, \
             patch.object(wrapper, '_log_execution') as mock_log:

            mock_check.return_value = Mock(is_valid=True)
            mock_exec.return_value = ExecutionResult(
                success=True,
                exit_code=0,
                stdout="hello world",
                stderr="",
                duration_ms=50.0,
                precondition_passed=True,
                command="echo hello",
                working_directory="/tmp"
            )

            result = wrapper.safe_exec(
                command="echo hello",
                working_directory="/tmp",
                timeout_seconds=30
            )

            assert result.success
            assert result.exit_code == 0
            assert "hello world" in result.stdout
            mock_log.assert_called_once()

    def test_precondition_failure_blocks_execution(self):
        """测试前置条件失败阻止执行"""
        from evolvai.area_detection.exec_wrapper import SafeExecWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeExecWrapper(mock_agent, mock_project)

        # 模拟前置条件检查失败
        with patch.object(wrapper, '_check_preconditions') as mock_check:
            mock_check.return_value = Mock(is_valid=False, errors=["Dangerous command"])

            result = wrapper.safe_exec(
                command="rm -rf /",
                working_directory="/",
                timeout_seconds=60
            )

            assert not result.success
            assert not result.precondition_passed
            assert "Dangerous command" in result.error_message

    def test_audit_logging_integrated(self):
        """测试审计日志集成"""
        # 用户故事：所有命令执行都被记录到审计日志

        from evolvai.area_detection.exec_wrapper import SafeExecWrapper

        mock_agent = Mock()
        mock_project = Mock()
        mock_project.root_path = "/tmp/test-project"

        wrapper = SafeExecWrapper(mock_agent, mock_project)

        # 模拟审计日志记录
        with patch.object(wrapper, '_check_preconditions') as mock_check, \
             patch.object(wrapper, '_execute_command') as mock_exec, \
             patch.object(wrapper.agent, 'execution_engine') as mock_engine:

            mock_check.return_value = Mock(is_valid=True)
            mock_exec.return_value = ExecutionResult(
                success=True,
                exit_code=0,
                stdout="success",
                stderr="",
                duration_ms=100.0,
                precondition_passed=True,
                command="ls",
                working_directory="/tmp"
            )

            wrapper.safe_exec(command="ls", working_directory="/tmp")

            # 验证审计日志被调用
            assert mock_engine.log_execution.called
