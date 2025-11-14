"""
Story 2.3: safe_exec - Day 1 PreconditionChecker Tests

BDD-driven TDD implementation for safe_exec wrapper.
Focus: 快速失败机制（依赖检查 + 工作目录验证 + 推理崩溃检测）

Key Design Principle: 减少TPST（Token浪费），不是系统安全防护
"""

import os
import time
from pathlib import Path

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
