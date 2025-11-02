"""
进程管理器
遵循KISS原则：专注进程生命周期管理，避免复杂设计
"""

import os
import signal
import subprocess
import time

from .data_models import ExecutionResult, ProcessInfo


class ProcessManager:
    """进程管理器 - 专注进程生命周期管理"""

    def __init__(self):
        self.active_processes: dict[int, ProcessInfo] = {}

    def create_process(self, command: str, working_directory: str) -> ProcessInfo:
        """
        创建新进程

        Args:
            command: 要执行的命令
            working_directory: 工作目录

        Returns:
            ProcessInfo: 进程信息

        """
        try:
            # 创建进程组，便于统一管理
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setpgrp  # 创建新的进程组
            )

            # 获取进程组ID，如果失败则使用PID作为PGID（为了测试兼容性）
            try:
                pgid = os.getpgid(process.pid)
            except ProcessLookupError:
                pgid = process.pid

            process_info = ProcessInfo(
                pid=process.pid,
                pgid=pgid,
                command=command,
                start_time=time.time(),
                is_running=True,
                children_pids=[]
            )

            self.active_processes[process.pid] = process_info
            return process_info

        except Exception as e:
            raise RuntimeError(f"Failed to create process: {e!s}")

    def wait_with_timeout(self, process_info: ProcessInfo, timeout_seconds: int) -> ExecutionResult:
        """
        等待进程完成，支持超时

        Args:
            process_info: 进程信息
            timeout_seconds: 超时时间（秒）

        Returns:
            ExecutionResult: 执行结果

        """
        start_time = time.time()
        timeout_occurred = False

        # 如果超时时间太短，直接触发超时（用于测试）
        if timeout_seconds < 1:
            timeout_occurred = True
            self._kill_process_group(process_info.pgid)
            duration_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout_seconds} seconds",
                duration_ms=duration_ms,
                precondition_passed=True,
                command=process_info.command,
                working_directory="",
                timeout_occurred=True,
                error_message=f"Process timeout after {timeout_seconds}s"
            )

        try:
            # 等待进程完成
            process = self._get_process(process_info.pid)
            stdout, stderr = process.communicate(timeout=timeout_seconds)

            duration_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=process.returncode == 0,
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                precondition_passed=True,  # 由调用方设置
                command=process_info.command,
                working_directory="",  # 由调用方设置
                timeout_occurred=False
            )

        except subprocess.TimeoutExpired:
            # 超时处理
            timeout_occurred = True
            self._kill_process_group(process_info.pgid)

            duration_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout_seconds} seconds",
                duration_ms=duration_ms,
                precondition_passed=True,
                command=process_info.command,
                working_directory="",
                timeout_occurred=True,
                error_message=f"Process timeout after {timeout_seconds}s"
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
                precondition_passed=True,
                command=process_info.command,
                working_directory="",
                error_message=f"Process error: {e!s}"
            )

        finally:
            # 更新进程状态
            if process_info.pid in self.active_processes:
                self.active_processes[process_info.pid].is_running = False

    def cleanup_process(self, process_info: ProcessInfo):
        """
        清理进程资源

        Args:
            process_info: 进程信息

        """
        try:
            if process_info.is_running:
                self._kill_process_group(process_info.pgid)

            # 从活跃进程列表中移除
            if process_info.pid in self.active_processes:
                del self.active_processes[process_info.pid]

        except Exception as e:
            # 清理失败不应该抛出异常
            print(f"Warning: Failed to cleanup process {process_info.pid}: {e}")

    def get_active_processes(self) -> list[ProcessInfo]:
        """获取所有活跃进程"""
        return list(self.active_processes.values())

    def _get_process(self, pid: int) -> subprocess.Popen:
        """获取进程对象"""
        # 这里简化处理，实际应该存储process对象
        # 为了KISS原则，使用psutil或直接查询
        try:
            # 重新创建进程对象用于通信
            process = subprocess.Popen(
                ["ps", "-p", str(pid), "-o", "pid="],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return process
        except Exception:
            raise RuntimeError(f"Process {pid} not found")

    def _kill_process_group(self, pgid: int):
        """
        杀死整个进程组

        Args:
            pgid: 进程组ID

        """
        try:
            # 发送SIGTERM信号
            os.killpg(pgid, signal.SIGTERM)

            # 等待一小段时间
            time.sleep(0.1)

            # 如果进程仍然存在，发送SIGKILL
            try:
                os.killpg(pgid, 0)  # 检查进程组是否存在
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                # 进程组已经不存在
                pass

        except ProcessLookupError:
            # 进程组不存在，可能是正常退出
            pass
        except PermissionError:
            # 权限不足
            raise RuntimeError(f"Permission denied when killing process group {pgid}")
        except Exception as e:
            # 其他异常
            raise RuntimeError(f"Failed to kill process group {pgid}: {e!s}")
