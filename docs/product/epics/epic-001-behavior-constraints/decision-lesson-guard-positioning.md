---
type: decision
category: product
status: approved
date: 2025-11-06
---

# [APPROVED] Decision: Lesson Guard 定位为 Epic-001 Phase 5

## Status
- **状态**: Approved
- **决策日期**: 2025-11-06
- **决策者**: EvolvAI Team
- **相关文档**:
  - [Reflection as Product Feature Research](../../../knowledge/research/reflection-as-product-feature.md)
  - [GPT-5 讨论记录](../../../knowledge/research/gpt5-lesson-guard-discussion.md)
  - [Epic-001 README](./README.md)

## Context

在 Feature 2.2 TDD 实施过程中，我们建立了 5 层反思持久化防护系统：
1. CLAUDE.md 强制检查点（100% 读取率）
2. Story TDD 计划模板（Task 级别清单）
3. BDD 测试模板（强制标注要求）
4. Definition of Done 映射
5. Serena Memory（教训沉淀）

**核心洞察**：反思如果不能被强制执行，就是浪费。我们手动创建的反思持久化机制，正是 EvolvAI 应该提供的核心功能。

**问题**：最初考虑作为 Epic-001 Feature 1.4，但深入分析后发现：
- Lesson Guard 包含完整子系统（教训库、检查点、规则引擎、MCP 工具、跨系统集成）
- 复杂度远超 Story 1.1-1.3（单一技术组件，2.5-3人天）
- 影响三大 Epic（Epic-001/002/003）的跨层能力
- 需要稳定的 ExecutionPlan 和 Safe Tools 基础设施

## Decision

**Lesson Guard 定位为 Epic-001 Phase 5**

在 Phase 4（Constitutional Constraints）完成后实施，作为行为约束系统的最后一环。

## Rationale

### 与 GPT-5 建议的对比

**✅ 完全采纳的战略决策**：
1. 作为独立模块（而非独立产品）- 命名 Lesson Guard
2. 不绑定 Claude Code - 支持多生态（MCP/CLI/IDE/CI）
3. CheckpointType 抽象（SESSION_START/TASK_START/TEST_WRITE/IMPLEMENTATION/COMMIT）
4. 与三大 Epic 集成的理念

**❌ 拒绝的过度设计**：
1. 复杂的目录结构（8个组件文件 → 2个文件）
2. SQLite 存储（与 Serena Memory 冲突 → 用 Markdown）
3. 复杂的数据模型（15+字段 → 5字段）
4. 规则引擎 DSL（YAML DSL → Python 函数）
5. 多平台同时开发（6个平台 → MCP only）

**核心原则**：采纳战略智慧，坚持 KISS 原则

### Considered Alternatives

**选项 A: Epic-001 Phase 5**（✅ 选择）
- 优点：与 Constitutional Constraints 类似的规则系统，有稳定基础
- 优点：可以复用 Phase 1-4 的基础设施
- 优点：有足够时间验证前期价值
- 缺点：延后到 Phase 4 完成后

**选项 B: 独立 Epic-004**
- 优点：反映其跨系统的性质
- 缺点：增加管理复杂度
- 缺点：失去与 Epic-001 的紧密集成

**选项 C: Phase 1.5 或 Phase 2.5**
- 优点：早期验证价值
- 缺点：打乱现有路线图
- 缺点：缺少稳定基础（ExecutionPlan/Safe Tools）

### Pros and Cons

**Pros**:
- ✅ 有稳定的 ExecutionPlan 和 ToolExecutionEngine 基础
- ✅ 有完整的 Safe Tools（safe_search/edit/exec）可集成
- ✅ 有 Constitutional Constraints 的规则系统经验
- ✅ 不打乱当前路线图（Phase 1-3 按计划进行）
- ✅ 与 Phase 4 形成完整的"规则系统双子星"（Constitutional + Lessons）

**Cons**:
- ⚠️ 价值验证延后（需要等到 Phase 4 完成）
- ⚠️ 如果前期阶段延误，会进一步推迟

## Consequences

### Positive Consequences
1. **技术基础充分**：Phase 1-4 提供完整基础设施
2. **设计经验丰富**：Phase 4 的规则系统经验可复用
3. **集成点清晰**：safe_* 工具、ExecutionPlan、审计日志都已稳定
4. **避免返工**：不会因为基础设施变化而需要重构
5. **KISS 原则**：有足够时间按 KISS 原则实施 MVP

### Negative Consequences
1. **价值验证延后**：无法早期验证"教训防护"的价值
2. **依赖前期进度**：如果 Phase 1-4 延误，会影响 Phase 5

### Mitigation Strategies
1. **手动机制继续使用**：CLAUDE.md、模板系统在 Phase 5 前持续发挥作用
2. **渐进式文档**：在 Phase 1-4 期间持续完善 Lesson Guard 设计文档
3. **经验积累**：Phase 2.2 的教训持续记录到 Serena Memory
4. **Phase 4 经验复用**：Constitutional Constraints 的规则系统设计直接指导 Phase 5

## Implementation

### Phase 5 实施计划（KISS 版本）

**Phase 5 总估算**: 6 人天（约 1.5 周）

#### Story 5.1: Lesson Library 核心实现（2 人天）
- **交付物**：
  - `src/evolvai/constraints/lessons.py`（~200行）
    - `Lesson` dataclass（5字段：name, checkpoint_type, pattern, message, severity）
    - `load_lessons_from_memory()` - 从 Serena Memory 加载
    - `check_lessons()` - 检索相关教训
  - 利用现有 Serena Memory（`.serena/memories/lessons/`）
  - 10-15 测试

#### Story 5.2: MCP 工具接口（2 人天）
- **交付物**：
  - `src/evolvai/constraints/lessons_tools.py`（~100行）
    - `check_lessons()` MCP 工具
    - `list_lessons()` MCP 工具
    - `validate_against_lessons()` MCP 工具
  - MCP 服务器集成
  - 8-10 测试

#### Story 5.3: ExecutionPlan 集成和验收（2 人天）
- **交付物**：
  - ToolExecutionEngine pre-execution hook 集成
  - 审计日志记录
  - 端到端测试
  - 文档和使用指南

### 数据模型（KISS 版本）

```python
@dataclass
class Lesson:
    name: str                    # "interface-mismatch"
    checkpoint_type: str         # "IMPLEMENTATION"
    pattern: str                 # 检测模式（字符串或regex）
    message: str                 # 警告消息
    severity: str                # "high"|"medium"|"low"
```

### 存储方案（KISS 版本）

```
.serena/memories/lessons/
├── lesson-interface-mismatch.md
├── lesson-over-engineering.md
├── lesson-mock-data-issues.md
└── lesson-parameter-mismatch.md
```

YAML frontmatter + Markdown 描述，复用现有 Serena Memory 系统。

### 平台支持（KISS 版本）

- **Phase 5 MVP**: 只支持 MCP（Claude Code/Desktop）
- **后续扩展**: 根据真实用户需求决定（CLI/IDE/CI）

### 集成点

**Epic-001 集成**：
- safe_search/safe_edit/safe_exec 的 pre-exec hook → check_lessons()
- ExecutionPlan.lessons 参数控制严格程度
- 审计日志记录违规和放行

**Epic-002 集成**（未来）：
- doc.validate 调用 → 规范失败自动生成教训草案

**Epic-003 集成**（未来）：
- GoT plan 生成前 → check_lessons() 提供风险提示

## References
- [Reflection as Product Feature Research](../../../knowledge/research/reflection-as-product-feature.md)
- [Feature 2.2 TDD Lessons Learned](../../../../.serena/memories/feature-2.2-tdd-lessons-learned)
- [CLAUDE.md - Development Mandatory Checkpoints](../../../../CLAUDE.md)
- [Story TDD Plan Template](../../../templates/story-tdd-plan-template.md)
- [BDD Test Template](../../../templates/bdd-test-template.md)

---

**最后更新**: 2025-11-06
**状态变更历史**:
- 2025-11-06: Approved（用户确认选项A）
