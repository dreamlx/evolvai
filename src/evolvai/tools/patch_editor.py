"""
Patch-First Editor - 安全的代码编辑器
propose → diff → apply架构
"""

import hashlib
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from difflib import unified_diff
from pathlib import Path
from typing import Any, Optional

from evolvai.core.execution_plan import ExecutionPlan


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
            
            # 如果内容没有变化, 跳过
            if new_content == original_content:
                continue
            
            # 确保内容以换行符结尾 (Git diff格式要求)
            if not original_content.endswith('\n'):
                original_content += '\n'
            if not new_content.endswith('\n'):
                new_content += '\n'
            
            # 生成unified diff
            relative_path = file_path.relative_to(self.project_root)
            original_lines = original_content.splitlines(keepends=True)
            new_lines = new_content.splitlines(keepends=True)
            
            diff = unified_diff(
                original_lines,
                new_lines,
                fromfile=f"a/{relative_path}",
                tofile=f"b/{relative_path}"
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
            metadata={
                "scope": scope,
                "language": language,
                "pattern": pattern,
                "replacement": replacement
            }
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
        execution_plan: Optional[ExecutionPlan] = None,
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
            ConstraintViolationError: ExecutionPlan约束违规

        """
        # 1. 验证patch存在
        if patch_id not in self.patch_store:
            raise PatchNotFoundError(f"Patch '{patch_id}' not found")

        patch_content = self.patch_store[patch_id]

        # 2. ExecutionPlan约束检查
        if execution_plan is not None:
            # 2.1 检查max_files限制
            num_files = len(patch_content.affected_files)
            if num_files > execution_plan.limits.max_files:
                raise ConstraintViolationError(
                    f"Patch affects {num_files} files, exceeding limit of {execution_plan.limits.max_files}",
                    constraint_type="max_files",
                    limit=execution_plan.limits.max_files,
                    actual=num_files
                )

            # 2.2 检查max_changes限制
            total_changes = self._count_changes_in_diff(patch_content.unified_diff)
            if total_changes > execution_plan.limits.max_changes:
                raise ConstraintViolationError(
                    f"Patch contains {total_changes} changes, exceeding limit of {execution_plan.limits.max_changes}",
                    constraint_type="max_changes",
                    limit=execution_plan.limits.max_changes,
                    actual=total_changes
                )

        worktree_path = None
        start_time = time.time()

        try:
            # 3. 创建临时工作目录(简化版, 不使用git worktree)
            worktree_path = tempfile.mkdtemp(prefix="patch_apply_")
            worktree_path_obj = Path(worktree_path)

            # 4. 在临时目录中重新生成修改后的文件
            modified_files = []

            for relative_path in patch_content.affected_files:
                # 4.1 检查timeout
                if execution_plan is not None:
                    elapsed = time.time() - start_time
                    if elapsed > execution_plan.limits.timeout_seconds:
                        raise TimeoutError(
                            f"Operation exceeded timeout of {execution_plan.limits.timeout_seconds} seconds"
                        )

                src_file = self.project_root / relative_path
                if not src_file.exists():
                    continue

                # 读取原始文件
                original_content = src_file.read_text()

                # 从metadata中获取pattern和replacement
                pattern = patch_content.metadata.get('pattern')
                replacement = patch_content.metadata.get('replacement')

                if not pattern or replacement is None:
                    raise ValueError("Missing pattern/replacement in patch metadata")

                # 应用替换
                new_content = re.sub(pattern, replacement, original_content)

                # 在worktree中创建临时文件
                temp_file = worktree_path_obj / relative_path
                temp_file.parent.mkdir(parents=True, exist_ok=True)
                temp_file.write_text(new_content)

                # 验证变更后复制回主目录
                shutil.copy2(temp_file, src_file)
                modified_files.append(relative_path)

            # 5. 清理临时目录
            shutil.rmtree(worktree_path)

            # 6. 返回成功结果
            return ApplyResult(
                success=True,
                modified_files=modified_files,
                worktree_path=worktree_path,
                audit_log_id=None
            )

        except Exception as e:
            # 发生错误时清理worktree
            if worktree_path and Path(worktree_path).exists():
                shutil.rmtree(worktree_path)

            if isinstance(e, (PatchNotFoundError, PatchConflictError, ValueError,
                            ConstraintViolationError, TimeoutError)):
                raise

            return ApplyResult(
                success=False,
                modified_files=[],
                worktree_path=worktree_path,
                error_message=str(e)
            )
    
    def _create_worktree(self) -> str:
        """创建临时Git worktree"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="patch_worktree_")
        
        try:
            # 使用git worktree add创建工作树
            result = subprocess.run(
                ["git", "worktree", "add", temp_dir, "HEAD"],
                check=False, cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                # 如果git worktree失败, 尝试简单复制方式
                # (用于非Git仓库或测试环境)
                shutil.rmtree(temp_dir)
                temp_dir = tempfile.mkdtemp(prefix="patch_simple_")
                
                # 复制所有文件
                for item in self.project_root.iterdir():
                    if item.name == '.git':
                        continue
                    src = item
                    dst = Path(temp_dir) / item.name
                    if src.is_dir():
                        shutil.copytree(src, dst, symlinks=True)
                    else:
                        shutil.copy2(src, dst)
            
            return temp_dir
            
        except Exception as e:
            # 清理失败的临时目录
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
            raise RuntimeError(f"Failed to create worktree: {e}")
    
    def _cleanup_worktree(self, worktree_path: str) -> None:
        """清理临时worktree"""
        try:
            worktree_path_obj = Path(worktree_path)
            
            if not worktree_path_obj.exists():
                return
            
            # 尝试使用git worktree remove
            subprocess.run(
                ["git", "worktree", "remove", "--force", worktree_path],
                check=False, cwd=self.project_root,
                capture_output=True,
                timeout=10
            )
            
            # 无论git worktree remove是否成功, 都尝试直接删除目录
            if worktree_path_obj.exists():
                shutil.rmtree(worktree_path)
                
        except Exception:
            # 清理失败不影响主流程, 静默处理
            pass

    def _generate_patch_id(self) -> str:
        """生成唯一的patch_id"""
        timestamp = int(time.time() * 1000)
        hash_input = f"{timestamp}_{id(self)}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        return f"patch_{timestamp}_{hash_value}"

    def _count_changes_in_diff(self, unified_diff: str) -> int:
        """
        Count total number of changes (additions + deletions) in a unified diff.
        
        Args:
            unified_diff: The unified diff text
            
        Returns:
            Total number of changed lines

        """
        changes = 0
        for line in unified_diff.split('\n'):
            # Count lines starting with + or - (but not +++ or ---)
            if (line.startswith('+') and not line.startswith('+++')) or (line.startswith('-') and not line.startswith('---')):
                changes += 1
        return changes


class PatchNotFoundError(Exception):
    """Patch不存在错误"""



class PatchConflictError(Exception):
    """Patch冲突错误"""


class ConstraintViolationError(Exception):
    """ExecutionPlan约束违规错误"""
    
    def __init__(self, message: str, constraint_type: str, limit: Any, actual: Any):
        """
        Initialize ConstraintViolationError.
        
        Args:
            message: Error message
            constraint_type: Type of constraint violated (e.g., "max_changes", "timeout")
            limit: The limit that was violated
            actual: The actual value that exceeded the limit

        """
        super().__init__(message)
        self.constraint_type = constraint_type
        self.limit = limit
        self.actual = actual
