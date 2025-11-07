"""
Patch-First Editor - 安全的代码编辑器
propose → diff → apply架构
"""

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from difflib import unified_diff
from pathlib import Path
from typing import Any, Optional


@dataclass
class ProposalResult:
    """编辑提案结果"""

    patch_id: str
    unified_diff: str
    affected_files: list[str]
    statistics: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ApplyResult:
    """应用补丁结果"""

    success: bool
    modified_files: list[str]
    worktree_path: Optional[str] = None
    audit_log_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PatchContent:
    """存储的补丁内容"""

    patch_id: str
    unified_diff: str
    affected_files: list[str]
    created_at: datetime
    metadata: dict[str, Any]


class PatchEditor:
    """
    Patch-First编辑器

    核心原则：
    1. propose_edit生成diff，不修改文件
    2. apply_edit通过Git worktree隔离执行
    3. 失败自动回滚，成功才合并
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化PatchEditor

        Args:
            project_root: 项目根目录，默认为当前目录

        """
        self.project_root = project_root or Path.cwd()
        self.patch_store: dict[str, PatchContent] = {}

    def propose_edit(
        self,
        pattern: str,
        replacement: str,
        scope: str = "**/*",
        language: Optional[str] = None,
        **kwargs
    ) -> ProposalResult:
        """
        生成编辑提案，不修改文件

        Args:
            pattern: 搜索模式（正则表达式或字符串）
            replacement: 替换内容
            scope: 文件范围（glob pattern）
            language: 语言过滤（可选）
            **kwargs: 其他参数

        Returns:
            ProposalResult: 包含patch_id和unified_diff

        Raises:
            ValueError: 参数无效
            FileNotFoundError: 找不到匹配文件

        """
        # 1. 扫描匹配的文件
        matched_files = list(self.project_root.glob(scope))
        matched_files = [f for f in matched_files if f.is_file()]
        
        if not matched_files:
            raise FileNotFoundError(f"No files found matching scope: {scope}")
        
        # 2. 对每个文件生成diff
        affected_files = []
        all_diffs = []
        lines_changed = 0
        
        for file_path in matched_files:
            try:
                original_content = file_path.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue  # 跳过二进制文件或无权限文件
            
            # 执行替换
            new_content = re.sub(pattern, replacement, original_content)
            
            # 如果内容没有变化，跳过
            if new_content == original_content:
                continue
            
            # 生成unified diff
            relative_path = file_path.relative_to(self.project_root)
            original_lines = original_content.splitlines(keepends=True)
            new_lines = new_content.splitlines(keepends=True)
            
            diff = unified_diff(
                original_lines,
                new_lines,
                fromfile=f"a/{relative_path}",
                tofile=f"b/{relative_path}",
                lineterm=""
            )
            
            diff_text = "".join(diff)
            if diff_text:
                all_diffs.append(diff_text)
                affected_files.append(str(relative_path))
                lines_changed += abs(len(new_lines) - len(original_lines))
        
        if not affected_files:
            raise ValueError("No changes would be made with the given pattern")
        
        # 3. 生成patch_id和结果
        patch_id = self._generate_patch_id()
        unified_diff_text = "\n".join(all_diffs)
        
        statistics = {
            "files_modified": len(affected_files),
            "lines_changed": lines_changed,
            "pattern": pattern,
            "replacement": replacement
        }
        
        # 4. 保存到patch_store
        patch_content = PatchContent(
            patch_id=patch_id,
            unified_diff=unified_diff_text,
            affected_files=affected_files,
            created_at=datetime.now(),
            metadata={"scope": scope, "language": language}
        )
        self.patch_store[patch_id] = patch_content
        
        # 5. 返回结果
        return ProposalResult(
            patch_id=patch_id,
            unified_diff=unified_diff_text,
            affected_files=affected_files,
            statistics=statistics
        )

    def apply_edit(
        self,
        patch_id: str,
        execution_plan: Optional[Any] = None,
        **kwargs
    ) -> ApplyResult:
        """
        应用已验证的patch

        Args:
            patch_id: 补丁ID
            execution_plan: ExecutionPlan约束（可选）
            **kwargs: 其他参数

        Returns:
            ApplyResult: 应用结果

        Raises:
            PatchNotFoundError: patch_id不存在
            PatchConflictError: patch冲突
            TimeoutError: 操作超时

        """
        raise NotImplementedError("apply_edit will be implemented in Day 3")

    def _generate_patch_id(self) -> str:
        """生成唯一的patch_id"""
        timestamp = int(time.time() * 1000)
        hash_input = f"{timestamp}_{id(self)}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        return f"patch_{timestamp}_{hash_value}"


class PatchNotFoundError(Exception):
    """Patch不存在错误"""



class PatchConflictError(Exception):
    """Patch冲突错误"""
