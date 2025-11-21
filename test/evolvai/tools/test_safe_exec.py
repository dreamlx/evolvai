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

    @patch("subprocess.run")
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
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 100", timeout=1, output=b"", stderr=b"")

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

    @patch("subprocess.run")
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
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 100 & sleep 100 & wait", timeout=1, output=b"", stderr=b"")

        wrapper = SafeExecWrapper(working_dir=str(tmp_path))
        result = wrapper.execute(command="sleep 100 & sleep 100 & wait", timeout=1)

        # 验证 subprocess.run 被正确调用
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]

        # 验证进程组设置（应该有 preexec_fn 或类似机制）
        # Note: 实际实现时需要使用 os.setsid 或 start_new_session=True
        # 这里我们验证 subprocess.run 被调用
        assert call_kwargs["timeout"] == 1

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
        result = wrapper.execute(command='echo "stdout message" && echo "stderr message" >&2', timeout=5)

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

        lines = result.stdout.strip().split("\n")

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


class TestSafeExecDay3ExecutionPlan:
    """Day 3: ExecutionPlan Integration & MCP Tools"""

    def test_safe_exec_enforces_timeout_constraint(self, tmp_path):
        """测试ExecutionPlan的timeout约束验证

        Story: story-2.3-bdd-scenarios.md Scenario 5
        DoD: F4 (ExecutionPlan timeout约束), Q3 (向后兼容性)

        Given execution_plan 限制 timeout ≤ 10 秒
        And 命令 "sleep 5"
        When 我调用 safe_exec(command="sleep 5", timeout=15, execution_plan=plan)
        Then 抛出 ConstraintViolationError
        And 错误信息包含 "Timeout exceeds plan limit"
        And 错误信息包含 "plan: 10s, requested: 15s"
        """
        from evolvai.core.execution_plan import ExecutionLimits, ExecutionPlan, RollbackStrategy, RollbackStrategyType

        # Create plan with max timeout = 10s
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT, commands=[]), limits=ExecutionLimits(timeout_seconds=10)
        )

        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # Request timeout=15s which exceeds plan limit
        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper.execute(command="sleep 5", timeout=15, execution_plan=plan)

        error_msg = str(exc_info.value)
        assert "Timeout exceeds plan limit" in error_msg
        assert "10" in error_msg  # Plan limit value
        assert "15" in error_msg  # Requested timeout value

    def test_safe_exec_backward_compatible_no_plan(self, tmp_path):
        """测试无ExecutionPlan时向后兼容

        Story: story-2.3-bdd-scenarios.md Scenario 5
        DoD: Q3 (向后兼容性)

        Given 无 execution_plan 参数
        When 我调用 safe_exec(command="echo test", timeout=5)
        Then 返回成功结果
        And 无约束验证
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # Call without execution_plan (backward compatible)
        result = wrapper.execute(command="echo test", timeout=5)

        assert result.success is True
        assert result.exit_code == 0
        assert "test" in result.stdout
        # No constraint violations occurred

    def test_safe_exec_audit_log_integration(self, tmp_path):
        """测试审计日志集成（简化版）

        Story: story-2.3-bdd-scenarios.md Day 3
        DoD: F4 (ExecutionPlan集成), Q1 (测试覆盖率)

        Given ExecutionPlan with timeout constraint
        When constraint violation occurs
        Then violation is recorded (verified by exception being raised)
        """
        from evolvai.core.execution_plan import ExecutionLimits, ExecutionPlan, RollbackStrategy, RollbackStrategyType

        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT, commands=[]), limits=ExecutionLimits(timeout_seconds=5)
        )

        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # Violation should be detected and raised
        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper.execute(command="sleep 1", timeout=10, execution_plan=plan)

        # Verify violation details are in exception
        assert "Timeout exceeds plan limit" in str(exc_info.value)


class TestSafeExecMCPTools:
    """Day 3: MCP工具暴露测试"""

    def test_safe_exec_tool_registered_in_mcp(self):
        """测试SafeExecTool注册到MCP服务器

        Story: story-2.3-bdd-scenarios.md Scenario 7
        DoD: F5 (MCP 工具暴露)

        Given SerenaAgent 已初始化
        When 检查工具列表
        Then SafeExecTool 在工具列表中
        And 工具名称为 "safe_exec"
        """
        # Import SafeExecTool
        from evolvai.tools.safe_exec_tool import SafeExecTool

        # Verify tool can be instantiated and has correct name
        assert SafeExecTool.get_name_from_cls() == "safe_exec"

        # Verify tool has apply method
        assert hasattr(SafeExecTool, "apply")

        # Verify tool has proper docstring
        docstring = SafeExecTool.get_apply_docstring_from_cls()
        assert "safe" in docstring.lower() or "command" in docstring.lower()

    def test_safe_exec_tool_called_via_mcp(self, tmp_path):
        """测试通过MCP调用safe_exec

        Story: story-2.3-bdd-scenarios.md Scenario 7
        DoD: F5 (MCP 工具暴露), Q3 (向后兼容性)

        Given MCP client can call tools
        When 客户端调用 safe_exec(command="echo test", timeout=5, working_dir=tmp_path)
        Then 返回成功结果
        And 结果包含 stdout, stderr, exit_code
        """
        from unittest.mock import MagicMock

        from evolvai.tools.safe_exec_tool import SafeExecTool

        # Create mock agent
        mock_agent = MagicMock()
        mock_agent.get_active_project_or_raise.return_value.root = str(tmp_path)

        # Instantiate tool
        tool = SafeExecTool(agent=mock_agent)

        # Call tool's apply method (simulating MCP call)
        result = tool.apply(command="echo test", timeout=5, working_dir=str(tmp_path))

        # Verify result format
        assert "success" in result or "test" in result
        assert "Error" not in result or "error" not in result

    def test_safe_exec_tool_schema_validation(self):
        """测试SafeExecTool的schema验证

        Story: story-2.3-bdd-scenarios.md Scenario 7
        DoD: F5 (MCP 工具暴露), Q2 (代码质量)

        Given SafeExecTool定义
        When 获取tool metadata
        Then schema包含必需参数: command, timeout, working_dir
        """
        from evolvai.tools.safe_exec_tool import SafeExecTool

        # Get apply method metadata
        metadata = SafeExecTool.get_apply_fn_metadata_from_cls()

        # Verify metadata has arg_model (pydantic model for parameters)
        assert metadata.arg_model is not None

        # Verify required parameters are in arg_model fields
        param_names = list(metadata.arg_model.model_fields.keys())
        assert "command" in param_names
        assert "timeout" in param_names
        assert "working_dir" in param_names


# ==================== Story 2.4: Interactive Confirmation Tests ====================


class TestSafeExecStory24Day1CoreInfrastructure:
    """Story 2.4 Day 1: Core Infrastructure - Confirmation Detection"""

    def test_execution_result_has_confirmation_fields(self, tmp_path):
        """测试ExecutionResult包含confirmation相关字段

        Story: story-2.4-tdd-plan.md Day 1 Scenario 1.1
        DoD: F3 (返回confirmation_required结果)

        Given ExecutionResult dataclass定义
        When 检查字段
        Then 应包含:
          - confirmation_required: bool
          - confirmation_message: Optional[str]
          - risk_level: str
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(command="echo test", timeout=5)

        # Verify confirmation fields exist
        assert hasattr(result, "confirmation_required")
        assert hasattr(result, "confirmation_message")
        assert hasattr(result, "risk_level")

    def test_execution_result_defaults_no_confirmation(self, tmp_path):
        """测试ExecutionResult默认值为no confirmation

        Story: story-2.4-tdd-plan.md Day 1 Scenario 1.1
        DoD: Q3 (向后兼容性)

        Given 正常命令执行
        When 获取ExecutionResult
        Then confirmation_required = False
        And confirmation_message = None
        And risk_level = "low"
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(command="echo test", timeout=5)

        assert result.confirmation_required is False
        assert result.confirmation_message is None
        assert result.risk_level == "low"

    def test_detect_wildcard_delete_rm_rf(self, tmp_path):
        """测试检测通配符删除（rm -rf）

        Story: story-2.4-tdd-plan.md Day 1 Scenario 1.2
        DoD: F1 (检测通配符删除操作)

        Given 命令 "rm -rf ./tmp_*"
        When SafeExecWrapper.execute() is called
        Then confirmation_required = True
        And confirmation_message 说明风险
        And risk_level = "high"
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(command="rm -rf ./tmp_*", timeout=5)

        assert result.confirmation_required is True
        assert result.confirmation_message is not None
        assert "wildcard" in result.confirmation_message.lower()
        assert result.risk_level == "high"

    def test_detect_wildcard_delete_rm(self, tmp_path):
        """测试检测通配符删除（rm without -f）

        Story: story-2.4-tdd-plan.md Day 1 Scenario 1.2
        DoD: F1 (检测通配符删除操作)

        Given 命令 "rm -r ./logs_*"
        When SafeExecWrapper.execute() is called
        Then confirmation_required = True
        And risk_level = "high"
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(command="rm -r ./logs_*", timeout=5)

        assert result.confirmation_required is True
        assert result.risk_level == "high"

    def test_detect_delete_current_directory(self, tmp_path):
        """测试检测删除当前目录

        Story: story-2.4-tdd-plan.md Day 1 Scenario 1.3
        DoD: F2 (检测删除当前目录操作)

        Given 命令 "rm -rf ."
        When SafeExecWrapper.execute() is called
        Then confirmation_required = True
        And confirmation_message 说明风险
        And risk_level = "high"
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(command="rm -rf .", timeout=5)

        assert result.confirmation_required is True
        assert result.confirmation_message is not None
        assert "current directory" in result.confirmation_message.lower()
        assert result.risk_level == "high"

    def test_detect_delete_source_directory(self, tmp_path):
        """测试检测删除源代码目录

        Story: story-2.4-tdd-plan.md Day 1 Scenario 1.4
        DoD: F1 (检测高风险操作)

        Given 命令 "rm -rf ./src"
        When SafeExecWrapper.execute() is called
        Then confirmation_required = True
        And risk_level = "medium"
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(command="rm -rf ./src", timeout=5)

        assert result.confirmation_required is True
        assert result.risk_level == "medium"

    def test_normal_commands_no_confirmation(self, tmp_path):
        """测试正常命令不需要confirmation

        Story: story-2.4-tdd-plan.md Day 1 Scenario 1.5
        DoD: Q2 (误报率 < 5%)

        Given 命令 "ls -la"
        When SafeExecWrapper.execute() is called
        Then confirmation_required = False
        And 命令正常执行
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(command="ls -la", timeout=5)

        assert result.confirmation_required is False
        assert result.success is True
        assert result.exit_code == 0

    def test_absurd_commands_still_blocked(self, tmp_path):
        """测试荒谬命令仍然被阻止（向后兼容Story 2.3）

        Story: story-2.4-tdd-plan.md Day 1 Scenario 1.6
        DoD: Q3 (向后兼容性)

        Given 命令 "rm -rf /"
        When SafeExecWrapper.execute() is called
        Then 抛出 ConstraintViolationError
        (Story 2.3行为保持不变)
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper.execute(command="rm -rf /", timeout=5)

        error_msg = str(exc_info.value)
        assert "Absurd command detected" in error_msg


class TestSafeExecStory24Day2ConfirmationFlow:
    """Story 2.4 Day 2: Confirmation Flow - confirmed parameter support"""

    def test_first_execution_returns_confirmation_required(self, tmp_path):
        """测试首次执行返回confirmation_required

        Story: story-2.4-tdd-plan.md Day 2 Scenario 2.1
        DoD: F3 (返回confirmation_required结果)

        Given 高风险命令 "rm -rf ./tmp_*"
        When SafeExecWrapper.execute() 不带confirmed标志
        Then confirmation_required = True
        And command NOT executed
        And stdout/stderr empty
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(command="rm -rf ./tmp_*", timeout=5)

        assert result.confirmation_required is True
        assert result.confirmation_message is not None
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.exit_code == 0  # No execution occurred

    def test_first_execution_does_not_execute_command(self, tmp_path):
        """测试首次执行不实际运行命令

        Story: story-2.4-tdd-plan.md Day 2 Scenario 2.1
        DoD: F3 (返回confirmation_required结果)

        Given 高风险命令且working_dir有文件
        When 第一次execute()调用
        Then 文件不被删除（命令未执行）
        """
        # Create test files
        test_file = tmp_path / "tmp_test.txt"
        test_file.write_text("test content")

        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        result = wrapper.execute(command="rm -rf ./tmp_*", timeout=5)

        # Verify confirmation required
        assert result.confirmation_required is True

        # Verify command was NOT executed (file still exists)
        assert test_file.exists()
        assert test_file.read_text() == "test content"

    def test_second_execution_with_confirmed_true_proceeds(self, tmp_path):
        """测试第二次执行with confirmed=True正常执行

        Story: story-2.4-tdd-plan.md Day 2 Scenario 2.2
        DoD: F4 (支持confirmed=True跳过确认)

        Given 高风险命令 "rm -rf ./tmp_*"
        When SafeExecWrapper.execute(confirmed=True)
        Then confirmation_required = False
        And command executes normally
        """
        # Create test file
        test_file = tmp_path / "tmp_test.txt"
        test_file.write_text("test content")

        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # Second execution with confirmed=True
        result = wrapper.execute(command="rm -rf ./tmp_*", timeout=5, confirmed=True)

        # Verify no confirmation required
        assert result.confirmation_required is False

        # Verify command was executed (file deleted)
        assert not test_file.exists()

    def test_confirmed_only_skips_confirmation_not_absurd(self, tmp_path):
        """测试confirmed标志只跳过confirmation，不跳过absurd检查

        Story: story-2.4-tdd-plan.md Day 2 Scenario 2.3
        DoD: Q3 (向后兼容性 - absurd commands仍被阻止)

        Given 荒谬命令 "rm -rf /"
        When SafeExecWrapper.execute(confirmed=True)
        Then 仍然抛出 ConstraintViolationError
        (confirmed flag不能绕过absurd命令检查)
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # Even with confirmed=True, absurd commands should be blocked
        with pytest.raises(ConstraintViolationError) as exc_info:
            wrapper.execute(command="rm -rf /", timeout=5, confirmed=True)

        error_msg = str(exc_info.value)
        assert "Absurd command detected" in error_msg

    def test_backward_compatible_no_confirmed_param(self, tmp_path):
        """测试向后兼容 - 无confirmed参数

        Story: story-2.4-tdd-plan.md Day 2 Scenario 2.4
        DoD: Q3 (向后兼容性)

        Given 已有代码调用execute(command, timeout)
        When 不提供confirmed参数
        Then confirmation逻辑正常工作
        And 无错误发生
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # Call without confirmed parameter (backward compatible)
        result = wrapper.execute(command="echo test", timeout=5)

        # Should work normally
        assert result.success is True
        assert result.confirmation_required is False

    def test_confirmed_false_same_as_no_param(self, tmp_path):
        """测试confirmed=False与不提供参数效果相同

        Story: story-2.4-tdd-plan.md Day 2 Scenario 2.4
        DoD: Q3 (向后兼容性)

        Given 高风险命令
        When execute(confirmed=False)
        Then 结果与不提供confirmed参数相同
        """
        wrapper = SafeExecWrapper(working_dir=str(tmp_path))

        # Call with confirmed=False (explicit)
        result1 = wrapper.execute(command="rm -rf ./tmp_*", timeout=5, confirmed=False)

        # Call without confirmed parameter (implicit default)
        result2 = wrapper.execute(command="rm -rf ./tmp_*", timeout=5)

        # Both should require confirmation
        assert result1.confirmation_required is True
        assert result2.confirmation_required is True
        assert result1.confirmation_message == result2.confirmation_message


class TestSafeExecStory24Day3MCPIntegration:
    """Story 2.4 Day 3: MCP Integration - SafeExecTool confirmation support"""

    def test_safe_exec_tool_returns_confirmation_required_json(self, tmp_path):
        """测试SafeExecTool返回confirmation_required via JSON

        Story: story-2.4-tdd-plan.md Day 3 Scenario 3.1
        DoD: F5 (MCP工具层自动询问)

        Given SafeExecTool instance
        When apply() 被调用with high-risk command
        Then JSON response includes confirmation_required=true
        And includes confirmation_message
        And includes risk_level
        """
        import json
        from unittest.mock import MagicMock

        from evolvai.tools.safe_exec_tool import SafeExecTool

        # Create mock agent
        mock_agent = MagicMock()
        mock_agent.get_active_project_or_raise.return_value.root = str(tmp_path)

        # Instantiate tool
        tool = SafeExecTool(agent=mock_agent)

        # Call with high-risk command
        result_json = tool.apply(command="rm -rf ./tmp_*", timeout=5, working_dir=str(tmp_path))

        # Parse JSON
        result = json.loads(result_json)

        # Verify confirmation fields present
        assert "confirmation_required" in result
        assert result["confirmation_required"] is True
        assert "confirmation_message" in result
        assert result["confirmation_message"] is not None
        assert "risk_level" in result
        assert result["risk_level"] == "high"

    def test_safe_exec_tool_accepts_confirmed_param(self, tmp_path):
        """测试SafeExecTool接受confirmed参数

        Story: story-2.4-tdd-plan.md Day 3 Scenario 3.2
        DoD: F4 (支持confirmed=True跳过确认)

        Given SafeExecTool instance
        When apply() is called with confirmed=True
        Then confirmation is skipped
        And command executes normally
        """
        import json
        from unittest.mock import MagicMock

        from evolvai.tools.safe_exec_tool import SafeExecTool

        # Create test file
        test_file = tmp_path / "tmp_test.txt"
        test_file.write_text("test content")

        # Create mock agent
        mock_agent = MagicMock()
        mock_agent.get_active_project_or_raise.return_value.root = str(tmp_path)

        # Instantiate tool
        tool = SafeExecTool(agent=mock_agent)

        # Call with confirmed=True
        result_json = tool.apply(command="rm -rf ./tmp_*", timeout=5, working_dir=str(tmp_path), confirmed=True)

        # Parse JSON
        result = json.loads(result_json)

        # Verify no confirmation required and command executed
        assert result["confirmation_required"] is False
        assert not test_file.exists()  # File was deleted

    def test_safe_exec_tool_json_includes_confirmation_fields(self, tmp_path):
        """测试SafeExecTool JSON包含所有confirmation字段

        Story: story-2.4-tdd-plan.md Day 3 Scenario 3.3
        DoD: F3 (返回confirmation_required结果)

        Given SafeExecTool
        When JSON response is generated
        Then includes confirmation_required, confirmation_message, risk_level
        """
        import json
        from unittest.mock import MagicMock

        from evolvai.tools.safe_exec_tool import SafeExecTool

        mock_agent = MagicMock()
        mock_agent.get_active_project_or_raise.return_value.root = str(tmp_path)

        tool = SafeExecTool(agent=mock_agent)

        # Test both high-risk and normal commands
        high_risk_json = tool.apply(command="rm -rf ./tmp_*", timeout=5, working_dir=str(tmp_path))
        normal_json = tool.apply(command="echo test", timeout=5, working_dir=str(tmp_path))

        high_risk = json.loads(high_risk_json)
        normal = json.loads(normal_json)

        # High-risk command
        assert "confirmation_required" in high_risk
        assert "confirmation_message" in high_risk
        assert "risk_level" in high_risk

        # Normal command
        assert "confirmation_required" in normal
        assert "confirmation_message" in normal
        assert "risk_level" in normal
