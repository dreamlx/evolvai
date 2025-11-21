# EvolvAI 项目历史与定位转变

**创建日期**: 2025-10-27  
**类型**: 项目定位记录  
**状态**: [ACTIVE]

---

## 项目演进历史

### 原始项目：Serena Agent (Fork)

**来源**: dreamlx/serena（开源项目fork）  
**原定位**: LSP-based semantic code analysis and editing toolkit for AI agents  
**核心能力**:
- Language Server Protocol (LSP) integration (25+ languages)
- Symbol-based code navigation and editing
- Model Context Protocol (MCP) server for AI tools
- Project memory and knowledge persistence

**原计划**: 增强 Serena 插件，添加智能记忆系统

### 关键转折点：2025-10-26

**决策**: 从增强插件 → 创建全新项目  
**触发原因**:
1. 发现 AI 辅助编程的核心痛点不是工具能力，而是 **行为效率**
2. 识别出 TPST (Tokens Per Solved Task) 作为关键指标
3. 意识到需要系统性的行为约束和思维优化，而不只是代码分析

**新项目命名**: EvolvAI - 智能开发环境学习助手

---

## 新项目定位：EvolvAI

### 核心价值主张

**从**: "语义代码分析工具"  
**到**: "AI 行为工程平台 - 让 AI 更高效地解决问题"

**核心差异**:
- **Serena**: 提供代码理解和编辑能力（工具能力）
- **EvolvAI**: 优化 AI 的行为模式和思维效率（行为工程）

### 三大 Epic 架构

这是完全原创的架构设计，不基于上游 Serena：

#### Epic-001: 行为约束系统 (Behavior Constraints)
- **目标**: 防止 AI 浪费 token 在低效行为上
- **核心工具**: safe_search, safe_edit, safe_exec
- **创新点**: ExecutionPlan 宪法系统，分批策略

#### Epic-002: 项目规范即服务 (Project Standards as MCP)
- **目标**: 减少文档返工和位置纠正的 token 浪费
- **核心能力**: .project_standards.yml 规范校验
- **创新点**: 90% 规则 + 10% 小模型的成本优化架构

#### Epic-003: Graph-of-Thought 引擎 (GoT Engine)
- **目标**: 降低思考 token 占比从 40% 到 ≤20%
- **核心技术**: Event Sourcing + 并行分支 + 早停策略
- **创新点**: 用事件溯源替代顺序思考链，支持并行探索

### 核心指标：TPST

**TPST (Tokens Per Solved Task)** = 总消耗 token / 成功解决的任务数

**目标**:
- MVP (Week 3): TPST 降低 ≥30%
- 完整版 (Week 6): TPST 降低 ≥50%
- 理想目标: TPST 降低 ≥70%

---

## 与上游 Serena 的关系

### 保留的技术基础

EvolvAI **继续使用** Serena 的技术基础设施：
- ✅ SolidLanguageServer (LSP wrapper)
- ✅ Symbol-based code navigation
- ✅ MCP protocol integration
- ✅ Multi-language support (25+ languages)
- ✅ Project memory system (enhanced)

### 全新创建的部分

EvolvAI **原创设计** 的核心系统：
- 🆕 Graph-of-Thought 引擎（Epic-003）
- 🆕 Behavior Constraints 系统（Epic-001）
- 🆕 Project Standards MCP 服务（Epic-002）
- 🆕 TPST 度量和优化框架
- 🆕 ExecutionPlan 宪法系统
- 🆕 事件溯源思维架构

**技术栈对比**:
```
Serena (上游):
└── LSP Tools ─→ AI Agent ─→ Code Changes

EvolvAI (新架构):
└── LSP Tools ─→ GoT Engine ─→ Behavior Constraints ─→ AI Agent ─→ Validated Code Changes
                     ↑               ↑
                     └───────────────┘
                  Project Standards MCP
```

---

## 遗留文档处理

以下文档来自上游 Serena 项目或早期探索，已归档：

### 归档文档列表

1. **custom_agent.md**
   - 来源: 上游 Serena
   - 内容: 原始代理系统设计
   - 归档原因: EvolvAI 采用新的 GoT 架构

2. **memory-reflection-and-redesign.md**
   - 来源: 早期探索（增强 Serena 插件阶段）
   - 内容: 记忆系统重构设计
   - 归档原因: 项目定位改变，从插件增强到全新平台

3. **serena-intelligent-memory-redesign.md**
   - 来源: 早期探索
   - 内容: 智能记忆系统设计
   - 归档原因: 已被 Epic-003 的事件溯源架构替代

4. **serena_on_chatgpt.md**
   - 来源: 上游 Serena
   - 内容: ChatGPT 集成文档
   - 归档原因: EvolvAI 采用 MCP 协议，不限于特定 AI 平台

5. **scala_setup_guide_for_serena.md**
   - 来源: 上游 Serena
   - 内容: Scala 语言支持配置
   - 归档原因: 技术文档，保留供参考但不属于核心文档体系

**归档位置**: `docs/archive/upstream-legacy/`

---

## 开源策略变化

### 原计划（Serena fork）
- 贡献改进回上游
- 保持兼容性
- 作为 Serena 的增强版本

### 新策略（EvolvAI 独立项目）
- 独立开源项目（全新 repo）
- 保留对 Serena 技术基础的致谢
- 专注于 AI 行为工程领域
- 目标：成为 AI 辅助编程效率优化的参考实现

**License**: MIT（继续使用宽松协议）  
**Attribution**: "Built on Serena's LSP infrastructure"

---

## 关键决策记录

### 为什么不继续作为 Serena 插件？

**原因分析**:
1. **问题域不同**: Serena 解决代码理解，EvolvAI 解决 AI 行为效率
2. **架构差异**: GoT 引擎是根本性的架构创新，不是增量功能
3. **用户群不同**: Serena 面向 AI agent 开发者，EvolvAI 面向所有使用 AI 编程的开发者
4. **产品定位**: 从"工具"到"平台"，需要独立品牌和叙事

### 为什么保留 Serena 技术基础？

**原因分析**:
1. **成熟稳定**: LSP 集成已支持 25+ 语言，无需重复开发
2. **专注创新**: 让团队专注于 GoT、Behavior Constraints 等核心创新
3. **开源精神**: 站在巨人肩膀上，继续开源贡献
4. **工程效率**: 快速验证 TPST 优化假设，而非重写基础设施

---

## 未来演进路径

### Phase 1: MVP (Week 1-3)
- 完成三大 Epic 核心功能
- 验证 TPST 降低 ≥30% 假设
- 保留 Serena 技术基础不变

### Phase 2: 独立开源 (Week 4-6)
- 建立独立 GitHub repo (dreamlx/evolvai)
- 完善文档和使用指南
- 发布 v0.1.0 (MVP 版本)

### Phase 3: 社区建设 (Month 2-3)
- 发布技术博客和论文
- 建立贡献者社区
- 推广 TPST 作为行业标准指标

### Phase 4: 平台化 (Month 4-6)
- 支持更多 AI 模型（除 Claude 外）
- 提供 SaaS 服务（可选）
- 建立插件生态系统

---

## 总结

EvolvAI 从 Serena fork 演进为独立项目，标志着从**工具思维**到**行为工程思维**的转变：

**核心洞察**: AI 辅助编程的瓶颈不是缺少工具能力，而是 AI 的行为效率问题。

**解决方案**: 通过 GoT 引擎、行为约束和项目规范，系统性地降低 TPST，让 AI 更高效地解决问题。

**长期愿景**: 让 EvolvAI 成为 AI 辅助编程效率优化的事实标准，就像 ESLint 是 JavaScript 代码质量的标准一样。

---

**维护者**: EvolvAI Team  
**最后更新**: 2025-10-27  
**相关文档**: 
- `docs/product/definition/product-definition-v1.md`
- `docs/product/roadmap/three-epics-relationship.md`
- `docs/development/architecture/adrs/001-graph-of-thought-over-sequential-thinking.md`
