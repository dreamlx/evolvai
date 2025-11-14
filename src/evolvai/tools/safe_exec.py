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

import math
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from evolvai.core.exceptions import ConstraintViolationError
from evolvai.core.execution_plan import ExecutionPlan
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
    
    # Day 2: Timeout管理和反馈循环
    timeout_occurred: bool = False
    actual_duration_seconds: float = 0.0
    suggested_timeout: Optional[int] = None


# Absurd command patterns (3-5 rules, not 30-50)
# These detect AI reasoning failure, not "dangerous commands"
ABSURD_COMMAND_PATTERNS = [
    (r'rm\s+(-rf|--recursive.*--force)\s+/\s*$', "rm_rf_root", "Deleting root directory"),
    (r'rm\s+(-rf|--recursive.*--force)\s+/\*', "rm_rf_root_wildcard", "Deleting root with wildcard"),
    (r'mkfs\.', "mkfs", "Formatting filesystem"),
    (r':\(\)\{.*:\|:.*\}.*;:', "fork_bomb", "Fork bomb pattern"),
]

# Day 2: Interactive command patterns (AI reasoning failure - wrong tool selected)
# These commands require user interaction and will hang in headless/MCP environments
INTERACTIVE_COMMAND_PATTERNS = [
    (r'\b(vim|vi|nano|emacs)\b', "text_editor", "Use safe_edit tool instead"),
    (r'\b(python|python3|node|irb|ghci)\b\s*$', "repl_environment", "Execute scripts directly: python script.py"),
    (r'\bssh\b\s+[\w@]+\s*$', "ssh_interactive", "Use ssh with explicit command or -N/-f flags"),
    (r'\b(apt|yum|dnf|pacman)\b\s+(install|remove|upgrade)(?!\s+-y)', "package_manager", "Use -y flag for non-interactive"),
    (r'\bsudo\b(?!\s+-[nS])', "sudo_interactive", "Use sudo -n for non-interactive or configure NOPASSWD"),
]

# Day 2: Timeout limits (防止交互命令无限等待)
MAX_TIMEOUT_SECONDS = 300  # 5 minutes hard limit


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

    def execute(self, command: str, timeout: int, execution_plan: Optional[ExecutionPlan] = None) -> ExecutionResult:
        """
        Execute command with precondition checks

        Args:
            command: Command to execute
            timeout: Timeout in seconds
            execution_plan: Optional ExecutionPlan for constraint validation (Day 3)

        Returns:
            ExecutionResult with execution details

        Raises:
            ConstraintViolationError: If preconditions fail

        """
        # Check preconditions first (fast-fail)
        start_time = time.perf_counter()
        self._check_preconditions(command, timeout, execution_plan)
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
            
            # Day 2: Calculate actual duration and suggested timeout
            actual_duration_sec = exec_duration / 1000
            suggested_timeout = None

            # If execution took > 80% of timeout, suggest increase
            if actual_duration_sec > timeout * 0.8:
                suggested_timeout = math.ceil(actual_duration_sec * 1.5)
            
            # Day 2: Truncate output (head 50 + tail 50)
            stdout_truncated = self._truncate_output(result.stdout)
            stderr_truncated = self._truncate_output(result.stderr)

            return ExecutionResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=stdout_truncated,
                stderr=stderr_truncated,
                duration_ms=total_duration,
                precondition_passed=True,
                error_message=None if result.returncode == 0 else result.stderr,
                # Day 2: Feedback loop fields
                timeout_occurred=False,
                actual_duration_seconds=actual_duration_sec,
                suggested_timeout=suggested_timeout,
            )

        except subprocess.TimeoutExpired as e:
            total_duration = (time.perf_counter() - start_time) * 1000
            
            # Day 2: Suggest 2x timeout on timeout
            suggested_timeout = timeout * 2
            
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                duration_ms=total_duration,
                precondition_passed=True,
                error_message=f"Command timed out after {timeout}s",
                # Day 2: Feedback loop fields
                timeout_occurred=True,
                actual_duration_seconds=float(timeout),
                suggested_timeout=suggested_timeout,
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

    def _truncate_output(self, output: str, max_lines: int = 50) -> str:
        """
        Truncate long output (Day 2: head + tail strategy)

        Args:
            output: Command output to truncate
            max_lines: Maximum lines for head and tail (default: 50)

        Returns:
            Truncated output with head 50 + omission marker + tail 50

        """
        if not output:
            return output

        lines = output.split('\n')

        # If output is short enough, return as-is
        if len(lines) <= max_lines * 2:
            return output

        # Truncate: head 50 + omission + tail 50
        head = lines[:max_lines]
        tail = lines[-max_lines:]
        omitted_count = len(lines) - (max_lines * 2)

        omission_marker = f"\n... ({omitted_count} lines omitted) ...\n"

        return '\n'.join(head) + omission_marker + '\n'.join(tail)

    def _check_preconditions(self, command: str, timeout: int, execution_plan: Optional[ExecutionPlan] = None) -> None:
        """
        Check preconditions before execution (fast-fail)

        Checks (in order of speed):
        0. ExecutionPlan timeout constraint (instant) → Day 3
        1. Timeout validation (instant) → Day 2
        2. Absurd commands (regex, <1ms) → AI reasoning failure detection
        3. Interactive commands (regex, <1ms) → Day 2
        4. Command existence (shutil.which, ~5ms) → Avoid wasted attempts
        5. Working directory (already validated in __init__)

        Args:
            command: Command to check
            timeout: Timeout to validate
            execution_plan: Optional ExecutionPlan for constraint validation

        Raises:
            ConstraintViolationError: If any precondition fails

        """
        # Check -1: ExecutionPlan timeout constraint (Day 3)
        if execution_plan is not None:
            plan_timeout = execution_plan.limits.timeout_seconds
            if timeout > plan_timeout:
                raise _create_violation_error(
                    field="timeout",
                    message=(
                        f"Timeout exceeds plan limit: requested {timeout}s exceeds plan limit {plan_timeout}s\n\n"
                        f"Requested timeout: {timeout}s\n"
                        f"Plan timeout limit: {plan_timeout}s\n\n"
                        f"This ensures AI operations stay within planned resource constraints.\n"
                        f"Consider adjusting the ExecutionPlan limits or breaking the operation into smaller steps."
                    ),
                )

        # Check 0: Timeout validation (Day 2)
        if timeout <= 0:
            raise _create_violation_error(
                field="timeout",
                message=(
                    f"Invalid timeout: {timeout}s\n"
                    f"Timeout must be greater than 0 seconds."
                ),
            )
        
        if timeout > MAX_TIMEOUT_SECONDS:
            raise _create_violation_error(
                field="timeout",
                message=(
                    f"Timeout exceeds maximum limit: {timeout}s > {MAX_TIMEOUT_SECONDS}s\n\n"
                    f"This prevents hanging on interactive commands.\n"
                    f"If you need longer execution, consider breaking into smaller steps."
                ),
            )
        
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
        
        # Check 2: Detect interactive commands (Day 2 - AI reasoning failure)
        for pattern, pattern_name, suggestion in INTERACTIVE_COMMAND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise _create_violation_error(
                    field="command",
                    message=(
                        f"Interactive command detected: {command}\n"
                        f"Pattern: {pattern_name}\n\n"
                        f"This command requires user interaction and will timeout.\n"
                        f"This suggests AI reasoning failure - wrong tool selected.\n\n"
                        f"💡 Recommended alternative:\n"
                        f"   {suggestion}\n\n"
                        f"Note: In MCP/headless environments, interactive commands\n"
                        f"cannot receive user input and will hang until timeout."
                    ),
                )

        # Check 3: Verify command exists (avoid wasted attempts)
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
        shell_builtins = {'cd', 'echo', 'export', 'set', 'pwd', 'test', '[', 'exit'}
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
