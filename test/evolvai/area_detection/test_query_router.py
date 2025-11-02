"""
测试QueryRouter的核心功能
"""

# 导入我们要测试的类
from evolvai.area_detection.data_models import ProjectArea
from evolvai.area_detection.router import QueryRouter


class TestQueryRouter:
    """测试QueryRouter的核心功能"""

    def test_query_routing_to_backend(self):
        """测试查询路由到后端区域"""
        router = QueryRouter()
        areas = [
            ProjectArea(name="backend-go", language="go", confidence="High", evidence=["go.mod"], file_patterns=["*.go"]),
            ProjectArea(
                name="frontend-ts", language="typescript", confidence="High", evidence=["package.json"], file_patterns=["*.ts", "*.tsx"]
            ),
        ]

        routing = router.route_query("find JWT authentication handler", areas)

        # JWT handler应该路由到Go后端
        backend_area = next(area for area in routing.applied_areas if area.name == "backend-go")
        assert backend_area.budget_files >= 35  # 获得主要预算70-80%
        assert backend_area.score > 0

    def test_query_routing_to_frontend(self):
        """测试查询路由到前端区域"""
        router = QueryRouter()
        areas = [
            ProjectArea(name="backend-go", language="go", confidence="High", evidence=["go.mod"], file_patterns=["*.go"]),
            ProjectArea(
                name="frontend-ts", language="typescript", confidence="High", evidence=["package.json"], file_patterns=["*.ts", "*.tsx"]
            ),
        ]

        routing = router.route_query("find React login component", areas)

        # React component应该路由到TS前端
        frontend_area = next(area for area in routing.applied_areas if area.name == "frontend-ts")
        assert frontend_area.budget_files >= 35  # 获得主要预算70-80%
        assert frontend_area.score > 0

    def test_balanced_routing(self):
        """测试均衡路由策略"""
        router = QueryRouter()
        areas = [
            ProjectArea(name="backend-go", language="go", confidence="High", evidence=["go.mod"], file_patterns=["*.go"]),
            ProjectArea(
                name="frontend-ts", language="typescript", confidence="High", evidence=["package.json"], file_patterns=["*.ts", "*.tsx"]
            ),
        ]

        routing = router.route_query("find authConfig usage", areas)

        # 模糊查询应该均衡分配
        total_budget = sum(area.budget_files for area in routing.applied_areas)
        for area in routing.applied_areas:
            assert abs(area.budget_files - total_budget / 2) <= 5  # 允许小幅偏差

    def test_budget_allocation_strategy(self):
        """测试预算分配策略"""
        router = QueryRouter()
        areas = [
            ProjectArea(name="backend-go", language="go", confidence="High", evidence=["go.mod"], file_patterns=["*.go"]),
            ProjectArea(
                name="frontend-ts", language="typescript", confidence="High", evidence=["package.json"], file_patterns=["*.ts", "*.tsx"]
            ),
            ProjectArea(name="shared-py", language="python", confidence="Medium", evidence=["requirements.txt"], file_patterns=["*.py"]),
        ]

        routing = router.route_query("find user service", areas)

        # 应该给最高分区域70-80%预算
        sorted_areas = sorted(routing.applied_areas, key=lambda x: x.score, reverse=True)
        primary_area = sorted_areas[0]

        primary_budget_ratio = primary_area.budget_files / 50  # 假设总预算50
        assert 0.7 <= primary_budget_ratio <= 0.8

    def test_no_keywords_fallback(self):
        """测试无关键词时的回退策略"""
        router = QueryRouter()
        areas = [
            ProjectArea(name="backend-go", language="go", confidence="High", evidence=["go.mod"], file_patterns=["*.go"]),
            ProjectArea(
                name="frontend-ts", language="typescript", confidence="High", evidence=["package.json"], file_patterns=["*.ts", "*.tsx"]
            ),
        ]

        routing = router.route_query("find something generic", areas)

        # 无关键词应该均衡分配
        for area in routing.applied_areas:
            assert area.budget_files > 0
            assert area.score == 0  # 无匹配关键词

    def test_area_keywords_coverage(self):
        """测试区域关键词覆盖"""
        router = QueryRouter()

        # 测试Go关键词
        go_score = router._calculate_keyword_score("goroutine context handler", "backend-go")
        assert go_score > 0

        # 测试TypeScript关键词
        ts_score = router._calculate_keyword_score("react component hook", "frontend-ts")
        assert ts_score > 0

    def test_query_routing_with_single_area(self):
        """测试单个区域的查询路由"""
        router = QueryRouter()
        areas = [ProjectArea(name="only-go", language="go", confidence="High", evidence=["go.mod"], file_patterns=["*.go"])]

        routing = router.route_query("find anything", areas)

        # 单个区域应该获得全部预算
        assert len(routing.applied_areas) == 1
        assert routing.applied_areas[0].budget_files == 50  # 默认总预算
        assert routing.applied_areas[0].name == "only-go"

    def test_score_calculation_edge_cases(self):
        """测试分数计算边界情况"""
        router = QueryRouter()

        # 空查询
        score1 = router._calculate_keyword_score("", "backend-go")
        assert score1 == 0

        # 无匹配关键词
        score2 = router._calculate_keyword_score("find nothing matching", "backend-go")
        assert score2 == 0

        # 重复关键词
        score3 = router._calculate_keyword_score("handler handler handler", "backend-go")
        assert score3 == 3
