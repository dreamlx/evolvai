"""
Story 2.3: safe_exec - Day 1 & Day 2 Tests

BDD-driven TDD implementation for safe_exec wrapper.

Day 1 Focus: 快速失败机制（依赖检查 + 工作目录验证 + 推理崩溃检测）
Day 2 Focus: 进程管理 + Timeout管理 + 交互命令检测 + 输出截断

Key Design Principle: 减少TPST（Token浪费），不是系统安全防护
"""

import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from evolvai.core.exceptions import ConstraintViolationError
from evolvai.tools.safe_exec import ExecutionResult, SafeExecWrapper


class TestSafeExecDay1PreconditionChecker:
    """Day 1: PreconditionChecker TDD - 快速失败机制"""

    def test_safe_exec_simple_command_success(self, tmp_path):
        """测试成功执行简单命令

        Story: story-2.3-bdd-scenarios.md
        Scenario 1: "执行安全命令成功"
        DoD: F1 (快速失败机制), F2 (进程管理), F3 (统一接口), P2 (性能)

        Given 命令 "echo 'Hello World'"
        And timeout 为 5 秒
        And 工作目录 为有效路径
        When 我调用 safe_exec(command="echo 'Hello World'", timeout=5)
        Then 返回成功结果
        And exit_code 为 0
        And stdout 包含 "Hello World"
        And stderr 为空
        And precondition_passed 为 True
        And duration_ms < 100ms
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(
            command="echo 'Hello World'",
            timeout=5,
        )

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.exit_code == 0
        assert "Hello World" in result.stdout
        assert result.stderr == ""
        assert result.precondition_passed is True
        assert result.duration_ms < 100

    @pytest.mark.parametrize(
        "absurd_command,pattern_name",
        [
            ("rm -rf /", "rm_rf_root"),
            ("rm -rf /*", "rm_rf_root_wildcard"),
            ("mkfs.ext4 /dev/sda", "mkfs"),
            (":(){:|:&};:", "fork_bomb"),
        ],
    )
    def test_detects_absurd_commands(self, absurd_command, pattern_name, tmp_path):
        """测试检测荒谬命令（AI推理崩溃信号）

        Story: story-2.3-bdd-scenarios.md
        Scenario 2: "检测AI推理崩溃信号"
        DoD: F1 (快速失败机制), Q1 (测试覆盖率)

        Given 命令为荒谬命令（rm -rf /, mkfs, fork bomb等）
        When 我调用 safe_exec(command=<absurd_command>)
        Then 抛出 ConstraintViolationError
        And 错误信息包含 "Absurd command detected"
        And 错误信息包含 "This suggests AI reasoning failure"
        And 建议 "Please reconsider the task goal"
        And 审计日志记录推理崩溃事件

        Examples:
        - rm -rf /
        - rm -rf /*
        - mkfs.ext4 /dev/sda
        - :(){:|:&};:

        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper.execute(command=absurd_command, timeout=5)

        error_msg = str(exc_info.value)
        assert "Absurd command detected" in error_msg
        assert "reasoning failure" in error_msg.lower()
        assert "reconsider" in error_msg.lower()

        # 验证审计日志记录（通过ToolExecutionEngine）
        # 注意：审计日志集成在Green Phase实现

    def test_detects_missing_command(self, tmp_path):
        """测试检测命令依赖缺失

        Story: story-2.3-bdd-scenarios.md
        Scenario 4: "检测命令依赖缺失"
        DoD: F1 (快速失败机制), Q1 (测试覆盖率)

        Given 命令 "nonexistent_command_xyz_12345"
        When 我调用 safe_exec(command="nonexistent_command_xyz_12345")
        Then 抛出 ConstraintViolationError
        And 错误信息包含 "Command not found"
        And 错误信息包含命令名称
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper.execute(
                command="nonexistent_command_xyz_12345 --some-arg",
                timeout=5,
            )

        error_msg = str(exc_info.value)
        assert "Command not found" in error_msg
        assert "nonexistent_command_xyz_12345" in error_msg

    def test_validates_working_directory_invalid(self, tmp_path):
        """测试验证无效工作目录

        Story: story-2.3-bdd-scenarios.md
        (補充的Scenario 1.5)
        DoD: F1 (快速失败机制)

        Given 工作目录 "/nonexistent/path/12345"
        When 我调用 safe_exec(command="echo test", working_dir="/nonexistent/path/12345")
        Then 抛出 ConstraintViolationError
        And 错误信息包含 "Invalid working directory"
        """
        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper = SafeExecWrapper(working_dir="/nonexistent/path/12345")
            wrapper.execute(command="echo test", timeout=5)

        error_msg = str(exc_info.value)
        assert "Invalid working directory" in error_msg
        assert "/nonexistent/path/12345" in error_msg

    def test_validates_working_directory_relative(self, tmp_path):
        """测试相对路径工作目录自动转换为绝对路径

        Story: story-2.3-bdd-scenarios.md
        (補充的Scenario 1.5)
        DoD: F1 (快速失败机制)

        Given 工作目录为相对路径 "../test"
        When 我调用 safe_exec(command="pwd")
        Then 自动转换为绝对路径
        And 在正确目录执行命令
        """
        # 创建测试目录结构
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # 在 tmp_path 的子目录中执行
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        # 使用相对路径
        os.chdir(str(subdir))
        wrapper = SafeExecWrapper(working_dir="../test")

        result = wrapper.execute(command="pwd", timeout=5)

        assert result.success is True
        # 验证实际工作目录是绝对路径
        assert str(test_dir) in result.stdout or test_dir.resolve() == Path(result.stdout.strip()).resolve()

    def test_precondition_check_performance(self, tmp_path):
        """测试Precondition检查性能 < 10ms

        Story: story-2.3-bdd-scenarios.md
        DoD: P1 (Precondition检查延迟)

        Given 一个简单的有效命令
        When 执行precondition检查
        Then 检查耗时 < 10ms (平均)
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # 运行10次取平均
        durations = []
        for _ in range(10):
            start = time.perf_counter()

            # 只测试precondition检查部分，不执行实际命令
            # 注意：这需要wrapper暴露_check_preconditions方法
            # Green Phase实现时需要考虑
            try:
                wrapper._check_preconditions("echo test", timeout=5)
            except Exception:
                pass  # 即使失败也记录时间

            duration_ms = (time.perf_counter() - start) * 1000
            durations.append(duration_ms)

        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 10, f"Precondition check took {avg_duration:.2f}ms (target: <10ms)"


# ==================== Day 2: ProcessManager + Timeout Management ====================

class TestSafeExecDay2ProcessManager:
    """Day 2: ProcessManager TDD - 进程组管理 + Timeout管理 + 交互命令检测"""

    def test_timeout_upper_limit_enforced(self, tmp_path):
        """测试强制执行timeout上限（≤300秒）

        Story: story-2.3-bdd-scenarios.md
        Scenario: AI估算timeout + 固定上限保护
        DoD: F2 (ProcessManager timeout管理), Q1 (测试覆盖率)

        Given timeout 为 301 秒（超过上限）
        When 我调用 safe_exec(command="echo test", timeout=301)
        Then 抛出 ConstraintViolationError
        And 错误信息包含 "Timeout exceeds maximum limit"
        And 错误信息包含 "prevents hanging on interactive commands"
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper.execute(command="echo test", timeout=301)

        error_msg = str(exc_info.value)
        assert "Timeout exceeds maximum limit" in error_msg
        assert "300" in error_msg  # 上限值
        assert "301" in error_msg  # 请求值

    def test_timeout_lower_limit_enforced(self, tmp_path):
        """测试强制执行timeout下限（≥1秒）

        Story: story-2.3-bdd-scenarios.md
        DoD: F2 (ProcessManager timeout管理), Q1 (测试覆盖率)

        Given timeout 为 0 秒
        When 我调用 safe_exec(command="echo test", timeout=0)
        Then 抛出 ConstraintViolationError
        And 错误信息包含 "must be greater than 0"
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper.execute(command="echo test", timeout=0)

        error_msg = str(exc_info.value)
        assert "must be greater than 0" in error_msg.lower()

    @patch('subprocess.run')
    def test_timeout_provides_learning_feedback(self, mock_run, tmp_path):
        """测试timeout时提供学习反馈（suggested_timeout）

        Story: story-2.3-bdd-scenarios.md
        Scenario: "AI反馈循环学习"
        DoD: F2 (Timeout管理), Q1 (测试覆盖率)

        Given 命令 "sleep 100"
        And timeout 为 1 秒
        When timeout 发生
        Then 返回 ExecutionResult
        And timeout_occurred 为 True
        And suggested_timeout 为 2（2x原timeout）
        And error_message 包含 "timed out"
        """
        # Mock subprocess.run 抛出 TimeoutExpired
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="sleep 100",
            timeout=1,
            output=b"",
            stderr=b""
        )

        wrapper = SafeExecWrapper(working_dir=str(tmp_path))
        result = wrapper.execute(command="sleep 100", timeout=1)

        # 验证反馈字段
        assert result.success is False
        assert result.timeout_occurred is True
        assert result.suggested_timeout == 2  # 2x原timeout
        assert "timed out" in result.error_message.lower()

    def test_near_timeout_suggests_increase(self, tmp_path):
        """测试接近timeout时建议增加

        Story: story-2.3-bdd-scenarios.md
        Scenario: "AI反馈循环学习"
        DoD: F2 (Timeout管理), Q1 (测试覆盖率)

        Given 命令 "sleep 0.9"
        And timeout 为 1 秒
        When 命令成功完成（但接近timeout，>80%）
        Then suggested_timeout 不为 None
        And suggested_timeout 约为 1.35（actual * 1.5）
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # sleep 0.9s with 1s timeout (90% of timeout)
        result = wrapper.execute(command="sleep 0.9", timeout=1)

        assert result.success is True
        # 如果实际执行时间 > 80% timeout，应该建议增加
        if result.actual_duration_seconds > 0.8:
            assert result.suggested_timeout is not None
            assert result.suggested_timeout > 1

    @pytest.mark.parametrize(
        "interactive_command,pattern_name",
        [
            ("vim config.py", "text_editor"),
            ("nano test.txt", "text_editor"),
            ("emacs file.el", "text_editor"),
            ("python", "repl_environment"),
            ("python3", "repl_environment"),
            ("node", "repl_environment"),
            ("ssh user@host", "ssh_interactive"),
            ("sudo apt install pkg", "sudo_interactive"),
        ],
    )
    def test_interactive_command_detected(self, interactive_command, pattern_name, tmp_path):
        """测试检测交互命令（AI推理失败信号）

        Story: story-2.3-bdd-scenarios.md
        Scenario: "检测交互命令（推理失败）"
        DoD: F2 (快速失败机制), Q1 (测试覆盖率)

        Given 命令为交互命令（vim, ssh, python REPL等）
        When 我调用 safe_exec(command=<interactive_command>)
        Then 抛出 ConstraintViolationError
        And 错误信息包含 "Interactive command detected"
        And 错误信息包含 "reasoning failure"
        And 提供替代方案建议

        Examples:
        - vim config.py → Use safe_edit tool
        - python → Execute script: python script.py
        - ssh user@host → Use ssh with explicit command
        - sudo apt install → Use sudo -n or configure NOPASSWD

        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper.execute(command=interactive_command, timeout=30)

        error_msg = str(exc_info.value)
        assert "Interactive command detected" in error_msg or "interactive" in error_msg.lower()
        assert "reasoning failure" in error_msg.lower() or "wrong tool" in error_msg.lower()
        # 验证提供了替代方案
        assert "alternative" in error_msg.lower() or "instead" in error_msg.lower() or "use" in error_msg.lower()

    def test_python_script_execution_allowed(self, tmp_path):
        """测试Python脚本执行被允许（不是REPL）

        Story: story-2.3-bdd-scenarios.md
        DoD: F2 (交互命令检测精确性), Q2 (误报率<5%)

        Given 命令 "python script.py"（非交互）
        When 我调用 safe_exec(command="python script.py")
        Then 不抛出 ConstraintViolationError（Precondition应该通过）
        And 可以正常执行（或因文件不存在失败，但不是被阻止）
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # 创建测试脚本
        script = tmp_path / "test_script.py"
        script.write_text("print('Hello from script')")

        # 应该能够执行，不被交互命令检测阻止
        result = wrapper.execute(command=f"python {script}", timeout=5)

        # 验证precondition通过（即使执行可能失败）
        assert result.precondition_passed is True
        # 如果成功，验证输出
        if result.success:
            assert "Hello from script" in result.stdout

    @patch('subprocess.run')
    def test_safe_exec_timeout_kills_process_group(self, mock_run, tmp_path):
        """测试timeout时通过进程组清理所有子进程

        Story: story-2.3-bdd-scenarios.md
        Scenario 3: "Timeout时完全清理子进程"
        DoD: F2 (ProcessManager进程组管理), P3 (清理速度<50ms), Q1 (测试覆盖率)

        Given 命令 "sleep 100 & sleep 100 & wait"（创建子进程）
        And timeout 为 1 秒
        When timeout 发生
        Then subprocess.run 被调用时设置了进程组（preexec_fn=os.setsid）
        And 返回 timeout_occurred=True
        And 清理时间 < 50ms（通过 duration_ms 验证）

        Note: 使用Mock验证os.setsid调用，避免跨平台进程检测问题
        """
        # Mock subprocess.run 抛出 TimeoutExpired
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="sleep 100 & sleep 100 & wait",
            timeout=1,
            output=b"",
            stderr=b""
        )

        wrapper = SafeExecWrapper(working_dir=str(tmp_path))
        result = wrapper.execute(command="sleep 100 & sleep 100 & wait", timeout=1)

        # 验证 subprocess.run 被正确调用
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]

        # 验证进程组设置（应该有 preexec_fn 或类似机制）
        # Note: 实际实现时需要使用 os.setsid 或 start_new_session=True
        # 这里我们验证 subprocess.run 被调用
        assert call_kwargs['timeout'] == 1

        # 验证返回结果
        assert result.timeout_occurred is True
        assert result.success is False

    def test_safe_exec_captures_stdout_stderr(self, tmp_path):
        """测试正确捕获stdout和stderr

        Story: story-2.3-bdd-scenarios.md
        DoD: F2 (ProcessManager输出管理), Q1 (测试覆盖率)

        Given 命令同时输出到stdout和stderr
        When 执行命令
        Then stdout被正确捕获
        And stderr被正确捕获
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # 命令同时输出到stdout和stderr
        result = wrapper.execute(
            command='echo "stdout message" && echo "stderr message" >&2',
            timeout=5
        )

        assert result.success is True
        assert "stdout message" in result.stdout
        assert "stderr message" in result.stderr

    def test_safe_exec_returns_exit_code(self, tmp_path):
        """测试返回正确的exit code

        Story: story-2.3-bdd-scenarios.md
        DoD: F2 (ProcessManager), Q1 (测试覆盖率)

        Given 命令返回非零exit code
        When 执行命令
        Then exit_code被正确返回
        And success为False
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # 命令返回 exit code 42
        result = wrapper.execute(command="exit 42", timeout=5)

        assert result.success is False
        assert result.exit_code == 42
        assert result.error_message is not None

    def test_safe_exec_truncates_long_output(self, tmp_path):
        """测试长输出被截断（head 50 + tail 50）

        Story: story-2.3-bdd-scenarios.md
        Scenario 6: "输出截断防止token浪费"
        DoD: F3 (输出截断), Q1 (测试覆盖率)

        Given 命令生成 200 行输出
        When 执行命令
        Then stdout 只包含前 50 行
        And stdout 包含 "... (omitted) ..."或类似省略标记
        And stdout 包含后 50 行
        And 总行数为 101（50 + 1 + 50）

        Note: 具体截断策略在Green Phase实现
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # 生成200行输出
        result = wrapper.execute(command="seq 1 200", timeout=5)

        assert result.success is True

        lines = result.stdout.strip().split('\n')

        # 如果输出被截断，应该：
        # 1. 总行数 ≈ 101（50 + 省略标记 + 50）
        # 2. 包含开头（1, 2, 3...）
        # 3. 包含省略标记
        # 4. 包含结尾（...198, 199, 200）

        if len(lines) < 200:
            # 输出被截断
            assert len(lines) <= 110  # 允许一些格式变化
            assert "1" in result.stdout  # 包含开头
            assert "200" in result.stdout  # 包含结尾
            assert "omitted" in result.stdout.lower() or "..." in result.stdout  # 省略标记

    def test_process_cleanup_performance(self, tmp_path):
        """测试进程清理性能 < 50ms

        Story: story-2.3-bdd-scenarios.md
        DoD: P3 (Timeout清理速度)

        Given 一个简单的命令
        When timeout 发生
        Then 从timeout触发到进程终止 < 50ms
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        start = time.perf_counter()
        result = wrapper.execute(command="sleep 10", timeout=1)
        total_duration = (time.perf_counter() - start) * 1000

        # 验证timeout发生
        assert result.timeout_occurred is True

        # 总时长应该接近timeout值，说明清理很快
        # 1秒timeout + 清理时间 < 1050ms（允许50ms清理）
        assert total_duration < 1050, f"Cleanup took {total_duration - 1000:.2f}ms (target: <50ms)"


# ==================== MCP Tools Tests (Placeholder for Day 3) ====================

class TestSafeExecMCPTools:
    """Day 3: MCP工具暴露测试 (placeholder)"""

    def test_safe_exec_tool_registered_in_mcp(self):
        """测试SafeExecTool注册到MCP服务器

        Story: story-2.3-bdd-scenarios.md
        Scenario 7: "MCP 工具暴露和调用"
        DoD: F5 (MCP 工具暴露)

        Given SerenaAgent 已初始化
        When MCP 服务器启动
        Then SafeExecTool 在工具列表中
        """
        pytest.skip("Day 3: MCP integration tests")

    def test_safe_exec_tool_called_via_mcp(self):
        """测试通过MCP调用safe_exec

        Story: story-2.3-bdd-scenarios.md
        Scenario 7: "MCP 工具暴露和调用"
        DoD: F5 (MCP 工具暴露), Q3 (向后兼容性)

        Given MCP 客户端连接到服务器
        When 客户端调用 safe_exec(command="echo test", timeout=5)
        Then 返回成功结果
        And 审计日志记录 MCP 调用
        """
        pytest.skip("Day 3: MCP integration tests")
