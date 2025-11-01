"""
区域检测的数据模型
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


@dataclass
class ProjectArea:
    """项目区域定义"""

    name: str
    language: str
    confidence: str  # High, Medium, Low, VeryHigh
    evidence: list[str]
    file_patterns: list[str]
    root_path: Optional[str] = None


@dataclass
class AppliedArea:
    """应用的区域配置"""

    name: str
    budget_files: int
    scanned_files: int
    match_count: int
    duration_ms: float
    score: int = 0


@dataclass
class QueryRouting:
    """查询路由结果"""

    areas: list[ProjectArea]
    applied_areas: list[AppliedArea]
    final_patterns: list[str]
    query: str


# 编辑验证相关数据模型

class RollbackStrategy(Enum):
    """回滚策略枚举"""
    GIT = "git"
    FILE_BACKUP = "file_backup"
    AUTO = "auto"


@dataclass
class EditValidationResult:
    """编辑验证结果"""

    is_valid: bool
    error_message: Optional[str] = None
    syntax_errors: List[str] = None
    warnings: List[str] = None
    affected_areas: List[str] = None
    changes_count: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    new_imports: List[str] = None
    removed_imports: List[str] = None

    def __post_init__(self):
        if self.syntax_errors is None:
            self.syntax_errors = []
        if self.warnings is None:
            self.warnings = []
        if self.affected_areas is None:
            self.affected_areas = []
        if self.new_imports is None:
            self.new_imports = []
        if self.removed_imports is None:
            self.removed_imports = []


@dataclass
class RollbackResult:
    """回滚操作结果"""

    success: bool
    strategy: RollbackStrategy
    message: Optional[str] = None
    error_message: Optional[str] = None
    rollback_hash: Optional[str] = None
    duration_ms: float = 0.0


class EditValidationError(Exception):
    """编辑验证异常"""

    def __init__(self,
                 error_type: str,
                 message: str,
                 file_path: Optional[str] = None,
                 line_number: Optional[int] = None,
                 details: Optional[dict] = None):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        self.details = details or {}

    def __str__(self):
        parts = [f"{self.error_type}: {self.message}"]
        if self.file_path:
            parts.append(f"file: {self.file_path}")
        if self.line_number:
            parts.append(f"line: {self.line_number}")
        return " | ".join(parts)
