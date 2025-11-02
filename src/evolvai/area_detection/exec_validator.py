"""
执行前置条件检查器
遵循KISS原则：专注核心验证逻辑，避免过度设计
"""

import os
import shutil
from pathlib import Path

from .data_models import ExecutionPrecondition, ExecutionRiskLevel


class ValidationResult:
    """验证结果 - 简单数据结构"""

    def __init__(self):
        self.is_valid = True
        self.errors: list[str] = []
        self.warnings: list[str] = []


class PreconditionChecker:
    """前置条件检查器 - 专注业务逻辑验证"""

    def __init__(self):
        # 危险命令模式 - 简单可配置
        self.dangerous_patterns = [
            "rm -rf /",
            "rm -rf /*",
            "dd if=/dev/zero",
            "mkfs",
            "format",
            "fdisk",
            ":(){ :|:& };:",  # fork bomb
            "sudo rm",
            "chmod 777 /",
            "chown root"
        ]

        # 高风险命令模式
        self.high_risk_patterns = [
            "rm ",
            "dd ",
            "mkfs",
            "fdisk",
            "format",
            "chmod 777",
            "chown"
        ]

    def validate(self, precondition: ExecutionPrecondition) -> ValidationResult:
        """
        验证执行前置条件

        Args:
            precondition: 执行前置条件

        Returns:
            ValidationResult: 验证结果

        """
        result = ValidationResult()

        # 1. 危险命令检查
        self._check_dangerous_commands(precondition, result)

        # 2. 权限检查
        self._check_permissions(precondition, result)

        # 3. 依赖检查
        self._check_dependencies(precondition, result)

        # 4. 工作目录检查
        self._check_working_directory(precondition, result)

        # 5. 超时合理性检查
        self._check_timeout(precondition, result)

        return result

    def _check_dangerous_commands(self, precondition: ExecutionPrecondition, result: ValidationResult):
        """检查危险命令"""
        command = precondition.command.lower()

        for pattern in self.dangerous_patterns:
            if pattern in command:
                result.is_valid = False
                result.errors.append(f"Dangerous command detected: {pattern}")
                return

        # 高风险命令检查
        for pattern in self.high_risk_patterns:
            if pattern in command and precondition.risk_level != ExecutionRiskLevel.LOW:
                result.warnings.append(f"High-risk command pattern: {pattern}")

    def _check_permissions(self, precondition: ExecutionPrecondition, result: ValidationResult):
        """检查权限"""
        work_dir = Path(precondition.working_directory)

        for permission in precondition.required_permissions:
            if permission == "read":
                if not os.access(work_dir, os.R_OK):
                    result.is_valid = False
                    result.errors.append(f"No read permission for directory: {precondition.working_directory}")
            elif permission == "write":
                if not os.access(work_dir, os.W_OK):
                    result.is_valid = False
                    result.errors.append(f"No write permission for directory: {precondition.working_directory}")
            elif permission == "execute":
                if not os.access(work_dir, os.X_OK):
                    result.is_valid = False
                    result.errors.append(f"No execute permission for directory: {precondition.working_directory}")

    def _check_dependencies(self, precondition: ExecutionPrecondition, result: ValidationResult):
        """检查系统依赖"""
        for dep in precondition.system_dependencies:
            # 检查命令是否存在
            if shutil.which(dep) is None:
                result.is_valid = False
                result.errors.append(f"Missing dependency: {dep}")

    def _check_working_directory(self, precondition: ExecutionPrecondition, result: ValidationResult):
        """检查工作目录"""
        work_dir = Path(precondition.working_directory)

        if not work_dir.exists():
            result.is_valid = False
            result.errors.append(f"Working directory does not exist: {precondition.working_directory}")

        if not work_dir.is_dir():
            result.is_valid = False
            result.errors.append(f"Working path is not a directory: {precondition.working_directory}")

    def _check_timeout(self, precondition: ExecutionPrecondition, result: ValidationResult):
        """检查超时设置合理性"""
        if precondition.timeout_seconds <= 0:
            result.is_valid = False
            result.errors.append("Timeout must be positive")

        if precondition.timeout_seconds > 300:  # 5分钟
            result.warnings.append(f"Long timeout ({precondition.timeout_seconds}s) may indicate inefficient command")

        # 高风险命令的超时限制
        if precondition.risk_level in [ExecutionRiskLevel.HIGH, ExecutionRiskLevel.CRITICAL]:
            max_safe_timeout = 60  # 1分钟
            if precondition.timeout_seconds > max_safe_timeout:
                result.is_valid = False
                result.errors.append(f"High-risk commands cannot exceed {max_safe_timeout}s timeout")
