# 🎯 EvolvAI Phase 2 行动计划

**目标**: 完成Epic-001 Phase 2 - Safe Operations Wrapper System + 通用基准测试框架
**时间**: 19.5人天（约4周全职 or 8周兼职50%）
**开始日期**: 2025-11-07
**目标日期**: 2025-11-19
**当前状态**: 🟢 Ready to Start

---

## 📊 Phase 2 整体结构（Story拆分）

```
Story 2.1: safe_search (4 + 1 + 0.5 = 5.5人天)
  ├─ 2.1: 核心功能 (4人天)
  ├─ 2.1.1: 单元基准测试 (1人天)
  └─ 2.1.2: MCP集成 (0.5人天)

Story 2.2: safe_edit (6 + 1 + 0.5 = 7.5人天) ⭐ 优先
  ├─ 2.2: 核心功能 - Patch-First重构 (6人天)
  ├─ 2.2.1: 单元基准测试 (1人天)
  └─ 2.2.2: MCP集成 (0.5人天)

Story 2.3: safe_exec (3 + 1 + 0.5 = 4.5人天)
  ├─ 2.3: 核心功能 (3人天)
  ├─ 2.3.1: 单元基准测试 (1人天)
  └─ 2.3.2: MCP集成 (0.5人天)

Story 2.4: 通用基准测试框架 (2人天) ⭐ 关键
  - UsageLogger/Replayer通用系统
  - BenchmarkReporter
  - CI/CD集成

总计: 19.5人天
```

---

## 🚨 关键决策和架构变更

### 决策1: Feature 2.2 Patch-First重构（2025-11-07）

**问题**: Feature 2.2旧实现89%测试失败，架构方向错误
**决策**: 采用方案A（完全重新实现Patch-First架构）
**理由**:
- 产品定义要求propose/apply分离 + Git worktree隔离
- 旧实现是直接文件编辑 + 文件拷贝备份
- 修复bug无法解决根本问题

**影响**:
- 3天修复 → 6天重新实现
- 删除~920行过度设计代码
- 新实现~550行（-29%但更强大）

**相关文档**:
- [Critical Analysis](docs/knowledge/critical-analysis-feature-2.2.md)
- [BDD Scenarios](docs/development/sprints/current/story-2.2-bdd-scenarios.md)
- [Deletion Checklist](DELETION_CHECKLIST.md)

### 决策2: safe_search预防性分析（2025-11-07）

**洞察**: safe_search尚未实现，可以完全按BDD → TDD正确实施
**行动**: 创建预防性分析文档，避免Feature 2.2错误
**关键建议**:
- MVP删除baseline_comparison字段（性能翻倍问题）
- 简化scope为单个glob pattern
- top_matches限制50个
- 不实现batch/mode/area_selector过度设计

**相关文档**:
- [Preventive Analysis](docs/knowledge/preventive-analysis-safe-search.md)
- [Baseline Testing Strategy](docs/knowledge/research/baseline-testing-strategy.md)

### 决策3: 通用基准测试框架（2025-11-07）

**用户洞察**: "safe_search需要基准测试，其他工具应该也需要，但我记得有统一执行入口的？"
**发现**: ToolExecutionEngine（Phase 0已完成）提供统一审计日志！
**决策**: 创建通用基准测试框架（Story 2.4），所有Safe Tools共享

**关键能力**:
- ToolExecutionEngine内置审计日志（duration, tokens, success）
- UsageLogger/Replayer通用系统（真实使用场景回放）
- BenchmarkReporter统一报告
- 模式切换（production/sampling/development）

**相关文档**:
- [通用基准测试框架](docs/development/architecture/universal-benchmarking-framework.md)

---

## 📅 实施计划（按优先级）

### Week 1: Story 2.2 - safe_edit Patch-First重构（6人天）

#### Day 1: Phase 1 - 备份和删除准备

**任务**:
- [ ] 创建备份分支 `archive/feature-2.2-old-implementation`
- [ ] 按DELETION_CHECKLIST.md删除over-engineering代码
  - [ ] 删除`safe_edit_batch()`（43行）
  - [ ] 删除mode系统（conservative/aggressive）
  - [ ] 删除`safe_edit_mcp()`方法
  - [ ] 删除过度复杂的area awareness
- [ ] 清理测试文件（删除测试不存在功能的用例）

**交付物**: 清理后的代码库，删除~920行

#### Day 2-3: Phase 2-3 - propose_edit和apply_edit实现

**Day 2** (propose_edit):
- [ ] 实现propose_edit核心逻辑
  - [ ] rg/ugrep扫描候选文件
  - [ ] difflib生成unified diff
  - [ ] patch_id机制（timestamp + hash）
  - [ ] 存储patch_id → patch_content
- [ ] BDD Scenario 1-4测试（propose功能）
- [ ] 运行Red → Green循环

**Day 3** (apply_edit):
- [ ] 实现apply_edit核心逻辑
  - [ ] Git worktree创建和管理
  - [ ] git apply --3way应用patch
  - [ ] 成功：copy到main + cleanup worktree
  - [ ] 失败：cleanup worktree + rollback
- [ ] BDD Scenario 5-7测试（apply功能）
- [ ] 运行Red → Green循环

**交付物**: 核心Patch-First功能完成

#### Day 4: Phase 4-5 - ExecutionPlan集成和MCP集成

**上午** (ExecutionPlan):
- [ ] 集成ExecutionPlan参数
- [ ] 实现约束验证
- [ ] BDD Scenario 8测试

**下午** (MCP):
- [ ] 创建SafeEditTool（Tool基类）
- [ ] MCP服务器注册
- [ ] 端到端测试

**交付物**: 完整功能 + MCP集成

#### Day 5: Phase 6 - 代码审查和重构

**上午**:
- [ ] 代码审查（clean code原则）
- [ ] 重构优化
- [ ] 提取重复逻辑

**下午**:
- [ ] 运行完整测试套件
- [ ] `uv run poe format`
- [ ] `uv run poe type-check`
- [ ] `uv run poe lint`

**验收标准**:
- ✅ 8个BDD场景100%通过
- ✅ 核心功能测试100%通过
- ✅ format/type-check/lint全通过

#### Day 6: Story 2.2.1 - safe_edit单元基准测试（1人天）

**任务**:
- [ ] 准备benchmark repos（small/medium/large）
- [ ] 编写10-15个基准测试用例
  - [ ] propose_edit性能
  - [ ] apply_edit性能
  - [ ] worktree操作开销
  - [ ] 大文件处理
- [ ] CI/CD集成
- [ ] baseline.json基线数据

**交付物**: 完整基准测试套件

---

### Week 2: Story 2.1 - safe_search + Story 2.4 - 通用框架（7.5人天）

#### Day 7-8: Story 2.1 - safe_search核心功能（4人天前2天）

**Day 7**:
- [ ] 创建BDD场景文档（基于预防性分析）
- [ ] 工具检测逻辑（ripgrep/ugrep/grep）
- [ ] BDD Scenario 1-3测试（基本搜索、降级、scope）
- [ ] TDD Red → Green

**Day 8**:
- [ ] JSON输出结构
- [ ] 结果截断逻辑（50个匹配）
- [ ] BDD Scenario 4-6测试（截断、超时、无结果）
- [ ] TDD Red → Green

#### Day 9: Story 2.1核心功能完成 + Story 2.1.1基准测试（2人天）

**上午** (核心功能收尾):
- [ ] ExecutionPlan集成
- [ ] UsageLogger集成（复用通用系统）
- [ ] BDD Scenario 7-8测试（JSON格式、MCP）

**下午** (基准测试):
- [ ] 准备3个benchmark repos
- [ ] 编写10-15个基准测试用例
  - [ ] rg vs grep公平对比
  - [ ] 搜索速度测试
  - [ ] 结果准确性验证

#### Day 10: Story 2.1.2 MCP集成 + Story 2.4开始（0.5 + 1人天）

**上午** (MCP集成):
- [ ] SafeSearchTool（Tool基类）
- [ ] MCP服务器注册
- [ ] 端到端测试

**下午** (Story 2.4 Day 1):
- [ ] UsageLogger通用实现
  - [ ] 工具无关的日志接口
  - [ ] 按日期分片JSONL格式
  - [ ] metadata灵活字段
- [ ] UsageReplayer通用实现
  - [ ] 通用回放逻辑
  - [ ] 工具类型分派
  - [ ] 性能对比计算

**交付物**: safe_search完整功能 + 通用日志系统

#### Day 11: Story 2.4完成 - 通用基准测试框架（1人天）

**上午**:
- [ ] BenchmarkReporter实现
  - [ ] 从ToolExecutionEngine获取审计日志
  - [ ] 按工具分组统计
  - [ ] P50/P95/P99性能指标
  - [ ] Markdown格式报告
- [ ] 模式切换支持
  - [ ] production/sampling/development
  - [ ] 环境变量控制

**下午**:
- [ ] CLI工具
  - [ ] evolvai-replay命令
  - [ ] evolvai-report命令
- [ ] CI/CD集成
  - [ ] 每周自动回放脚本
  - [ ] 性能回归检测
- [ ] 文档和使用指南

**交付物**: 完整通用基准测试框架

---

### Week 3: Story 2.3 - safe_exec + 集成验证（4.5人天）

#### Day 12-13: Story 2.3 - safe_exec核心功能（3人天前2天）

**Day 12**:
- [ ] 进程组管理实现
  - [ ] os.setsid新会话
  - [ ] os.killpg进程树清理
- [ ] precondition验证
- [ ] 输出截断（head 50 + tail 50）

**Day 13**:
- [ ] timeout清理机制
- [ ] ExecutionPlan集成
- [ ] UsageLogger集成
- [ ] 测试套件（TDD）

#### Day 14: Story 2.3收尾 + Story 2.3.1基准测试（1 + 1人天）

**上午** (核心收尾):
- [ ] 完整测试套件
- [ ] format/type-check/lint

**下午** (基准测试):
- [ ] 命令执行速度测试
- [ ] 超时处理测试
- [ ] 进程清理验证
- [ ] CI/CD集成

#### Day 15: Story 2.3.2 MCP集成 + Phase 2验收（0.5 + 0.5人天）

**上午** (MCP集成):
- [ ] SafeExecTool（Tool基类）
- [ ] MCP服务器注册
- [ ] 端到端测试

**下午** (Phase 2验收):
- [ ] 运行所有三个Safe Tools测试套件
- [ ] 运行通用基准测试框架测试
- [ ] 生成完整性能报告
- [ ] 验收标准检查

**验收标准**:
- ✅ safe_search: 100%功能完成 + MCP集成
- ✅ safe_edit: 100%功能完成 + MCP集成
- ✅ safe_exec: 100%功能完成 + MCP集成
- ✅ 通用基准测试框架: 100%完成
- ✅ 所有测试: ≥95%通过率
- ✅ format/type-check/lint: 全通过

---

### Week 4: Dogfooding和文档（2人天）

#### Day 16-17: Dogfooding实战（2人天）

**目标**: 使用Level 2系统（所有safe tools + 基准测试）完成真实开发任务

**任务选择**: Story 1.1 - PlanValidator核心实现（Phase 1首个Story）

**Day 16** (safe_search使用):
- [ ] 使用safe_search查找相关代码
  - [ ] 搜索ValidationResult数据类
  - [ ] 搜索PlanValidator类
  - [ ] 查找ExecutionPlan引用
- [ ] 记录每次搜索
  - [ ] 查询内容
  - [ ] 执行时间
  - [ ] 结果质量
  - [ ] vs原生工具对比

**Day 17** (safe_edit使用):
- [ ] 使用safe_edit实现PlanValidator
  - [ ] propose_edit生成代码修改
  - [ ] 预览diff
  - [ ] apply_edit应用修改
- [ ] 记录编辑操作
  - [ ] propose时间
  - [ ] diff准确性
  - [ ] apply成功率
  - [ ] vs原生编辑对比

**交付物**:
- `docs/knowledge/dogfooding/safe-search-case-study.md`
- `docs/knowledge/dogfooding/safe-edit-case-study.md`
- `docs/knowledge/dogfooding/improvement-recommendations.md`

#### Day 18: 文档和Phase 2总结（1人天）

**上午** (文档更新):
- [ ] 更新Epic-001 README（标记Phase 2完成）
- [ ] 更新PROJECT README（添加功能演示）
- [ ] 创建快速开始指南
- [ ] 录制5分钟演示视频

**下午** (Phase 2总结):
- [ ] 编写Phase 2 Completion Report
  - [ ] 完成的功能
  - [ ] 基准测试结果
  - [ ] Dogfooding经验
  - [ ] 学到的教训
  - [ ] Phase 3建议
- [ ] 提交git commit
- [ ] 更新BACKLOG.md

**交付物**: `docs/development/sprints/current/phase-2-completion-report.md`

---

## 🎯 验收标准总览

### 功能验收（所有必须✅）

**Story 2.1 - safe_search**:
- [ ] 工具检测和选择（rg/ugrep/grep）✅
- [ ] scope限制验证 ✅
- [ ] JSON格式输出 ✅
- [ ] 结果截断（50个匹配）✅
- [ ] ExecutionPlan集成 ✅
- [ ] UsageLogger集成 ✅
- [ ] MCP工具暴露 ✅
- [ ] 8个BDD场景100%通过 ✅

**Story 2.2 - safe_edit**:
- [ ] Patch-First架构（propose/apply）✅
- [ ] Git worktree隔离 ✅
- [ ] unified diff生成 ✅
- [ ] patch_id机制 ✅
- [ ] 冲突处理 ✅
- [ ] ExecutionPlan集成 ✅
- [ ] UsageLogger集成 ✅
- [ ] MCP工具暴露 ✅
- [ ] 8个BDD场景100%通过 ✅

**Story 2.3 - safe_exec**:
- [ ] 进程组管理（killpg）✅
- [ ] precondition验证 ✅
- [ ] 输出截断 ✅
- [ ] timeout清理 ✅
- [ ] ExecutionPlan集成 ✅
- [ ] UsageLogger集成 ✅
- [ ] MCP工具暴露 ✅
- [ ] 测试套件100%通过 ✅

**Story 2.4 - 通用基准测试框架**:
- [ ] UsageLogger通用实现 ✅
- [ ] UsageReplayer通用实现 ✅
- [ ] BenchmarkReporter ✅
- [ ] CLI工具（replay/report）✅
- [ ] 模式切换（3种模式）✅
- [ ] CI/CD集成 ✅
- [ ] 文档和使用指南 ✅

### 质量验收（所有必须✅）

- [ ] 代码格式化: 100%通过（`uv run poe format`）
- [ ] 类型检查: 0错误（`uv run poe type-check`）
- [ ] Lint检查: 0警告（`uv run poe lint`）
- [ ] 测试覆盖率: ≥85%（核心模块≥90%）
- [ ] 所有测试通过率: ≥95%

### 基准测试验收

- [ ] 每个Safe Tool有10-15个基准测试用例 ✅
- [ ] 所有工具有baseline.json基线数据 ✅
- [ ] CI/CD自动运行基准测试 ✅
- [ ] 每周自动回放和报告 ✅

### Dogfooding验收

- [ ] 至少2个真实案例（safe_search + safe_edit）✅
- [ ] 每个案例有完整记录（操作+数据+对比）✅
- [ ] 改进建议文档 ✅
- [ ] Level 2功能评估报告 ✅

### 文档验收

- [ ] Epic-001 README更新（Phase 2完成）✅
- [ ] 通用基准测试框架设计文档 ✅
- [ ] Phase 2 Completion Report ✅
- [ ] 演示视频（5分钟）✅
- [ ] 快速开始指南 ✅

---

## 🚨 风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| Feature 2.2重构超时 | 中 | 高 | 严格按BDD场景实施，不添加额外功能 |
| 通用框架设计复杂 | 低 | 中 | 复用ToolExecutionEngine审计日志 |
| Dogfooding发现严重问题 | 中 | 高 | 快速修复或降级功能，记录改进需求 |
| 基准测试数据不理想 | 中 | 中 | 分析瓶颈，调整参数，不过度优化 |
| 时间估算过于乐观 | 高 | 中 | 每周review进度，必要时调整范围 |

---

## 📈 成功指标

### 技术指标（必达）

- ✅ 三个Safe Tools 100%功能完成
- ✅ 通用基准测试框架100%完成
- ✅ 所有测试通过率≥95%
- ✅ format/type-check/lint全通过

### 产品指标（期望）

- ✅ Level 2 Dogfooding可用
- ✅ 基准测试数据支撑价值
- ✅ 改进建议明确Phase 3方向

### 学习指标（重要）

- ✅ Feature 2.2教训应用到safe_search（预防性分析）
- ✅ TDD流程完整执行（BDD → Red → Green → Refactor）
- ✅ 通用框架设计经验积累
- ✅ Dogfooding真实反馈收集

---

## 🔗 相关文档

### 产品和架构
- [Epic-001 README](docs/product/epics/epic-001-behavior-constraints/README.md) ⭐ 主文档
- [通用基准测试框架](docs/development/architecture/universal-benchmarking-framework.md) ⭐ 架构设计

### Feature 2.2
- [Critical Analysis](docs/knowledge/critical-analysis-feature-2.2.md) ⭐ 问题分析
- [BDD Scenarios](docs/development/sprints/current/story-2.2-bdd-scenarios.md) ⭐ 实施规范
- [Deletion Checklist](DELETION_CHECKLIST.md) ⭐ 删除计划

### safe_search
- [Preventive Analysis](docs/knowledge/preventive-analysis-safe-search.md) ⭐ 预防性分析
- [Baseline Testing Strategy](docs/knowledge/research/baseline-testing-strategy.md) ⭐ 基准测试策略

### 开发标准
- [TDD Refactoring Guidelines](docs/testing/standards/tdd-refactoring-guidelines.md)
- [Definition of Done (DoD) Standards](docs/development/standards/definition-of-done.md)

---

## 📋 每日检查清单

### 每天开始
- [ ] Review昨天完成的任务
- [ ] 确认今天的任务清单
- [ ] 检查依赖是否就绪

### 每天结束
- [ ] 运行测试套件
- [ ] 运行format/type-check/lint
- [ ] 提交git commit（如有新代码）
- [ ] 更新任务状态

### 每周检查
- [ ] Review本周完成情况
- [ ] 更新Epic README进度
- [ ] 评估下周任务可行性
- [ ] 调整计划（如需要）

---

**最后更新**: 2025-11-07
**负责人**: EvolvAI Team
**状态**: 🟢 Ready to Execute
**预计完成**: 2025-11-19 (Phase 2 Complete, Dogfooding Ready)
