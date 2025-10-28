# [ACTIVE] Epic 001: 行为约束系统

**Epic ID**: EPIC-001
**创建日期**: 2025-10-26
**负责人**: EvolvAI Team
**状态**: [ACTIVE]
**优先级**: [P0]

---

## 📋 Epic概述

### 业务价值
通过**物理删除错误执行路径**而非依赖提示词约束，从根本上改变AI助手的行为模式。让AI无法绕过约束，而是从接口层面就只能看到"正确的选项"。

核心理念：**行为工程 > 提示词工程**

### 目标用户
- AI编程助手（Claude Code, Cursor, Roo Code等）
- MCP客户端开发者
- 需要可控AI工具的开发团队

### 成功指标
- **TPST降低**: 相比原生工具降低30%以上（MVP目标）
- **首次成功率**: >75%的任务首次执行成功
- **工具调用准确率**: >90%的工具调用符合约束
- **Token浪费率**: <10%的token用于错误尝试

---

## 🎯 Epic目标

### 主要目标
1. **ExecutionPlan宪法系统**: 用JSON Schema强制约束工具行为
2. **三大safe工具**: safe_search, safe_edit, safe_exec实现物理路径删除
3. **可验证性**: 所有操作可预览、验证、回滚
4. **MCP集成**: 通过MCP协议暴露给AI助手

### 次要目标
- 建立TPST基线测试套件
- 生成可复现的英雄场景演示
- 为Phase 2的索引系统奠定基础

---

## 📦 开发阶段

### Phase 0: 工具调用链路简化（优先级最高⭐）

**为什么优先**：Epic-001 的约束系统需要统一的执行入口和完整的审计能力。当前 7 层调用链路无法满足 TPST 优化需求。

#### Story 0.1: 实现 ToolExecutionEngine ✅
- **描述**: 创建统一执行引擎，实现 4 阶段执行流程和 ExecutionContext
- **优先级**: [P0]
- **估算**: 5人天
- **状态**: ✅ **[Completed]** - Merged to develop (commit: db98dbf)
- **关键交付物**:
  - ✅ `ExecutionPhase` 枚举
  - ✅ `ExecutionContext` 数据类（完整审计信息）
  - ✅ `ToolExecutionEngine` 类（4 阶段流程）
  - ✅ 审计日志接口
  - ✅ TPST 分析接口

#### Story 0.2: ExecutionPlan Schema ✅
- **描述**: 实现 ExecutionPlan Pydantic 模型和完整测试套件
- **优先级**: [P0]
- **估算**: 3人天
- **状态**: ✅ **[Completed]** - Merged to develop (commit: 6e95e17)
- **关键交付物**:
  - ✅ ExecutionPlan Pydantic v2 schema
  - ✅ 23 comprehensive tests (100% passing)
  - ✅ Performance benchmarks (<1ms instantiation)
  - ✅ Full validation with boundary checking

#### Story 0.3: 回归测试和性能验证 ✅
- **描述**: 验证简化后的链路正确性和性能
- **优先级**: [P0]
- **估算**: 2人天
- **状态**: ✅ **[Completed]** - Phase 0 validated (2025-10-28)
- **关键交付物**:
  - ✅ 313/372 existing tests passing (84% - zero new regressions)
  - ✅ 30/32 LSP integration tests passing (93.8%)
  - ✅ Audit log validation complete
  - ✅ Performance baseline established (<10ms overhead)
  - ✅ Phase 0 Completion Report generated

---

### Phase 1: ExecutionPlan 验证框架

#### Feature 1.1: ExecutionPlan Schema
- **Feature ID**: FEATURE-001
- **描述**: 实现 ExecutionPlan Pydantic 模型
- **优先级**: [P0]
- **估算**: 3人天（简化后，直接集成到执行引擎）
- **状态**: [Backlog]

#### Feature 1.2: PlanValidator
- **Feature ID**: FEATURE-002
- **描述**: 实现计划合理性验证器
- **优先级**: [P0]
- **估算**: 4人天
- **状态**: [Backlog]

#### Feature 1.3: 集成到 ToolExecutionEngine
- **Feature ID**: FEATURE-003
- **描述**: 将验证器集成到执行引擎的 pre-execution 阶段
- **优先级**: [P0]
- **估算**: 2人天（简化后，单一注入点）
- **状态**: [Backlog]

---

### Phase 2: Safe Operations Wrapper System

#### Feature 2.1: safe_search wrapper
- **Feature ID**: FEATURE-004
- **描述**: 实现 safe_search，增加 scope 限制
- **优先级**: [P0]
- **估算**: 4人天
- **状态**: [Backlog]

#### Feature 2.2: safe_edit wrapper
- **Feature ID**: FEATURE-005
- **描述**: 实现 safe_edit，增加 impact 评估
- **优先级**: [P0]
- **估算**: 7人天
- **状态**: [Backlog]

#### Feature 2.3: safe_exec wrapper
- **Feature ID**: FEATURE-006
- **描述**: 实现 safe_exec，增加 precondition 检查
- **优先级**: [P1]
- **估算**: 3人天
- **状态**: [Backlog]

---

### Phase 3: Intelligent Batching Engine

#### Feature 3.1: 操作序列分析器
- **Feature ID**: FEATURE-007
- **描述**: 分析 ExecutionPlan，识别可批处理的模式
- **优先级**: [P1]
- **估算**: 5人天
- **状态**: [Backlog]

#### Feature 3.2: 批处理转换器
- **Feature ID**: FEATURE-008
- **描述**: 将多个操作转换为单个批处理操作
- **优先级**: [P1]
- **估算**: 7人天
- **状态**: [Backlog]

#### Feature 3.3: 批处理执行器
- **Feature ID**: FEATURE-009
- **描述**: 执行批处理操作，返回结果映射
- **优先级**: [P1]
- **估算**: 5人天
- **状态**: [Backlog]

---

### Phase 4: Constitutional Constraints System

#### Feature 4.1: 约束规则 DSL
- **Feature ID**: FEATURE-010
- **描述**: 创建声明式规则定义语言
- **优先级**: [P0]
- **估算**: 5人天
- **状态**: [Backlog]

#### Feature 4.2: 约束规则引擎
- **Feature ID**: FEATURE-011
- **描述**: 执行约束规则，判断操作是否违反约束
- **优先级**: [P0]
- **估算**: 6人天
- **状态**: [Backlog]

#### Feature 4.3: 规则配置系统
- **Feature ID**: FEATURE-012
- **描述**: 支持从 YAML 加载约束规则
- **优先级**: [P1]
- **估算**: 3人天
- **状态**: [Backlog]

---

## 📊 时间线

### 实际时间
- **开始日期**: 2025-10-27
- **Phase 0 完成**: ✅ **2025-10-28** (实际: 10人天)
- **Phase 1 开始**: 2025-10-29 (计划)
- **Phase 1 完成**: 2025-11-08 (9人天, 预计)
- **Phase 2 完成**: 2025-11-15 (14人天, 预计)
- **Phase 3 完成**: 2025-11-25 (17人天, 预计)
- **Phase 4 完成**: 2025-12-02 (14人天, 预计)
- **总工作量**: 64人天 (约 13 周)

### 里程碑
- [x] Product Definition完成 - 2025-10-26
- [x] ADR-003: 工具链路简化决策 - 2025-10-27
- [x] ✅ **Phase 0 完成** - 2025-10-28 ⭐ 关键里程碑达成
  - Story 0.1: ToolExecutionEngine ✅
  - Story 0.2: ExecutionPlan Schema ✅
  - Story 0.3: Regression Testing ✅
  - [Phase 0 Completion Report](../../../development/sprints/current/phase-0-completion-report.md) 📄
- [ ] Phase 1 完成（ExecutionPlan 验证） - 2025-11-08
- [ ] Phase 2 完成（Safe Operations） - 2025-11-15
- [ ] Phase 3 完成（Batching Engine） - 2025-11-25
- [ ] Phase 4 完成（Constitutional Constraints） - 2025-12-02
- [ ] Epic-001 全面测试和文档 - 2025-12-06

---

## 🔗 依赖关系

### 依赖的Epic
无 - 这是第一个Epic

### 被依赖的Epic
- EPIC-002: MCP集成与TPST审计 - 需要本Epic提供的safe工具

---

## 🎯 验收标准

### Epic级验收标准
- [ ] ExecutionPlan Schema用Pydantic定义，包含所有强制字段
- [ ] safe_search可自动选择ripgrep/ugrep/grep并返回JSON格式
- [ ] safe_edit使用Patch-First架构，propose和apply一致
- [ ] safe_exec可正确管理进程组，timeout时完全清理
- [ ] 所有工具通过MCP暴露给AI助手
- [ ] 基线测试通过（pytest, fastapi, superset三个repo）

---

## 🛡️ 风险与对策

### 技术风险
| 风险 | 影响 | 概率 | 对策 |
|------|------|------|------|
| difflib性能问题（大文件） | Medium | Low | 限制单次编辑文件大小<10MB |
| git apply冲突处理复杂 | High | Medium | 使用--3way模式，提供冲突解决指导 |
| 进程killpg权限问题 | Medium | Low | 文档说明需要的权限，提供sudo方案 |
| ripgrep不可用时降级 | Low | Low | 提供grep fallback，文档说明依赖 |

### 业务风险
| 风险 | 影响 | 概率 | 对策 |
|------|------|------|------|
| TPST改进不达30% | High | Medium | 严格测量baseline，识别优化点 |
| MCP客户端兼容性 | Medium | Medium | 先支持Claude Code，逐步扩展 |

---

## 📝 备注

### 设计原则
1. **接口层约束 > 提示词约束**: 物理删除错误路径
2. **Patch-First**: propose和apply阶段必须使用同一个diff
3. **Git Worktree隔离**: 每个任务独立worktree，避免污染主目录
4. **Fair Baseline**: 使用git ls-files确保grep和rg对比公平

### 技术栈
- Python 3.11
- Pydantic for schemas
- subprocess for command execution
- difflib for unified diff generation
- MCP protocol for tool exposure

---

## 📚 相关文档

### 架构设计
- [ADR-003: 工具调用链路简化](../../../development/architecture/adrs/003-tool-execution-engine-simplification.md) ⭐ 核心架构决策
- [Phase 0: 工具调用链路简化 - 详细设计](../../../development/architecture/phase-0-tool-execution-engine.md)
- [ADR-001: Graph-of-Thought over Sequential Thinking](../../../development/architecture/adrs/001-graph-of-thought-over-sequential-thinking.md)
- [ADR-002: Monorepo with Epic-003 Future Split](../../../development/architecture/adrs/002-monorepo-with-epic-003-future-split.md)

### 产品文档
- [产品定义 v1.0](../../definition/product-definition-v1.md)
- [讨论总结 2025-10-26](../../definition/discussion-summary-2025-10-26.md)
- [TPST Metrics Reference](../../specs/metrics-reference.md)

### 开发规范
- [Definition of Done (DoD) Standards](../../../development/standards/definition-of-done.md)

---

**最后更新**: 2025-10-27
**更新人**: EvolvAI Team
