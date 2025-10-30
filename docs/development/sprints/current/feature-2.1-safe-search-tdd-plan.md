# Feature 2.1: safe_search Wrapper - TDD Implementation Plan

**Feature ID**: FEATURE-004
**Priority**: P0
**Estimate**: 3 person-days (优化后)
**Status**: Ready for TDD

## 🎯 Feature Overview

智能搜索包装器，通过scope限制和参数化约束防止搜索范围过大导致的性能问题。

## 🏗️ Architecture Design

### Core Components

```
safe_search wrapper
├── AreaDetector          # 区域检测器 (哨兵文件+轻量抽样+缓存)
├── QueryRouter          # 查询路由器 (关键词映射+预算分配)
├── FileTypeIntelligence # 智能文件类型推断 (复用现有Language.get_source_fn_matcher)
├── SafeSearchExecutor    # 安全执行器 (Story 1.3集成)
└── FeedbackSystem       # 可观测反馈系统
```

### GPT-5优化方案集成

基于与GPT-5的讨论，采用更先进的**区域检测与路由**架构：

#### **1. 低成本区域检测管道**

```python
class AreaDetector:
    """零成本混合项目区域检测"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.cache = {}  # 缓存检测结果

    def detect_areas(self, sample_limit: int = 200) -> list[ProjectArea]:
        """多层检测管道，O(1)到O(小文件数)"""
        # 1. 显式配置优先 (Project.language)
        if explicit_config := self._check_explicit_config():
            return explicit_config

        # 2. 哨兵文件匹配 (go.mod, package.json, Gemfile等)
        if sentinel_areas := self._match_sentinel_files():
            return sentinel_areas

        # 3. 轻量抽样统计 (N≤200, 跳过大目录)
        return self._lightweight_sampling(sample_limit)

    def _match_sentinel_files(self) -> list[ProjectArea]:
        """哨兵文件检测，近乎零开销"""
        sentinel_patterns = {
            # Go: go.mod, Makefile, CMakeLists.txt, src/, internal/, cmd/
            "go": ["go.mod", "Makefile", "CMakeLists.txt"],
            # Ruby: Gemfile, *.gemspec, Rakefile, .ruby-version
            "ruby": ["Gemfile", "*.gemspec", "Rakefile"],
            # TypeScript: package.json, tsconfig.json
            "typescript": ["package.json", "tsconfig.json"],
            # Python: pyproject.toml, requirements.txt, setup.py
            "python": ["pyproject.toml", "requirements.txt", "setup.py"],
        }
```

#### **2. 智能查询路由**

```python
class QueryRouter:
    """查询关键词到区域的智能路由"""

    def __init__(self):
        self.area_keywords = {
            "backend-go": [
                "goroutine", "context", "gin", "echo", "grpc",
                "handler", "repository", "service", "middleware"
            ],
            "frontend-ts": [
                "react", "component", "hook", "tsx", "vite",
                "next", "webpack", "useState", "useEffect"
            ],
            "ruby": [
                "rails", "active_record", "controller", "model",
                "view", "erb", "rake", "gem"
            ]
        }

    def route_query(self, query: str, areas: list[ProjectArea]) -> QueryRouting:
        """基于查询内容路由到最相关区域"""
        query_lower = query.lower()
        area_scores = {}

        for area in areas:
            score = 0
            for keyword in self.area_keywords.get(area.name, []):
                if keyword in query_lower:
                    score += 1
            area_scores[area.name] = score

        # 预算分配: 主区域70-80%，次区域20-30%
        return self._allocate_budget(area_scores, areas)
```

#### **3. 可观测反馈系统**

```python
class FeedbackSystem:
    """LLM可观测的反馈系统"""

    def create_execution_report(self, routing: QueryRouting, results: SearchResults) -> ExecutionReport:
        return ExecutionReport(
            detected_areas=[
                {
                    "name": area.name,
                    "language": area.language,
                    "root": area.root_path,
                    "confidence": area.confidence,
                    "evidence": area.evidence
                }
                for area in routing.areas
            ],
            applied_areas=[
                {
                    "name": area.name,
                    "budget_files": area.budget_files,
                    "budget_timeout": area.budget_timeout
                }
                for area in routing.applied_areas
            ],
            applied_patterns=routing.final_patterns,
            coverage={
                area.name: {
                    "scanned": area.scanned_files,
                    "found": area.match_count,
                    "duration_ms": area.duration_ms
                }
                for area in routing.applied_areas
            }
        )
```

## 📊 TDD Cycle Plan (基于GPT-5优化)

### Cycle 1: AreaDetector + 哨兵文件检测 (1 day)

**Acceptance Criteria**:
- ✅ 哨兵文件检测 (go.mod, package.json, Gemfile等)
- ✅ 轻量抽样统计 (N≤200, 跳过大目录)
- ✅ 混合项目区域识别
- ✅ 缓存机制 (O(1)命中)

**Test Cases**:
```python
def test_sentinel_file_detection_go():
    """测试Go项目哨兵文件检测"""
    detector = AreaDetector("/tmp/test-go-project")

    # 模拟存在go.mod
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("os.listdir") as mock_listdir:
            mock_listdir.return_value = ["go.mod", "main.go"]

            areas = detector.detect_areas()

            go_area = next(area for area in areas if area.language == "go")
            assert "go.mod" in go_area.evidence
            assert go_area.confidence == "High"

def test_sentinel_file_detection_ruby():
    """测试Ruby项目哨兵文件检测"""
    detector = AreaDetector("/tmp/test-ruby-project")

    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("os.listdir") as mock_listdir:
            mock_listdir.return_value = ["Gemfile", "app", "config"]

            areas = detector.detect_areas()

            ruby_area = next(area for area in areas if area.language == "ruby")
            assert "Gemfile" in ruby_area.evidence
            assert ruby_area.confidence == "High"

def test_mixed_project_detection():
    """测试混合项目检测 (Go+TS)"""
    detector = AreaDetector("/tmp/test-mixed-project")

    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("os.listdir") as mock_listdir:
            # 模拟前端目录
            def mock_listdir_side_effect(path):
                if "frontend" in path:
                    return ["package.json", "tsconfig.json", "src"]
                elif "backend" in path:
                    return ["go.mod", "main.go", "cmd"]
                return []

            mock_listdir.side_effect = mock_listdir_side_effect

            areas = detector.detect_areas()

            # 应该检测到两个区域
            languages = [area.language for area in areas]
            assert "go" in languages
            assert "typescript" in languages

def test_area_cache_mechanism():
    """测试区域检测缓存机制"""
    detector = AreaDetector("/tmp/test-project")

    # 首次调用
    with patch.object(detector, "_match_sentinel_files") as mock_match:
        mock_match.return_value = []

        areas1 = detector.detect_areas()
        assert mock_match.call_count == 1

        # 第二次调用应该命中缓存
        areas2 = detector.detect_areas()
        assert mock_match.call_count == 1  # 没有增加
        assert areas1 == areas2

def test_lightweight_sampling():
    """测试轻量抽样统计"""
    detector = AreaDetector("/tmp/test-project")

    # 模拟抽样200个文件
    with patch.object(detector, "_lightweight_sampling") as mock_sampling:
        mock_sampling.return_value = [
            ProjectArea(
                name="detected-python",
                language="python",
                confidence="Medium",
                evidence=["sampled 150 files"],
                file_patterns=["*.py"]
            )
        ]

        areas = detector.detect_areas(sample_limit=200)

        assert len(areas) == 1
        assert areas[0].language == "python"
        assert areas[0].confidence == "Medium"
```

### Cycle 2: QueryRouter + 智能预算分配 (1 day)

**Acceptance Criteria**:
- ✅ 查询关键词到区域的路由
- ✅ 智能预算分配 (主区域70-80%)
- ✅ 混合项目搜索优先级
- ✅ 预算不足时的回退策略

**Test Cases**:
```python
def test_query_routing_to_backend():
    """测试查询路由到后端区域"""
    router = QueryRouter()
    areas = [
        ProjectArea(name="backend-go", language="go"),
        ProjectArea(name="frontend-ts", language="typescript")
    ]

    routing = router.route_query("find JWT authentication handler", areas)

    # JWT handler应该路由到Go后端
    backend_area = next(area for area in routing.applied_areas if area.name == "backend-go")
    assert backend_area.budget_files >= 35  # 获得主要预算

def test_query_routing_to_frontend():
    """测试查询路由到前端区域"""
    router = QueryRouter()
    areas = [
        ProjectArea(name="backend-go", language="go"),
        ProjectArea(name="frontend-ts", language="typescript")
    ]

    routing = router.route_query("find React login component", areas)

    # React component应该路由到TS前端
    frontend_area = next(area for area in routing.applied_areas if area.name == "frontend-ts")
    assert frontend_area.budget_files >= 35  # 获得主要预算

def test_balanced_routing():
    """测试均衡路由策略"""
    router = QueryRouter()
    areas = [
        ProjectArea(name="backend-go", language="go"),
        ProjectArea(name="frontend-ts", language="typescript")
    ]

    routing = router.route_query("find authConfig usage", areas)

    # 模糊查询应该均衡分配
    total_budget = sum(area.budget_files for area in routing.applied_areas)
    for area in routing.applied_areas:
        assert abs(area.budget_files - total_budget/2) <= 5  # 允许小幅偏差

def test_budget_allocation_strategy():
    """测试预算分配策略"""
    router = QueryRouter()
    areas = [
        ProjectArea(name="backend-go", language="go"),
        ProjectArea(name="frontend-ts", language="typescript"),
        ProjectArea(name="shared-py", language="python")
    ]

    routing = router.route_query("find user service", areas)

    # 应该给最高分区域70-80%预算
    sorted_areas = sorted(routing.applied_areas, key=lambda x: x.score, reverse=True)
    primary_area = sorted_areas[0]
    secondary_areas = sorted_areas[1:]

    primary_budget_ratio = primary_area.budget_files / 50  # 假设总预算50
    assert 0.7 <= primary_budget_ratio <= 0.8
```

### Cycle 3: FeedbackSystem + Story 1.3集成 (1 day)

**Acceptance Criteria**:
- ✅ 可观测反馈系统 (detected_areas, applied_areas, coverage)
- ✅ LLM友好的执行报告
- ✅ Story 1.3的ExecutionContext.check_limits()集成
- ✅ 错误分类和修复建议

**Test Cases**:
```python
def test_execution_report_generation():
    """测试执行报告生成"""
    feedback = FeedbackSystem()

    routing = QueryRouting(
        areas=[
            ProjectArea(name="backend-go", language="go", confidence="High", evidence=["go.mod"]),
            ProjectArea(name="frontend-ts", language="typescript", confidence="High", evidence=["package.json"])
        ],
        applied_areas=[
            AppliedArea(name="backend-go", budget_files=35, scanned_files=35, match_count=8),
            AppliedArea(name="frontend-ts", budget_files=15, scanned_files=15, match_count=2)
        ],
        final_patterns=["backend/**/*.go", "frontend/**/*.ts"]
    )

    report = feedback.create_execution_report(routing, MockSearchResults())

    # 验证检测到的区域信息
    detected_languages = [area["language"] for area in report.detected_areas]
    assert "go" in detected_languages
    assert "typescript" in detected_languages

    # 验证应用的区域预算
    backend_applied = next(area for area in report.applied_areas if area["name"] == "backend-go")
    assert backend_applied["budget_files"] == 35

    # 验证覆盖率信息
    assert "coverage" in report
    assert report["coverage"]["backend-go"]["scanned"] == 35
    assert report["coverage"]["backend-go"]["found"] == 8

def test_story13_integration():
    """测试Story 1.3集成"""
    mock_agent = Mock()
    mock_project = Mock()

    wrapper = SafeSearchWrapper(mock_agent, mock_project)

    # 创建带约束的ExecutionPlan
    limits = ExecutionLimits(max_files=50, timeout_seconds=20)
    execution_plan = ExecutionPlan(
        description="Test safe search with constraints",
        tool_name="safe_search",
        limits=limits
    )

    # 模拟执行引擎
    with patch.object(mock_agent, "execution_engine") as mock_engine:
        mock_engine.execute.return_value = "Found 3 matches"

        result = wrapper.execute("find getUserData", execution_plan=execution_plan)

        # 验证ExecutionPlan被传递给执行引擎
        mock_engine.execute.assert_called_once()
        call_kwargs = mock_engine.execute.call_args[1]
        assert "execution_plan" in call_kwargs

def test_constraint_violation_feedback():
    """测试约束违规的反馈"""
    mock_agent = Mock()
    mock_project = Mock()

    wrapper = SafeSearchWrapper(mock_agent, mock_project)

    # 模拟约束违规
    with patch.object(mock_agent, "execution_engine") as mock_engine:
        mock_engine.execute.side_effect = FileLimitExceededError(
            "Too many files", files_processed=60, max_files=50
        )

        with pytest.raises(FileLimitExceededError) as exc_info:
            wrapper.execute("find .*", max_files=50)

        # 验证异常信息包含详细信息
        assert exc_info.value.files_processed == 60
        assert exc_info.value.max_files == 50

def test_llm_friendly_error_messages():
    """测试LLM友好的错误消息"""
    feedback = FeedbackSystem()

    # 测试业务冲突错误
    business_error = feedback.create_error_response(
        "business_conflict",
        "Query pattern '.*' is too broad",
        {"suggestion": "Use more specific search pattern"}
    )

    assert business_error.error_type == "business_conflict"
    assert "too broad" in business_error.fix_suggestion.summary
    assert "specific search pattern" in business_error.fix_suggestion.code_example

def test_mcp_schema_with_area_support():
    """测试支持区域的MCP Schema"""
    schema = safe_search_tool.get_schema()

    # 验证区域选择参数
    assert "area_selector" in schema["properties"]
    assert "auto" in schema["properties"]["area_selector"]["enum"]

    # 验证区域包含参数
    assert "include_areas" in schema["properties"]

    # 验证示例包含区域使用
    area_example = next(
        ex for ex in schema["examples"]
        if "area_selector" in ex["parameters"]
    )
    assert area_example["parameters"]["area_selector"] == "auto"
```

## 🔧 GPT-5优化后的MCP Interface Design

### 支持区域检测的JSON Schema

```json
{
  "name": "safe_search",
  "description": "Multi-area intelligent search with automatic project detection and constraint enforcement",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query or pattern",
        "examples": [
          "find JWT authentication handler",
          "locate React login component",
          "search for TODO comments in backend"
        ],
        "negative_examples": [
          ".*",  # Too broad
          "find everything",  # Too vague
          "all files"  # Too general
        ]
      },
      "area_selector": {
        "type": "string",
        "description": "Area selection strategy",
        "enum": ["auto", "backend-go", "frontend-ts", "ruby", "python"],
        "default": "auto",
        "examples": [
          "auto - automatically detect and route to relevant areas",
          "backend-go - search only Go backend area",
          "frontend-ts - search only TypeScript frontend area"
        ]
      },
      "include_areas": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "root": {"type": "string"},
            "include_globs": {"type": "array", "items": {"type": "string"}},
            "exclude_globs": {"type": "array", "items": {"type": "string"}}
          }
        },
        "description": "Explicit area definitions (overrides auto-detection)"
      },
      "max_files": {
        "type": "integer",
        "description": "Maximum files to search per area",
        "minimum": 1,
        "maximum": 1000,
        "default": 50,
        "field_dependencies": {
          "area_count": {
            "single": {"default": 50},
            "multiple": {"default": 30}
          }
        }
      },
      "mode": {
        "type": "string",
        "description": "Search mode affecting budget allocation",
        "enum": ["conservative", "balanced", "broad"],
        "default": "balanced",
        "examples": [
          "conservative - strict limits, 20 files per area",
          "balanced - standard limits, 30 files per area",
          "broad - relaxed limits, 50 files per area"
        ]
      }
    },
    "required": ["query"]
  },
  "examples": [
    {
      "name": "Auto-Detected Backend Search",
      "parameters": {
        "query": "find JWT authentication handler",
        "area_selector": "auto",
        "mode": "balanced"
      },
      "expected_outcome": "Auto-routes to Go backend area with 35 file budget"
    },
    {
      "name": "Explicit Frontend Search",
      "parameters": {
        "query": "locate React login component",
        "area_selector": "frontend-ts",
        "max_files": 40
      },
      "expected_outcome": "Searches only TypeScript frontend with 40 file limit"
    },
    {
      "name": "Multi-Area Configuration",
      "parameters": {
        "query": "find authConfig usage",
        "include_areas": [
          {
            "name": "backend-go",
            "root": "backend",
            "include_globs": ["backend/**/*.go"],
            "exclude_globs": ["backend/vendor/**"]
          },
          {
            "name": "frontend-ts",
            "root": "frontend",
            "include_globs": ["frontend/**/*.ts", "frontend/**/*.tsx"],
            "exclude_globs": ["frontend/node_modules/**"]
          }
        ]
      },
      "expected_outcome": "Searches both configured areas with custom patterns"
    }
  ],
  "response_format": {
    "detected_areas": [
      {
        "name": "backend-go",
        "language": "go",
        "root": "backend",
        "confidence": "High",
        "evidence": ["go.mod", "cmd/", "internal/"]
      }
    ],
    "applied_areas": [
      {
        "name": "backend-go",
        "budget_files": 35,
        "scanned_files": 35,
        "found_matches": 8,
        "duration_ms": 45
      }
    ],
    "applied_patterns": ["backend/**/*.go"],
    "total_results": 8,
    "execution_time_ms": 47
  }
}
```

### 新增工具: get_language_hint

```json
{
  "name": "get_language_hint",
  "description": "Detect project areas and languages with zero-cost analysis",
  "parameters": {
    "type": "object",
    "properties": {
      "sample_limit": {
        "type": "integer",
        "description": "Maximum files to sample for analysis",
        "minimum": 50,
        "maximum": 500,
        "default": 200
      },
      "exclude_dirs": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Directories to exclude from sampling",
        "default": [".git", "node_modules", "vendor", "target", "build", "dist"]
      }
    }
  },
  "response_format": {
    "areas": [
      {
        "name": "backend-go",
        "language": "go",
        "root": "backend",
        "confidence": "High",
        "evidence": ["go.mod", "cmd/"],
        "suggested_globs": ["backend/**/*.go"],
        "exclude_globs": ["backend/vendor/**"]
      }
    ],
    "cache_status": "hit|miss",
    "analysis_time_ms": 12
  }
}
```

### GPT-5方案的核心优势总结

#### **1. Epic-001目标符合度 (显著提升)**

| 指标 | 原方案 | GPT-5方案 | 提升 |
|------|--------|-----------|------|
| Token节省 | 40-60% | 60-80% | ⬆️+20% |
| 性能开销 | <1ms | <10ms | ⬆️+9ms |
| 复杂度 | 低 | 中低 | ✅可控 |
| 混合项目支持 | ❌ | ✅完美 | ⭐⭐⭐⭐⭐ |

#### **2. 关键创新点**

- **区域检测**: 解决monorepo痛点，现代项目必备
- **哨兵文件**: 零成本高准确率，避免全库扫描
- **智能路由**: 查询关键词→精准区域，大幅减少无关结果
- **可观测反馈**: LLM可学习，用户可复制修复

#### **3. 实施建议**

**优先级调整**:
1. **Cycle 1**: AreaDetector (哨兵文件+缓存) - 核心创新
2. **Cycle 2**: QueryRouter (智能路由) - 价值巨大
3. **Cycle 3**: FeedbackSystem (可观测) - LLM友好

**复杂度控制**:
- 严格遵循KISS原则
- 规则驱动，无ML依赖
- 复用现有基础设施
- 渐进式实施

---

## 🎯 **最终建议**

GPT-5的讨论方案在**混合项目支持**和**可观测反馈**方面显著超越我们原设计，建议：

1. **采纳核心架构**: AreaDetector + QueryRouter + FeedbackSystem
2. **保持KISS原则**: 规则驱动，零成本优先
3. **渐进实施**: 先实现哨兵文件检测，再扩展智能路由
4. **复用现有基础**: 充分利用Serena已有的语言检测设施

**这个整合方案如何在您看来？我们是否应该按照GPT-5优化的架构来实施Feature 2.1？**

## 🎯 Implementation Readiness

**Dependencies**: Story 1.3 ✅ Complete
**Risks**: Low (基于现有成功模式)
**Success Criteria**:
- 智能参数优化准确率 > 80%
- 搜索违规减少 > 90%
- 性能提升 > 30%
- 100% 向后兼容

---

**Next Step**: 准备开始 Cycle 1: SearchScopeAnalyzer TDD implementation