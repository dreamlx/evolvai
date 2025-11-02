# ADR-004: Story 1.3 RuntimeConstraintMonitor 优化决策

**状态**: [APPROVED]
**创建日期**: 2025-10-30
**决策者**: EvolvAI Team
**影响范围**: Epic-001 Phase 1

---

## 📋 决策概述

**决策**: 保留 `RuntimeConstraintMonitor` 作为 Story 1.3 的核心组件，但优化其实现设计，从独立组件改为与 `ToolExecutionEngine` 深度集成。

**理由**: 基于 Epic-001 战略目标分析，RuntimeConstraintMonitor 是 Safe Tools 和 Constitutional Constraints 的必要基础设施，对 TPST 优化目标至关重要。

---

## 🎯 背景上下文

### 原始设计
- Story 1.3 计划创建独立的 `RuntimeConstraintMonitor` 组件
- 估算工作量: 3 person-days
- 6个 TDD cycles，复杂的约束规则接口

### 触发分析
- 完成 Story 1.1 (PlanValidator) 和 Story 1.2 (ToolExecutionEngine Integration)
- 发现 `ExecutionLimits` 已存在但未被使用
- 重新评估 Epic-001 的整体战略路径

---

## 🔍 决策分析

### 战略必要性分析

#### 1. **Safe Tools 的强制执行基础**
```
Phase 2: Safe Operations (safe_search, safe_edit, safe_exec)
    ↓ 依赖
Story 1.3: RuntimeConstraintMonitor (运行时强制力)
    ↓ 依赖
Phase 1: Validation Framework (静态验证)
```

没有 RuntimeConstraintMonitor，Safe Tools 无法强制执行 ExecutionPlan 限制。

#### 2. **Constitutional Constraints 的运行时环境**
Phase 4 的约束规则引擎需要运行时执行环境：
```python
# Phase 4 需要的基础设施
class ConstraintRule:
    def check_runtime(self, context: ExecutionContext) -> ConstraintResult:
        # 依赖 Story 1.3 提供的运行时数据
        if context.files_processed > self.limits.max_files:
            return ConstraintResult(violated=True)
```

#### 3. **TPST 优化的核心机制**
RuntimeConstraintMonitor 通过早期失败减少 TPST：
- 第1个文件超限 → 立即停止，避免后续 token 浪费
- 第1个变更违规 → 立即回滚，避免连锁错误

### 技术优化机会

#### 现有基础设施
- ✅ `ExecutionPlan.limits` 已定义完整
- ✅ `ToolExecutionEngine` 4阶段架构已建立
- ✅ `ExecutionContext` 审计追踪已实现
- ✅ 异常处理和违规记录机制已存在

#### 优化空间
- 避免独立组件的复杂性
- 利用现有执行流程集成点
- 重用现有异常和审计系统

---

## 🚀 决策内容

### 保留的核心价值
1. **战略基础设施**: 为 Safe Tools 提供运行时强制力
2. **Phase 4 基础**: 为 Constitutional Constraints 提供运行时环境
3. **TPST 核心**: 通过早期失败减少 token 浪费

### 优化实现方案

#### 架构优化
```python
# 优化前：独立组件
class RuntimeConstraintMonitor:
    def check_files_processed(self, count: int) -> None: ...
    def check_changes_made(self, count: int) -> None: ...
    def check_elapsed_time(self, time: float) -> None: ...

# 优化后：集成式设计
class ExecutionContext:
    # 集成运行时跟踪器
    files_processed: int = 0
    changes_made: int = 0

    def check_limits(self) -> None:
        """内联约束检查，复用 ExecutionPlan.limits"""
        if self.execution_plan:
            limits = self.execution_plan.limits
            if self.files_processed > limits.max_files:
                raise FileLimitExceededError(...)
```

#### 实施优化
- **工作量**: 从 3 person-days 优化为 2.5 person-days
- **TDD Cycles**: 从 6 cycles 优化为 4 cycles
- **集成点**: 在 ToolExecutionEngine.execute() 的 EXECUTION 阶段内联检查
- **复用性**: 重用现有异常处理和审计日志机制

---

## 📊 影响评估

### 正面影响
- ✅ 保持战略路径完整性
- ✅ 减少实现复杂性
- ✅ 降低维护成本
- ✅ 提高代码复用性

### 负面影响
- ⚠️ 需要修改 Story 1.3 的详细设计
- ⚠️ 需要更新 Phase 1 实施计划
- ⚠️ 需要重新制定 TDD 计划

---

## 🔄 实施计划

### 立即行动
1. **创建本 ADR** ✅
2. **更新 Phase 1 实施计划**
3. **更新 Epic-001 README**
4. **创建优化后的 Story 1.3 TDD 计划**

### 后续实施
1. **Story 1.3 开发** (2.5 person-days)
2. **Phase 1 完成**
3. **Phase 2 Safe Tools 开始** (依赖 Story 1.3)

---

## 🎯 成功标准

### 功能标准
- ✅ 运行时文件数限制强制执行
- ✅ 运行时变更数限制强制执行
- ✅ 运行时超时限制强制执行
- ✅ 违规时正确抛出异常并记录审计日志

### 性能标准
- ✅ 运行时检查开销 <2ms
- ✅ 不影响现有执行性能
- ✅ 内存使用最小化

### 战略标准
- ✅ 为 Phase 2 Safe Tools 提供基础设施
- ✅ 为 Phase 4 Constitutional Constraints 奠定基础
- ✅ 支持早期失败以优化 TPST

---

## 📝 文档更新

### 需要更新的文档
1. ✅ `docs/development/architecture/adrs/004-runtime-constraint-monitor-optimization.md` (本文件)
2. ⏳ `docs/development/sprints/current/phase-1-implementation-plan.md`
3. ⏳ `docs/product/epics/epic-001-behavior-constraints/README.md`
4. ⏳ 创建 `docs/development/sprints/current/story-1.3-tdd-plan.md`

---

## 🔗 相关决策

- **ADR-003**: ToolExecutionEngine Simplification - 提供了 4 阶段执行架构
- **ADR-001**: Graph-of-Thought over Sequential Thinking - TPST 优化目标
- **Epic-001**: Behavior Constraints System - 整体战略框架

---

**最后更新**: 2025-10-30
**下次审查**: Story 1.3 开发完成后