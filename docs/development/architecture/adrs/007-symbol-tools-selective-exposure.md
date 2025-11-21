# ADR-007: Symbol Tools Selective Exposure

**Status**: Accepted
**Date**: 2025-11-21
**Decision Makers**: EvolvAI Team

---

## Context

EvolvAI 之前的工具优化策略（Phase 1-4）隐藏了所有 7 个 Serena 符号工具，理由是：
- LLM 应该使用高层工具（batch_edit, safe_search）
- 符号操作应该是内部实现细节
- 减少 Token 消耗和认知负担

**但用户观察到**：
- 在其他项目中，`find_symbol` 被频繁使用
- 其他符号编辑操作（replace_symbol_body 等）使用很少
- 符号读取操作提供了 Grep 无法替代的「语义级代码导航」能力

---

## Decision

**选择性暴露符号工具**：暴露 4 个高价值工具，继续隐藏 3 个低频工具。

### 暴露的工具（4个）

| 工具 | 类型 | 价值 |
|------|------|------|
| `find_symbol` | Read | 符号定位，理解代码结构 |
| `get_symbols_overview` | Read | 文件符号概览 |
| `find_referencing_symbols` | Read | 查找所有引用 |
| `rename_symbol` | Edit | 语义安全的重命名 |

### 继续隐藏的工具（3个）

| 工具 | 原因 |
|------|------|
| `replace_symbol_body` | 完整重写场景少，Edit/replace_regex 够用 |
| `insert_after_symbol` | replace_regex 可替代 |
| `insert_before_symbol` | replace_regex 可替代 |

---

## Rationale

### 1. 符号读取 vs 符号编辑的使用模式

**观察结果**：
- 符号读取工具（find_symbol）：高频使用
- 符号编辑工具（replace_symbol_body）：低频使用

**结论**：AI 主要需要符号工具来「理解」代码，而不是「编辑」代码。

### 2. find_symbol 的独特价值

```python
# find_symbol 能力（Grep 无法替代）
- 通过符号路径快速定位：find_symbol("MyClass/my_method")
- 获取结构化信息：参数签名、返回类型、父类
- 支持模糊搜索：find_symbol("*Controller*")
- 语义级导航：理解作用域和继承关系
```

### 3. rename_symbol vs batch_edit

| 场景 | rename_symbol | batch_edit |
|------|---------------|------------|
| 语义准确性 | ✅ 理解作用域 | ❌ 可能误改 |
| 自动更新引用 | ✅ LSP 保证 | ⚠️ 需要精确正则 |
| 跨文件 | ✅ 自动处理 | ✅ glob 支持 |
| 复杂变换 | ❌ 只能重命名 | ✅ 支持捕获组 |

**结论**：rename_symbol 在「重命名」场景下比 batch_edit 更安全。

### 4. 工具自描述原则

**改进**：优化 docstring 添加 "When to use" / "When NOT to use"

**原因**：
- 好的 MCP 工具应该自描述
- 不应该依赖 CLAUDE.md 解释工具用法
- 帮助 LLM 做出正确的工具选择

---

## Consequences

### Positive

1. **恢复语义导航能力**：AI 可以精确定位和理解代码结构
2. **保持简洁**：只暴露 4 个工具（vs 原来 7 个）
3. **功能互补**：符号工具（理解） + EvolvAI 工具（编辑）
4. **Token 优化**：只增加约 1-2k tokens

### Negative

1. **工具数量增加**：12 → 16 个暴露工具
2. **学习曲线**：LLM 需要学会何时用符号工具 vs Grep

### Neutral

1. **两套工具体系共存**：EvolvAI（文本级） + Serena（符号级）
2. **未来可能整合**：考虑 Agent 架构统一两套工具

---

## Implementation

1. ✅ 移除 4 个工具的 `ToolMarkerOptional`
2. ✅ 优化 docstring（When to use / When NOT to use）
3. ❌ 不修改 CLAUDE.md（工具应自描述）

---

## Future Considerations

### Agent 架构探索

考虑将符号操作封装为 Agent，使用低成本 LLM（如 DeepSeek）处理：

```
Claude Code (用户交互)
    ↓ 自然语言指令
MCP Symbol Agent (DeepSeek)
    ↓ 符号操作
LSP / 代码库
```

**潜在收益**：
- Token 成本降低 ~80%
- 复杂编排在低成本 LLM 上执行
- 简化 Claude 的工具选择

**需要验证**：
- DeepSeek 工具调用能力
- 错误处理和回滚机制
- 上下文传递效率

---

## References

- [INBOX.md - MCP 工具暴露优化反思](../../../workspace/INBOX.md)
- Phase 1-4 优化 commits: `449b329`, `8e93efe`
- Serena symbol_tools.py 源码

---

**Last Updated**: 2025-11-21
