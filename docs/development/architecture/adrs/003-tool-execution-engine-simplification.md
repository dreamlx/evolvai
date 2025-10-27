# ADR-003: 工具调用链路简化 - ToolExecutionEngine

**状态**: [APPROVED]
**日期**: 2025-10-27
**决策者**: EvolvAI Team
**影响范围**: Epic-001, SerenaAgent 核心架构

---

## 📋 背景

### 问题陈述

在分析 SerenaAgent 与 MCP 的集成架构时，发现当前工具调用链路过于复杂：

```
AI Client → FastMCP → MCP Tool wrapper → Tool.apply_ex()
→ SerenaAgent.execute_task() → ThreadPoolExecutor → Tool.apply()
```

**7 层调用链路**导致：
1. **审计困难**：token 消耗路径分散，无法清晰追踪 TPST
2. **职责混乱**：`Tool.apply_ex()` 混杂 6 种职责（检查、日志、异常、统计、线程池、执行）
3. **扩展困难**：Epic-001 的约束系统需要在多处注入检查点
4. **性能开销**：每层都有包装和转换成本

### EvolvAI 的核心定位

EvolvAI 的核心价值是 **TPST (Tokens Per Solved Task) 优化**，这要求：
- **清晰的 token 消耗路径**：必须知道每个环节消耗了多少 token
- **可审计的执行过程**：能够分析哪些操作导致 token 浪费
- **可优化的执行引擎**：能够注入约束、批处理等优化策略

当前的 7 层链路**无法满足审计和优化需求**。

---

## 🎯 决策

### 核心决策

创建统一的 **ToolExecutionEngine**，将工具调用链路从 **7 层简化到 4 层**：

```
AI Client → FastMCP → ToolExecutionEngine → Tool.apply()
```

### ToolExecutionEngine 职责

```python
class ToolExecutionEngine:
    """
    统一工具执行引擎

    职责：
    1. 统一执行流程（4 个阶段：pre-validation → pre-execution → execution → post-execution）
    2. 集成约束检查（Epic-001 的 ExecutionPlan、Constitutional Constraints）
    3. 审计追踪（完整的 ExecutionContext，支持 TPST 分析）
    4. 线程池管理（异步执行，从 SerenaAgent 迁移过来）
    5. 性能监控（识别慢工具、token 浪费）
    """
```

### 执行流程

```yaml
Phase 1 - Pre-validation:
  - 检查工具激活状态
  - 检查项目要求
  - 检查 Language Server 状态

Phase 2 - Pre-execution (Epic-001):
  - ExecutionPlan 验证（feature flag 控制）
  - Constitutional Constraints 检查
  - Batching 机会检测

Phase 3 - Execution:
  - Token 估算（执行前）
  - 线程池异步执行
  - Token 统计（执行后）

Phase 4 - Post-execution:
  - 日志记录
  - 统计上报
  - 性能监控
```

### ExecutionContext（审计核心）

```python
@dataclass
class ExecutionContext:
    """执行上下文（完整的审计信息）"""
    tool_name: str
    kwargs: dict[str, Any]
    execution_plan: Any | None

    # 时间追踪
    start_time: float
    end_time: float
    phase: ExecutionPhase

    # 约束检查（Epic-001）
    constraint_violations: list[str]
    should_batch: bool

    # 执行结果
    result: str | None
    error: Exception | None

    # Token 追踪（TPST 核心）
    estimated_tokens: int
    actual_tokens: int

    def to_audit_record(self) -> dict:
        """转换为审计记录（用于 TPST 分析）"""
        return {
            'tool': self.tool_name,
            'phase': self.phase.value,
            'duration': self.end_time - self.start_time,
            'tokens': self.actual_tokens,
            'success': self.error is None,
            'constraints': self.constraint_violations,
            'batched': self.should_batch
        }
```

---

## 🎨 架构变化

### 简化前

```
┌─────────────────────────────────────────┐
│ AI Client                               │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ FastMCP Server                          │ ← Layer 1
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ MCP Tool (execute_fn wrapper)           │ ← Layer 2 ❌ 冗余
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Tool.apply_ex()                         │ ← Layer 3 ❌ 职责过多
│ - 检查激活状态                           │
│ - 检查项目                               │
│ - 检查 LSP                               │
│ - 日志记录                               │
│ - 异常处理                               │
│ - 统计记录                               │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ SerenaAgent.execute_task()              │ ← Layer 4 ❌ 简单包装
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ ThreadPoolExecutor                      │ ← Layer 5 ❌ 可合并
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Tool.apply() - 业务逻辑                  │ ← Layer 6 ✅ 必需
└─────────────────────────────────────────┘
```

### 简化后

```
┌─────────────────────────────────────────┐
│ AI Client                               │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ FastMCP Server                          │ ← Layer 1 ✅ 协议层
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ ToolExecutionEngine                     │ ← Layer 2 ⭐ 统一入口
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Pre-validation                  │   │
│ │ - 工具激活检查                   │   │
│ │ - 项目检查                       │   │
│ │ - LSP 检查                       │   │
│ └─────────────────────────────────┘   │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Pre-execution (Epic-001)        │   │
│ │ - ExecutionPlan 验证            │   │
│ │ - Constraints 检查              │   │
│ │ - Batching 优化                 │   │
│ └─────────────────────────────────┘   │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Execution                       │   │
│ │ - Token 估算                    │   │
│ │ - 线程池执行                     │   │
│ │ - Token 统计                    │   │
│ └─────────────────────────────────┘   │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Post-execution                  │   │
│ │ - 日志记录                       │   │
│ │ - 统计上报                       │   │
│ │ - 性能监控                       │   │
│ └─────────────────────────────────┘   │
│                                         │
│ ExecutionContext (完整审计信息)        │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Tool.apply() - 业务逻辑                  │ ← Layer 3 ✅ 必需
└─────────────────────────────────────────┘
```

---

## 📊 影响分析

### 正面影响

1. **审计能力提升** ⭐⭐⭐⭐⭐
   - 完整的 ExecutionContext 记录
   - 清晰的 token 消耗路径
   - 支持 TPST 精确分析

2. **Epic-001 集成简化** ⭐⭐⭐⭐⭐
   - 单一注入点（`_pre_execution_with_constraints`）
   - Feature flag 控制（`enable_constraints`）
   - 不需要修改每个工具

3. **代码可维护性提升** ⭐⭐⭐⭐
   - 职责集中（分散的 6 种职责 → 统一引擎）
   - 易于理解（4 个清晰的执行阶段）
   - 易于测试（统一的执行流程）

4. **性能监控能力** ⭐⭐⭐⭐
   - 识别慢工具（duration > threshold）
   - 识别 token 浪费（actual > estimated）
   - 生成优化建议（batching opportunities）

### 负面影响

1. **代码量增加** ⭐⭐
   - ToolExecutionEngine: ~150 lines
   - ExecutionContext: ~30 lines
   - 总计：+180 lines

   **缓解**：代码量虽增加，但复杂度降低（集中 vs 分散）

2. **重构风险** ⭐⭐⭐
   - 需要修改 Tool.apply_ex()
   - 需要修改 SerenaAgent 初始化
   - 可能影响现有工具

   **缓解**：
   - 充分的回归测试
   - 渐进式迁移
   - 保持向后兼容

3. **学习成本** ⭐⭐
   - 新的执行流程
   - 新的 ExecutionContext 概念

   **缓解**：
   - 清晰的文档
   - 4 阶段易于理解
   - KISS 原则（简单通用）

---

## 🎯 实施计划

### Phase 0: 链路简化（优先级最高）

```yaml
Story 0.1: 实现 ToolExecutionEngine
  - 创建 ExecutionContext 数据类
  - 实现 4 阶段执行流程
  - 实现审计日志
  - 实现 TPST 分析接口
  工期: 5 天
  风险: 🟡 中

Story 0.2: 集成到 SerenaAgent
  - 修改 Tool.apply_ex() 委托给执行引擎
  - 移除 SerenaAgent.execute_task()
  - 更新 MCP 适配器
  - 添加 feature flag 控制
  工期: 3 天
  风险: 🔴 高

Story 0.3: 回归测试
  - 运行所有现有测试
  - 验证工具调用行为不变
  - 验证审计日志正确性
  工期: 2 天
  风险: 🟢 低
```

### 与 Epic-001 的关系

Phase 0 完成后，Epic-001 的 4 个 Features 将**直接注入到 ToolExecutionEngine**：

```python
class ToolExecutionEngine:
    def _pre_execution_with_constraints(self, tool, ctx):
        """Epic-001 统一入口"""

        # Feature 1: ExecutionPlan Validation
        if not self._constraint_engine.validate_plan(ctx.execution_plan):
            raise InvalidExecutionPlanError(...)

        # Feature 2-4: Constitutional Constraints + Batching
        violations = self._constraint_engine.check_constraints(tool, ctx.kwargs)
        if violations:
            raise ConstraintViolationError(...)

        if self._constraint_engine.should_batch(tool, ctx.kwargs):
            ctx.result = self._constraint_engine.execute_batched(...)
            raise BatchExecutionCompleted()
```

---

## 🔄 可逆性

### 回滚策略

如果 ToolExecutionEngine 出现严重问题，可以回滚到原来的架构：

1. **Feature flag 禁用**：`enable_execution_engine = False`
2. **恢复 Tool.apply_ex()**：保留原来的实现作为 fallback
3. **保留 SerenaAgent.execute_task()**：暂不删除，保持兼容

### 灰度发布

- Week 1: 仅在测试环境启用
- Week 2: 在部分工具启用（低风险工具）
- Week 3: 全量启用
- Week 4: 移除旧代码

---

## 📚 参考资料

### 设计原则

- **KISS (Keep It Simple, Stupid)**: 简单通用优于复杂精确
- **单一职责原则**: 每个类只有一个变化的理由
- **开闭原则**: 对扩展开放，对修改关闭

### 相关 ADR

- [ADR-001: Graph-of-Thought over Sequential Thinking](001-graph-of-thought-over-sequential-thinking.md)
- [ADR-002: Monorepo with Epic-003 Future Split](002-monorepo-with-epic-003-future-split.md)

### 参考实现

- **责任链模式**（Chain of Responsibility）
- **中间件模式**（Middleware Pattern）
- **管道模式**（Pipeline Pattern）

---

## 🤔 替代方案

### 方案 A：保持现状 + Epic-001 注入

**描述**：在 Tool.apply_ex() 中直接注入 Epic-001 的约束检查

**优点**：
- 不需要重构
- 风险最低

**缺点**：
- 无法解决审计问题
- 无法解决链路复杂问题
- 不符合 EvolvAI 的核心定位

**决策**：❌ 拒绝（不符合项目定位）

### 方案 B：装饰器模式

**描述**：为每个工具添加装饰器实现约束

**优点**：
- 细粒度控制
- 渐进式迁移

**缺点**：
- 需要修改每个工具
- 无法统一审计
- 不符合 KISS 原则

**决策**：❌ 拒绝（过于复杂）

### 方案 C：ToolExecutionEngine（当前方案）

**优点**：
- 统一执行入口
- 完整审计能力
- 易于扩展
- 符合 KISS 原则

**缺点**：
- 需要重构
- 短期风险较高

**决策**：✅ 采纳（最符合项目定位）

---

## ✅ 决策确认

- [x] **决策已批准** - 2025-10-27
- [x] **架构评审通过** - EvolvAI Team
- [ ] **实施开始** - 预计 2025-10-28
- [ ] **Phase 0 完成** - 预计 2025-11-03
- [ ] **生产部署** - 预计 2025-11-10

---

**最后更新**: 2025-10-27
**更新人**: EvolvAI Team
