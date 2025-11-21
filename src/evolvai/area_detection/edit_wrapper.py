"""
安全编辑包装器
集成AreaDetector、FeedbackSystem和RollbackManager
提供安全的编辑操作接口

Story 2.2 简化版：
- 核心价值：原子性文件写入 + 自动回滚安全网
- 移除了EditValidator验证层（信任AI + 失败时回滚）
- 专注于批量编辑自动化和性能优化
"""

import time
from pathlib import Path
from typing import Any, Optional

from .data_models import EditValidationError, RollbackStrategy
from .detector import AreaDetector
from .feedback import FeedbackSystem
from .rollback_manager import RollbackManager


class SafeEditWrapper:
    """安全编辑包装器（Story 2.2简化版）

    核心功能：
    1. 原子性文件写入（temp file + atomic replace）
    2. 自动回滚安全网（RollbackManager集成）
    3. 批量编辑支持（safe_edit_batch）
    4. 性能指标追踪（TPST优化）

    设计原则：
    - 信任AI生成的代码质量
    - 失败时通过回滚恢复
    - 避免过度验证导致的token浪费
    """

    def __init__(self, agent: Any = None, project: Any = None, config: Optional[dict[str, Any]] = None):
        """
        初始化安全编辑包装器

        Args:
            agent: 代理实例（用于获取项目信息和反馈系统）
            project: 项目实例
            config: 配置参数

        """
        self.agent = agent
        self.project = project
        self.config = config or {}

        # 初始化组件
        self.area_detector = AreaDetector(project.root_path) if project else None
        self.feedback_system = FeedbackSystem() if agent else None

        # 组件将在第一次使用时初始化
        # self._edit_validator: Optional[EditValidator] = None  # Removed in Story 2.2
        self._rollback_manager: Optional[RollbackManager] = None

        # 性能指标
        self.performance_metrics = {
            "total_edits": 0,
            "successful_edits": 0,
            "failed_edits": 0,
            "rollbacks_executed": 0,
            "total_duration_ms": 0.0,
        }

    def safe_edit(self, file_path: str, content: str, auto_rollback: bool = True, **kwargs) -> dict[str, Any]:
        """
        安全编辑文件（简化版 - Story 2.2）

        核心价值：原子性文件写入 + 自动回滚安全网
        验证已移除 - 信任AI + 失败时回滚

        Args:
            file_path: 文件路径
            content: 文件内容
            auto_rollback: 是否自动创建回滚点（默认True）
            **kwargs: 保留向后兼容性

        Returns:
            Dict[str, Any]: 编辑结果
                - success: bool - 是否成功
                - file_path: str - 文件路径
                - rollback_id: Optional[str] - 回滚点ID
                - error: Optional[str] - 错误信息
                - duration_ms: float - 执行时长

        """
        start_time = time.time()
        self.performance_metrics["total_edits"] += 1

        result = {
            "success": False,
            "file_path": file_path,
            "duration_ms": 0.0,
            "rollback_id": None,
            "error": None,
        }

        try:
            # 1. 初始化回滚管理器
            if not self._rollback_manager:
                self._rollback_manager = RollbackManager()

            # 2. 读取原始内容（用于回滚）
            original_content = self._read_file(file_path)

            # 3. 创建回滚点（可选）
            if auto_rollback:
                rollback_result = self._create_rollback_point(file_path, original_content)
                if rollback_result["success"]:
                    result["rollback_id"] = rollback_result["rollback_hash"]

            # 4. 执行文件写入
            write_result = self._write_file(file_path, content)
            if not write_result["success"]:
                result["error"] = write_result["error"]

                # 如果写入失败且有回滚点，尝试自动回滚
                if auto_rollback and result["rollback_id"]:
                    rollback_info = {
                        "strategy": rollback_result["strategy"],
                        "rollback_hash": result["rollback_id"],
                        "file_path": file_path,
                    }
                    self._execute_rollback(rollback_info)
                    self.performance_metrics["rollbacks_executed"] += 1

                self.performance_metrics["failed_edits"] += 1
                return result

            # 5. 标记成功
            result["success"] = True
            self.performance_metrics["successful_edits"] += 1

        except Exception as e:
            result["error"] = f"编辑过程中发生错误: {e!s}"
            self.performance_metrics["failed_edits"] += 1

        finally:
            # 记录持续时间
            duration = (time.time() - start_time) * 1000
            result["duration_ms"] = duration
            self.performance_metrics["total_duration_ms"] += duration

        return result

    def safe_edit_batch(self, edits: list[dict[str, Any]], stop_on_error: bool = True, **kwargs) -> dict[str, Any]:
        """
        批量安全编辑（简化版 - Story 2.2）

        Args:
            edits: 编辑列表，每个元素包含 file_path, content
            stop_on_error: 遇到错误是否停止
            **kwargs: 传递给safe_edit的额外参数

        Returns:
            Dict[str, Any]: 批量编辑结果

        """
        start_time = time.time()
        results = []

        for i, edit in enumerate(edits):
            result = self.safe_edit(file_path=edit["file_path"], content=edit["content"], auto_rollback=True, **kwargs)

            result["edit_index"] = i
            results.append(result)

            # 如果出错且配置为停止，则退出循环
            if stop_on_error and not result["success"]:
                break

        return {
            "success": all(r["success"] for r in results),
            "total_edits": len(edits),
            "successful_edits": sum(1 for r in results if r["success"]),
            "failed_edits": sum(1 for r in results if not r["success"]),
            "results": results,
            "duration_ms": (time.time() - start_time) * 1000,
        }

    def rollback_edit(
        self, file_path: str, backup_info: Optional[dict[str, Any]] = None, strategy: Optional[RollbackStrategy] = None
    ) -> dict[str, Any]:
        """
        回滚编辑操作（Story 2.2简化版）

        支持两种回滚模式：
        1. 智能回滚：自动选择最近的回滚点
        2. 指定回滚：使用特定的backup_info和strategy

        Args:
            file_path: 文件路径
            backup_info: 备份信息（包含rollback_hash和可选的message）
            strategy: 回滚策略（GIT或FILE_BACKUP）

        Returns:
            Dict[str, Any]: 回滚结果
                - success: bool - 是否成功
                - strategy: str - 使用的回滚策略
                - message: str - 回滚信息
                - error: Optional[str] - 错误信息
                - duration_ms: float - 执行时长

        """
        if not self._rollback_manager:
            self._rollback_manager = RollbackManager()

        if not backup_info:
            # 尝试智能回滚
            rollback_result = self._rollback_manager.smart_rollback(file_path)
        else:
            # 使用指定的备份信息回滚
            if strategy == RollbackStrategy.GIT:
                rollback_result = self._rollback_manager.git_rollback(backup_info["rollback_hash"], backup_info.get("message"))
            else:
                rollback_result = self._rollback_manager.rollback_file_backup(backup_info["rollback_hash"], file_path)

        if rollback_result.success:
            self.performance_metrics["rollbacks_executed"] += 1

        return {
            "success": rollback_result.success,
            "strategy": rollback_result.strategy.value,
            "message": rollback_result.message,
            "error": rollback_result.error_message,
            "duration_ms": rollback_result.duration_ms,
        }

    def get_edit_statistics(self) -> dict[str, Any]:
        """
        获取编辑统计信息

        Returns:
            Dict[str, Any]: 统计信息

        """
        metrics = self.performance_metrics.copy()

        # 计算成功率
        if metrics["total_edits"] > 0:
            metrics["success_rate"] = metrics["successful_edits"] / metrics["total_edits"]
            metrics["average_duration_ms"] = metrics["total_duration_ms"] / metrics["total_edits"]
        else:
            metrics["success_rate"] = 0.0
            metrics["average_duration_ms"] = 0.0

        # 添加回滚管理器性能指标
        if self._rollback_manager:
            metrics["rollback_performance"] = self._rollback_manager.get_performance_metrics()

        return metrics

    def _read_file(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return ""  # 新文件

            return path_obj.read_text(encoding="utf-8")
        except Exception as e:
            raise EditValidationError(error_type="FILE_READ_ERROR", message=f"无法读取文件: {e!s}", file_path=file_path)

    def _write_file(self, file_path: str, content: str) -> dict[str, Any]:
        """写入文件"""
        try:
            path_obj = Path(file_path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)

            # 写入临时文件，然后原子性移动（避免部分写入）
            temp_file = path_obj.with_suffix(path_obj.suffix + ".tmp")
            temp_file.write_text(content, encoding="utf-8")
            temp_file.replace(path_obj)

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"文件写入失败: {e!s}"}

    def _create_rollback_point(self, file_path: str, original_content: str) -> dict[str, Any]:
        """创建回滚点"""
        if not self._rollback_manager:
            self._rollback_manager = RollbackManager()

        result = self._rollback_manager.create_file_backup(file_path)

        return {
            "success": result.success,
            "strategy": result.strategy.value,
            "rollback_hash": result.rollback_hash,
            "message": result.message,
            "error": result.error_message,
            "duration_ms": result.duration_ms,
        }

    def _execute_rollback(self, rollback_info: dict[str, Any]):
        """执行回滚操作"""
        if rollback_info["strategy"] == "git":
            if self._rollback_manager:
                self._rollback_manager.git_rollback(rollback_info["rollback_hash"])
        else:
            if self._rollback_manager:
                self._rollback_manager.rollback_file_backup(rollback_info["rollback_hash"], rollback_info["file_path"])

    def _send_edit_feedback(self, file_path: str, validation_results: dict[str, Any], mode: str):
        """发送编辑反馈（已废弃 - Story 2.2移除）

        保留此方法仅为向后兼容，实际不再使用。
        """
        if not self.feedback_system:
            return

        # Method deprecated - kept for backward compatibility only
