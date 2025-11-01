"""
安全执行包装器
遵循KISS原则：专注安全执行的核心功能，避免过度设计
"""

import time
from typing import Any, Optional

from .data_models import ExecutionPrecondition, ExecutionResult, ExecutionRiskLevel
from .exec_manager import ProcessManager
from .exec_validator import PreconditionChecker


class SafeExecWrapper:
    """安全执行包装器 - 专注安全执行的核心功能"""

    def __init__(self, agent=None, project=None, config: Optional[dict[str, Any]] = None):
        """
        初始化安全执行包装器

        Args:
            agent: 代理实例
            project: 项目实例
            config: 配置参数

        """
        self.agent = agent
        self.project = project
        self.config = config or {}

        # 初始化组件
        self.precondition_checker = PreconditionChecker()
        self.process_manager = ProcessManager()

        # 性能指标
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "blocked_executions": 0,
            "total_duration_ms": 0.0
        }

    def safe_exec(
        self,
        command: str,
        working_directory: str = "/tmp",
        timeout_seconds: int = 30,
        required_permissions: Optional[list] = None,
        system_dependencies: Optional[list] = None,
        environment_variables: Optional[dict] = None,
        risk_level: ExecutionRiskLevel = ExecutionRiskLevel.MEDIUM
    ) -> ExecutionResult:
        """
        安全执行命令

        Args:
            command: 要执行的命令
            working_directory: 工作目录
            timeout_seconds: 超时时间（秒）
            required_permissions: 所需权限列表
            system_dependencies: 系统依赖列表
            environment_variables: 环境变量
            risk_level: 风险级别

        Returns:
            ExecutionResult: 执行结果

        """
        start_time = time.time()
        self.execution_stats["total_executions"] += 1

        # 设置默认值
        required_permissions = required_permissions or []
        system_dependencies = system_dependencies or []
        environment_variables = environment_variables or {}

        try:
            # 1. 创建前置条件
            precondition = ExecutionPrecondition(
                command=command,
                working_directory=working_directory,
                timeout_seconds=timeout_seconds,
                required_permissions=required_permissions,
                system_dependencies=system_dependencies,
                environment_variables=environment_variables,
                risk_level=risk_level
            )

            # 2. 检查前置条件
            validation_result = self._check_preconditions(precondition)
            if not validation_result.is_valid:
                self.execution_stats["blocked_executions"] += 1
                error_message = "Precondition validation failed: " + "; ".join(validation_result.errors)
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="\n".join(validation_result.errors),
                    duration_ms=0.0,
                    precondition_passed=False,
                    command=command,
                    working_directory=working_directory,
                    error_message=error_message
                )

            # 3. 执行命令
            execution_result = self._execute_command(precondition)

            # 4. 更新统计
            if execution_result.success:
                self.execution_stats["successful_executions"] += 1
            else:
                self.execution_stats["failed_executions"] += 1

            self.execution_stats["total_duration_ms"] += execution_result.duration_ms

            # 5. 记录审计日志
            self._log_execution(precondition, execution_result, validation_result)

            return execution_result

        except Exception as e:
            self.execution_stats["failed_executions"] += 1
            duration_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                precondition_passed=False,
                command=command,
                working_directory=working_directory,
                error_message=f"Safe execution failed: {e!s}"
            )

    def _check_preconditions(self, precondition: ExecutionPrecondition):
        """检查前置条件"""
        return self.precondition_checker.validate(precondition)

    def _execute_command(self, precondition: ExecutionPrecondition) -> ExecutionResult:
        """执行命令"""
        # 创建进程
        process_info = self.process_manager.create_process(
            command=precondition.command,
            working_directory=precondition.working_directory
        )

        try:
            # 等待执行完成
            result = self.process_manager.wait_with_timeout(
                process_info=process_info,
                timeout_seconds=precondition.timeout_seconds
            )

            # 设置工作目录到结果中
            result.working_directory = precondition.working_directory
            result.precondition_passed = True

            return result

        finally:
            # 清理进程资源
            self.process_manager.cleanup_process(process_info)

    def _log_execution(self, precondition: ExecutionPrecondition, result: ExecutionResult, validation_result):
        """记录执行日志"""
        try:
            # 构建审计日志
            audit_data = {
                "type": "safe_exec",
                "command": precondition.command,
                "working_directory": precondition.working_directory,
                "risk_level": precondition.risk_level.value,
                "validation_errors": validation_result.errors,
                "validation_warnings": validation_result.warnings,
                "execution_success": result.success,
                "exit_code": result.exit_code,
                "duration_ms": result.duration_ms,
                "timeout_occurred": result.timeout_occurred,
                "timestamp": time.time()
            }

            # 如果有执行引擎，记录到审计日志
            if self.agent and hasattr(self.agent, 'execution_engine'):
                self.agent.execution_engine.log_execution(audit_data)
            else:
                # 简单的控制台输出
                print(f"[SafeExec] {precondition.command} -> {'SUCCESS' if result.success else 'FAILED'}")

        except Exception as e:
            # 日志记录失败不应该影响主流程
            print(f"Warning: Failed to log execution: {e}")

    def get_execution_statistics(self) -> dict[str, Any]:
        """获取执行统计信息"""
        stats = self.execution_stats.copy()

        # 计算成功率
        if stats["total_executions"] > 0:
            stats["success_rate"] = (
                stats["successful_executions"] / stats["total_executions"]
            )
            stats["average_duration_ms"] = (
                stats["total_duration_ms"] / stats["total_executions"]
            )
        else:
            stats["success_rate"] = 0.0
            stats["average_duration_ms"] = 0.0

        # 添加活跃进程信息
        stats["active_processes"] = len(self.process_manager.get_active_processes())

        return stats

    def cleanup_all_processes(self):
        """清理所有活跃进程"""
        active_processes = self.process_manager.get_active_processes()
        for process_info in active_processes:
            self.process_manager.cleanup_process(process_info)
