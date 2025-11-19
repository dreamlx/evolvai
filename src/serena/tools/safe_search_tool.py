"""
Story 2.1.2: safe_search MCP集成

将safe_search暴露为MCP工具，提供智能搜索功能。
"""

import json
from typing import Any, Optional

from evolvai.tools.safe_search import SafeSearchResult, SafeSearchWrapper
from serena.tools.tools_base import Tool, ToolMarkerCanEdit


class SafeSearchTool(Tool, ToolMarkerCanEdit):
    """Intelligent search with auto area detection and resource limits.

    When to use:
    - High-level search query ("find auth logic")
    - Don't know exact file locations
    - Multi-area projects (backend + frontend)
    - Need protection from search explosion

    When NOT to use:
    - Know exact pattern and files (use search_for_pattern or Native Grep)
    - Need precise control over glob patterns
    - Single-area project (overhead not worth it)
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
        """Execute intelligent search with auto area detection and constraints.

        Args:
            query: Natural language search query
            area_selector: "auto" (detect) or specific area like "backend-go" (default "auto")
            include_areas: Optional explicit area definitions (overrides auto-detection)
            mode: "conservative" | "balanced" | "broad" (default "balanced")
            max_files: Max files per area (default 50)
            max_results: Max total results (default 100)
            timeout_seconds: Max search time (default 30)
            scope: Legacy glob pattern (default "**/*")

        Returns: JSON with success, query, total_results, execution_report, raw_results
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
