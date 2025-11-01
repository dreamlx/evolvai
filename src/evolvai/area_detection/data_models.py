"""
区域检测的数据模型
"""

from dataclasses import dataclass
from typing import Optional


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
