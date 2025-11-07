"""
Story 2.1.2: safe_search MCP集成

将safe_search暴露为MCP工具，提供智能搜索功能。
"""

import json
from typing import Any, Optional

from evolvai.tools.safe_search import SafeSearchResult, SafeSearchWrapper
from serena.tools.tools_base import Tool, ToolMarkerCanEdit


class SafeSearchTool(Tool, ToolMarkerCanEdit):
    """智能搜索工具 - safe_search的MCP接口

    多区域智能搜索，自动项目检测和约束执行。
    支持区域检测、查询路由、预算分配和性能监控。
    """

    def apply(
        self,
        query: str,
        area_selector: str = "auto",
        include_areas: Optional[list[dict[str, Any]]] = None,
        max_files: int = 50,
        max_results: int = 100,
        mode: str = "balanced",
        timeout_seconds: int = 30,
        scope: str = "**/*",
    ) -> str:
        """
        执行智能搜索，支持自动区域检测和约束执行

        Args:
            query: 搜索查询或模式
                Examples: ["find JWT authentication handler", "locate React login component", "search for TODO comments"]
                Negative examples: [".*", "find everything", "all files"]
            area_selector: 区域选择策略
                Enum: ["auto", "backend-go", "frontend-ts", "ruby", "python"]
                Default: "auto"
                Examples: [
                    "auto - automatically detect and route to relevant areas",
                    "backend-go - search only Go backend area",
                    "frontend-ts - search only TypeScript frontend area"
                ]
            include_areas: 显式区域定义（覆盖自动检测）
                Schema: {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "root": {"type": "string"},
                            "include_globs": {"type": "array", "items": {"type": "string"}},
                            "exclude_globs": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            max_files: 每个区域最大搜索文件数
                Range: [1, 1000]
                Default: 50
                Field dependencies: {
                    "area_count": {
                        "single": {"default": 50},
                        "multiple": {"default": 30}
                    }
                }
            mode: 搜索模式影响预算分配
                Enum: ["conservative", "balanced", "broad"]
                Default: "balanced"
                Examples: [
                    "conservative - strict limits, 20 files per area",
                    "balanced - standard limits, 30 files per area",
                    "broad - relaxed limits, 50 files per area"
                ]
            max_results: 最大结果数
                Range: [1, 500]
                Default: 100
            timeout_seconds: 超时时间（秒）
                Range: [5, 300]
                Default: 30
            scope: 搜索范围模式（向后兼容）
                Default: "**/*"

        Returns:
            JSON string containing:
            - success: boolean - 搜索是否成功
            - query: string - 搜索查询
            - total_results: integer - 结果总数
            - execution_report: object - 详细执行报告
                - detected_areas: array - 检测到的项目区域
                - applied_areas: array - 应用的区域配置
                - applied_patterns: array - 应用的搜索模式
                - execution_time_ms: float - 执行时间
                - coverage: object - 区域覆盖率统计
                - performance: object - 性能指标
            - raw_results: array - 原始搜索结果（可选）
            - error: object - 错误信息（如果有）

        Examples:
            Auto-Detected Backend Search:
                query="find JWT authentication handler", area_selector="auto", mode="balanced"
                Expected: Auto-routes to Go backend area with 35 file budget

            Explicit Frontend Search:
                query="locate React login component", area_selector="frontend-ts", max_files=40
                Expected: Searches only TypeScript frontend with 40 file limit

            Multi-Area Configuration:
                query="find authConfig usage", include_areas=[
                    {"name": "backend-go", "root": "backend", "include_globs": ["backend/**/*.go"]},
                    {"name": "frontend-ts", "root": "frontend", "include_globs": ["frontend/**/*.ts"]}
                ]
                Expected: Searches both configured areas with custom patterns

        """
        try:
            # 获取项目根目录
            project_root = self.agent.get_project_root()

            # 创建safe_search包装器
            search_wrapper = SafeSearchWrapper(project_root, self.agent)

            # 验证查询安全性
            validation = search_wrapper.validate_query(query)
            if validation.error_type != "validation_passed":
                return json.dumps(
                    {
                        "success": False,
                        "error": {
                            "type": validation.error_type,
                            "message": validation.summary,
                            "suggestion": validation.fix_suggestion.summary,
                        },
                        "query": query,
                    },
                    indent=2,
                )

            # 执行搜索
            result: SafeSearchResult = search_wrapper.search(
                query=query,
                scope=scope,
                max_files=max_files,
                max_results=max_results,
                timeout_seconds=timeout_seconds,
                area_selector=area_selector,
                include_areas=include_areas,
                mode=mode,
            )

            return result.to_json()

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error": {
                        "type": "execution_error",
                        "message": str(e),
                        "suggestion": "Check search parameters and project structure",
                    },
                    "query": query,
                },
                indent=2,
            )


class GetLanguageHintTool(Tool):
    """项目语言检测工具 - zero-cost项目分析

    检测项目区域和语言，提供零成本的项目结构分析。
    """

    def apply(
        self,
        sample_limit: int = 200,
        exclude_dirs: Optional[list[str]] = None,
    ) -> str:
        """
        检测项目区域和语言

        Args:
            sample_limit: 最大抽样文件数
                Range: [50, 500]
                Default: 200
            exclude_dirs: 排除的目录列表
                Default: [".git", "node_modules", "vendor", "target", "build", "dist"]

        Returns:
            JSON string containing:
            - areas: array - 检测到的项目区域
                - name: string - 区域名称
                - language: string - 编程语言
                - root: string - 根路径
                - confidence: string - 置信度
                - evidence: array - 检测证据
                - suggested_globs: array - 建议的文件模式
                - exclude_globs: array - 建议排除的模式
            - cache_status: string - 缓存状态
            - analysis_time_ms: float - 分析时间

        Example:
            sample_limit=200
            Expected: Detects project areas like Go backend, TypeScript frontend

        """
        try:
            # 获取项目根目录
            project_root = self.agent.get_project_root()

            # 创建检测器
            from evolvai.area_detection.detector import AreaDetector

            detector = AreaDetector(project_root)

            # 设置默认排除目录
            if exclude_dirs is None:
                exclude_dirs = [".git", "node_modules", "vendor", "target", "build", "dist"]

            # 执行区域检测
            import time

            start_time = time.time()
            areas = detector.detect_areas(sample_limit)
            analysis_time_ms = (time.time() - start_time) * 1000

            # 转换为响应格式
            areas_response = []
            for area in areas:
                area_data = {
                    "name": area.name,
                    "language": area.language,
                    "root": area.root_path,
                    "confidence": area.confidence,
                    "evidence": area.evidence,
                    "suggested_globs": area.file_patterns,
                    "exclude_globs": exclude_dirs,
                }
                areas_response.append(area_data)

            # 检查缓存状态
            cache_key = f"{project_root}:{sample_limit}"
            cache_status = "hit" if cache_key in detector.cache else "miss"

            response = {
                "areas": areas_response,
                "cache_status": cache_status,
                "analysis_time_ms": round(analysis_time_ms, 2),
                "total_areas": len(areas_response),
            }

            return json.dumps(response, indent=2)

        except Exception as e:
            return json.dumps(
                {
                    "error": {
                        "type": "detection_error",
                        "message": str(e),
                        "suggestion": "Check project structure and permissions",
                    },
                    "areas": [],
                    "cache_status": "error",
                    "analysis_time_ms": 0,
                },
                indent=2,
            )


# 导出工具类
__all__ = ["GetLanguageHintTool", "SafeSearchTool"]
