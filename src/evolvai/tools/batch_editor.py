"""
Story 2.2 - BatchEditor核心实现
统一批量编辑工具，支持预览模式和ExecutionPlan约束
"""

import difflib
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from evolvai.area_detection.rollback_manager import RollbackManager
from evolvai.core.execution_plan import ExecutionPlan


@dataclass
class BatchEditResult:
    """批量编辑结果"""

    success: bool
    affected_files: list[Path] = field(default_factory=list)
    changes_count: int = 0
    unified_diff: str = ""
    rollback_id: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class FileChange:
    """单个文件的变更"""

    file_path: Path
    original_content: str
    new_content: str
    match_count: int
    rollback_hash: Optional[str] = None  # 文件级备份ID（精确回滚）


class BatchEditor:
    """统一批量编辑器（Story 2.2简化版）

    核心功能：
    1. 批量搜索和替换（regex支持）
    2. 预览模式（diff without apply）
    3. ExecutionPlan约束验证
    4. 自动回滚安全网

    设计原则：
    - 信任AI生成的pattern和replacement
    - 提供preview选项让AI验证变更
    - ExecutionPlan防止意外大规模修改
    - 失败时自动回滚
    """

    def __init__(self, project_root: Path):
        """初始化批量编辑器

        Args:
            project_root: 项目根目录

        """
        self.project_root = Path(project_root)
        self.rollback_manager = RollbackManager()

    def batch_edit(
        self,
        pattern: str,
        replacement: str,
        scope: str = "**/*",
        preview: bool = False,
        execution_plan: Optional[ExecutionPlan] = None,
    ) -> BatchEditResult:
        r"""批量编辑文件

        Args:
            pattern: 正则表达式搜索模式
            replacement: 替换文本（支持\1, \2等捕获组引用）
            scope: Glob模式（如"*.py", "src/**/*.ts"）
            preview: True=仅预览diff, False=直接应用
            execution_plan: ExecutionPlan约束（max_files, max_changes）

        Returns:
            BatchEditResult: 包含affected_files, changes_count, unified_diff等

        """
        start_time = time.time()
        result = BatchEditResult(success=False)

        try:
            # 1. 编译正则表达式
            try:
                regex = re.compile(pattern)
            except re.error as e:
                result.error_message = f"Invalid regex pattern: {e}"
                result.duration_ms = (time.time() - start_time) * 1000
                return result

            # 2. 查找匹配文件
            files = self._find_files(scope)
            if not files:
                # 无匹配文件，返回空成功结果
                result.success = True
                result.duration_ms = (time.time() - start_time) * 1000
                return result

            # 3. 生成变更
            changes = self._generate_changes(files, regex, replacement)
            if not changes:
                # 无匹配内容，返回空成功结果
                result.success = True
                result.duration_ms = (time.time() - start_time) * 1000
                return result

            # 4. 检查ExecutionPlan约束
            if execution_plan:
                constraint_error = self._check_constraints(changes, execution_plan)
                if constraint_error:
                    result.error_message = constraint_error
                    result.duration_ms = (time.time() - start_time) * 1000
                    return result

            # 5. 生成unified diff
            result.unified_diff = self._create_unified_diff(changes)
            result.affected_files = [change.file_path for change in changes]
            result.changes_count = sum(change.match_count for change in changes)

            # 6. 预览模式：返回diff不应用
            if preview:
                result.success = True
                result.duration_ms = (time.time() - start_time) * 1000
                return result

            # 7. 应用模式：创建备份 → 写入文件 + 回滚安全网
            try:
                # 7.1 先创建备份（获取rollback_id）
                rollback_id = self._create_backups(changes)
                result.rollback_id = rollback_id

                # 7.2 然后写入文件
                self._write_changes(changes)
                result.success = True
            except Exception as e:
                # 应用失败，尝试回滚
                result.error_message = f"Apply failed: {e}"
                # rollback_id已经保存在result中
                if result.rollback_id:
                    self._rollback_changes(changes)  # 传递changes列表而不是rollback_id
                result.duration_ms = (time.time() - start_time) * 1000
                return result

        except Exception as e:
            result.error_message = f"Batch edit error: {e}"

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    def _find_files(self, scope: str) -> list[Path]:
        """查找匹配scope的文件

        Args:
            scope: Glob模式（如"*.py", "**/*.ts"）

        Returns:
            匹配的文件列表

        """
        files = list(self.project_root.glob(scope))
        # 仅返回文件，不包括目录
        return [f for f in files if f.is_file()]

    def _generate_changes(self, files: list[Path], regex: re.Pattern, replacement: str) -> list[FileChange]:
        """生成文件变更列表

        Args:
            files: 要处理的文件列表
            regex: 编译后的正则表达式
            replacement: 替换文本

        Returns:
            FileChange列表（仅包含有匹配的文件）

        """
        changes = []
        for file_path in files:
            try:
                original_content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                # 跳过无法读取的文件（二进制文件、无权限等）
                continue

            # 执行正则替换
            new_content, match_count = regex.subn(replacement, original_content)

            # 仅添加有变更的文件
            if match_count > 0:
                changes.append(
                    FileChange(
                        file_path=file_path,
                        original_content=original_content,
                        new_content=new_content,
                        match_count=match_count,
                    )
                )

        return changes

    def _create_unified_diff(self, changes: list[FileChange]) -> str:
        """生成unified diff格式的变更摘要

        Args:
            changes: 文件变更列表

        Returns:
            Unified diff字符串

        """
        diff_lines = []
        for change in changes:
            # 生成单个文件的diff
            original_lines = change.original_content.splitlines(keepends=True)
            new_lines = change.new_content.splitlines(keepends=True)

            file_diff = difflib.unified_diff(
                original_lines,
                new_lines,
                fromfile=f"a/{change.file_path.relative_to(self.project_root)}",
                tofile=f"b/{change.file_path.relative_to(self.project_root)}",
                lineterm="",
            )

            diff_lines.extend(file_diff)

        return "\n".join(diff_lines)

    def _check_constraints(self, changes: list[FileChange], plan: ExecutionPlan) -> Optional[str]:
        """检查ExecutionPlan约束

        Args:
            changes: 文件变更列表
            plan: ExecutionPlan约束

        Returns:
            错误信息（如果违反约束），否则None

        """
        # 检查max_files约束
        if len(changes) > plan.limits.max_files:
            return (
                f"ExecutionPlan constraint violation: "
                f"Attempting to modify {len(changes)} files, "
                f"but max_files={plan.limits.max_files}"
            )

        # 检查max_changes约束
        total_changes = sum(change.match_count for change in changes)
        if total_changes > plan.limits.max_changes:
            return f"ExecutionPlan constraint violation: Attempting {total_changes} changes, but max_changes={plan.limits.max_changes}"

        return None

    def _create_backups(self, changes: list[FileChange]) -> str:
        """创建文件备份

        Args:
            changes: 文件变更列表（会修改change.rollback_hash）

        Returns:
            rollback_id: 批次回滚点ID（第一个文件的hash）

        Raises:
            RuntimeError: 备份创建失败时抛出

        """
        for change in changes:
            result = self.rollback_manager.create_file_backup(str(change.file_path))
            if not result.success:
                raise RuntimeError(f"Failed to create backup for {change.file_path}")
            # 保存每个文件的精确rollback_hash
            change.rollback_hash = result.rollback_hash

        # 返回第一个文件的hash作为批次ID（向后兼容）
        return changes[0].rollback_hash if changes else None

    def _write_changes(self, changes: list[FileChange]) -> None:
        """原子性写入文件变更

        Args:
            changes: 文件变更列表

        Raises:
            RuntimeError: 写入失败时抛出

        """
        try:
            for change in changes:
                # 写入临时文件，然后原子性移动
                temp_file = change.file_path.with_suffix(change.file_path.suffix + ".tmp")
                temp_file.write_text(change.new_content, encoding="utf-8")
                temp_file.replace(change.file_path)
        except Exception as e:
            # 写入失败，抛出异常让上层处理回滚
            raise RuntimeError(f"Write failed: {e}") from e

    def _rollback_changes(self, changes: list[FileChange]) -> None:
        """精确回滚变更（使用文件级备份ID）

        Args:
            changes: 需要回滚的文件变更列表（必须有rollback_hash）

        设计原则：
        - 只恢复batch_edit修改的文件（不影响用户其他工作）
        - 使用精确的rollback_hash（不依赖smart_rollback猜测）
        - 逐个回滚，单个失败不影响其他文件

        """
        for change in changes:
            if not change.rollback_hash:
                # 没有备份ID，跳过（理论上不应该发生）
                continue

            try:
                # 使用精确的rollback_hash恢复文件
                result = self.rollback_manager.rollback_file_backup(change.rollback_hash, str(change.file_path))
                if not result.success:
                    # 记录失败但继续其他文件
                    pass
            except Exception:
                # 单个文件回滚失败，继续回滚其他文件
                # 确保尽可能多的文件被恢复
                pass
