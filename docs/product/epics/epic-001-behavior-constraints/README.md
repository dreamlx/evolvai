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
- 为Epic-002和Epic-003提供约束基础设施

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

**📄 实施计划**: [Phase 1 Implementation Plan](../../../development/sprints/current/phase-1-implementation-plan.md)

#### Story 1.1: PlanValidator 核心实现
- **Story ID**: STORY-1.1
- **描述**: 实现 ExecutionPlan 合理性验证器，检查约束一致性
- **优先级**: [P0]
- **估算**: 3人天 (优化后，从4人天减少)
- **状态**: [Backlog]
- **📄 TDD 计划**: [Story 1.1 TDD Plan](../../../development/sprints/current/story-1.1-tdd-plan.md)
- **交付物**:
  - ValidationResult 数据类 (验证结果封装)
  - PlanValidator 类 (业务规则验证，不重复Pydantic边界检查)
  - 20-25 测试 (优化后，100% 覆盖率)
  - 性能 <1ms

#### Story 1.2: ToolExecutionEngine 集成
- **Story ID**: STORY-1.2
- **描述**: 将 PlanValidator 集成到执行引擎的 pre-execution 阶段
- **优先级**: [P0]
- **估算**: 3人天
- **状态**: [Backlog]
- **交付物**:
  - 更新 ToolExecutionEngine._pre_execution_with_constraints()
  - ConstraintViolationError 异常处理
  - 违规记录到审计日志
  - 向后兼容性验证

#### Story 1.3: Runtime Constraint Monitoring
- **Story ID**: STORY-1.3
- **描述**: 实现集成式运行时约束监控，为 Safe Tools 和 Constitutional Constraints 提供关键基础设施
- **优先级**: [P1]
- **估算**: 2.5人天 (优化后，从3人天减少)
- **状态**: [Backlog]
- **📄 决策**: [ADR-004: RuntimeConstraintMonitor Optimization](../../../development/architecture/adrs/004-runtime-constraint-monitor-optimization.md)
- **交付物**:
  - 增强 ExecutionContext (集成运行时跟踪器)
  - 运行时约束违规异常类
  - 集成式约束检查机制
  - 为 Phase 2 Safe Tools 和 Phase 4 Constitutional Constraints 奠定基础

**🎯 战略重要性**:
- **关键基础设施**: Safe Tools 运行时强制执行的必要条件
- **Phase 4 基础**: Constitutional Constraints 的运行时环境
- **TPST 核心**: 通过早期失败减少 token 浪费

**Phase 1 总工作量**: 8.5人天 (~2周) (优化后，从9人天减少)

---

### Phase 2: Safe Operations Wrapper System

**📄 架构设计**: [通用基准测试框架](../../../development/architecture/universal-benchmarking-framework.md) ⭐ 所有Safe Tools共享

#### Story 2.1: safe_search核心功能
- **Story ID**: STORY-2.1
- **描述**: 实现safe_search核心搜索功能，BDD驱动TDD开发
- **优先级**: [P0]
- **估算**: 4人天
- **状态**: [Backlog]
- **📄 分析**: [safe_search预防性分析](../../../knowledge/preventive-analysis-safe-search.md)
- **📄 基准测试**: [baseline testing strategy](../../../knowledge/research/baseline-testing-strategy.md)
- **交付物**:
  - safe_search工具实现
  - 工具检测和选择（ripgrep/ugrep/grep）
  - scope限制验证
  - JSON格式输出
  - ExecutionPlan集成
  - UsageLogger集成（复用通用系统）
  - BDD场景驱动的完整测试套件

#### Story 2.1.1: safe_search单元基准测试
- **Story ID**: STORY-2.1.1
- **描述**: 建立safe_search的单元基准测试套件
- **优先级**: [P0]
- **估算**: 1人天
- **状态**: [Backlog]
- **交付物**:
  - 3个benchmark repos（small/medium/large）
  - 10-15个基准测试用例
  - rg vs grep公平对比
  - CI/CD集成和回归检测
  - baseline.json基线数据

#### Story 2.1.2: safe_search MCP集成
- **Story ID**: STORY-2.1.2
- **描述**: 将safe_search暴露为MCP工具
- **优先级**: [P0]
- **估算**: 0.5人天
- **状态**: [Backlog]
- **交付物**:
  - SafeSearchTool（Tool基类）
  - MCP服务器注册
  - 端到端测试

#### Story 2.2: safe_edit核心功能
- **Story ID**: STORY-2.2
- **描述**: 实现safe_edit，Patch-First架构，BDD驱动TDD开发
- **优先级**: [P0]
- **估算**: 6人天（从7人天优化）
- **状态**: [Backlog]
- **📄 分析**: [Feature 2.2 Critical Analysis](../../../knowledge/critical-analysis-feature-2.2.md)
- **📄 BDD场景**: [Story 2.2 BDD Scenarios](../../../development/sprints/current/story-2.2-bdd-scenarios.md)
- **📄 删除计划**: [DELETION_CHECKLIST.md](../../../../DELETION_CHECKLIST.md)
- **交付物**:
  - Patch-First架构（propose_edit/apply_edit）
  - Git worktree隔离
  - unified diff生成（difflib）
  - patch_id机制
  - ExecutionPlan集成
  - UsageLogger集成（复用通用系统）
  - 冲突处理机制
  - BDD场景驱动的完整测试套件

#### Story 2.2.1: safe_edit单元基准测试
- **Story ID**: STORY-2.2.1
- **描述**: 建立safe_edit的单元基准测试套件
- **优先级**: [P0]
- **估算**: 1人天
- **状态**: [Backlog]
- **交付物**:
  - 基准测试用例（编辑速度、patch生成、worktree操作）
  - propose/apply性能对比
  - CI/CD集成

#### Story 2.2.2: safe_edit MCP集成
- **Story ID**: STORY-2.2.2
- **描述**: 将safe_edit暴露为MCP工具
- **优先级**: [P0]
- **估算**: 0.5人天
- **状态**: [Backlog]
- **交付物**:
  - SafeEditTool（Tool基类）
  - MCP服务器注册
  - 端到端测试

#### Story 2.3: safe_exec核心功能
- **Story ID**: STORY-2.3
- **描述**: 实现safe_exec，进程组管理和输出截断
- **优先级**: [P1]
- **估算**: 3人天
- **状态**: [Backlog]
- **交付物**:
  - safe_exec工具实现
  - 进程组管理（os.setsid, killpg）
  - precondition验证
  - 输出截断（head 50 + tail 50）
  - timeout清理机制
  - ExecutionPlan集成
  - UsageLogger集成（复用通用系统）

#### Story 2.3.1: safe_exec单元基准测试
- **Story ID**: STORY-2.3.1
- **描述**: 建立safe_exec的单元基准测试套件
- **优先级**: [P1]
- **估算**: 1人天
- **状态**: [Backlog]
- **交付物**:
  - 基准测试用例（命令执行速度、超时处理、进程清理）
  - CI/CD集成

#### Story 2.3.2: safe_exec MCP集成
- **Story ID**: STORY-2.3.2
- **描述**: 将safe_exec暴露为MCP工具
- **优先级**: [P1]
- **估算**: 0.5人天
- **状态**: [Backlog]
- **交付物**:
  - SafeExecTool（Tool基类）
  - MCP服务器注册
  - 端到端测试

#### Story 2.4: 通用基准测试框架 ⭐ 新增
- **Story ID**: STORY-2.4
- **描述**: 实现通用基准测试基础设施（所有Safe Tools共享）
- **优先级**: [P0]
- **估算**: 2人天
- **状态**: [Backlog]
- **📄 设计**: [通用基准测试框架](../../../development/architecture/universal-benchmarking-framework.md)
- **依赖**: ToolExecutionEngine（Phase 0已完成）
- **交付物**:
  - UsageLogger通用实现（src/evolvai/benchmarks/usage_logger.py）
  - UsageReplayer通用实现（src/evolvai/benchmarks/usage_replayer.py）
  - BenchmarkReporter实现（src/evolvai/benchmarks/reporter.py）
  - CLI工具（evolvai-replay, evolvai-report）
  - CI/CD集成（每周自动回放）
  - 模式切换支持（production/sampling/development）
  - 文档和使用指南

**Phase 2总工作量**: 19.5人天（约4周）- 从14人天增加，但获得完整基准测试能力

**🎯 关键创新**:
- 所有Safe Tools共享统一的基准测试基础设施
- ToolExecutionEngine（Phase 0）提供内置审计日志和TPST分析
- UsageLogger/Replayer支持真实使用场景的长期数据收集
- 未来新增Safe Tools自动获得基准测试能力

---

### Phase 3: Intelligent Batching Engine

#### Story 3.1: 操作序列分析器
- **Story ID**: STORY-3.1
- **描述**: 分析 ExecutionPlan，识别可批处理的模式
- **优先级**: [P1]
- **估算**: 5人天
- **状态**: [Backlog]
- **交付物**:
  - 操作序列分析逻辑
  - 批处理模式识别算法
  - 依赖关系分析
  - 可批处理性评分

#### Story 3.2: 批处理转换器
- **Story ID**: STORY-3.2
- **描述**: 将多个操作转换为单个批处理操作
- **优先级**: [P1]
- **估算**: 7人天
- **状态**: [Backlog]
- **交付物**:
  - 批处理转换引擎
  - 多操作合并逻辑
  - 结果解包和映射
  - 错误处理和回滚

#### Story 3.3: 批处理执行器
- **Story ID**: STORY-3.3
- **描述**: 执行批处理操作，返回结果映射
- **优先级**: [P1]
- **估算**: 5人天
- **状态**: [Backlog]
- **交付物**:
  - 批处理执行引擎
  - 并行执行协调
  - 结果收集和聚合
  - 性能监控和优化

**Phase 3 总工作量**: 17人天 (~3.5周)

---

### Phase 4: Constitutional Constraints System

#### Story 4.1: 约束规则 DSL
- **Story ID**: STORY-4.1
- **描述**: 创建声明式规则定义语言
- **优先级**: [P0]
- **估算**: 5人天
- **状态**: [Backlog]
- **交付物**:
  - 规则 DSL 语法定义
  - 规则解析器
  - 规则验证器
  - DSL 文档和示例

#### Story 4.2: 约束规则引擎
- **Story ID**: STORY-4.2
- **描述**: 执行约束规则，判断操作是否违反约束
- **优先级**: [P0]
- **估算**: 6人天
- **状态**: [Backlog]
- **交付物**:
  - 规则执行引擎
  - 约束匹配逻辑
  - 违规检测和报告
  - 性能优化（规则索引）

#### Story 4.3: 规则配置系统
- **Story ID**: STORY-4.3
- **描述**: 支持从 YAML 加载约束规则
- **优先级**: [P1]
- **估算**: 3人天
- **状态**: [Backlog]
- **交付物**:
  - YAML 规则配置加载
  - 规则热重载支持
  - 规则版本管理
  - 默认规则集

**Phase 4 总工作量**: 14人天 (~3周)

---

### Phase 5: Lesson Guard System (Reflection Persistence)

**📄 决策文档**: [Decision: Lesson Guard Positioning](./decision-lesson-guard-positioning.md)

**业务价值**: 让 AI 从历史错误中持续学习，通过强制执行的检查点系统防止重复犯错，降低 token 浪费。

**核心理念**: "反思如果不能被强制执行，就是浪费"

**依赖**: Phase 1-4（需要稳定的 ExecutionPlan、Safe Tools、Constitutional Constraints 基础）

#### Story 5.1: Lesson Library 核心实现
- **Story ID**: STORY-5.1
- **描述**: 实现教训库的加载、检索和匹配逻辑
- **优先级**: [P1]
- **估算**: 2人天
- **状态**: [Planned]
- **交付物**:
  - Lesson dataclass（5字段：name, checkpoint_type, pattern, message, severity）
  - load_lessons_from_memory() - 复用 Serena Memory
  - check_lessons() - 检索相关教训
  - 10-15 测试

#### Story 5.2: MCP 工具接口
- **Story ID**: STORY-5.2
- **描述**: 暴露教训检查能力为 MCP 工具
- **优先级**: [P1]
- **估算**: 2人天
- **状态**: [Planned]
- **交付物**:
  - check_lessons() MCP 工具
  - list_lessons() MCP 工具
  - validate_against_lessons() MCP 工具
  - MCP 服务器集成

#### Story 5.3: ExecutionPlan 集成和验收
- **Story ID**: STORY-5.3
- **描述**: 将 Lesson Guard 集成到 ExecutionPlan 的 pre-execution 阶段
- **优先级**: [P1]
- **估算**: 2人天
- **状态**: [Planned]
- **交付物**:
  - ToolExecutionEngine pre-execution hook
  - 审计日志记录
  - 端到端测试
  - 使用指南文档

**Phase 5 总工作量**: 6人天 (~1.5周)

**设计原则（KISS）**:
- 存储：复用 Serena Memory（Markdown 文件），不引入 SQLite
- 数据模型：5 字段足够，不要 15+ 字段的复杂模型
- 规则引擎：Python 函数，不要发明 DSL
- 平台支持：MVP 只支持 MCP，不要同时开发 6 个平台

---

## 📊 时间线

### 实际时间
- **开始日期**: 2025-10-27
- **Phase 0 完成**: ✅ **2025-10-28** (实际: 10人天)
- **Phase 1 开始**: 2025-10-29 (计划)
- **Phase 1 完成**: 2025-11-07 (8.5人天, 优化后)
- **Phase 2 完成**: 2025-11-19 (19.5人天, 增加基准测试框架)
- **Phase 3 完成**: 2025-12-02 (17人天, 预计)
- **Phase 4 完成**: 2025-12-10 (14人天, 预计)
- **Phase 5 完成**: 2025-12-13 (6人天, 预计)
- **总工作量**: 75人天 (约 15 周，包含 Phase 5) - 从69.5人天增加

### 里程碑
- [x] Product Definition完成 - 2025-10-26
- [x] ADR-003: 工具链路简化决策 - 2025-10-27
- [x] ✅ **Phase 0 完成** - 2025-10-28 ⭐ 关键里程碑达成
  - Story 0.1: ToolExecutionEngine ✅
  - Story 0.2: ExecutionPlan Schema ✅
  - Story 0.3: Regression Testing ✅
  - [Phase 0 Completion Report](../../../development/sprints/current/phase-0-completion-report.md) 📄
- [ ] **Phase 1 完成**（ExecutionPlan验证） - 2025-11-08
- [ ] **Phase 2 完成**（Safe Operations + 基准测试框架） - 2025-11-19 ⭐ Dogfooding Ready
  - 所有三个Safe Tools可用（search/edit/exec）
  - 通用基准测试框架就绪
  - 使用日志系统运行
  - Level 2 Dogfooding开始
- [ ] Phase 3 完成（Batching Engine） - 2025-12-02
- [ ] Phase 4 完成（Constitutional Constraints） - 2025-12-10
- [ ] Phase 5 完成（Lesson Guard System） - 2025-12-13
- [ ] Epic-001 全面测试和文档 - 2025-12-16

---

## 🔗 依赖关系

### 依赖的Epic
无 - 这是第一个Epic

### 被依赖的Epic
- EPIC-002: MCP集成与TPST审计 - 需要本Epic提供的safe工具

---

## 🎯 验收标准

### Epic级验收标准

**Phase 0-1: 基础架构**
- [x] ExecutionPlan Schema用Pydantic定义，包含所有强制字段
- [ ] PlanValidator 可检查约束一致性，性能 <1ms
- [ ] 运行时约束监控集成到 ExecutionContext

**Phase 2: Safe Operations**
- [ ] safe_search可自动选择ripgrep/ugrep/grep并返回JSON格式
- [ ] safe_edit使用Patch-First架构，propose和apply一致
- [ ] safe_exec可正确管理进程组，timeout时完全清理

**Phase 3: Batching**
- [ ] 批处理引擎可识别可合并的操作序列
- [ ] 批处理执行减少至少 30% 的工具调用次数

**Phase 4: Constitutional Constraints**
- [ ] 约束规则 DSL 可表达复杂的约束逻辑
- [ ] 规则引擎可在 pre-execution 阶段阻止违规操作
- [ ] 支持从 YAML 加载和热重载规则

**Phase 5: Lesson Guard**
- [ ] Lesson Guard 可从 Serena Memory 加载教训
- [ ] check_lessons/validate_against_lessons MCP 工具正常工作
- [ ] 教训违规记录到审计日志
- [ ] 新会话可自动检索相关历史教训

**整体验收**
- [ ] 所有工具通过MCP暴露给AI助手
- [ ] 基线测试通过（pytest, fastapi, superset三个repo）
- [ ] TPST 相比原生工具降低 ≥30%

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

**最后更新**: 2025-11-06
**更新人**: EvolvAI Team
**更新内容**:
- 统一命名：Feature → Story（Phase 2/3/4）
- 补充各 Phase 交付物和总工作量
- 添加 Phase 5: Lesson Guard System
- 完善验收标准（按 Phase 分组）
- 修正次要目标描述