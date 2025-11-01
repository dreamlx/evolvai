"""
查询路由器 - 智能查询路由和预算分配 (修复版本)
"""

from .data_models import AppliedArea, ProjectArea, QueryRouting


class QueryRouter:
    """查询关键词到区域的智能路由"""

    def __init__(self):
        self.area_keywords = {
            "backend-go": [
                "goroutine",
                "context",
                "gin",
                "echo",
                "grpc",
                "handler",
                "repository",
                "service",
                "middleware",
                "interface",
                "struct",
                "func",
                "go",
                "golang",
            ],
            "frontend-ts": [
                "react",
                "component",
                "hook",
                "tsx",
                "vite",
                "next",
                "webpack",
                "usestate",
                "useeffect",
                "typescript",
                "interface",
                "type",
                "enum",
            ],
            "ruby": ["rails", "active_record", "controller", "model", "view", "erb", "rake", "gem", "ruby"],
            "python": ["django", "flask", "fastapi", "pydantic", "asyncio", "class", "def", "import", "python"],
        }

    def route_query(self, query: str, areas: list[ProjectArea], total_budget: int = 50) -> QueryRouting:
        """基于查询内容路由到最相关区域"""
        query_lower = query.lower()
        area_scores = {}

        # 计算每个区域的匹配分数
        for area in areas:
            score = self._calculate_keyword_score(query_lower, area.name)
            area_scores[area.name] = score

        # Budget allocation: primary areas 70-80%, secondary areas 20-30%
        applied_areas = self._allocate_budget(area_scores, areas, total_budget)

        # 生成最终的搜索模式
        final_patterns = self._generate_search_patterns(applied_areas)

        return QueryRouting(areas=areas, applied_areas=applied_areas, final_patterns=final_patterns, query=query)

    def _calculate_keyword_score(self, query: str, area_name: str) -> int:
        """计算查询在特定区域的匹配分数"""
        if area_name not in self.area_keywords:
            return 0

        keywords = self.area_keywords[area_name]
        score = 0

        query_words = query.split()
        for word in query_words:
            if word in keywords:
                score += 1

        return score

    def _allocate_budget(self, area_scores: dict[str, int], areas: list[ProjectArea], total_budget: int) -> list[AppliedArea]:
        """预算分配算法：主区域70-80%，剩余平分给次区域"""
        applied_areas: list[AppliedArea] = []
        max_score = max(area_scores.values()) if area_scores else 0

        # 分离有分数和无分数的区域
        scored_areas = []
        unscored_areas = []

        for area in areas:
            score = area_scores.get(area.name, 0)
            if score > 0:
                scored_areas.append((area, score))
            else:
                unscored_areas.append(area)

        # 有匹配的情况
        if max_score > 0 and scored_areas:
            # 找出最高分区域
            primary_areas = [area for area, score in scored_areas if score == max_score]
            secondary_areas = [area for area, score in scored_areas if score < max_score and score > 0]

            # 主区域分配70-80%
            primary_budget = int(total_budget * 0.75)  # 使用75%作为中间值

            if len(primary_areas) > 1:
                # 多个主区域平分主预算
                primary_budget_per_area = primary_budget // len(primary_areas)
                remaining_for_primary = primary_budget % len(primary_areas)

                # 分配给主区域
                for i, area in enumerate(primary_areas):
                    budget = primary_budget_per_area
                    if i < remaining_for_primary:  # 分配余数
                        budget += 1

                    applied_areas.append(
                        AppliedArea(name=area.name, budget_files=budget, scanned_files=0, match_count=0, duration_ms=0.0, score=max_score)
                    )
            else:
                # 单个主区域
                applied_areas.append(
                    AppliedArea(
                        name=primary_areas[0].name,
                        budget_files=primary_budget,
                        scanned_files=0,
                        match_count=0,
                        duration_ms=0.0,
                        score=max_score,
                    )
                )

            secondary_budget = total_budget - sum(area.budget_files for area in applied_areas)

            # 次区域平分剩余预算
            if secondary_areas and secondary_budget > 0:
                secondary_budget_per_area = secondary_budget // len(secondary_areas)
                remaining_for_secondary = secondary_budget % len(secondary_areas)

                for i, area in enumerate(secondary_areas):
                    budget = secondary_budget_per_area
                    if i < remaining_for_secondary:
                        budget += 1

                    applied_areas.append(
                        AppliedArea(
                            name=area.name,
                            budget_files=budget,
                            scanned_files=0,
                            match_count=0,
                            duration_ms=0.0,
                            score=area_scores.get(area.name, 0),
                        )
                    )

            # 无分数区域获得最小预算
            if unscored_areas and len(applied_areas) < len(areas):
                budget_per_unscored = 2  # 统一给2个文件的最小预算
                for area in unscored_areas:
                    applied_areas.append(
                        AppliedArea(
                            name=area.name, budget_files=budget_per_unscored, scanned_files=0, match_count=0, duration_ms=0.0, score=0
                        )
                    )

        # 无匹配的情况 - 均衡分配
        else:
            budget_per_area = total_budget // len(areas)
            remaining = total_budget % len(areas)

            for i, area in enumerate(areas):
                budget = budget_per_area
                if i < remaining:
                    budget += 1

                applied_areas.append(
                    AppliedArea(
                        name=area.name,
                        budget_files=budget,
                        scanned_files=0,
                        match_count=0,
                        duration_ms=0.0,
                        score=area_scores.get(area.name, 0),
                    )
                )

        return applied_areas

    def _generate_search_patterns(self, applied_areas: list[AppliedArea]) -> list[str]:
        """生成搜索模式"""
        patterns = []
        for area in applied_areas:
            # 根据区域名生成基本模式
            if "backend" in area.name.lower() or "go" in area.name.lower():
                patterns.append("**/*.go")
            elif "frontend" in area.name.lower() or "ts" in area.name.lower():
                patterns.extend(["**/*.ts", "**/*.tsx"])
            elif "ruby" in area.name.lower():
                patterns.extend(["**/*.rb", "**/*.erb"])
            elif "python" in area.name.lower() or "py" in area.name.lower():
                patterns.append("**/*.py")
            else:
                patterns.append("**/*")

        return patterns
