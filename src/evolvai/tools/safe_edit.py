"""
SafeEditTool - Patch-First安全编辑工具

架构决策: ADR-006 - 基于工作目录操作，不使用Git worktree
Story: STORY-2.2

核心原则：
1. propose_edit 生成diff，基于工作目录（包含所有用户修改）
2. apply_edit 只接受 patch_id，带约束检查和回滚
3. 文件备份回滚机制（不是Git worktree）
"""

import hashlib
import re
import time
from dataclasses import dataclass
from datetime import datetime
from difflib import unified_diff
from pathlib import Path
from typing import Any, Optional


# 自定义异常
class PatchNotFoundError(Exception):
    """Patch ID 不存在"""


class PatchAlreadyAppliedError(Exception):
    """Patch 已经被应用过"""


class PatchOutdatedError(Exception):
    """Patch 过期（文件已变化）"""


class ConstraintViolationError(Exception):
    """ExecutionPlan 约束违规"""

    def __init__(self, message: str, constraint_type: str = "", limit: int = 0, actual: int = 0):
        super().__init__(message)
        self.constraint_type = constraint_type
        self.limit = limit
        self.actual = actual


class ApplyError(Exception):
    """应用 Patch 时发生错误"""


@dataclass
class PatchContent:
    """存储的补丁内容"""

    patch_id: str
    unified_diff: str
    affected_files: list[str]
    created_at: datetime
    changes: list[dict[str, Any]]  # [{"file": str, "original": str, "new": str, "hash": str}]
    metadata: dict[str, Any]
    applied: bool = False


class SafeEditTool:
    """
    安全编辑工具 - Patch-First 架构

    使用方式:
    1. result = tool.propose_edit(pattern, replacement, scope)
    2. 用户检查 result["unified_diff"]
    3. tool.apply_edit(result["patch_id"])
    """

    def __init__(self, project_root: Optional[Path] = None, rollback_manager: Any = None):
        """
        初始化 SafeEditTool

        Args:
            project_root: 项目根目录
            rollback_manager: 回滚管理器（可选，用于依赖注入）

        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.patch_store: dict[str, PatchContent] = {}
        self.rollback_manager = rollback_manager

    def propose_edit(self, pattern: str, replacement: str, scope: str = "**/*.py", **kwargs: Any) -> dict[str, Any]:
        """
        生成编辑提案，不修改文件

        基于工作目录操作，包含用户所有修改（unstaged, staged, untracked）

        Args:
            pattern: 搜索模式（正则表达式）
            replacement: 替换内容
            scope: 文件范围（glob pattern）
            **kwargs: 附加参数（存储到 metadata）

        Returns:
            dict: {
                "patch_id": str,
                "unified_diff": str,
                "affected_files": list[str],
                "statistics": dict
            }

        """
        # 1. 扫描工作目录文件（包含所有用户修改）
        matched_files = list(self.project_root.glob(scope))
        matched_files = [f for f in matched_files if f.is_file()]

        # 2. 对每个文件生成 diff
        affected_files = []
        all_diffs = []
        changes = []
        lines_changed = 0

        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        for file_path in matched_files:
            try:
                original_content = file_path.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue  # 跳过二进制文件或无权限文件

            # 执行替换
            new_content = regex.sub(replacement, original_content)

            # 如果内容没有变化，跳过
            if new_content == original_content:
                continue

            # 计算文件哈希（用于检测 Patch 过期）
            file_hash = hashlib.md5(original_content.encode()).hexdigest()

            # 生成 unified diff
            relative_path = str(file_path.relative_to(self.project_root))

            # 确保内容以换行符结尾
            orig_for_diff = original_content
            new_for_diff = new_content
            if not orig_for_diff.endswith("\n"):
                orig_for_diff += "\n"
            if not new_for_diff.endswith("\n"):
                new_for_diff += "\n"

            diff = unified_diff(
                orig_for_diff.splitlines(keepends=True),
                new_for_diff.splitlines(keepends=True),
                fromfile=f"a/{relative_path}",
                tofile=f"b/{relative_path}",
            )

            diff_text = "".join(diff)
            if diff_text:
                all_diffs.append(diff_text)
                affected_files.append(relative_path)

                # 计算变更行数
                added = diff_text.count("\n+") - 1  # 排除 +++ 行
                removed = diff_text.count("\n-") - 1  # 排除 --- 行
                lines_changed += added + removed

                # 保存变更详情
                changes.append({"file": relative_path, "original": original_content, "new": new_content, "hash": file_hash})

        # 3. 生成 patch_id
        patch_id = self._generate_patch_id()
        unified_diff_text = "\n".join(all_diffs) if all_diffs else ""

        # 4. 统计信息
        statistics = {"files_modified": len(affected_files), "lines_changed": lines_changed, "pattern": pattern, "replacement": replacement}

        # 5. 保存到 patch_store
        patch_content = PatchContent(
            patch_id=patch_id,
            unified_diff=unified_diff_text,
            affected_files=affected_files,
            created_at=datetime.now(),
            changes=changes,
            metadata={"scope": scope, "pattern": pattern, "replacement": replacement, **kwargs},
        )
        self.patch_store[patch_id] = patch_content

        # 6. 返回结果
        return {"patch_id": patch_id, "unified_diff": unified_diff_text, "affected_files": affected_files, "statistics": statistics}

    def apply_edit(self, patch_id: str, execution_plan: Any = None) -> dict[str, Any]:
        """
        应用已验证的 patch

        Args:
            patch_id: Patch ID
            execution_plan: ExecutionPlan 约束（可选，Cycle 3 实现）

        Returns:
            dict: {
                "success": bool,
                "rollback_id": str,
                "modified_files": list[str]
            }

        Raises:
            PatchNotFoundError: patch_id 不存在
            PatchAlreadyAppliedError: patch 已经被应用过
            PatchOutdatedError: 文件在 propose 后被修改

        """
        # 1. 验证 patch_id 存在
        if patch_id not in self.patch_store:
            raise PatchNotFoundError(f"Patch '{patch_id}' not found")

        patch = self.patch_store[patch_id]

        # 2. 检查 patch 是否已经应用过
        if patch.applied:
            raise PatchAlreadyAppliedError(f"Patch '{patch_id}' has already been applied")

        # 3. ExecutionPlan 约束检查（在任何修改之前）
        if execution_plan is not None:
            # 3.1 检查 max_files 约束
            num_files = len(patch.affected_files)
            if num_files > execution_plan.limits.max_files:
                raise ConstraintViolationError(
                    f"Patch affects {num_files} files, exceeding limit of {execution_plan.limits.max_files}",
                    constraint_type="max_files",
                    limit=execution_plan.limits.max_files,
                    actual=num_files,
                )

            # 3.2 检查 max_changes 约束
            total_changes = self._count_changes(patch)
            if total_changes > execution_plan.limits.max_changes:
                raise ConstraintViolationError(
                    f"Patch contains {total_changes} changes, exceeding limit of {execution_plan.limits.max_changes}",
                    constraint_type="max_changes",
                    limit=execution_plan.limits.max_changes,
                    actual=total_changes,
                )

            # 3.3 检查 dry_run 模式
            if execution_plan.dry_run:
                return {"success": True, "dry_run": True, "rollback_id": None, "modified_files": patch.affected_files}

        # 4. 检查文件是否在 propose 后被修改（过期检测）
        for change in patch.changes:
            file_path = self.project_root / change["file"]
            if file_path.exists():
                current_content = file_path.read_text()
                current_hash = hashlib.md5(current_content.encode()).hexdigest()
                if current_hash != change["hash"]:
                    raise PatchOutdatedError(
                        f"File '{change['file']}' has changed since propose_edit. Please re-run propose_edit to get updated diff."
                    )

        # 4. 创建备份（用于回滚）
        backups: dict[str, str] = {}
        for change in patch.changes:
            file_path = self.project_root / change["file"]
            if file_path.exists():
                backups[change["file"]] = file_path.read_text()

        # 5. 应用变更
        modified_files = []
        try:
            for change in patch.changes:
                file_path = self.project_root / change["file"]
                file_path.write_text(change["new"])
                modified_files.append(change["file"])

            # 6. 标记 patch 为已应用
            patch.applied = True

            # 7. 生成 rollback_id
            rollback_id = self._generate_rollback_id(patch_id)

            # 8. 如果有 rollback_manager，保存备份
            if self.rollback_manager is not None:
                self.rollback_manager.save_backup(rollback_id, backups)
            else:
                # 简单实现：保存到内存
                if not hasattr(self, "_rollback_store"):
                    self._rollback_store: dict[str, dict[str, str]] = {}
                self._rollback_store[rollback_id] = backups

            return {"success": True, "rollback_id": rollback_id, "modified_files": modified_files}

        except Exception as e:
            # 发生错误时回滚所有已修改的文件（只回滚实际成功写入的）
            for file_name in modified_files:
                if file_name in backups:
                    file_path = self.project_root / file_name
                    file_path.write_text(backups[file_name])
            raise ApplyError(f"Apply failed: {e}")

    def rollback(self, rollback_id: str) -> None:
        """
        手动回滚到之前的状态

        Args:
            rollback_id: apply_edit 返回的 rollback_id

        Raises:
            ValueError: rollback_id 不存在

        """
        # 检查内部存储
        if hasattr(self, "_rollback_store") and rollback_id in self._rollback_store:
            backups = self._rollback_store[rollback_id]
            for file_name, original_content in backups.items():
                file_path = self.project_root / file_name
                file_path.write_text(original_content)
            # 删除已使用的备份
            del self._rollback_store[rollback_id]
            return

        # 检查外部 rollback_manager
        if self.rollback_manager is not None:
            self.rollback_manager.restore_backup(rollback_id)
            return

        raise ValueError(f"Rollback ID '{rollback_id}' not found")

    def _get_patch(self, patch_id: str) -> Optional[dict[str, Any]]:
        """
        获取 Patch 详情

        Args:
            patch_id: Patch ID

        Returns:
            dict 或 None

        """
        if patch_id not in self.patch_store:
            return None

        patch = self.patch_store[patch_id]
        return {
            "patch_id": patch.patch_id,
            "unified_diff": patch.unified_diff,
            "affected_files": patch.affected_files,
            "changes": patch.changes,
            "created_at": patch.created_at,
            "metadata": patch.metadata,
            "applied": patch.applied,
        }

    def _generate_patch_id(self) -> str:
        """生成唯一的 patch_id"""
        timestamp = int(time.time() * 1000)
        hash_input = f"{timestamp}_{id(self)}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        return f"patch_{timestamp}_{hash_value}"

    def _generate_rollback_id(self, patch_id: str) -> str:
        """生成唯一的 rollback_id"""
        timestamp = int(time.time() * 1000)
        hash_input = f"{patch_id}_{timestamp}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        return f"rollback_{timestamp}_{hash_value}"

    def _count_changes(self, patch: PatchContent) -> int:
        """
        计算 patch 中的变更数量

        通过计算 unified diff 中的 +/- 行数来统计
        """
        changes = 0
        for line in patch.unified_diff.split("\n"):
            # 计算以 + 或 - 开头的行（但排除 +++ 和 ---）
            if (line.startswith("+") and not line.startswith("+++")) or (line.startswith("-") and not line.startswith("---")):
                changes += 1
        return changes


# 导出
__all__ = [
    "ApplyError",
    "ConstraintViolationError",
    "PatchAlreadyAppliedError",
    "PatchNotFoundError",
    "PatchOutdatedError",
    "SafeEditTool",
]
