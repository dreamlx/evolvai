"""
编辑验证器
提供语法、区域、大小和导入验证功能
"""

import ast
import re
from pathlib import Path
from typing import Optional

from .data_models import AppliedArea, EditValidationError, EditValidationResult, ProjectArea


class EditValidator:
    """编辑验证器"""

    def __init__(self, areas: Optional[list[ProjectArea]] = None, applied_areas: Optional[list[AppliedArea]] = None):
        """
        初始化编辑验证器

        Args:
            areas: 项目区域列表
            applied_areas: 已应用的区域列表

        """
        self.areas = areas or []
        self.applied_areas = applied_areas or []
        self._max_file_size = 10 * 1024 * 1024  # 10MB
        self._max_lines_per_edit = 1000
        self._max_files_per_edit = 10

    def validate_edit_syntax(
        self,
        original_code: str,
        edited_code: str,
        file_path: str,
        language: str
    ) -> EditValidationResult:
        """
        验证编辑语法

        Args:
            original_code: 原始代码
            edited_code: 编辑后的代码
            file_path: 文件路径
            language: 编程语言

        Returns:
            EditValidationResult: 验证结果

        """
        syntax_errors: list[str] = []
        warnings: list[str] = []

        try:
            # 根据语言验证语法
            if language.lower() in ['python', 'py']:
                syntax_errors.extend(self._validate_python_syntax(edited_code, file_path))
            elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
                syntax_errors.extend(self._validate_js_syntax(edited_code, file_path))
            elif language.lower() in ['go', 'golang']:
                syntax_errors.extend(self._validate_go_syntax(edited_code, file_path))
            elif language.lower() in ['java']:
                syntax_errors.extend(self._validate_java_syntax(edited_code, file_path))

            # 检查是否为空编辑
            if original_code.strip() == edited_code.strip():
                warnings.append("未检测到代码变更")

        except Exception as e:
            syntax_errors.append(f"语法验证失败: {e!s}")

        is_valid = len(syntax_errors) == 0
        return EditValidationResult(
            is_valid=is_valid,
            error_message=" | ".join(syntax_errors) if syntax_errors else None,
            syntax_errors=syntax_errors,
            warnings=warnings
        )

    def validate_edit_area(
        self,
        file_path: str,
        areas: Optional[list[ProjectArea]] = None
    ) -> EditValidationResult:
        """
        验证编辑区域匹配

        Args:
            file_path: 文件路径
            areas: 项目区域列表（如果为None则使用初始化时的areas）

        Returns:
            EditValidationResult: 验证结果

        """
        affected_areas: list[str] = []
        warnings: list[str] = []

        # 使用传入的areas或初始化时的areas
        areas_to_check = areas or self.areas

        # 检查文件是否在允许的区域
        path_obj = Path(file_path)
        for area in areas_to_check:
            if any(path_obj.match(pattern) for pattern in area.file_patterns):
                affected_areas.append(area.name)

        # 如果没有匹配的区域，添加跨区域编辑警告
        if not affected_areas:
            if areas_to_check:
                warnings.append(f"File {file_path} does not belong to any defined area (cross-area edit)")
            else:
                warnings.append(f"No areas defined for file {file_path} (cross-area edit)")

        return EditValidationResult(
            is_valid=True,
            affected_areas=affected_areas,
            warnings=warnings
        )

    def validate_edit_size(
        self,
        original_code: str,
        edited_code: str,
        max_changes: Optional[int] = None,
        max_lines_added: Optional[int] = None,
        max_lines_removed: Optional[int] = None
    ) -> EditValidationResult:
        """
        验证编辑大小

        Args:
            original_code: 原始代码
            edited_code: 编辑后代码
            max_changes: 最大变更数量
            max_lines_added: 最大新增行数
            max_lines_removed: 最大删除行数

        Returns:
            EditValidationResult: 验证结果

        """
        warnings: list[str] = []
        changes_count = 0
        lines_added = 0
        lines_removed = 0

        # 计算行数变更
        original_lines = original_code.split('\n')
        edited_lines = edited_code.split('\n')

        lines_added = max(0, len(edited_lines) - len(original_lines))
        lines_removed = max(0, len(original_lines) - len(edited_lines))

        # 估算变更数量（简单diff）
        changes_count = self._estimate_changes(original_code, edited_code)

        # 检查限制
        max_changes_limit = max_changes or self._max_lines_per_edit
        max_lines_added_limit = max_lines_added or self._max_lines_per_edit
        max_lines_removed_limit = max_lines_removed or self._max_lines_per_edit

        if changes_count > max_changes_limit:
            return EditValidationResult(
                is_valid=False,
                error_message=f"Changes count ({changes_count}) exceeds limit ({max_changes_limit})",
                changes_count=changes_count,
                lines_added=lines_added,
                lines_removed=lines_removed
            )

        if lines_added > max_lines_added_limit:
            return EditValidationResult(
                is_valid=False,
                error_message=f"Lines added ({lines_added}) exceeds limit ({max_lines_added_limit})",
                changes_count=changes_count,
                lines_added=lines_added,
                lines_removed=lines_removed
            )

        if lines_removed > max_lines_removed_limit:
            return EditValidationResult(
                is_valid=False,
                error_message=f"Lines removed ({lines_removed}) exceeds limit ({max_lines_removed_limit})",
                changes_count=changes_count,
                lines_added=lines_added,
                lines_removed=lines_removed
            )

        if changes_count > 100:
            warnings.append(f"Large number of changes detected ({changes_count}), consider batching")

        return EditValidationResult(
            is_valid=True,
            warnings=warnings,
            changes_count=changes_count,
            lines_added=lines_added,
            lines_removed=lines_removed
        )

    def validate_imports(
        self,
        original_code: str,
        edited_code: str,
        language: str
    ) -> EditValidationResult:
        """
        验证导入变更

        Args:
            original_code: 原始代码
            edited_code: 编辑后代码
            language: 编程语言

        Returns:
            EditValidationResult: 验证结果

        """
        return self.validate_import_changes(original_code, edited_code, "test.py", language)

    def validate_comprehensive(
        self,
        original_code: str,
        edited_code: str,
        file_path: str,
        language: str,
        areas: Optional[list[ProjectArea]] = None,
        max_changes: Optional[int] = None,
        max_lines_added: Optional[int] = None,
        max_lines_removed: Optional[int] = None
    ) -> EditValidationResult:
        """
        综合验证（语法、区域、大小、导入）

        Args:
            original_code: 原始代码
            edited_code: 编辑后代码
            file_path: 文件路径
            language: 编程语言
            areas: 项目区域列表
            max_changes: 最大变更数量
            max_lines_added: 最大新增行数
            max_lines_removed: 最大删除行数

        Returns:
            EditValidationResult: 综合验证结果

        """
        # 1. 语法验证
        syntax_result = self.validate_edit_syntax(original_code, edited_code, file_path, language)
        if not syntax_result.is_valid:
            return syntax_result

        # 2. 区域验证
        area_result = self.validate_edit_area(file_path, areas)

        # 3. 大小验证
        size_result = self.validate_edit_size(original_code, edited_code, max_changes, max_lines_added, max_lines_removed)
        if not size_result.is_valid:
            return size_result

        # 4. 导入验证
        import_result = self.validate_imports(original_code, edited_code, language)

        # 合并所有结果
        all_warnings = syntax_result.warnings + area_result.warnings + size_result.warnings + import_result.warnings

        return EditValidationResult(
            is_valid=True,
            warnings=all_warnings,
            syntax_errors=syntax_result.syntax_errors,
            affected_areas=area_result.affected_areas,
            changes_count=size_result.changes_count,
            lines_added=size_result.lines_added,
            lines_removed=size_result.lines_removed,
            new_imports=import_result.new_imports,
            removed_imports=import_result.removed_imports
        )

    def validate_area_constraints(
        self,
        file_path: str,
        content: str,
        mode: str = "safe"
    ) -> EditValidationResult:
        """
        验证区域约束

        Args:
            file_path: 文件路径
            content: 文件内容
            mode: 编辑模式 (safe, normal, aggressive)

        Returns:
            EditValidationResult: 验证结果

        """
        affected_areas: list[str] = []
        warnings: list[str] = []

        # 检查文件是否在允许的区域
        path_obj = Path(file_path)
        for area in self.areas:
            if any(path_obj.match(pattern) for pattern in area.file_patterns):
                affected_areas.append(area.name)

        # 检查是否有受保护的区域
        protected_areas = [a for a in self.areas if a.confidence in ['High', 'VeryHigh']]
        conflicts = [a for a in affected_areas if a in [pa.name for pa in protected_areas]]

        if mode == "safe" and conflicts:
            raise EditValidationError(
                error_type="AREA_CONSTRAINT_VIOLATION",
                message=f"安全模式下不允许编辑高置信度区域: {', '.join(conflicts)}",
                file_path=file_path,
                details={"conflicts": conflicts}
            )

        # 检查应用区域数量限制
        if len(affected_areas) > self._max_files_per_edit:
            raise EditValidationError(
                error_type="AREA_LIMIT_EXCEEDED",
                message=f"单次编辑影响的区域数量超过限制 ({self._max_files_per_edit})",
                file_path=file_path,
                details={"area_count": len(affected_areas), "limit": self._max_files_per_edit}
            )

        return EditValidationResult(
            is_valid=True,
            affected_areas=affected_areas,
            warnings=warnings
        )

    def validate_size_constraints(
        self,
        file_path: str,
        original_content: str,
        edited_content: str
    ) -> EditValidationResult:
        """
        验证大小约束

        Args:
            file_path: 文件路径
            original_content: 原始内容
            edited_content: 编辑后内容

        Returns:
            EditValidationResult: 验证结果

        """
        warnings: list[str] = []
        changes_count = 0
        lines_added = 0
        lines_removed = 0

        # 检查文件大小
        edited_size = len(edited_content.encode('utf-8'))
        if edited_size > self._max_file_size:
            raise EditValidationError(
                error_type="FILE_SIZE_EXCEEDED",
                message=f"编辑后文件大小 ({edited_size} bytes) 超过限制 ({self._max_file_size} bytes)",
                file_path=file_path,
                details={"size": edited_size, "limit": self._max_file_size}
            )

        # 计算行数变更
        original_lines = original_content.split('\n')
        edited_lines = edited_content.split('\n')

        lines_added = max(0, len(edited_lines) - len(original_lines))
        lines_removed = max(0, len(original_lines) - len(edited_lines))

        # 检查行数变更限制
        if lines_added > self._max_lines_per_edit:
            raise EditValidationError(
                error_type="LINES_ADDED_EXCEEDED",
                message=f"新增行数 ({lines_added}) 超过限制 ({self._max_lines_per_edit})",
                file_path=file_path,
                details={"lines_added": lines_added, "limit": self._max_lines_per_edit}
            )

        if lines_removed > self._max_lines_per_edit:
            raise EditValidationError(
                error_type="LINES_REMOVED_EXCEEDED",
                message=f"删除行数 ({lines_removed}) 超过限制 ({self._max_lines_per_edit})",
                file_path=file_path,
                details={"lines_removed": lines_removed, "limit": self._max_lines_per_edit}
            )

        # 估算变更数量（简单diff）
        changes_count = self._estimate_changes(original_content, edited_content)

        if changes_count > 100:
            warnings.append(f"Large number of changes detected ({changes_count}), consider batching")

        return EditValidationResult(
            is_valid=True,
            warnings=warnings,
            changes_count=changes_count,
            lines_added=lines_added,
            lines_removed=lines_removed
        )

    def validate_import_changes(
        self,
        original_code: str,
        edited_code: str,
        file_path: str,
        language: str
    ) -> EditValidationResult:
        """
        验证导入变更

        Args:
            original_code: 原始代码
            edited_code: 编辑后代码
            file_path: 文件路径
            language: 编程语言

        Returns:
            EditValidationResult: 验证结果

        """
        new_imports: list[str] = []
        removed_imports: list[str] = []
        warnings: list[str] = []

        try:
            # 提取导入语句
            original_imports = self._extract_imports(original_code, language)
            edited_imports = self._extract_imports(edited_code, language)

            # 找出新增和删除的导入
            new_imports = list(edited_imports - original_imports)
            removed_imports = list(original_imports - edited_imports)

            # 检查敏感导入
            sensitive_imports = self._check_sensitive_imports(new_imports, language)
            if sensitive_imports:
                warnings.append(f"检测到敏感导入: {', '.join(sensitive_imports)}")

            # 检查删除的导入是否被使用
            if removed_imports:
                # 简化检查：假设删除的导入如果不在新代码中则可能有问题
                unused_removals = self._check_unused_import_removals(
                    removed_imports, edited_code, language
                )
                if unused_removals:
                    warnings.append(f"可能删除了未使用的导入: {', '.join(unused_removals)}")

        except Exception as e:
            warnings.append(f"导入验证失败: {e!s}")

        return EditValidationResult(
            is_valid=True,
            new_imports=new_imports,
            removed_imports=removed_imports,
            warnings=warnings
        )

    def _validate_python_syntax(self, code: str, file_path: str) -> list[str]:
        """验证Python语法"""
        errors: list[str] = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Python syntax error: {e.msg} (line {e.lineno})")
        except Exception as e:
            errors.append(f"Python validation failed: {e!s}")
        return errors

    def _validate_js_syntax(self, code: str, file_path: str) -> list[str]:
        """验证JavaScript/TypeScript语法"""
        errors: list[str] = []
        # 简单的语法检查
        # 实际项目中应该使用eslint或typescript编译器
        try:
            # 检查基本语法问题
            if code.count('{') != code.count('}'):
                errors.append("Mismatched braces")
            if code.count('(') != code.count(')'):
                errors.append("Mismatched parentheses")
        except Exception as e:
            errors.append(f"JavaScript validation failed: {e!s}")
        return errors

    def _validate_go_syntax(self, code: str, file_path: str) -> list[str]:
        """验证Go语法"""
        errors: list[str] = []
        # 简单的Go语法检查
        # 实际项目中应该使用go fmt或go vet
        try:
            # 检查包声明
            if not re.match(r'^\s*package\s+\w+', code):
                errors.append("Missing or invalid package declaration")
        except Exception as e:
            errors.append(f"Go validation failed: {e!s}")
        return errors

    def _validate_java_syntax(self, code: str, file_path: str) -> list[str]:
        """验证Java语法"""
        errors: list[str] = []
        # 简单的Java语法检查
        # 实际项目中应该使用javac
        try:
            # 检查类声明
            if 'class ' in code and not re.search(r'\bclass\s+\w+', code):
                errors.append("Invalid class declaration")
        except Exception as e:
            errors.append(f"Java validation failed: {e!s}")
        return errors

    def _extract_imports(self, code: str, language: str) -> set[str]:
        """提取导入语句"""
        imports: set[str] = set()

        if language.lower() in ['python', 'py']:
            # Python导入
            import_patterns = [
                r'^\s*import\s+([\w.]+)',
                r'^\s*from\s+([\w.]+)\s+import'
            ]
            for line in code.split('\n'):
                for pattern in import_patterns:
                    match = re.match(pattern, line)
                    if match:
                        imports.add(match.group(1))

        elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
            # JavaScript/TypeScript导入
            import_patterns = [
                r'^\s*import\s+.*?\s+from\s+[\'"](.+?)[\'"]',
                r'^\s*import\s+[\'"](.+?)[\'"]',
                r'^\s*require\([\'"](.+?)[\'"]\)'
            ]
            for line in code.split('\n'):
                for pattern in import_patterns:
                    match = re.match(pattern, line)
                    if match:
                        imports.add(match.group(1))

        elif language.lower() in ['go', 'golang']:
            # Go导入
            import_pattern = r'^\s*import\s+[\'"](.+?)[\'"]'
            for line in code.split('\n'):
                match = re.match(import_pattern, line)
                if match:
                    imports.add(match.group(1))

        elif language.lower() in ['java']:
            # Java导入
            import_pattern = r'^\s*import\s+([\w.]+);'
            for line in code.split('\n'):
                match = re.match(import_pattern, line)
                if match:
                    imports.add(match.group(1))

        return imports

    def _check_sensitive_imports(self, imports: list[str], language: str) -> list[str]:
        """检查敏感导入"""
        sensitive: list[str] = []

        if language.lower() in ['python', 'py']:
            sensitive_patterns = [
                'os', 'sys', 'subprocess', 'eval', 'exec', 'pickle', 'marshal'
            ]
        elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
            sensitive_patterns = [
                'child_process', 'fs', 'eval', 'Function', 'require'
            ]
        elif language.lower() in ['go', 'golang']:
            sensitive_patterns = [
                'os/exec', 'syscall', 'os', 'reflect'
            ]
        else:
            sensitive_patterns = []

        for imp in imports:
            if any(imp.startswith(pattern) for pattern in sensitive_patterns):
                sensitive.append(imp)

        return sensitive

    def _check_unused_import_removals(
        self,
        removed_imports: list[str],
        edited_code: str,
        language: str
    ) -> list[str]:
        """检查可能未使用的导入删除"""
        # 简化实现：检查导入名称是否仍在代码中使用
        unused: list[str] = []
        for imp in removed_imports:
            # 提取导入的基础名称
            base_name = imp.split('.')[-1]
            # 如果基础名称不在编辑后的代码中，则可能是未使用的
            if base_name not in edited_code:
                unused.append(imp)
        return unused

    def _estimate_changes(self, original: str, edited: str) -> int:
        """估算变更数量"""
        # 简单的差异估算
        # 实际项目中应该使用真正的diff算法
        orig_lines = original.split('\n')
        edit_lines = edited.split('\n')

        changes = abs(len(edit_lines) - len(orig_lines))

        # 检查每行的变更
        min_lines = min(len(orig_lines), len(edit_lines))
        for i in range(min_lines):
            if orig_lines[i] != edit_lines[i]:
                changes += 1

        return changes
