# Dogfooding Readiness Assessment - EvolvAI/Serena

**评估日期**: 2025-01-14
**评估人**: Claude Code + User
**目的**: 确定何时可以开始"吃自己的狗粮"（使用 EvolvAI 开发 EvolvAI）

---

## 📊 当前进度概览

### Epic-001: 行为约束系统

| Phase | Story | 状态 | 完成度 | 关键交付物 |
|-------|-------|------|---------|-----------|
| **Phase 0** | Story 0.1: ToolExecutionEngine | ✅ | 100% | 统一执行引擎 + 审计日志 |
| **Phase 0** | Story 0.2: ExecutionPlan Schema | ✅ | 100% | Pydantic schema + 23 tests |
| **Phase 0** | Story 0.3: 回归测试验证 | ✅ | 100% | 313/372 tests passing |
| **Phase 1** | Story 1.1: PlanValidator | ⏳ | 0% | 待实施 |
| **Phase 1** | Story 1.2: Engine集成 | ⏳ | 0% | 待实施 |
| **Phase 1** | Story 1.3: Runtime Monitoring | ⏳ | 0% | 待实施 |
| **Phase 2** | Story 2.1: safe_search | ⏳ | 0% | 待实施 |
| **Phase 2** | Story 2.2: safe_edit | ⏳ | 0% | 待实施 |
| **Phase 2** | **Story 2.3: safe_exec** | ✅ | **100%** | **33/33 tests, MCP 暴露** |

### Story 2.3 详细交付

**✅ 已完成功能**:
- ✅ SafeExecWrapper (完整实现)
- ✅ SafeExecTool (MCP 暴露)
- ✅ PreconditionChecker (快速失败)
- ✅ Timeout 管理 + AI 反馈循环
- ✅ 交互命令检测
- ✅ ExecutionPlan 集成
- ✅ 输出截断优化
- ✅ 33/33 测试全部通过

### Story 2.4 设计（待实施）

**核心功能**: 交互确认高风险操作

**关键场景**:
1. **通配符删除确认**: `rm -rf ./tmp_*` → 询问用户确认
2. **范围误判保护**: "清理一下" → 明确具体范围
3. **目标混淆检测**: "这个删除一下" → 确认指代对象

**设计决策**: 交互确认（而非直接阻止）
- ✅ 用户保留最终控制权
- ✅ 避免误报阻止合理操作
- ✅ KISS 原则（不需要复杂语义分析）

---

## 🎯 Dogfooding 就绪度分析

### 当前可用功能

#### ✅ 已可用
1. **ToolExecutionEngine**: 统一执行框架 + 完整审计
2. **ExecutionPlan Schema**: 约束定义和验证
3. **safe_exec**: 命令执行包装器
   - 快速失败机制
   - Timeout 管理
   - 交互命令检测
   - ExecutionPlan 约束

#### ⏳ 部分可用（需要集成）
- **safe_search**: 底层实现存在，但未重构为 Safe Wrapper
- **safe_edit**: 底层实现存在，但未重构为 Safe Wrapper

#### ❌ 缺失关键功能
1. **PlanValidator**: 执行计划合理性验证
2. **Runtime Monitoring**: 运行时约束监控
3. **Constitutional Constraints**: 批处理策略和回滚

---

## 🔍 Dogfooding 场景评估

### 场景 1: 使用 safe_exec 运行测试

**可行性**: ✅ **立即可用**

```python
from evolvai.tools.safe_exec import SafeExecWrapper

# 使用 safe_exec 运行 pytest
wrapper = SafeExecWrapper(working_dir="/project")
result = wrapper.execute(
    command="uv run poe test test/evolvai/tools/",
    timeout=60
)

# AI 可以从 suggested_timeout 学习
if result.suggested_timeout:
    print(f"建议下次使用 timeout={result.suggested_timeout}s")
```

**价值**:
- ✅ 避免交互命令（如果 AI 误用 `pytest -s`）
- ✅ Timeout 自动管理
- ✅ 输出截断节省 token

### 场景 2: 使用 safe_exec 格式化代码

**可行性**: ✅ **立即可用**

```python
# 使用 safe_exec 运行格式化
result = wrapper.execute(
    command="uv run poe format",
    timeout=30
)
```

**价值**:
- ✅ 检测命令可用性（`ruff` 是否安装）
- ✅ 防止无限挂起

### 场景 3: 使用 safe_exec 提交代码

**可行性**: ⚠️ **部分可用**（Story 2.4 后更佳）

```python
# Day 3 已可用
result = wrapper.execute(
    command="git add .",
    timeout=10
)

# Story 2.4 后：交互确认
result = wrapper.execute(
    command="rm -rf ./build/*",
    timeout=5
)
# → 返回 confirmation_required=True
# → AI 询问用户确认
```

**价值**:
- ✅ Day 3: 基本安全检查
- ⏳ Story 2.4: 交互确认增强

### 场景 4: 完整 TDD 循环（Red-Green-Refactor）

**可行性**: ⏳ **需要 safe_edit**

```python
# 需要 safe_edit 支持
safe_edit.propose_edit(
    file_path="src/module.py",
    change_description="Add new function",
    execution_plan=plan
)
# → 生成 patch preview
# → 用户确认
# → apply_edit()
```

**状态**: safe_edit 底层实现存在，但需要重构为 Safe Wrapper

### 场景 5: 智能搜索代码

**可行性**: ⏳ **需要 safe_search**

```python
# 需要 safe_search 支持
safe_search.search(
    pattern="class.*Tool",
    scope="./src/serena/tools/",
    execution_plan=plan
)
```

**状态**: safe_search 底层实现存在，但需要重构

---

## 🚀 Dogfooding 路线图

### Milestone 1: Minimal Dogfooding (最早可用)

**时间**: **现在 - 1周后**

**可用功能**:
- ✅ safe_exec (Story 2.3 完成)
- ⏳ safe_exec + 交互确认 (Story 2.4, 估算 2-3 天)

**可做的事**:
1. ✅ 使用 safe_exec 运行所有命令（测试、格式化、类型检查）
2. ✅ 使用 safe_exec 执行 git 操作
3. ⏳ 使用交互确认保护高风险操作（Story 2.4 后）

**限制**:
- ❌ 不能用 safe_edit（需手动编辑）
- ❌ 不能用 safe_search（需手动搜索）
- ⏳ ExecutionPlan 约束有限（仅 timeout）

**TPST 改进预期**: **10-20%**
- 节省：命令失败的 token 浪费
- 节省：交互命令超时的 token 浪费
- 节省：输出截断节省的 token

### Milestone 2: Core Dogfooding (核心功能可用)

**时间**: **2-3 周后**

**需要完成**:
- ⏳ Story 2.4: 交互确认 (2-3 天)
- ⏳ Story 2.1: safe_search (4 天)
- ⏳ Story 2.2: safe_edit (6 天)

**可做的事**:
1. ✅ 完整的 TDD 循环（搜索、编辑、测试）
2. ✅ 智能搜索代码位置
3. ✅ Patch-first 编辑流程
4. ✅ 完整的 Safe Operations

**TPST 改进预期**: **30-40%**
- Milestone 1 的 10-20%
- + safe_search 减少搜索错误 (10-15%)
- + safe_edit patch preview 减少编辑返工 (10-15%)

### Milestone 3: Full Dogfooding (完整体验)

**时间**: **4-6 周后**

**需要完成**:
- ⏳ Phase 1 完成 (PlanValidator + Runtime Monitoring)
- ⏳ Constitutional Constraints 基础
- ⏳ 批处理策略

**可做的事**:
1. ✅ ExecutionPlan 完整约束验证
2. ✅ 批处理优化（减少工具调用次数）
3. ✅ 运行时监控和早期失败
4. ✅ 完整的 TPST 优化

**TPST 改进预期**: **50-70%** (Epic-001 目标)

---

## 🎯 推荐行动计划

### 立即可做（本周）

#### ✅ **Milestone 1 验证**

**Day 1-2**: Story 2.4 实施
- 交互确认机制（通配符、高风险操作）
- BDD 场景驱动 TDD
- 目标：8-10 个测试

**Day 3**: Minimal Dogfooding 开始
- 使用 safe_exec 执行所有命令
- 记录 token 使用情况（baseline）
- 验证 10-20% TPST 改进

**Day 4-5**: 持续使用 + 反馈
- 收集使用数据
- 发现问题并快速修复
- 调整 timeout 建议算法

### 短期目标（2-3周）

#### ⏳ **Milestone 2 实施**

**Week 2**:
- Story 2.1: safe_search (4 天)
- Story 2.1.1: 基准测试 (1 天)

**Week 3**:
- Story 2.2: safe_edit (6 天)

**Week 3 末**: Core Dogfooding 开始
- 完整 TDD 循环
- 测量 30-40% TPST 改进

### 中期目标（4-6周）

#### ⏳ **Milestone 3 准备**

**Week 4-5**: Phase 1 实施
- Story 1.1: PlanValidator
- Story 1.2: Engine 集成
- Story 1.3: Runtime Monitoring

**Week 6**: Full Dogfooding
- 完整约束系统
- 批处理优化
- 达成 50-70% TPST 目标

---

## 📈 成功指标

### Milestone 1 (现在可验证)

- ✅ safe_exec 使用率 > 80% (所有命令执行)
- ⏳ TPST 降低 10-20% (baseline vs safe_exec)
- ⏳ 命令失败率 < 5% (precondition 检测效果)
- ⏳ 交互命令误用次数 = 0

### Milestone 2 (2-3周后)

- ⏳ Safe Operations 覆盖率 > 90% (search + edit + exec)
- ⏳ TPST 降低 30-40%
- ⏳ 首次编辑成功率 > 75%
- ⏳ 搜索准确率 > 85%

### Milestone 3 (4-6周后)

- ⏳ ExecutionPlan 使用率 > 90%
- ⏳ TPST 降低 50-70% (Epic-001 目标)
- ⏳ 工具调用准确率 > 90%
- ⏳ Token 浪费率 < 10%

---

## 💡 关键洞察

### 1. 渐进式 Dogfooding 可行

**结论**: 不需要等所有功能完成才开始使用

**策略**:
- ✅ Milestone 1: **现在就可以开始**（仅 safe_exec）
- ⏳ Milestone 2: 2-3 周后（+ safe_search + safe_edit）
- ⏳ Milestone 3: 4-6 周后（完整系统）

### 2. Story 2.4 是关键增强

**Why**: 通配符确认是用户最关注的安全增强
- 用户原话："尤其是通配符操作"
- 场景：`rm -rf ./tmp_*` 误删重要备份

**优先级**: ⭐ **P0** - 应该在 Milestone 1 完成

### 3. 数据驱动优化

**建议**:
1. ✅ 建立 baseline（当前 TPST）
2. ⏳ Milestone 1 后测量（safe_exec only）
3. ⏳ Milestone 2 后测量（+ search + edit）
4. ⏳ 持续优化 timeout 建议算法

### 4. 快速反馈循环

**价值**: Dogfooding 会快速发现真实问题
- User: "很多时候 AI 理解用户的模糊命令..."
- 这类洞察只有在实际使用中才能发现

---

## 🎯 回答用户问题

### Q1: Story 2.4 什么功能？

**A**: **交互确认高风险操作**

核心场景：
1. **通配符删除**: `rm -rf ./tmp_*` → 询问确认
2. **范围误判**: "清理一下" → 明确具体范围
3. **目标混淆**: "这个删除一下" → 确认指代对象

设计：交互确认机制（用户决策权 + KISS 原则）

估算：2-3 天（8-10 个测试）

### Q2: 什么时候可以 dogfooding？

**A**: **分三个阶段，最早本周就可以开始**

#### ✅ **Milestone 1: 本周可开始**
- **功能**: safe_exec (已完成) + 交互确认 (2-3 天)
- **可做**: 所有命令执行、git 操作、高风险确认
- **价值**: 10-20% TPST 改进
- **状态**: **Story 2.4 完成后立即可用**

#### ⏳ **Milestone 2: 2-3 周后**
- **功能**: + safe_search (4天) + safe_edit (6天)
- **可做**: 完整 TDD 循环（搜索、编辑、测试）
- **价值**: 30-40% TPST 改进

#### ⏳ **Milestone 3: 4-6 周后**
- **功能**: + Phase 1 完成 + Constitutional Constraints
- **可做**: 完整约束系统 + 批处理优化
- **价值**: 50-70% TPST 改进（Epic-001 目标）

---

## 🚀 建议：立即开始 Minimal Dogfooding

### 行动计划

**本周任务**:
1. ✅ 完成 Story 2.4 (2-3 天)
2. ⏳ 建立 TPST baseline（记录当前 token 使用）
3. ⏳ 开始 Milestone 1 Dogfooding
4. ⏳ 收集使用数据和反馈

**下周开始**:
- 使用 safe_exec 开发 safe_search
- 使用 safe_exec 开发 safe_edit
- 逐步验证 TPST 改进

**优势**:
- ✅ 快速验证核心假设
- ✅ 真实场景发现问题
- ✅ 数据驱动优化方向
- ✅ 建立信心和动力

---

**评估结论**:
- ✅ **Story 2.3 完成 → Minimal Dogfooding 基础已就绪**
- ⏳ **Story 2.4 完成 → 可立即开始 Milestone 1**
- 🎯 **建议本周完成 Story 2.4 并开始 dogfooding**

---

**准备人**: Claude Code
**审阅**: 待用户确认
**下一步**: Story 2.4 实施或其他优先级调整
