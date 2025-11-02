---
type: decision
category: architecture
decision_id: ADR-001
status: accepted
date: 2025-10-27
related: [epic-003]
---

# ADR 001: 选择Graph-of-Thought而非SequentialThinking

**状态**: [ACCEPTED]
**日期**: 2025-10-27
**决策者**: EvolvAI Team
**标签**: `AI-Reasoning`, `Thinking-Engine`, `Performance-Optimization`, `Epic-003`

---

## 📋 背景 (Context)

### 问题描述

AI助手（如Claude Code、Cursor等）在处理复杂编程任务时，需要一个结构化的"思维引擎"来推理、规划和验证执行计划。目前主流的方案是**SequentialThinking**（串行思考），但它在实际应用中暴露出严重局限性：

**SequentialThinking的核心问题**:
1. **串行思考**：无法并行探索多个方案，只能一步步试错
2. **ID不可靠**：`through_thought_id`经常失败，思维上下文丢失
3. **冗长低效**：思考过程是长文本，token浪费严重（占总TPST的40%）
4. **缺乏验证**：输出的是自由文本而非可验证的结构化计划
5. **范围受限**：无法处理动态拆解、分支逻辑、自适应规划

### 业务影响

- **Token成本高昂**：思考过程占40% TPST，直接影响API成本与延迟
- **首次成功率低**：平均5-8轮试错才能得到可行方案（~50%首次成功率）
- **用户体验差**：长篇思考对话冗长，用户难以理解AI推理过程
- **扩展性差**：难以支持复杂的多步骤、多分支任务规划

### 当前状况

EvolvAI项目正在设计Epic-003（思维MCP），需要选择一个"思维引擎"作为核心。候选方案包括：
1. 继续使用现有的SequentialThinking
2. 升级到Graph-of-Thought（图结构思维）
3. 自研简化版思维引擎

**决策时间紧迫**：Epic-003的技术选型将影响后续Epic-001、Epic-002的集成设计，必须尽快确定。

---

## 🎯 决策 (Decision)

### 选择的方案

**选择Graph-of-Thought（GoT）作为Epic-003的核心思维引擎**，替代SequentialThinking。

### 核心理由

1. **并行探索**：GoT支持fork并行分支，同时评估多个方案，早停劣解，2-3x加速
2. **可验证性**：GoT输出结构化Plan（JSON Schema），不是文本废话，可硬校验
3. **Token效率**：思考token从40%降至15%（-62%），内容限长400字符+摘要机制
4. **可回放审计**：事件溯源设计，append-only日志，完整思维图谱可回放
5. **与Epic-001/002闭环**：GoT产出ExecutionPlan/DocPlan，直接对接safe_*和doc.*工具

**决策依据**：
- 学术支持：Graph-of-Thought论文（arXiv:2305.16582）证明图结构优于链式推理
- 实际需求：EvolvAI的"行为工程"体系需要"想得清楚→做得靠谱→写得规范"闭环
- 技术可行：基于SQLite+WAL+事件溯源，实现复杂度可控

---

## 🔍 考虑的方案 (Considered Options)

### 方案A: 继续使用SequentialThinking

**描述**:
沿用现有的SequentialThinking MCP工具，通过改进prompts和添加验证层来优化。

**优点**:
- ✅ 现成可用，无需开发新引擎
- ✅ 团队熟悉，学习成本低
- ✅ MCP生态已有集成案例

**缺点**:
- ❌ **串行限制无法解决**：本质架构问题，无法并行探索
- ❌ **ID失败问题**：`through_thought_id`机制不可靠，无法彻底修复
- ❌ **Token低效**：长文本思考，优化空间有限（最多-20%）
- ❌ **不可验证**：输出仍是文本，无法强制Schema
- ❌ **无法回放**：没有事件溯源，思维过程丢失后无法复现

**选择原因**: ❌ **不选择**
虽然短期成本低，但长期无法满足EvolvAI的核心需求（并行探索、可验证计划、TPST大幅降低）。改进SequentialThinking相当于"给自行车装发动机"，不如直接设计汽车。

---

### 方案B: Graph-of-Thought (GoT)

**描述**:
设计全新的图结构思维引擎，支持：
- 并行分支（fork/parallel.run/merge）
- 事件溯源（append-only日志）
- Schema校验（ExecutionPlan/DocPlan）
- 预算控制（token/时间/分支数硬限制）
- 失败自愈（签名去重、策略匹配）

**优点**:
- ✅ **并行探索**：同时评估多个方案，早停劣解，2-3x加速
- ✅ **Token高效**：限长400字符+摘要机制，思考token降低62%
- ✅ **可验证**：输出必须通过Schema校验，拒绝无效Plan
- ✅ **可回放**：事件溯源+WAL，思维图谱可审计、复现
- ✅ **可扩展**：支持bandit调度、动态预算、策略学习
- ✅ **与Epic-001/002闭环**：直接产出ExecutionPlan和DocPlan

**缺点**:
- ❌ **开发成本高**：需要3周开发（8个Feature，16人天）
- ❌ **复杂度高**：事件溯源+向量时钟+并行调度，技术栈复杂
- ❌ **学习曲线**：团队需要学习新架构和工具

**选择原因**: ✅ **选择**
虽然短期开发成本高，但长期收益巨大：
- 直接解决SequentialThinking的根本问题
- 支撑完整的"想→做→写"闭环（三Epic协同）
- TPST累加效应达到-70%（单凭Epic-003就能-40%）
- 学术验证+可扩展架构，技术债务低

---

### 方案C: 简化版自研思维引擎

**描述**:
轻量级思维引擎，保留并行探索功能，但去掉事件溯源、向量时钟等复杂特性。

**优点**:
- ✅ 开发快速（1周MVP）
- ✅ 复杂度低，易维护
- ✅ 支持基本的并行探索

**缺点**:
- ❌ **缺乏审计**：没有事件溯源，无法回放思维过程
- ❌ **扩展性差**：后期难以增加bandit调度、策略学习等高级功能
- ❌ **可靠性低**：无向量时钟，并发冲突检测不完整
- ❌ **不适合生产**：缺乏崩溃恢复、checkpoint等生产级特性

**选择原因**: ❌ **不选择**
虽然开发快，但"快而不稳"，长期维护成本更高。EvolvAI定位是生产级AI行为工程平台，需要可靠、可审计、可扩展的基础设施，简化版无法满足。

---

## ⚖️ 决策权衡 (Trade-offs)

### 短期影响（0-3个月）

**正面**:
- ✅ **技术领先性**：Graph-of-Thought是前沿思维引擎设计，有学术支撑
- ✅ **差异化竞争**：市面上AI助手大多用SequentialThinking，GoT是壁垒
- ✅ **团队能力提升**：学习事件溯源、图算法、并行调度等高级技术

**负面**:
- ❌ **开发周期长**：需要3周（vs 方案C的1周）
- ❌ **学习成本**：团队需要学习新架构（事件溯源、向量时钟）
- ❌ **集成风险**：Epic-003与Epic-001/002的集成需要仔细设计

### 长期影响（3-12个月）

**正面**:
- ✅ **TPST大幅降低**：累加效应达到-70%（单凭Epic-003就-40%）
- ✅ **首次成功率提升**：从~50%提升到90%（减少试错）
- ✅ **可扩展架构**：支持bandit调度、策略学习、多模型协同
- ✅ **生产级可靠**：事件溯源+WAL+checkpoint，崩溃恢复完善
- ✅ **商业价值**：可审计思维图谱，支持企业级需求（安全审计、合规）

**负面**:
- ❌ **维护成本**：相比SequentialThinking，维护复杂度更高
- ❌ **存储开销**：事件溯源需要更多存储（但SQLite足够轻量）

---

## 🎯 后果 (Consequences)

### 技术后果

**正面**:
1. **架构升级**：从"长对话"升级到"可并行、可验证、可回放的图结构"
2. **性能提升**：思考token降低62%，首次成功率从50%→90%
3. **可观测性**：思维图谱可导出Mermaid图，用户可视化理解AI推理
4. **闭环能力**：与Epic-001/002形成完整"想→做→写"闭环

**负面**:
1. **技术债务初期高**：需要3周开发+2周打磨，技术栈复杂
2. **依赖SQLite**：单机部署限制（长期可升级LiteFS/PostgreSQL）

### 团队后果

**正面**:
1. **技术能力提升**：学习事件溯源、图算法、并行调度
2. **产品差异化**：GoT是竞争壁垒，团队掌握核心技术
3. **工程实践**：TDD+Gitflow+Sprint管理，规范化流程

**负面**:
1. **学习曲线**：团队需要2-3周适应新架构
2. **协调成本**：Epic-003需要与Epic-001/002紧密协调

### 业务后果

**正面**:
1. **成本降低**：TPST降低70%，直接降低API成本
2. **用户体验提升**：首次成功率90%，减少重复试错
3. **商业壁垒**：可审计思维图谱，企业级客户需求
4. **品牌差异化**："行为工程"+"Graph-of-Thought"，技术领先标签

**负面**:
1. **上市延迟**：相比简化版，晚2周上市（Week 3 vs Week 5）
2. **早期风险**：新架构需要验证，可能有未知bug

---

## 📊 度量指标 (Metrics)

### 成功指标

| 指标 | 基线（SequentialThinking） | MVP目标（Week 3） | 最终目标（Month 3） |
|------|---------------------------|-------------------|---------------------|
| **思考token占比** | 40% | 20% | 15% |
| **平均思考回合数** | 5-8 | 2-3 | 1-2 |
| **首次计划成功率** | ~50% | 75% | 90% |
| **并行分支收敛速度** | N/A（无并行） | 2x | 3x |
| **Plan Schema通过率** | N/A（无Schema） | 90% | 95% |
| **事件溯源可靠性** | N/A | 99.9% | 99.99% |

### 监控方式

**实时监控**:
- Token审计条（实时显示预算使用）
- 分支状态面板（并行分支执行情况）
- 失败签名统计（自愈策略命中率）

**离线分析**:
- TPST对比报告（每周生成，对比基线）
- 思维图谱可视化（Mermaid导出）
- 证据链审计（Plan→执行→验证完整链路）

**基准测试**:
- 3个仓库 × 3个任务 = 9个对比场景
- 每场景运行5次取平均值
- 记录：token消耗、时延、首次成功率、Model-hops

---

## 🔗 相关决策 (Related Decisions)

### 依赖的ADR
- 待定：ADR-002（Event Sourcing存储选型：SQLite vs PostgreSQL）
- 待定：ADR-003（并行调度策略：Race vs Bandit vs Majority Vote）

### 被依赖的ADR
- Epic-001技术选型将依赖本ADR（ExecutionPlan Schema定义）
- Epic-002技术选型将依赖本ADR（DocPlan Schema定义）

### 替代的ADR
- 本ADR替代了"继续使用SequentialThinking"的隐式决策

---

## 📚 参考资料 (References)

### 学术论文
- [Graph of Thoughts: Solving Elaborate Problems with Large Language Models](https://arxiv.org/abs/2305.16582)
- [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601)

### 工程实践
- [Event Sourcing Pattern - Martin Fowler](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Upper Confidence Bound (UCB) Algorithm](https://en.wikipedia.org/wiki/Multi-armed_bandit#Upper_Confidence_Bound_algorithm)
- [Vector Clocks for Distributed Systems](https://en.wikipedia.org/wiki/Vector_clock)

### MCP生态
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)

---

## 📝 备注 (Notes)

### 实施建议

**Phase 1（Week 1-2）: 核心引擎MVP**
- 优先实现：Session管理、Event Store、基础Plan生成
- 延后实现：Bandit调度、复杂评分算法
- 验收标准：单线性思维流程跑通，可产出ExecutionPlan

**Phase 2（Week 3）: 并行与验证**
- 实现：Fork/Parallel.run（race策略）、Schema校验
- 集成：与Epic-001 safe_*工具打通
- 验收标准：并行分支+验证闭环运行

**Phase 3（Week 4-5）: 工程化能力**
- 实现：预算控制、失败自愈、Token审计条
- 打磨：性能优化、错误恢复、文档完善
- 验收标准：TPST降低≥50%（对比基线）

### 潜在风险

1. **事件溯源复杂度**
   - 风险：向量时钟、WAL、checkpoint实现可能有bug
   - 缓解：使用成熟库（SQLite+WAL），充分测试

2. **并行调度性能**
   - 风险：线程池开销、GIL限制可能影响性能
   - 缓解：限制并行数≤5，使用ThreadPoolExecutor（IO密集）

3. **与Epic-001/002集成**
   - 风险：Schema不兼容、接口变更频繁
   - 缓解：Week 1设计评审，锁定接口，版本化API

4. **团队学习曲线**
   - 风险：团队不熟悉事件溯源、图算法
   - 缓解：技术分享会（2次），结对编程，渐进式学习

### 回滚计划

**如果GoT在Week 3验证失败（TPST降低<30%）**:
1. **短期回滚**：暂时使用SequentialThinking，但保留GoT架构
2. **问题诊断**：分析失败原因（是并行调度？Schema设计？还是评分算法？）
3. **局部修正**：只修复核心问题模块，不推倒重来
4. **重新验证**：修正后再次对比基准测试

**如果GoT开发延期超过1周**:
1. **范围削减**：去掉Bandit调度、复杂评分等高级特性，先保证race策略可用
2. **并行开发**：Epic-003 MVP稳定后，Epic-001/002立即开始（不等完整版）
3. **渐进交付**：先交付核心功能（并行+验证），后续迭代增强

**最坏情况（GoT完全失败）**:
- 保留事件溯源和Schema校验特性
- 退化为单线性流程（类似SequentialThinking），但输出仍是结构化Plan
- 预期TPST降低20-30%（虽然没有并行，但Schema+限长仍有优化）

---

**创建日期**: 2025-10-27
**最后审查**: 2025-10-27
**下次审查**: 2025-11-10（Week 3 MVP验证后）
