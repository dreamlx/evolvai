# 🔍 safe_search 预防性分析报告

**分析日期**: 2025-11-07
**文档类型**: 预防性分析（Implementation-Before Analysis）
**分析师**: EvolvAI Team
**应用原则**: Feature 2.2 Critical Analysis Lessons

---

## 📊 Executive Summary

### 核心发现

✅ **好消息**: safe_search **尚未实现**，这是应用Feature 2.2教训的**完美时机**！

🎯 **关键洞察**:
> "在AI时代，**不写代码比写代码更重要**。预防性分析比事后修复成本低90%。"

### 状态概览

| 维度 | 状态 | 评估 |
|------|------|------|
| 产品定义 | ✅ 存在且详细 | docs/product/definition/product-definition-v1.md |
| 实现代码 | ❌ 不存在 | Story 2.1 [Backlog] |
| 测试用例 | ❌ 不存在 | 无测试文件 |
| **风险等级** | 🟢 **低风险** | 可以完全按BDD → TDD正确实施 |

### 建议行动

1. ✅ **先创建BDD场景文档**（参考story-2.2-bdd-scenarios.md模板）
2. ✅ **基于场景写测试**（Red阶段）
3. ✅ **实现最小功能集**（Green阶段）
4. ✅ **重构优化**（Refactor阶段）
5. ❌ **不要直接写代码**（避免Feature 2.2错误）

---

## 🎯 产品定义分析

### 明确定义的功能（Good！）

产品定义文档（v1.0, lines 171-214）**清晰定义**了safe_search的核心功能：

#### 1. 工具智能编排 ✅

```python
优先级：ripgrep > ugrep > grep
- ripgrep: 极速JSON输出，尊重ignore规则
- ugrep: 高性能替代方案
- grep: 降级兜底（提示性能损失）
```

**评估**: ✅ 清晰、可实现、有明确优先级

#### 2. 公平基线对比 ✅

```bash
# 确保grep和rg使用相同文件集
git ls-files -z | xargs -0 grep -nE "pattern"
git ls-files -z | xargs -0 rg -n "pattern"
```

**评估**: ✅ 对比方法正确，避免了不公平对比陷阱

#### 3. JSON输出结构 ✅

```json
{
    "tool_used": "ripgrep",
    "stats": {
        "hits_count": 127,
        "files_matched": 23
    },
    "top_matches": [...],
    "execution_time_ms": 280,
    "baseline_comparison": {
        "grep_time_s": 5.2,
        "rg_time_s": 0.28,
        "speedup": "18.6x"
    }
}
```

**评估**: ✅ 结构合理，包含必要的TPST分析数据

### 潜在过度设计风险（Warning！）

#### ⚠️ 风险1: baseline_comparison字段

**问题**: 产品定义要求**每次搜索都运行grep和rg对比**

```json
"baseline_comparison": {
    "grep_time_s": 5.2,
    "rg_time_s": 0.28,
    "speedup": "18.6x"
}
```

**过度设计分析**:
- ❌ 每次搜索运行2次（rg + grep）→ 性能开销翻倍
- ❌ 用户不需要每次看到对比数据
- ❌ 违反"safe_search应该更快"的初衷

**建议**:
1. **MVP阶段**: 只运行rg，**不返回**baseline_comparison字段
2. **基准测试阶段**: 专门的测试套件做对比，不在生产工具中
3. **Phase 3**: 如果用户需要，添加`--benchmark`开关

**决策**:
```python
# ✅ MVP实现（推荐）
return {
    "tool_used": "ripgrep",
    "stats": {...},
    "top_matches": [...],
    "execution_time_ms": 280
    # ❌ 删除baseline_comparison字段
}

# ❌ 产品定义版本（过度设计）
return {
    ...,
    "baseline_comparison": {...}  # 需要运行2次搜索
}
```

#### ⚠️ 风险2: top_matches截断逻辑

**问题**: 产品定义未明确截断规则

```json
"top_matches": [
    {"file": "src/auth.py", "line": 45, "snippet": "..."}
]
```

**需要明确**:
- ❓ top_matches返回多少条？10？50？100？
- ❓ snippet包含多少上下文？1行？3行？5行？
- ❓ 如果匹配5000个文件，如何处理？

**建议**:
```python
# ✅ 明确的MVP截断规则
MAX_TOP_MATCHES = 50  # 最多返回50个匹配
MAX_SNIPPET_LINES = 3  # 每个匹配上下文3行

# 如果匹配超过50个，返回统计信息
if hits_count > MAX_TOP_MATCHES:
    return {
        "stats": {"hits_count": 5127, "files_matched": 823},
        "top_matches": matches[:50],  # 前50个
        "truncated": True,
        "truncated_count": 5077
    }
```

#### ⚠️ 风险3: scope参数复杂度

**问题**: Epic README提到scope限制，但产品定义未详细说明

从Epic README (line 150):
```
- scope 限制验证
```

**需要明确**:
- ❓ scope是什么格式？Glob pattern？目录路径？
- ❓ 是否支持多个scope？
- ❓ 如何与ExecutionPlan.scope整合？

**建议**:
```python
# ✅ MVP简化版（推荐）
def safe_search(
    query: str,
    scope: str = "**/*",  # 单个glob pattern
    execution_plan: Optional[ExecutionPlan] = None
) -> SearchResult:
    # scope直接传给rg --glob
    pass

# ❌ 过度设计版本（不推荐）
def safe_search(
    query: str,
    scopes: List[SearchScope],  # 复杂对象
    area_selector: str = "auto",  # 自动检测
    smart_filter: bool = True,   # 智能过滤
    ...
) -> SearchResult:
    pass
```

---

## 🚫 **不需要**的功能（YAGNI原则）

基于Feature 2.2教训，这些功能**产品定义未要求，不应实现**：

### ❌ 1. safe_search_batch（批量搜索）

**理由**:
- 产品定义未提及
- Phase 3 Batching Engine会统一处理
- Feature 2.2的`safe_edit_batch`就是过度设计案例

**代码示例（不要写）**:
```python
# ❌ 不要实现这个
def safe_search_batch(
    queries: List[str],
    continue_on_error: bool = False,
    max_parallel: int = 5
) -> List[SearchResult]:
    """批量搜索（不需要！）"""
    pass
```

### ❌ 2. mode参数系统

**理由**:
- Feature 2.2的mode系统（conservative/aggressive）是YAGNI违规
- safe_search只需一种模式：快速+准确

**代码示例（不要写）**:
```python
# ❌ 不要实现这个
def safe_search(
    query: str,
    mode: Literal["fast", "thorough", "smart"] = "smart",
    ...
):
    """mode系统是伪需求"""
    pass
```

### ❌ 3. 复杂的area_selector系统

**理由**:
- safe_search主要靠tool选择（rg/grep）优化
- 不需要复杂的区域检测

**代码示例（不要写）**:
```python
# ❌ 不要实现这个
def safe_search(
    query: str,
    area_selector: Literal["auto", "frontend", "backend", "fullstack"] = "auto",
    smart_scope: bool = True,
    ...
):
    """过度抽象的区域系统"""
    pass
```

### ❌ 4. safe_search_mcp包装方法

**理由**:
- Feature 2.2犯的错误：误解MCP集成方式
- Tool基类自动暴露，不需要单独的`_mcp()`方法

**代码示例（不要写）**:
```python
# ❌ 不要实现这个
class SafeSearchWrapper:
    def safe_search(self, ...):
        """核心方法"""
        pass

    def safe_search_mcp(self, ...):  # ❌ 不需要！
        """MCP包装（误解）"""
        return json.dumps(self.safe_search(...))
```

**正确做法**:
```python
# ✅ 正确的MCP集成
# src/serena/tools/safe_search_tool.py
class SafeSearchTool(Tool):
    def apply(self, query: str, **kwargs) -> str:
        wrapper = SafeSearchWrapper(...)
        result = wrapper.safe_search(query, **kwargs)
        return json.dumps(result)  # Tool系统自动MCP暴露
```

---

## ✅ **需要**的功能（MVP核心）

基于产品定义，safe_search的**最小可用功能集**：

### 1. 工具检测和选择 ✅

```python
def detect_available_tools() -> str:
    """检测可用的搜索工具"""
    if shutil.which("rg"):
        return "ripgrep"
    elif shutil.which("ugrep"):
        return "ugrep"
    elif shutil.which("grep"):
        return "grep"
    else:
        raise ToolNotFoundError("No search tool available")
```

### 2. 基本搜索执行 ✅

```python
def safe_search(
    query: str,
    scope: str = "**/*",
    execution_plan: Optional[ExecutionPlan] = None
) -> SearchResult:
    """核心搜索功能"""
    tool = detect_available_tools()

    if tool == "ripgrep":
        return _search_with_ripgrep(query, scope)
    elif tool == "ugrep":
        return _search_with_ugrep(query, scope)
    else:
        return _search_with_grep(query, scope)
```

### 3. JSON结构化输出 ✅

```python
@dataclass
class SearchResult:
    tool_used: str
    stats: Dict[str, int]  # hits_count, files_matched
    top_matches: List[Match]  # 最多50个
    execution_time_ms: float
    truncated: bool = False
    truncated_count: int = 0
```

### 4. ExecutionPlan集成 ✅

```python
def safe_search(
    query: str,
    scope: str = "**/*",
    execution_plan: Optional[ExecutionPlan] = None
) -> SearchResult:
    """ExecutionPlan约束"""
    if execution_plan:
        # 验证scope在允许范围内
        # 应用timeout限制
        # 记录到审计日志
        pass
```

### 5. MCP工具封装 ✅

```python
# src/serena/tools/safe_search_tool.py
class SafeSearchTool(Tool):
    def apply(self, query: str, scope: str = "**/*", **kwargs) -> str:
        wrapper = SafeSearchWrapper(
            agent=self.agent,
            project=self.agent.active_project
        )
        result = wrapper.safe_search(query, scope, **kwargs)
        return json.dumps(result, indent=2)
```

---

## 📝 BDD场景建议

基于产品定义，建议的**核心BDD场景**（6-8个即可）：

### Scenario 1: 基本搜索（ripgrep可用）

```gherkin
Given ripgrep已安装
  And 项目目录包含3个Python文件
When 我调用 safe_search(query="def test_", scope="**/*.py")
Then 返回成功结果
  And tool_used == "ripgrep"
  And stats.hits_count == 5
  And stats.files_matched == 2
  And top_matches包含文件路径和行号
```

### Scenario 2: 工具降级（ripgrep不可用）

```gherkin
Given ripgrep未安装但grep可用
  And 项目目录包含测试文件
When 我调用 safe_search(query="class")
Then 返回成功结果
  And tool_used == "grep"
  And 结果格式与ripgrep一致
```

### Scenario 3: scope限制

```gherkin
Given 项目包含src/和test/目录
When 我调用 safe_search(query="import", scope="src/**/*.py")
Then 只搜索src/目录
  And test/目录被忽略
```

### Scenario 4: 结果截断（>50个匹配）

```gherkin
Given 搜索结果包含200个匹配
When 我调用 safe_search(query="def")
Then top_matches最多返回50个
  And truncated == true
  And truncated_count == 150
  And stats.hits_count == 200  # 完整统计
```

### Scenario 5: ExecutionPlan timeout限制

```gherkin
Given ExecutionPlan.limits.timeout_s == 5
  And 搜索预计耗时10秒
When 我调用 safe_search(query="complex_pattern", execution_plan=plan)
Then 搜索在5秒后被终止
  And 返回TimeoutError
  And 审计日志记录timeout违规
```

### Scenario 6: 无匹配结果

```gherkin
Given 项目目录存在但无匹配内容
When 我调用 safe_search(query="nonexistent_pattern")
Then 返回成功结果
  And stats.hits_count == 0
  And stats.files_matched == 0
  And top_matches == []
```

### Scenario 7: JSON格式验证

```gherkin
Given safe_search执行成功
When 我解析返回的JSON字符串
Then JSON包含所有必需字段
  And tool_used是字符串
  And stats是字典
  And top_matches是列表
  And execution_time_ms是浮点数
```

### Scenario 8: MCP工具调用（集成测试）

```gherkin
Given SerenaAgent已启动
  And safe_search已注册为MCP工具
When AI助手调用 safe_search(query="test")
Then 返回格式化的JSON字符串
  And 结果可被AI助手解析
  And 审计日志记录工具调用
```

---

## 🎯 实施建议（TDD流程）

### Day 1: BDD场景文档（4小时）

1. 创建`story-2.1-bdd-scenarios.md`（参考story-2.2模板）
2. 详细描述8个核心场景（Gherkin格式）
3. 每个场景映射到DoD标准
4. 用户审查和确认

**交付物**:
- ✅ `docs/development/sprints/current/story-2.1-bdd-scenarios.md`

### Day 2: TDD Red阶段（1人天）

1. 创建`test/evolvai/tools/test_safe_search_wrapper.py`
2. 基于BDD场景编写测试（先写测试！）
3. 每个测试包含Story/Scenario/DoD注释
4. 运行测试 → 全部失败（Red阶段）

**测试结构**:
```python
class TestSafeSearch:
    def test_basic_search_with_ripgrep(self):
        """Scenario 1: Basic search with ripgrep available

        Story: story-2.1-bdd-scenarios.md Scenario 1
        DoD: F1 - Basic search functionality

        Given ripgrep is installed
        When I call safe_search(query="def test_")
        Then return successful result with correct tool
        """
        # Test implementation
```

### Day 3-4: TDD Green阶段（1.5人天）

1. 创建`src/evolvai/tools/safe_search_wrapper.py`
2. 实现最小功能集（让测试通过）
3. **不实现**任何产品定义未要求的功能
4. 运行测试 → 逐个通过（Green阶段）

**实现检查清单**:
- ✅ 只实现8个场景对应的功能
- ❌ 不实现batch功能
- ❌ 不实现mode系统
- ❌ 不实现复杂area_selector
- ❌ 不实现baseline_comparison（MVP阶段）

### Day 5: Refactor阶段（0.5人天）

1. 优化代码结构
2. 提取重复逻辑
3. 改善可读性
4. 运行测试 → 全部通过

### Day 6: MCP集成（0.5人天）

1. 创建`src/serena/tools/safe_search_tool.py`
2. 注册到`desktop-app.yml`
3. 编写MCP集成测试
4. 端到端验证

**总计**: 4人天（比Epic估算的4人天精确！）

---

## 🔍 对比：Feature 2.2 vs safe_search

| 维度 | Feature 2.2（失败案例） | safe_search（正确做法） |
|------|------------------------|------------------------|
| **实施顺序** | 实现 → 测试 → 发现错误 | BDD → TDD → 实现 |
| **产品对齐** | 三方脱节（产品/实现/测试） | BDD场景明确对齐 |
| **过度设计** | safe_edit_batch, mode系统 | **提前识别**，不实现 |
| **测试质量** | 测试不存在的方法 | 测试明确的场景 |
| **通过率** | 8%（1/13） | 目标: 100%（8/8） |
| **重构成本** | 6天重写 | 0天（预防了） |

### 关键差异分析

**Feature 2.2犯的错误（现在避免）**:
1. ❌ 没有BDD场景就开始实现
2. ❌ 测试基于实现细节而非需求
3. ❌ 实现了产品定义未要求的功能
4. ❌ 假设了错误的MCP集成方式

**safe_search的正确做法**:
1. ✅ **先写BDD场景**（需求清晰化）
2. ✅ **基于场景写测试**（需求驱动）
3. ✅ **只实现测试要求的功能**（避免过度设计）
4. ✅ **预防性识别YAGNI违规**（节省开发时间）

---

## 📊 风险评估矩阵

| 风险类型 | 概率 | 影响 | 预防措施 | 状态 |
|---------|------|------|---------|------|
| 实现过度设计功能 | 中 | 高 | BDD场景约束 | ✅ 已防范 |
| 测试假设错误接口 | 低 | 中 | TDD先写测试 | ✅ 已防范 |
| baseline_comparison性能问题 | 高 | 中 | MVP不实现 | ✅ 已决策 |
| scope参数复杂度膨胀 | 中 | 中 | 简化为单个glob | ✅ 已建议 |
| 与ExecutionPlan集成不一致 | 低 | 高 | Phase 0基础已完成 | ✅ 低风险 |

---

## 🎯 最终建议

### 立即行动（Next Steps）

1. **创建BDD场景文档** (4小时)
   ```bash
   # 基于本文档的Scenario 1-8
   cp story-2.2-bdd-scenarios.md story-2.1-bdd-scenarios.md
   # 编辑为safe_search场景
   ```

2. **用户审查和确认** (1小时)
   - 场景是否覆盖核心功能？
   - 是否有遗漏的关键场景？
   - scope简化方案是否接受？
   - baseline_comparison是否MVP不实现？

3. **TDD实施** (3.5人天)
   - Day 1: 写测试（Red）
   - Day 2-3: 写实现（Green）
   - Day 4: 重构（Refactor）
   - Day 5: MCP集成

### 关键成功因素

✅ **坚持TDD**: 先写测试，后写实现
✅ **拒绝过度设计**: YAGNI原则
✅ **BDD场景驱动**: 所有测试映射到场景
✅ **用户确认**: 实施前确认BDD场景

### 预期结果

如果按此计划执行：

- ✅ **测试通过率**: 100%（8/8）
- ✅ **无过度设计**: 0个未使用功能
- ✅ **重构成本**: 0天（预防了）
- ✅ **用户价值**: 核心功能100%实现

---

## 📚 参考文档

### 经验总结
- [Feature 2.2 Critical Analysis](./critical-analysis-feature-2.2.md) ⭐ 失败案例深度分析
- [Feature 2.2 BDD Scenarios](../development/sprints/current/story-2.2-bdd-scenarios.md) ⭐ BDD模板参考

### 产品定义
- [Product Definition v1.0](../product/definition/product-definition-v1.md) - safe_search定义 (lines 171-214)
- [Epic-001 README](../product/epics/epic-001-behavior-constraints/README.md) - Story 2.1定义

### 开发标准
- [TDD Refactoring Guidelines](../testing/standards/tdd-refactoring-guidelines.md)
- [Definition of Done (DoD) Standards](../development/standards/definition-of-done.md)

---

## 💡 核心哲学

> **"在AI时代，最重要的技能不是写代码，而是知道什么该写、什么不该写。**
>
> **预防性分析的成本 < 10% 事后修复成本。"**

### Feature 2.2教训应用

1. **理解需求** > 生产代码
2. **删除过度设计** > 添加功能
3. **BDD场景驱动** > 实现细节驱动
4. **预防性分析** > 事后修复

---

**最后更新**: 2025-11-07
**状态**: 📋 Ready for BDD Scenario Creation
**下一步**: 创建`story-2.1-bdd-scenarios.md`并获取用户确认

---

## ✅ 决策记录

| 决策 | 理由 | 状态 |
|------|------|------|
| MVP不实现baseline_comparison | 性能开销翻倍，用户价值低 | ✅ 建议 |
| scope简化为单个glob pattern | 避免复杂度膨胀 | ✅ 建议 |
| 不实现safe_search_batch | Phase 3统一处理 | ✅ 建议 |
| 不实现mode参数系统 | YAGNI违规 | ✅ 建议 |
| TDD流程：BDD → Test → Impl | Feature 2.2教训 | ✅ 强烈建议 |

**需要用户确认的决策**:
1. ❓ MVP是否删除baseline_comparison字段？
2. ❓ scope是否简化为单个glob pattern？
3. ❓ top_matches是否限制为50个？

---

**🎯 准备好开始正确的TDD流程！**
