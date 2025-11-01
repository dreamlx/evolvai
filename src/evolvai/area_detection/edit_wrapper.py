"""
安全编辑包装器
集成AreaDetector、FeedbackSystem、EditValidator和RollbackManager
提供安全的编辑操作接口
"""

import json
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .data_models import (
    ProjectArea,
    AppliedArea,
    EditValidationResult,
    RollbackResult,
    RollbackStrategy,
    EditValidationError
)
from .edit_validator import EditValidator
from .rollback_manager import RollbackManager
from .detector import AreaDetector
from .feedback import FeedbackSystem


class SafeEditWrapper:
    """安全编辑包装器"""

    def __init__(
        self,
        agent: Any = None,
        project: Any = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化安全编辑包装器

        Args:
            agent: 代理实例（用于获取项目信息）
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
        self._edit_validator: Optional[EditValidator] = None
        self._rollback_manager: Optional[RollbackManager] = None

        # 性能指标
        self.performance_metrics = {
            "total_edits": 0,
            "successful_edits": 0,
            "failed_edits": 0,
            "rollbacks_executed": 0,
            "total_duration_ms": 0.0
        }

    def safe_edit(
        self,
        file_path: str,
        content: str,
        mode: str = "safe",
        language: Optional[str] = None,
        auto_rollback: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        安全编辑文件

        Args:
            file_path: 文件路径
            content: 文件内容
            mode: 编辑模式 (safe, normal, aggressive)
            language: 编程语言（自动检测如果未提供）
            auto_rollback: 是否自动创建回滚点

        Returns:
            Dict[str, Any]: 编辑结果
        """
        start_time = time.time()
        self.performance_metrics["total_edits"] += 1

        result = {
            "success": False,
            "file_path": file_path,
            "mode": mode,
            "duration_ms": 0.0,
            "validation_result": None,
            "rollback_info": None,
            "error": None,
            "warnings": []
        }

        try:
            # 1. 检测项目区域和语言
            areas, applied_areas = self._get_project_areas()
            detected_language = language or self._detect_language(file_path, content)

            # 2. 初始化验证器和回滚管理器
            self._edit_validator = EditValidator(areas, applied_areas)
            self._rollback_manager = RollbackManager()

            # 3. 读取原始内容
            original_content = self._read_file(file_path)

            # 4. 执行验证链
            validation_results = self._execute_validation_chain(
                file_path=file_path,
                original_content=original_content,
                edited_content=content,
                language=detected_language,
                mode=mode
            )

            result["validation_result"] = validation_results

            # 检查验证是否通过
            if not validation_results.get("is_valid", False):
                result["error"] = validation_results.get("error_message", "验证失败")
                result["warnings"] = validation_results.get("warnings", [])
                self.performance_metrics["failed_edits"] += 1
                return result

            # 5. 创建回滚点（如果启用）
            if auto_rollback:
                rollback_result = self._create_rollback_point(file_path, original_content)
                result["rollback_info"] = rollback_result

                if not rollback_result["success"]:
                    # 如果回滚点创建失败，警告但不阻止编辑
                    result["warnings"].append(f"回滚点创建失败: {rollback_result['error']}")

            # 6. 执行文件写入
            write_result = self._write_file(file_path, content)
            if not write_result["success"]:
                result["error"] = write_result["error"]

                # 如果写入失败且有回滚点，尝试自动回滚
                if auto_rollback and result["rollback_info"] and result["rollback_info"]["success"]:
                    self._execute_rollback(result["rollback_info"])
                    result["rollback_executed"] = True
                    self.performance_metrics["rollbacks_executed"] += 1

                self.performance_metrics["failed_edits"] += 1
                return result

            # 7. 发送反馈
            if self.feedback_system:
                self._send_edit_feedback(
                    file_path=file_path,
                    validation_results=validation_results,
                    mode=mode
                )

            # 8. 标记成功
            result["success"] = True
            result["warnings"] = validation_results.get("warnings", [])
            self.performance_metrics["successful_edits"] += 1

        except EditValidationError as e:
            result["error"] = str(e)
            result["error_type"] = e.error_type
            self.performance_metrics["failed_edits"] += 1

        except Exception as e:
            result["error"] = f"编辑过程中发生未预期错误: {str(e)}"
            self.performance_metrics["failed_edits"] += 1

        finally:
            # 记录持续时间
            duration = (time.time() - start_time) * 1000
            result["duration_ms"] = duration
            self.performance_metrics["total_duration_ms"] += duration

        return result

    def safe_edit_batch(
        self,
        edits: List[Dict[str, Any]],
        mode: str = "safe",
        stop_on_error: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        批量安全编辑

        Args:
            edits: 编辑列表，每个元素包含 file_path, content
            mode: 编辑模式
            stop_on_error: 遇到错误是否停止

        Returns:
            Dict[str, Any]: 批量编辑结果
        """
        start_time = time.time()
        results = []

        for i, edit in enumerate(edits):
            result = self.safe_edit(
                file_path=edit["file_path"],
                content=edit["content"],
                mode=mode,
                auto_rollback=True,
                **kwargs
            )

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
            "duration_ms": (time.time() - start_time) * 1000
        }

    def rollback_edit(
        self,
        file_path: str,
        backup_info: Optional[Dict[str, Any]] = None,
        strategy: Optional[RollbackStrategy] = None
    ) -> Dict[str, Any]:
        """
        回滚编辑操作

        Args:
            file_path: 文件路径
            backup_info: 备份信息
            strategy: 回滚策略

        Returns:
            Dict[str, Any]: 回滚结果
        """
        if not self._rollback_manager:
            self._rollback_manager = RollbackManager()

        if not backup_info:
            # 尝试智能回滚
            rollback_result = self._rollback_manager.smart_rollback(file_path)
        else:
            # 使用指定的备份信息回滚
            if strategy == RollbackStrategy.GIT:
                rollback_result = self._rollback_manager.git_rollback(
                    backup_info["rollback_hash"],
                    backup_info.get("message")
                )
            else:
                rollback_result = self._rollback_manager.rollback_file_backup(
                    backup_info["rollback_hash"],
                    file_path
                )

        if rollback_result.success:
            self.performance_metrics["rollbacks_executed"] += 1

        return {
            "success": rollback_result.success,
            "strategy": rollback_result.strategy.value,
            "message": rollback_result.message,
            "error": rollback_result.error_message,
            "duration_ms": rollback_result.duration_ms
        }

    def get_edit_statistics(self) -> Dict[str, Any]:
        """
        获取编辑统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        metrics = self.performance_metrics.copy()

        # 计算成功率
        if metrics["total_edits"] > 0:
            metrics["success_rate"] = (
                metrics["successful_edits"] / metrics["total_edits"]
            )
            metrics["average_duration_ms"] = (
                metrics["total_duration_ms"] / metrics["total_edits"]
            )
        else:
            metrics["success_rate"] = 0.0
            metrics["average_duration_ms"] = 0.0

        # 添加回滚管理器性能指标
        if self._rollback_manager:
            metrics["rollback_performance"] = (
                self._rollback_manager.get_performance_metrics()
            )

        return metrics

    def validate_edit_only(
        self,
        file_path: str,
        content: str,
        mode: str = "safe",
        **kwargs
    ) -> Dict[str, Any]:
        """
        仅验证编辑（不执行实际编辑）

        Args:
            file_path: 文件路径
            content: 文件内容
            mode: 编辑模式

        Returns:
            Dict[str, Any]: 验证结果
        """
        # 获取项目区域
        areas, applied_areas = self._get_project_areas()

        # 检测语言
        original_content = self._read_file(file_path)
        detected_language = kwargs.get("language") or self._detect_language(file_path, original_content)

        # 执行验证
        self._edit_validator = EditValidator(areas, applied_areas)
        validation_results = self._execute_validation_chain(
            file_path=file_path,
            original_content=original_content,
            edited_content=content,
            language=detected_language,
            mode=mode
        )

        return validation_results

    def _get_project_areas(self) -> tuple[List[ProjectArea], List[AppliedArea]]:
        """获取项目区域信息"""
        if self.area_detector:
            # 获取项目区域
            areas = self.area_detector.get_areas()
            applied_areas = self.area_detector.get_applied_areas()
            return areas, applied_areas

        # 返回空列表（如果没有区域检测器）
        return [], []

    def _detect_language(self, file_path: str, content: str) -> str:
        """检测编程语言"""
        path_obj = Path(file_path)

        # 根据文件扩展名检测
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".sh": "bash"
        }

        extension = path_obj.suffix.lower()
        if extension in extension_map:
            return extension_map[extension]

        # 尝试从内容中检测
        if "#!/usr/bin/python" in content or "import " in content and " from " in content:
            return "python"
        if "package main" in content or "func " in content:
            return "go"
        if "public class " in content or "System.out.println" in content:
            return "java"
        if "function " in content or "const " in content or "import " in content:
            return "javascript"

        return "text"  # 默认值

    def _read_file(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return ""  # 新文件

            return path_obj.read_text(encoding='utf-8')
        except Exception as e:
            raise EditValidationError(
                error_type="FILE_READ_ERROR",
                message=f"无法读取文件: {str(e)}",
                file_path=file_path
            )

    def _write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """写入文件"""
        try:
            path_obj = Path(file_path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)

            # 写入临时文件，然后原子性移动（避免部分写入）
            temp_file = path_obj.with_suffix(path_obj.suffix + ".tmp")
            temp_file.write_text(content, encoding='utf-8')
            temp_file.replace(path_obj)

            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error": f"文件写入失败: {str(e)}"
            }

    def _execute_validation_chain(
        self,
        file_path: str,
        original_content: str,
        edited_content: str,
        language: str,
        mode: str
    ) -> Dict[str, Any]:
        """执行完整的验证链"""
        combined_result = {
            "is_valid": True,
            "warnings": [],
            "syntax_errors": [],
            "area_violations": [],
            "size_warnings": [],
            "import_warnings": []
        }

        # 1. 语法验证
        syntax_result = self._edit_validator.validate_edit_syntax(
            original_content,
            edited_content,
            file_path,
            language
        )

        if not syntax_result.is_valid:
            combined_result["is_valid"] = False
            combined_result["syntax_errors"] = syntax_result.syntax_errors
            combined_result["syntax_error_message"] = syntax_result.error_message

        combined_result["warnings"].extend(syntax_result.warnings)

        # 2. 区域约束验证
        try:
            area_result = self._edit_validator.validate_area_constraints(
                file_path,
                edited_content,
                mode
            )
            combined_result["warnings"].extend(area_result.warnings)
        except EditValidationError as e:
            combined_result["is_valid"] = False
            combined_result["area_violations"].append({
                "type": e.error_type,
                "message": e.message,
                "file": e.file_path
            })

        # 3. 大小约束验证
        size_result = self._edit_validator.validate_size_constraints(
            file_path,
            original_content,
            edited_content
        )

        if not size_result.is_valid:
            combined_result["is_valid"] = False
            combined_result["size_error"] = size_result.error_message

        combined_result["warnings"].extend(size_result.warnings)
        combined_result["changes_count"] = size_result.changes_count
        combined_result["lines_added"] = size_result.lines_added
        combined_result["lines_removed"] = size_result.lines_removed

        # 4. 导入变更验证
        import_result = self._edit_validator.validate_import_changes(
            original_content,
            edited_content,
            file_path,
            language
        )

        combined_result["warnings"].extend(import_result.warnings)
        combined_result["new_imports"] = import_result.new_imports
        combined_result["removed_imports"] = import_result.removed_imports

        # 合并错误消息
        all_errors = []
        if syntax_result.error_message:
            all_errors.append(syntax_result.error_message)
        if size_result.error_message:
            all_errors.append(size_result.error_message)

        if all_errors:
            combined_result["error_message"] = " | ".join(all_errors)

        return combined_result

    def _create_rollback_point(self, file_path: str, original_content: str) -> Dict[str, Any]:
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
            "duration_ms": result.duration_ms
        }

    def _execute_rollback(self, rollback_info: Dict[str, Any]):
        """执行回滚操作"""
        if rollback_info["strategy"] == "git":
            if self._rollback_manager:
                self._rollback_manager.git_rollback(rollback_info["rollback_hash"])
        else:
            if self._rollback_manager:
                self._rollback_manager.rollback_file_backup(
                    rollback_info["rollback_hash"],
                    rollback_info["file_path"]
                )

    def _send_edit_feedback(self, file_path: str, validation_results: Dict[str, Any], mode: str):
        """发送编辑反馈"""
        if not self.feedback_system:
            return

        try:
            feedback_data = {
                "type": "safe_edit",
                "file_path": file_path,
                "mode": mode,
                "validation": validation_results,
                "success": validation_results.get("is_valid", False)
            }

            # 发送反馈（具体实现取决于FeedbackSystem的API）
            # self.feedback_system.send_feedback(feedback_data)
        except Exception as e:
            # 反馈发送失败不影响主流程
            print(f"发送反馈失败: {e}")