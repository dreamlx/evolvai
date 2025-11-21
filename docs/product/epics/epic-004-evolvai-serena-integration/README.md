# [DRAFT] Epic 004: EvolvAI-Serena 架构整合与优化

**Epic ID**: EPIC-004
**创建日期**: 2025-01-19
**负责人**: EvolvAI Team
**状态**: [DRAFT]
**优先级**: [P1]
**触发来源**: [workspace/INBOX.md - MCP 工具暴露优化后的反思](#相关背景)

---

## 📋 Epic概述

### 业务价值

**关键发现**: EvolvAI 和 Serena 是**两套独立的工具体系**,没有集成:
- **EvolvAI**: 文本级操作 (regex, ripgrep, subprocess)
- **Serena**: 符号级操作 (LSP-based, tree-sitter)

**问题**:
1. **功能重复**: 两套工具体系独立存在,造成 Token 浪费和认知负担
2. **精确性缺失**: EvolvAI 高层工具 (batch_edit, safe_search) 只是文本操作,缺少符号级精确性
3. **架构混乱**: 两套工具体系共存但未整合,架构定位不清

**价值**:
- 统一工具架构,减少 Token 消耗
- 提升编辑精确性 (符号级 vs 文本级)
- 清晰的架构边界和职责划分
- 为 AI 提供更强大的工具能力

### 目标用户
- AI 编程助手 (Claude Code, Cursor 等)
- MCP 客户端开发者
- EvolvAI 内部架构

### 成功指标
- **Token 优化**: 相比双工具体系减少 20-30% MCP 工具描述 Token
- **功能完整性**: batch_edit 获得符号级精确编辑能力
- **工具调用准确率**: >90% 的编辑操作使用正确的工具 (符号级 vs 文本级)
- **架构清晰度**: 明确的工具层次和职责划分

---

## 🎯 Epic目标

### 主要目标

1. **架构方向决策**: 选择并实施 4 个架构选项中的最优方案
2. **工具整合**: 统一 EvolvAI 和 Serena 工具体系
3. **符号级能力**: 为高层工具 (batch_edit) 提供符号级精确性
4. **Token 优化**: 减少 MCP 工具暴露的 Token 消耗

### 次要目标

- 建立清晰的工具分层设计文档
- 为未来新工具提供集成指南
- 优化 MCP 工具描述 (docstring)

---

## 🔍 相关背景

### 触发事件

**2025-01-19**: MCP 工具优化 (Phase 1-4) 完成后,发现关键架构问题:

**验证结果**:
1. **batch_edit**: 使用 `regex.subn()` - **纯正则替换**,未使用符号工具
2. **safe_search**: 使用 ripgrep,未使用符号级搜索
3. **propose_edit/apply_edit**: 未使用符号操作

**架构现状**:
```
EvolvAI 高层工具 (batch_edit, safe_search, safe_exec)
  ↓ (不依赖)
  ✗ (隔离)
  ↓
Serena 符号工具 (find_symbol, replace_symbol_body, ...)
  ↓ (基于)
  LSP (Language Server Protocol)
```

**文档**: [workspace/INBOX.md](../../../../workspace/INBOX.md)

---

## 📦 包含的 Features

### Feature 4.1: 架构方向决策与分析

- **Feature ID**: FEATURE-4.1
- **描述**: 深入分析 4 个架构选项,选择最优方案
- **优先级**: [P0]
- **估算**: 5 人天
- **状态**: [Planning]

**交付物**:
- 4 个架构选项的详细技术分析 (ADR)
- 权衡矩阵 (Token, 功能, 复杂度, 维护性)
- 架构决策记录 (ADR-00X)
- 实施路线图

**4 个架构选项**:

#### 选项 A: 保持现状 - 双工具体系独立共存
**描述**: EvolvAI (文本级) 和 Serena (符号级) 各自独立

**优点**:
- ✅ 无需重构,零成本
- ✅ 各自独立,互不干扰
- ✅ 灵活性高,适应不同场景

**缺点**:
- ❌ 功能重叠,Token 浪费
- ❌ LLM 需要选择用哪套工具,认知负担重
- ❌ 缺少符号级精确编辑能力

**Token 影响**: 当前 ~7k (12 工具暴露),如果暴露两套工具 ~15k

#### 选项 B: 集成架构 - EvolvAI 底层使用 Serena 符号工具
**描述**: 重构 EvolvAI 高层工具,底层调用 Serena 符号操作

**优点**:
- ✅ 统一架构,batch_edit 获得符号级精确性
- ✅ 单一工具集,Token 最优
- ✅ 清晰的分层: 高层工具 → 符号操作 → LSP

**缺点**:
- ❌ 需要重构 EvolvAI (batch_edit, safe_search)
- ❌ 增加复杂度 (LSP 依赖, tree-sitter 配置)
- ❌ 性能开销 (符号解析)

**Token 影响**: ~7k (保持 12 工具,但内部使用符号操作)

**技术风险**:
- LSP 服务器不可用时的降级策略
- tree-sitter 语言支持的覆盖范围
- 符号级操作的性能开销 (大文件)

#### 选项 C: 暴露两套工具 - 给 LLM 选择权
**描述**: 同时暴露 EvolvAI 和 Serena 工具,让 LLM 根据场景选择

**优点**:
- ✅ 灵活性最高,适应不同场景
- ✅ 无需重构,快速实现
- ✅ 文本级和符号级操作都可用

**缺点**:
- ❌ 认知负担重,LLM 需要理解两套工具的差异
- ❌ Token 消耗大 (两套工具描述)
- ❌ 工具选择错误率高

**Token 影响**: ~15k (暴露 EvolvAI 12 工具 + Serena 6 符号工具)

#### 选项 D (当前): 只暴露 EvolvAI - 隐藏 Serena 符号工具
**描述**: Phase 1-4 已实施,只暴露 EvolvAI 12 工具

**优点**:
- ✅ 简洁,Token 最优
- ✅ 单一工具集,认知负担低
- ✅ 已实施,无需额外工作

**缺点**:
- ❌ 失去符号级精确操作能力
- ❌ batch_edit 只是文本替换,容易出错
- ❌ 无法利用 Serena 的符号分析能力

**Token 影响**: ~7k (12 工具)

---

### Feature 4.2: 工具整合实施 (待决策后确定)

- **Feature ID**: FEATURE-4.2
- **描述**: 根据 Feature 4.1 决策,实施工具整合
- **优先级**: [P0]
- **估算**: 待定 (根据选择的方案)
- **状态**: [Blocked - 等待 Feature 4.1 完成]

**可能的 Story** (根据选择的方案):

**如果选择方案 B (集成架构)**:
- Story 4.2.1: 重构 batch_edit 使用 Serena 符号工具
- Story 4.2.2: 重构 safe_search 集成符号级搜索
- Story 4.2.3: LSP 降级策略实现
- Story 4.2.4: 性能优化和基准测试

**如果选择方案 C (双工具暴露)**:
- Story 4.2.1: 优化两套工具的 docstring (减少 Token)
- Story 4.2.2: 添加工具选择指南 (docstring 中)
- Story 4.2.3: 实现工具选择验证器

**如果选择方案 A (保持现状)** 或 **方案 D (当前方案)**:
- 无需实施,记录决策理由即可

---

### Feature 4.3: MCP 工具描述优化

- **Feature ID**: FEATURE-4.3
- **描述**: 优化 MCP 工具 docstring,减少 Token 消耗
- **优先级**: [P1]
- **估算**: 2 人天
- **状态**: [Planning]

**交付物**:
- 优化所有 MCP 工具的 docstring
- 建立 docstring 优化指南
- Token 减少 >20%

---

## 📊 时间线

### 预计时间
- **开始日期**: 2025-01-19
- **Feature 4.1 完成**: 2025-01-26 (5 人天)
- **Feature 4.2 完成**: 待定 (根据选择的方案)
- **Feature 4.3 完成**: 2025-01-28 (2 人天)
- **Epic 完成**: 待定

### 里程碑
- [ ] Feature 4.1: 架构决策完成 - 2025-01-26
- [ ] ADR-00X: 架构整合决策文档 - 2025-01-26
- [ ] Feature 4.2: 工具整合实施完成 - 待定
- [ ] Feature 4.3: MCP docstring 优化完成 - 2025-01-28
- [ ] Epic-004 验收和文档 - 待定

---

## 🔗 依赖关系

### 依赖的 Epic
- EPIC-001: 行为约束系统 - Phase 2 (Safe Tools 已实现)

### 被依赖的 Epic
- 无

### 相关工作
- MCP 工具优化 (Phase 1-4) - 已完成 (2025-01-19)
- workspace/INBOX.md - 架构反思问题

---

## 🎯 验收标准

### Epic 级验收标准

**Feature 4.1: 架构决策**
- [ ] 4 个架构选项的详细技术分析完成
- [ ] 权衡矩阵完成 (Token, 功能, 复杂度, 维护性)
- [ ] ADR-00X 文档完成
- [ ] 实施路线图清晰

**Feature 4.2: 工具整合** (待定)
- [ ] 根据选择的方案,完成相应的实施
- [ ] 所有测试通过 (单元测试 + 集成测试)
- [ ] 性能基准测试达标
- [ ] 文档更新完成

**Feature 4.3: MCP 优化**
- [ ] 所有 MCP 工具 docstring 优化完成
- [ ] Token 减少 ≥20%
- [ ] docstring 优化指南文档完成

**整体验收**
- [ ] 架构清晰,职责明确
- [ ] Token 消耗优化达标
- [ ] 工具调用准确率 >90%
- [ ] 用户文档和开发文档完整

---

## 🛡️ 风险与对策

### 技术风险

| 风险 | 影响 | 概率 | 对策 |
|------|------|------|------|
| LSP 服务器不可用 (方案 B) | High | Medium | 实现降级策略,回退到文本级操作 |
| tree-sitter 语言支持不全 (方案 B) | Medium | Medium | 维护支持语言列表,不支持时降级 |
| 符号级操作性能开销大 (方案 B) | Medium | Medium | 大文件限制,性能基准测试,优化缓存 |
| 工具选择错误率高 (方案 C) | High | High | 提供清晰的工具选择指南,示例丰富 |

### 业务风险

| 风险 | 影响 | 概率 | 对策 |
|------|------|------|------|
| 重构工作量大,延期 (方案 B) | High | Medium | 分阶段实施,先 MVP 后优化 |
| Token 优化不达预期 (方案 C) | Medium | Medium | 严格测量 baseline,识别优化点 |
| 架构决策失误,需要返工 | High | Low | 充分分析,技术验证,社区讨论 |

---

## 📝 备注

### 设计原则

1. **架构清晰 > 功能完整**: 清晰的架构边界比功能完整更重要
2. **Token 优化优先**: MCP 工具 Token 是稀缺资源,必须优化
3. **渐进式实施**: 先 MVP,后优化,避免过度设计
4. **降级策略必备**: 符号级操作失败时必须有文本级降级

### 关键问题

**为什么 EvolvAI 不用 Serena 符号工具?**
- 历史原因: EvolvAI 和 Serena 并行开发,未集成
- 技术原因: LSP 依赖复杂,tree-sitter 配置繁琐
- 设计原因: 可能认为文本级操作已足够?

**如果 batch_edit 不用符号工具,为什么?**
- 实现困难? 性能问题? 设计决策? 需要深入分析

**工具暴露策略应该基于什么?**
- 当前: LLM 调用意图 (编辑/搜索/执行)
- 备选: 功能完整性 (文本级 + 符号级)
- 权衡: 简洁性 vs 精确性 vs Token 消耗

---

## 📚 相关文档

### 触发文档
- [workspace/INBOX.md](../../../../workspace/INBOX.md) - 架构反思问题
- [MCP Tool Optimization (Phase 1-4)](../../../knowledge/lessons/mcp-docstring-token-optimization.md)

### 架构设计
- [ADR-00X: EvolvAI-Serena 架构整合](../../../development/architecture/adrs/00X-evolvai-serena-integration.md) - 待创建

### 相关 Epic
- [Epic-001: 行为约束系统](../epic-001-behavior-constraints/README.md)

### 实施文档
- [Feature 4.1: 架构决策分析](./feature-4.1-architecture-decision.md) - 待创建
- [Feature 4.2: 工具整合实施](./feature-4.2-tool-integration.md) - 待创建
- [Feature 4.3: MCP docstring 优化](./feature-4.3-mcp-docstring-optimization.md) - 待创建

---

**最后更新**: 2025-01-19
**更新人**: EvolvAI Team
**更新内容**:
- 创建 Epic-004 初稿
- 定义 4 个架构选项
- 规划 3 个 Features
- 建立验收标准和风险对策
