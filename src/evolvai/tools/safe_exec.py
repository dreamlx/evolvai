"""
Story 2.3: safe_exec - Command Execution Wrapper

核心价值（Epic-001目标）：减少TPST，不是系统安全防护
- 快速失败机制（依赖检查 + 工作目录验证 + 推理崩溃检测）
- Timeout管理（避免卡住浪费时间）
- 输出截断（head 50 + tail 50，减少token消耗）
- 有用错误信息（帮助AI快速修正路径）

Design Principles (深度反思):
- 黑名单的真正价值：检测AI推理崩溃，不是系统安全
- 极简规则（3-5条），不是复杂规则引擎
- 错误信息强调"推理失败"而非"危险"
"""

import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from evolvai.core.exceptions import ConstraintViolationError
from evolvai.core.validation_result import ValidationResult, ValidationViolation, ViolationSeverity


def _create_violation_error(field: str, message: str) -> ConstraintViolationError:
    """Helper to create ConstraintViolationError with proper ValidationResult.

    Args:
        field: The field that failed (e.g., "command", "working_dir")
        message: Human-readable error message

    Returns:
        ConstraintViolationError with single violation

    """
    violation = ValidationViolation(
        field=field,
        message=message,
        severity=ViolationSeverity.ERROR,
    )
    result = ValidationResult(is_valid=False, violations=[violation])
    return ConstraintViolationError(result)


@dataclass
class ExecutionResult:
    """命令执行结果"""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    precondition_passed: bool
    error_message: Optional[str] = None


# Absurd command patterns (3-5 rules, not 30-50)
# These detect AI reasoning failure, not "dangerous commands"
ABSURD_COMMAND_PATTERNS = [
    (r'rm\s+(-rf|--recursive.*--force)\s+/\s*$', "rm_rf_root", "Deleting root directory"),
    (r'rm\s+(-rf|--recursive.*--force)\s+/\*', "rm_rf_root_wildcard", "Deleting root with wildcard"),
    (r'mkfs\.', "mkfs", "Formatting filesystem"),
    (r':\(\)\{.*:\|:.*\}.*;:', "fork_bomb", "Fork bomb pattern"),
]


class SafeExecWrapper:
    """Safe command execution wrapper with fast-fail preconditions

    Key Design:
    - Fast-fail: Detect issues before wasting tokens
    - Simple: 3-5 absurd command patterns, not complex rules
    - Helpful: Error messages point to reasoning problems
    """

    def __init__(self, working_dir: str):
        """
        Initialize SafeExecWrapper

        Args:
            working_dir: Working directory for command execution

        Raises:
            ConstraintViolationError: If working directory is invalid

        """
        # Validate and resolve working directory
        working_path = Path(working_dir).resolve()

        if not working_path.exists():
            raise _create_violation_error(
                field="working_dir",
                message=(
                    f"Invalid working directory: {working_dir}\n"
                    f"Resolved to: {working_path}\n"
                    f"This path does not exist. Please check the directory path."
                ),
            )

        if not working_path.is_dir():
            raise _create_violation_error(
                field="working_dir",
                message=(
                    f"Invalid working directory: {working_dir}\n"
                    f"Resolved to: {working_path}\n"
                    f"This is not a directory."
                ),
            )

        self.working_dir = str(working_path)

    def execute(self, command: str, timeout: int) -> ExecutionResult:
        """
        Execute command with precondition checks

        Args:
            command: Command to execute
            timeout: Timeout in seconds

        Returns:
            ExecutionResult with execution details

        Raises:
            ConstraintViolationError: If preconditions fail

        """
        # Check preconditions first (fast-fail)
        start_time = time.perf_counter()
        self._check_preconditions(command, timeout)
        precondition_time = (time.perf_counter() - start_time) * 1000

        # Execute command
        try:
            exec_start = time.perf_counter()

            result = subprocess.run(
                command,
                check=False, shell=True,
                cwd=self.working_dir,
                timeout=timeout,
                capture_output=True,
                text=True,
            )

            exec_duration = (time.perf_counter() - exec_start) * 1000
            total_duration = precondition_time + exec_duration

            return ExecutionResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=total_duration,
                precondition_passed=True,
                error_message=None if result.returncode == 0 else result.stderr,
            )

        except subprocess.TimeoutExpired as e:
            total_duration = (time.perf_counter() - start_time) * 1000
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                duration_ms=total_duration,
                precondition_passed=True,
                error_message=f"Command timed out after {timeout}s",
            )

        except Exception as e:
            total_duration = (time.perf_counter() - start_time) * 1000
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=total_duration,
                precondition_passed=True,
                error_message=str(e),
            )

    def _check_preconditions(self, command: str, timeout: int) -> None:
        """
        Check preconditions before execution (fast-fail)

        Checks (in order of speed):
        1. Absurd commands (regex, <1ms) → AI reasoning failure detection
        2. Command existence (shutil.which, ~5ms) → Avoid wasted attempts
        3. Working directory (already validated in __init__)

        Args:
            command: Command to check
            timeout: Timeout to validate

        Raises:
            ConstraintViolationError: If any precondition fails

        """
        # Check 1: Detect absurd commands (AI reasoning failure signal)
        for pattern, pattern_name, description in ABSURD_COMMAND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise _create_violation_error(
                    field="command",
                    message=(
                        f"Absurd command detected: {description}\n"
                        f"Command: {command}\n"
                        f"Pattern: {pattern_name}\n\n"
                        f"This suggests AI reasoning failure.\n"
                        f"Please reconsider the task goal.\n\n"
                        f"Note: This is NOT a security check. In a Git-protected development\n"
                        f"environment, most operations are reversible. This check detects when\n"
                        f"AI reasoning has gone off track to avoid wasting tokens."
                    ),
                )

        # Check 2: Verify command exists (avoid wasted attempts)
        # Extract base command (first word, before arguments)
        command_parts = command.strip().split()
        if not command_parts:
            raise _create_violation_error(
                field="command",
                message=(
                    "Empty command provided.\n"
                    "Please specify a command to execute."
                ),
            )

        base_command = command_parts[0]

        # Skip shell built-ins and complex expressions
        shell_builtins = {'cd', 'echo', 'export', 'set', 'pwd', 'test', '['}
        if base_command not in shell_builtins and '|' not in command and '>' not in command:
            if not shutil.which(base_command):
                raise _create_violation_error(
                    field="command",
                    message=(
                        f"Command not found: {base_command}\n"
                        f"Full command: {command}\n\n"
                        f"The command '{base_command}' is not available in the system.\n"
                        f"Please install it or check the command name.\n\n"
                        f"This check helps avoid wasting tokens on unavailable commands."
                    ),
                )
