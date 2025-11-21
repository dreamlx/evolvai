# Feature 4.1: EvolvAI-Serena 架构整合决策分析

**Feature ID**: FEATURE-4.1
**创建日期**: 2025-01-19
**负责人**: EvolvAI Team
**状态**: [Planning]
**优先级**: [P0]

---

## 📋 背景

### 问题发现

**2025-01-19 MCP 工具优化后的关键发现**:

EvolvAI 和 Serena 是**两套完全独立的工具体系**,没有任何集成:

```
Layer 1: EvolvAI 高层工具 (LLM 调用层)
├── batch_edit(pattern, replacement)
│   └── 实现: regex.subn() - 纯文本替换 ❌ 未使用符号工具
├── safe_search(query)
│   └── 实现: ripgrep - 文本搜索 ❌ 未使用符号工具
└── safe_exec(command, timeout)
    └── 实现: subprocess - 命令执行

Layer 2: Serena 符号工具 (隐藏层)
├── find_symbol(name_path) - LSP 符号查找
├── replace_symbol_body(name_path, new_body) - LSP 符号替换
└── find_referencing_symbols(name_path) - LSP 引用查找
    └── 实现: tree-sitter + LSP
```

**证据**:
- `src/evolvai/tools/batch_editor.py:196` - `regex.subn(replacement, original_content)`
- Grep 搜索: `evolvai/tools/` 中没有任何符号工具调用
- 两套工具体系完全隔离,未集成

---

## 🎯 目标

### 主要目标

1. **选择最优架构方案** - 从 4 个选项中选择
2. **建立决策依据** - 技术分析 + 权衡矩阵
3. **形成实施路线** - 根据选择的方案制定实施计划
4. **记录架构决策** - 创建 ADR 文档

### 成功标准

- [ ] 4 个架构选项的详细技术分析完成
- [ ] 权衡矩阵完成 (Token, 功能, 复杂度, 维护性, 性能)
- [ ] ADR-00X 文档完成
- [ ] 实施路线图清晰
- [ ] 团队/社区讨论完成,达成共识

---

## 🔍 4 个架构选项详细分析

### 选项 A: 保持现状 - 双工具体系独立共存

#### 架构图

```
┌─────────────────────────────────────────┐
│         MCP Interface (26 tools)        │
├─────────────────────────────────────────┤
│  EvolvAI Tools (12)    Serena Tools (6) │
│  ├── batch_edit         ├── find_symbol │
│  ├── safe_search        ├── replace_..  │
│  └── safe_exec          └── insert_...  │
├─────────────────────────────────────────┤
│  Text Operations        Symbol Ops      │
│  (regex, ripgrep)       (LSP, tree-sit) │
└─────────────────────────────────────────┘
```

#### 技术细节

**EvolvAI 工具体系**:
- **实现**: Python regex, subprocess, ripgrep
- **依赖**: 无 LSP 依赖
- **操作级别**: 文本级 (行, 正则模式)
- **语言支持**: 全语言 (文本通用)
- **性能**: 快速 (无符号解析开销)

**Serena 工具体系**:
- **实现**: tree-sitter, LSP
- **依赖**: tree-sitter grammar, LSP 服务器
- **操作级别**: 符号级 (函数, 类, 方法)
- **语言支持**: 需要 tree-sitter grammar (Python, Go, TypeScript...)
- **性能**: 较慢 (符号解析开销)

#### 优点

1. **✅ 零重构成本**: 无需修改任何代码
2. **✅ 互不干扰**: 两套工具独立运行,互不影响
3. **✅ 灵活性高**: LLM 可根据场景选择合适工具
4. **✅ 降级简单**: EvolvAI 工具始终可用 (无 LSP 依赖)

#### 缺点

1. **❌ Token 浪费**: 需要暴露两套工具 (~15k tokens vs 当前 7k)
2. **❌ 认知负担**: LLM 需要理解两套工具的区别和使用场景
3. **❌ 功能重叠**: batch_edit vs replace_symbol_body 功能重叠
4. **❌ 工具选择错误**: LLM 可能选择错误的工具 (文本级 vs 符号级)

#### Token 分析

| 工具集 | 工具数 | 估算 Token |
|--------|--------|-----------|
| EvolvAI | 12 | ~7k |
| Serena 符号工具 | 6 | ~5k |
| 其他 MCP 工具 | 8 | ~18k |
| **总计** | **26** | **~30k** |

**影响**: MCP 工具 Token 从 ~24k 增加到 ~30k (+25%)

#### 适用场景

- **适合**: 短期方案,快速验证
- **不适合**: 长期架构,Token 优化需求高

---

### 选项 B: 集成架构 - EvolvAI 底层使用 Serena 符号工具

#### 架构图

```
┌─────────────────────────────────────────┐
│         MCP Interface (12 tools)        │
├─────────────────────────────────────────┤
│         EvolvAI High-Level Tools        │
│  ├── batch_edit (智能选择)              │
│  │    ├─> 符号级编辑 (replace_symbol)  │
│  │    └─> 文本级编辑 (regex fallback)  │
│  ├── safe_search (智能选择)             │
│  │    ├─> 符号级搜索 (find_symbol)     │
│  │    └─> 文本级搜索 (ripgrep)         │
│  └── safe_exec (unchanged)              │
├─────────────────────────────────────────┤
│      Serena Symbol Layer (内部)         │
│  ├── find_symbol                        │
│  ├── replace_symbol_body                │
│  └── find_referencing_symbols           │
├─────────────────────────────────────────┤
│      LSP + tree-sitter (底层)           │
└─────────────────────────────────────────┘
```

#### 技术细节

**batch_edit 重构**:
```python
class BatchEditTool:
    def apply(self, pattern, replacement, scope="**/*", execution_plan=None):
        # 步骤 1: 检测是否可用符号级编辑
        if self._can_use_symbol_edit(pattern, scope):
            # 符号级精确编辑
            return self._symbol_level_edit(pattern, replacement, scope)
        else:
            # 降级到文本级编辑 (当前实现)
            return self._text_level_edit(pattern, replacement, scope)

    def _can_use_symbol_edit(self, pattern, scope):
        """检查是否满足符号级编辑条件"""
        # 条件 1: LSP 服务器可用
        if not self.lsp_available:
            return False
        # 条件 2: pattern 看起来像符号名 (不是复杂正则)
        if not self._is_symbol_like(pattern):
            return False
        # 条件 3: scope 在支持的语言范围内
        if not self._is_supported_language(scope):
            return False
        return True

    def _symbol_level_edit(self, pattern, replacement, scope):
        """使用 Serena 符号工具进行精确编辑"""
        # 1. find_symbol(pattern) - 查找符号
        symbols = self.serena.find_symbol(pattern, scope)
        # 2. replace_symbol_body() - 替换符号体
        results = []
        for symbol in symbols:
            result = self.serena.replace_symbol_body(
                symbol.name_path,
                replacement
            )
            results.append(result)
        return results
```

**降级策略**:
```python
class SymbolEditFallback:
    """符号级编辑降级策略"""

    def __init__(self):
        self.lsp_available = self._check_lsp()
        self.supported_languages = ["python", "go", "typescript", ...]

    def _check_lsp(self) -> bool:
        """检查 LSP 服务器是否可用"""
        try:
            # 尝试启动 LSP 服务器
            lsp = LSPClient()
            lsp.initialize()
            return True
        except Exception:
            logger.warning("LSP unavailable, falling back to text-level")
            return False

    def should_use_symbol_edit(self, pattern, scope) -> bool:
        """决策逻辑: 是否使用符号级编辑"""
        # 决策树
        if not self.lsp_available:
            return False
        if self._is_complex_regex(pattern):
            return False  # 复杂正则用文本级
        if not self._language_supported(scope):
            return False
        return True
```

#### 优点

1. **✅ 符号级精确性**: batch_edit 获得符号级编辑能力
2. **✅ 统一架构**: 单一工具集,清晰的分层
3. **✅ Token 最优**: 只暴露 12 工具 (~7k tokens)
4. **✅ 智能降级**: LSP 不可用时自动降级到文本级

#### 缺点

1. **❌ 重构工作量大**: 需要重构 batch_edit, safe_search
2. **❌ 复杂度增加**: LSP 依赖, tree-sitter 配置
3. **❌ 性能开销**: 符号解析比文本替换慢
4. **❌ 语言支持受限**: tree-sitter 不支持的语言无法用符号级

#### Token 分析

| 工具集 | 工具数 | 估算 Token |
|--------|--------|-----------|
| EvolvAI (集成符号) | 12 | ~8k (+1k 用于说明符号级能力) |
| 其他 MCP 工具 | 8 | ~18k |
| **总计** | **20** | **~26k** |

**影响**: MCP 工具 Token 保持 ~24k (当前水平)

#### 技术风险

| 风险 | 缓解措施 |
|------|----------|
| LSP 服务器启动失败 | 自动降级到文本级 |
| tree-sitter grammar 不可用 | 维护支持语言列表 |
| 符号解析性能慢 | 大文件 (>10k 行) 强制文本级 |
| 复杂正则无法映射到符号 | 检测复杂正则,降级到文本级 |

#### 实施工作量

| 任务 | 估算 |
|------|------|
| batch_edit 重构 | 5 人天 |
| safe_search 重构 | 3 人天 |
| 降级策略实现 | 2 人天 |
| LSP 集成优化 | 3 人天 |
| 性能优化和基准测试 | 3 人天 |
| 测试和文档 | 4 人天 |
| **总计** | **20 人天** |

#### 适用场景

- **适合**: 长期架构,追求符号级精确性,Token 优化需求高
- **不适合**: 快速迭代,短期验证

---

### 选项 C: 暴露两套工具 - 给 LLM 选择权

#### 架构图

```
┌─────────────────────────────────────────┐
│         MCP Interface (18 tools)        │
├──────────────────┬──────────────────────┤
│  EvolvAI Tools   │   Serena Tools       │
│  (Text-Level)    │   (Symbol-Level)     │
├──────────────────┼──────────────────────┤
│  batch_edit      │  replace_symbol_body │
│  (regex-based)   │  (LSP-based)         │
│                  │                      │
│  safe_search     │  find_symbol         │
│  (ripgrep)       │  (LSP search)        │
│                  │                      │
│  safe_exec       │  find_referencing... │
│  (subprocess)    │  (LSP references)    │
└──────────────────┴──────────────────────┘

LLM 决策逻辑 (通过 docstring):
- 简单文本替换 → batch_edit
- 精确符号编辑 → replace_symbol_body
- 文本搜索 → safe_search
- 符号查找 → find_symbol
```

#### 技术细节

**工具 docstring 优化** - 清晰说明使用场景:

```python
class BatchEditTool:
    """Text-level batch editing with regex patterns.

    When to use:
    - Simple text replacements across multiple files
    - Regex pattern matching (e.g., "old.*?new")
    - Language-agnostic edits
    - Fast, no LSP dependency

    When NOT to use:
    - Need symbol-level precision (use replace_symbol_body)
    - Renaming functions/classes (use rename_symbol)
    - Understanding code structure (use find_symbol)
    """

class ReplaceSymbolBodyTool:
    """Symbol-level precise editing using LSP.

    When to use:
    - Rename functions/classes/methods
    - Replace entire function bodies
    - Need to understand code structure
    - Want refactoring-safe edits

    When NOT to use:
    - Simple text replacements (use batch_edit - faster)
    - Regex-based edits
    - LSP not available for language

    Supported languages: Python, Go, TypeScript, Rust, ...
    """
```

#### 优点

1. **✅ 灵活性最高**: LLM 根据场景选择最合适工具
2. **✅ 无需重构**: 两套工具独立存在
3. **✅ 功能完整**: 文本级和符号级都可用
4. **✅ 快速实现**: 只需优化 docstring

#### 缺点

1. **❌ Token 消耗大**: 需要暴露 18 工具 (~12k tokens)
2. **❌ 认知负担重**: LLM 需要理解工具选择逻辑
3. **❌ 选择错误率高**: LLM 可能选择不当工具
4. **❌ 重复功能**: batch_edit vs replace_symbol_body 功能重叠

#### Token 分析

| 工具集 | 工具数 | 估算 Token | 备注 |
|--------|--------|-----------|------|
| EvolvAI | 12 | ~7k | 需优化 docstring |
| Serena 符号工具 | 6 | ~4k | 需优化 docstring |
| 其他 MCP 工具 | 8 | ~18k | - |
| **总计** | **26** | **~29k** | 优化后约 ~26k |

**优化策略**: 压缩 docstring,只保留 "When to use" / "When NOT to use"

#### 工具选择错误率分析

**假设场景**: 重命名函数 `calculate_total` → `compute_sum`

**LLM 选择错误示例**:
```python
# ❌ 错误选择: batch_edit (文本级)
batch_edit(
    pattern="calculate_total",
    replacement="compute_sum"
)
# 问题: 可能误替换字符串、注释中的 "calculate_total"

# ✅ 正确选择: rename_symbol (符号级)
rename_symbol(
    name_path="MyClass/calculate_total",
    new_name="compute_sum"
)
# 优势: 只重命名符号定义和引用,不影响字符串
```

**错误率估算**:
- 保守估计: 20-30% (LLM 选择不当工具)
- 影响: Token 浪费 (尝试错误 → 重试),编辑错误

#### 实施工作量

| 任务 | 估算 |
|------|------|
| EvolvAI docstring 优化 | 1 人天 |
| Serena docstring 优化 | 1 人天 |
| 工具选择指南文档 | 1 人天 |
| 测试和验证 | 2 人天 |
| **总计** | **5 人天** |

#### 适用场景

- **适合**: 需要最大灵活性,可接受 Token 成本
- **不适合**: Token 优化需求高,追求简洁架构

---

### 选项 D (当前): 只暴露 EvolvAI - 隐藏 Serena 符号工具

#### 架构图

```
┌─────────────────────────────────────────┐
│         MCP Interface (12 tools)        │
├─────────────────────────────────────────┤
│         EvolvAI Tools (暴露)             │
│  ├── batch_edit (regex)                 │
│  ├── safe_search (ripgrep)              │
│  └── safe_exec (subprocess)             │
├─────────────────────────────────────────┤
│      Serena Symbol Tools (隐藏)         │
│  ├── find_symbol (不暴露)               │
│  ├── replace_symbol_body (不暴露)       │
│  └── find_referencing_symbols (不暴露)  │
└─────────────────────────────────────────┘
```

#### 技术细节

**当前状态** (Phase 1-4 已实施):
- 暴露 12 EvolvAI 工具 + 8 其他 MCP 工具 = 20 工具
- Token: ~24k
- 6 个 Serena 符号工具标记为 `ToolMarkerOptional` (隐藏)

#### 优点

1. **✅ 简洁**: 单一工具集,认知负担最低
2. **✅ Token 最优**: ~24k tokens (当前水平)
3. **✅ 已实施**: Phase 1-4 完成,无需额外工作
4. **✅ 快速**: 文本级操作速度快

#### 缺点

1. **❌ 缺少符号级能力**: batch_edit 只是文本替换
2. **❌ 编辑精确性差**: 容易误替换 (字符串、注释)
3. **❌ 浪费 Serena 开发**: 符号工具已开发但未使用
4. **❌ 功能不完整**: 无法进行重构级操作 (重命名、提取方法)

#### Token 分析

| 工具集 | 工具数 | 估算 Token |
|--------|--------|-----------|
| EvolvAI | 12 | ~7k |
| 其他 MCP 工具 | 8 | ~18k |
| **总计** | **20** | **~25k** |

#### 功能缺失示例

**场景 1: 重命名函数**
```python
# 当前 (方案 D): batch_edit
batch_edit(pattern="old_func", replacement="new_func")
# 问题:
# - 误替换字符串 "call old_func()"
# - 误替换注释 "# old_func is deprecated"
# - 需要手动检查所有替换

# 理想 (方案 B): 符号级
rename_symbol("MyClass/old_func", "new_func")
# 优势:
# - 只重命名符号,不影响字符串/注释
# - 自动更新所有引用
```

**场景 2: 查找函数引用**
```python
# 当前 (方案 D): safe_search
safe_search(query="my_function")
# 问题:
# - 返回所有文本匹配 (包括注释、字符串)
# - 无法区分定义和引用
# - 需要人工过滤

# 理想 (方案 B): 符号级
find_referencing_symbols("MyClass/my_function")
# 优势:
# - 只返回真实引用 (函数调用)
# - 区分定义和引用
# - 结果精确
```

#### 适用场景

- **适合**: 短期 dogfooding,简单编辑场景
- **不适合**: 需要重构级操作,精确编辑需求高

---

## 📊 权衡矩阵

### 综合评分

| 维度 | 权重 | 选项 A | 选项 B | 选项 C | 选项 D |
|------|------|--------|--------|--------|--------|
| **Token 优化** | 25% | 2/10 | 9/10 | 5/10 | 10/10 |
| **功能完整性** | 25% | 8/10 | 10/10 | 10/10 | 5/10 |
| **实施复杂度** | 20% | 10/10 | 3/10 | 8/10 | 10/10 |
| **维护性** | 15% | 5/10 | 7/10 | 4/10 | 8/10 |
| **性能** | 10% | 7/10 | 6/10 | 7/10 | 9/10 |
| **LLM 认知负担** | 5% | 3/10 | 9/10 | 2/10 | 10/10 |
| **加权总分** | 100% | **5.85** | **7.40** | **6.85** | **8.15** |

### 详细评分说明

#### Token 优化 (权重 25%)
- **选项 A**: 2/10 - ~30k tokens,增加 25%
- **选项 B**: 9/10 - ~26k tokens,保持当前水平
- **选项 C**: 5/10 - ~26k tokens (优化后),但仍高于选项 D
- **选项 D**: 10/10 - ~25k tokens,最优

#### 功能完整性 (权重 25%)
- **选项 A**: 8/10 - 两套工具都可用,但重复
- **选项 B**: 10/10 - 符号级 + 文本级,智能选择
- **选项 C**: 10/10 - 两套工具都可用,最大灵活性
- **选项 D**: 5/10 - 只有文本级,缺少符号级

#### 实施复杂度 (权重 20%)
- **选项 A**: 10/10 - 无需任何重构
- **选项 B**: 3/10 - 需要大量重构 (20 人天)
- **选项 C**: 8/10 - 只需 docstring 优化 (5 人天)
- **选项 D**: 10/10 - 已实施

#### 维护性 (权重 15%)
- **选项 A**: 5/10 - 两套工具体系,维护成本高
- **选项 B**: 7/10 - 统一架构,但 LSP 依赖复杂
- **选项 C**: 4/10 - 两套工具,重复功能
- **选项 D**: 8/10 - 单一工具集,简单

#### 性能 (权重 10%)
- **选项 A**: 7/10 - 两套工具,性能各异
- **选项 B**: 6/10 - 符号解析有开销,但有降级
- **选项 C**: 7/10 - LLM 可选快速工具
- **选项 D**: 9/10 - 纯文本操作,最快

#### LLM 认知负担 (权重 5%)
- **选项 A**: 3/10 - 需要理解两套工具区别
- **选项 B**: 9/10 - 单一工具集,智能决策
- **选项 C**: 2/10 - 工具选择复杂
- **选项 D**: 10/10 - 最简单,单一选择

---

## 💡 推荐方案

### 🏆 推荐: **选项 B (集成架构)**

**理由**:
1. **长期价值最高**: 符号级编辑能力 + Token 优化
2. **架构最清晰**: 统一的工具分层,清晰的职责划分
3. **智能降级**: LSP 不可用时自动降级,鲁棒性强
4. **功能最完整**: 文本级和符号级都支持

**前提条件**:
- ✅ 有足够开发时间 (20 人天)
- ✅ 追求长期架构清晰
- ✅ 需要符号级精确编辑能力
- ✅ 可接受 LSP 依赖

### 🥈 备选: **选项 D (当前方案)**

**理由**:
1. **短期最优**: 已实施,Token 最优
2. **实施成本零**: 无需任何开发
3. **性能最快**: 纯文本操作

**适用场景**:
- ⏰ 短期 dogfooding 验证
- 💰 开发资源有限
- ⚡ 追求极致性能

**缺点接受**:
- ❌ 缺少符号级能力 (未来可能需要)
- ❌ 编辑精确性差 (需要人工检查)

---

## 🗺️ 实施路线图

### 如果选择 方案 B (集成架构)

#### Phase 1: 基础设施准备 (5 人天)
- [ ] LSP 集成层实现
- [ ] tree-sitter 配置管理
- [ ] 降级策略框架
- [ ] 语言支持检测

#### Phase 2: batch_edit 重构 (5 人天)
- [ ] 符号级编辑逻辑
- [ ] 智能决策器 (符号级 vs 文本级)
- [ ] 降级到文本级
- [ ] 单元测试 + 集成测试

#### Phase 3: safe_search 重构 (3 人天)
- [ ] 符号级搜索集成
- [ ] 智能决策器
- [ ] 降级策略
- [ ] 测试

#### Phase 4: 性能优化 (3 人天)
- [ ] 符号解析缓存
- [ ] 大文件检测和降级
- [ ] 基准测试

#### Phase 5: 文档和验收 (4 人天)
- [ ] ADR 文档
- [ ] 用户文档
- [ ] 开发文档
- [ ] 验收测试

**总计**: 20 人天 (~4 周)

### 如果选择 方案 D (保持现状)

- [ ] 更新 INBOX.md,记录决策理由
- [ ] 创建 ADR 文档,说明为何选择方案 D
- [ ] 文档说明符号工具的使用场景 (何时手动使用)

**总计**: 1 人天

---

## 📝 下一步行动

### 立即行动
1. **与用户讨论**: 展示这份分析,讨论偏好
2. **技术验证**: 如果倾向方案 B,先做技术 POC (2 人天)
3. **社区反馈**: 如果是开源项目,征求社区意见

### 决策后
- **如果选择 方案 B**: 创建实施计划,启动 Phase 1
- **如果选择 方案 D**: 记录决策,更新文档
- **创建 ADR**: 记录架构决策和理由

---

**最后更新**: 2025-01-19
**更新人**: EvolvAI Team
**状态**: 等待用户讨论和决策
