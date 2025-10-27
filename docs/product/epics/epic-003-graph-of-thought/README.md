# [ACTIVE] Epic 003: Graph-of-Thought引擎 (GoT Engine)

**Epic ID**: EPIC-003
**创建日期**: 2025-10-27
**负责人**: EvolvAI Team
**状态**: [ACTIVE]
**优先级**: [P0] - **基础设施级**
**估算**: 8人天 (1.5周 MVP)

---

## 📋 Epic概述

### 问题陈述

**当前困境**：AI助手的"思考"过程混乱且低效
- 🧵 **线性思考**：SequentialThinking是串行的，无法并行探索方案
- 💥 **ID混乱**：through id经常失败，思维上下文丢失
- 📝 **冗长啰嗦**：思考过程是长文本，token浪费严重
- 🔁 **重复试错**：缺乏验证机制，反复尝试同一错误
- 🚫 **范围受限**：无法处理动态拆解、分支逻辑、自适应规划

**根本原因**：
```
AI思考 = 自由文本对话
    ↓
无结构、不可验证、不可并行
    ↓
依赖"运气"而非"结构化推理"
    ↓
TPST浪费 + 首次成功率低
```

### 业务价值

**核心理念**：**Graph-of-Thought > Sequential Thinking**

将AI推理从"长对话"升级为"可并行、可验证、可回放的图结构"，输出的是**可执行计划**而非文本废话。

**直接收益**：
- **减少无效回合**：结构化思维取代冗长解释，token减少40-60%
- **并行探索**：同时评估多个方案，早停劣解，收敛优解
- **可验证计划**：输出必须通过Schema校验，避免"想得好、做不实"
- **可回放调试**：思维图谱可审计、复盘、重放

**战略价值**：
- **思维层约束**：与Epic-001（代码约束）、Epic-002（文档约束）形成完整"行为工程"体系
- **Token效率核心**：从源头优化推理效率，TPST影响最大
- **AI能力放大器**：让AI"想得更清楚"而不只是"做得更多"

### 目标用户

- **AI助手**：需要高效推理的Claude Code、Cursor、Copilot
- **开发者**：需要理解AI推理过程的技术人员
- **质量保证**：需要审计AI决策的QA团队

---

## 🎯 成功指标

### TPST影响（主指标）

| 指标 | 基线 | MVP目标 | 最终目标 |
|------|------|---------|----------|
| **思考token占比** | ~40% | 20% | 15% |
| **平均思考回合数** | 5-8 | 2-3 | 1-2 |
| **首次计划成功率** | ~50% | 75% | 90% |
| **并行分支收敛速度** | N/A | 2x | 3x |

**测量方式**：
```python
# 对比实验：同一复杂任务
baseline_tokens = solve_with_sequential_thinking()  # ~2000 tokens思考
optimized_tokens = solve_with_got_engine()         # ~800 tokens思考
reduction = (baseline - optimized) / baseline      # 60%降低
```

### 推理质量指标

| 指标 | MVP目标 | 最终目标 |
|------|---------|----------|
| **计划Schema通过率** | 90% | 95% |
| **分支早停准确率** | 75% | 85% |
| **思维图可读性评分** | 0.7 | 0.8 |
| **执行验证匹配率** | 80% | 90% |

### 系统性能指标

| 指标 | MVP目标 |
|------|---------|
| **思维图生成延迟** | <2s |
| **并行分支数** | 3-5 |
| **事件溯源可靠性** | 99.9% |

---

## 📦 包含的Features

### Feature 1: GoT Core Engine
- **Feature ID**: FEATURE-008
- **描述**: Graph-of-Thought核心引擎，事件溯源与图管理
- **估算**: 3人天
- **状态**: [Backlog]
- **包含内容**:
  - Session管理（start, goal, checkpoint, export）
  - 事件溯源（append-only event log, parent_ids引用）
  - 图结构存储（事件表 + 边表）
  - 冲突检测（乐观并发控制）

### Feature 2: Parallel Thinking & Branching
- **Feature ID**: FEATURE-009
- **描述**: 并行思考与分支策略
- **估算**: 2人天
- **状态**: [Backlog]
- **包含内容**:
  - `branch.fork()` - 生成并行候选
  - `parallel.run()` - 并发执行与聚合
  - 早停策略（race, best, vote）
  - 资源分配（预算驱动，bandit风格）

### Feature 3: Plan Validation & Schema
- **Feature ID**: FEATURE-010
- **描述**: 计划验证与Schema校验
- **估算**: 2人天
- **状态**: [Backlog]
- **包含内容**:
  - `validate.plan()` - Schema校验
  - ExecutionPlan/DocPlan集成
  - 风险评分器（影响范围、缺失测试）
  - 失败驱动修订（critic角色）

### Feature 4: Context Optimization
- **Feature ID**: FEATURE-011
- **描述**: 上下文优化与轻量交互
- **估算**: 1人天
- **状态**: [Backlog]
- **包含内容**:
  - `digest()` - 思维摘要生成（≤200 tokens）
  - Redaction层（private vs public）
  - 去冗传输（只传最新摘要+引用id）
  - 可视化导出（Mermaid图）

### Feature 5: Budget & Admission Control
- **Feature ID**: FEATURE-012
- **描述**: 预算与准入控制机制
- **估算**: 2人天
- **状态**: [Backlog]
- **包含内容**:
  - 硬预算设定（max_tokens, max_branches, max_walltime, max_retries）
  - 阶段早停（任一分支达"可验证"即触发收敛）
  - 失败签名去重（stderr+args指纹，避免重复重试）
  - 资源配额与抢占机制

### Feature 6: Event Sourcing Reliability
- **Feature ID**: FEATURE-013
- **描述**: 事件溯源的幂等与恢复
- **估算**: 2人天
- **状态**: [Backlog]
- **包含内容**:
  - 幂等键（idempotency_key）与去重检测
  - 向量时钟（vector_clock）与冲突解决
  - WAL + checkpoint崩溃恢复
  - 事件导出与回放功能

### Feature 7: Observability & Metrics
- **Feature ID**: FEATURE-014
- **描述**: 可观测性与指标系统
- **估算**: 2人天
- **状态**: [Backlog]
- **包含内容**:
  - 分支级指标（tokens、时延、得分、早停原因、失败归因）
  - 会话级指标（TPST、Model-hops、Waste ratio、First-pass success）
  - 审计视图（Plan→执行→验证的证据链）
  - Token审计条与实时监控

### Feature 8: Failure Taxonomy & Self-Healing
- **Feature ID**: FEATURE-015
- **描述**: 失败分类与自愈策略库
- **估算**: 2人天
- **状态**: [Backlog]
- **包含内容**:
  - 失败分类（权限/端口/锁/超时/缺依赖/路径不合规/测试失败/语法错误）
  - 自愈策略（降并发、分批、切换工具、按需展开、回滚提示）
  - 策略匹配引擎与历史成功率
  - 失败签名归档与模式识别

---

## 🏗️ 技术架构

### 核心组件

```
┌─────────────────────────────────────────┐
│       Graph-of-Thought MCP Service      │
├─────────────────────────────────────────┤
│  think.session.*    ← 会话管理          │
│  think.plan.step    ← 添加思维步骤      │
│  think.branch.fork  ← 并行分支          │
│  think.parallel.run ← 并行执行与聚合    │
│  think.validate.*   ← 计划验证          │
│  think.merge        ← 分支合并          │
│  think.digest       ← 摘要生成          │
├─────────────────────────────────────────┤
│       Event Sourcing Layer              │
│  ├─ Append-only event log               │
│  ├─ Parent-child references             │
│  ├─ Optimistic concurrency (409)        │
│  └─ Checkpoint & recovery               │
├─────────────────────────────────────────┤
│       Graph Management Layer            │
│  ├─ DAG structure (events + edges)      │
│  ├─ Branch lifecycle (fork→run→merge)   │
│  ├─ Early stopping rules                │
│  └─ Resource budget allocation          │
├─────────────────────────────────────────┤
│       Validation & Scoring Layer        │
│  ├─ ExecutionPlan/DocPlan schema        │
│  ├─ Risk scorer (scope, tests)          │
│  ├─ Failure-driven revision             │
│  └─ Constraint propagation              │
├─────────────────────────────────────────┤
│       Integration Layer                 │
│  ├─ ExecutionController ← Plan output   │
│  ├─ safe_* tools ← Execution feedback   │
│  └─ TPST metrics ← Token tracking       │
└─────────────────────────────────────────┘
```

### 事件结构

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class ThinkEvent(BaseModel):
    """思维事件"""
    id: str = Field(..., description="事件唯一ID: evt_{uuid}")
    session_id: str = Field(..., description="会话ID")
    idempotency_key: str = Field(..., description="幂等键，用于去重检测")

    type: Literal[
        "plan_step",     # 计划步骤
        "critique",      # 批判性评审
        "branch",        # 分支创建
        "merge",         # 分支合并
        "validate",      # 验证结果
        "checkpoint",    # 检查点
        "evidence"       # 执行反馈证据
    ]
    parent_ids: List[str] = Field(default_factory=list, description="父事件ID列表")
    vector_clock: dict = Field(default_factory=dict, description="向量时钟")

    # 内容
    role: Literal["planner", "critic", "tester", "decider"]
    content: str = Field(..., max_length=400, description="思维内容（限长）")
    constraints: Optional[dict] = None  # {"max_changes": 200, "timeout": 60}

    # 评分（扩充）
    score: Optional[dict] = None  # {
        # "completeness": 0.9,  # 必填字段完整度
        # "risk": 0.2,         # 风险评分（影响范围/未知符号率）
        # "cost": 850,         # 预计tokens/时间
        # "history_prior": 0.7 # 历史成功率
    # }

    # 状态
    status: Literal["open", "done", "rejected", "early_stopped"] = "open"
    early_stop_reason: Optional[str] = None  # "race_winner", "budget_exceeded", "validation_failed"

    # 失败相关
    failure_signature: Optional[str] = None  # stderr+args的指纹
    retry_count: int = Field(default=0, description="重试次数")

    # 元数据
    token_cost: int = Field(default=0, description="本事件token消耗")
    walltime_ms: int = Field(default=0, description="实际执行时长（毫秒）")
    ts: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1, description="Schema版本")

class Session(BaseModel):
    """思维会话"""
    id: str = Field(..., description="会话ID: sess_{uuid}")
    goal: str = Field(..., description="任务目标")
    success_criteria: List[str] = Field(default_factory=list)

    # 预算（硬限制）
    token_budget: int = Field(default=5000, description="Token预算")
    time_budget: int = Field(default=300, description="时间预算（秒）")
    max_branches: int = Field(default=5, description="最大并行分支数")
    max_retries: int = Field(default=3, description="单一失败签名最大重试次数")
    max_walltime: int = Field(default=600, description="最大墙钟时间（秒）")

    # 状态
    status: Literal["active", "completed", "failed", "timeout", "budget_exceeded"] = "active"

    # 统计
    events_count: int = 0
    branches_count: int = 0
    token_used: int = 0
    walltime_elapsed: int = 0  # 实际消耗时间（秒）

    # 失败追踪
    failure_signatures: dict = Field(default_factory=dict, description="失败签名→次数映射")

    # 审计字段
    first_pass_success: bool = False
    model_hops: int = 0  # 模型交互回合数
    waste_ratio: float = 0.0  # 浪费token比例

    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class ExecutionPlanExtended(BaseModel):
    """扩展的ExecutionPlan Schema（用于GoT输出）"""
    # 基础字段（继承自Epic-001）
    type: Literal["ExecutionPlan"] = "ExecutionPlan"
    dry_run: bool = Field(default=True, description="必须先dry_run")
    rollback: dict = Field(..., description="回滚策略")
    limits: dict = Field(..., description="变更限制")

    # GoT扩充字段
    capabilities_required: List[str] = Field(default_factory=list, description="需要的工具能力")
    risk_estimate: dict = Field(
        default_factory=dict,
        description="{
            'scope_impact': 0.3,  # 影响范围（文件数/行数）
            'test_coverage': 0.8, # 测试覆盖率
            'unknown_symbols': 0.05  # 未解析符号率
        }"
    )
    batching_strategy: Optional[str] = None  # "none", "file_level", "hunk_level"
    approval_needed: bool = Field(default=False, description="是否需要人工批准")
    success_criteria: List[str] = Field(default_factory=list, description="成功条件")

    # 上下文充分性指标
    context_sufficiency: dict = Field(
        default_factory=dict,
        description="{
            'unresolved_symbol_rate': 0.02,
            'callgraph_coverage': 0.95,
            'required_fields_coverage': 1.0
        }"
    )
```

### MCP端点设计

#### 1. Session管理
```python
@mcp_tool
def think_session_start(
    goal: str,
    success_criteria: List[str],
    token_budget: int = 5000,
    time_budget: int = 300
) -> dict:
    """
    启动思维会话

    Returns:
        {
            "session_id": "sess_abc123",
            "goal": "安全批量重命名并通过受影响测试",
            "token_budget": 5000,
            "time_budget": 300,
            "status": "active"
        }
    """
```

#### 2. 计划步骤
```python
@mcp_tool
def think_plan_step(
    session_id: str,
    parent_ids: List[str],
    role: Literal["planner", "critic", "tester", "decider"],
    content: str,  # ≤400 chars
    constraints: Optional[dict] = None
) -> dict:
    """
    添加一步思维

    Returns:
        {
            "event_id": "evt_xyz789",
            "status": "done",
            "token_cost": 85
        }
    """
```

#### 3. 并行分支
```python
@mcp_tool
def think_branch_fork(
    session_id: str,
    from_id: str,
    variants: List[str]  # 不同策略描述
) -> dict:
    """
    创建并行分支

    Args:
        variants: ["文本替换+白名单", "ast-grep结构化", "codemod模板"]

    Returns:
        {
            "branch_ids": ["branch_1", "branch_2", "branch_3"],
            "parent_event": "evt_xyz789"
        }
    """

@mcp_tool
def think_parallel_run(
    session_id: str,
    branch_ids: List[str],
    aggregator: Literal["race", "best", "vote"]
) -> dict:
    """
    并行执行分支并聚合

    Aggregators:
    - race: 第一个有效方案
    - best: 评分最高方案
    - vote: 多数投票

    Returns:
        {
            "winner_branch": "branch_2",
            "winner_event": "evt_abc456",
            "rationale": "覆盖率高且误伤风险低",
            "eliminated_branches": ["branch_1", "branch_3"]
        }
    """
```

#### 4. 计划验证
```python
@mcp_tool
def think_validate_plan(
    session_id: str,
    plan_id: str,
    schema: Literal["ExecutionPlan", "DocPlan"]
) -> dict:
    """
    验证计划是否符合Schema

    Returns:
        {
            "ok": false,
            "violations": [
                {
                    "rule": "missing_field:rollback",
                    "severity": "error",
                    "message": "ExecutionPlan必须包含rollback策略"
                }
            ],
            "risk_score": 0.7,
            "suggestions": [
                "添加git_revert回滚策略",
                "设置max_changes上限"
            ]
        }
    """
```

#### 5. 分支合并
```python
@mcp_tool
def think_merge(
    session_id: str,
    winner_branch_id: str,
    rationale: str
) -> dict:
    """
    选择优胜分支并合并

    Returns:
        {
            "merged_plan": {
                "type": "ExecutionPlan",
                "dry_run": true,
                "rollback": {"strategy": "git_revert"},
                "limits": {"max_changes": 50}
            },
            "confidence": 0.85
        }
    """
```

#### 6. 上下文优化
```python
@mcp_tool
def think_digest(
    session_id: str,
    mode: Literal["summary", "todo", "next_step"]
) -> dict:
    """
    生成思维摘要（≤200 tokens）

    Returns (summary):
        {
            "summary": "评估3种重命名策略，选择ast-grep因安全性最高",
            "key_decisions": [
                "排除文本替换（误伤风险）",
                "选择ast-grep（结构化安全）"
            ],
            "next_actions": ["验证ExecutionPlan", "执行dry_run"],
            "token_saved": 1200
        }
    """

@mcp_tool
def think_export_graph(
    session_id: str,
    format: Literal["mermaid", "json"]
) -> dict:
    """
    导出思维图谱

    Returns (mermaid):
        {
            "graph": "graph TD\nA[Goal] --> B[Plan1]\nA --> C[Plan2]\n...",
            "url": "https://mermaid.ink/img/..."
        }
    """
```

---

## 🔗 与Epic-001、Epic-002的关系

### 三层架构

```
┌────────────────────────────────────────┐
│     Epic-003: 思维层（GoT Engine）      │  ← 产出可执行计划
│  动态拆解、分支推演、验证收敛           │
└──────────────┬─────────────────────────┘
               │ ExecutionPlan/DocPlan
┌──────────────▼─────────────────────────┐
│     Epic-001: 执行层（代码操作约束）    │  ← 执行并反馈
│  safe_search, safe_edit, safe_exec     │
└──────────────┬─────────────────────────┘
               │ 实际操作结果
┌──────────────▼─────────────────────────┐
│     Epic-002: 规范层（文档约束）        │  ← 验证规范
│  位置、命名、结构、原则校验             │
└────────────────────────────────────────┘
```

### 协作流程

**完整闭环**：
1. **GoT Engine思考**：生成ExecutionPlan草案
2. **Validate校验**：检查是否符合Schema + 风险评分
3. **Safe_* 执行**：遵守约束执行（dry_run → 确认 → 执行）
4. **结果反馈**：执行结果写回GoT → critic评估 → 可能触发修订

**示例场景**：
```
用户: "重构auth模块"

→ GoT: fork 3个分支
  ├─ branch_1: 纯重命名（风险低）
  ├─ branch_2: 提取函数（中等复杂）
  └─ branch_3: 全面重构（风险高）

→ GoT: parallel.run(aggregator=best)
  winner: branch_2 (平衡复杂度与收益)

→ GoT: validate.plan(ExecutionPlan)
  ✅ 包含dry_run, rollback, limits
  ✅ risk_score=0.3（可接受）

→ 输出ExecutionPlan给Epic-001

→ safe_edit: 执行提取函数
  dry_run → 预览 → 确认 → 执行
  结果: ✅ 测试通过

→ 反馈到GoT
  critic: "成功，无需修订"
```

### 优先级建议

**方案A：顺序开发**
```
Week 1-2: Epic-003 (思维引擎基础)
Week 3-4: Epic-001 (代码操作约束)
Week 5-6: Epic-002 (文档规范约束)
```
理由：思维层是基础，先有"想得清楚"才能"做得靠谱"

**方案B：混合开发**（推荐）
```
Week 1: Epic-003 MVP (核心引擎)
Week 2: Epic-001 + Epic-003集成（边思考边执行）
Week 3: Epic-002准备 + Epic-001完成
Week 4: Epic-002完成
```
理由：Epic-003的价值需要Epic-001验证，早期集成风险更低

---

## 📊 时间线

### 预计时间
- **开始日期**: 2025-10-28（最高优先级）
- **结束日期**: 2025-11-22
- **总工作量**: 16人天 (3周完整版，含工程化能力)

### 里程碑

#### Week 1: 核心引擎 (Day 1-5)
- [ ] Feature-008 完成：GoT Core Engine - 2025-11-01
  - [ ] Story-013: Session管理 + 事件溯源
  - [ ] Story-014: 图结构存储 + 冲突检测
- [ ] Feature-009 完成：Parallel Thinking - 2025-11-03
  - [ ] Story-015: branch.fork + parallel.run
  - [ ] Story-016: 早停策略 + 资源分配

#### Week 2: 验证与集成 (Day 6-10)
- [ ] Feature-010 完成：Plan Validation - 2025-11-06
  - [ ] Story-017: validate.plan + Schema集成
  - [ ] Story-018: 风险评分 + 失败修订
- [ ] Feature-011 完成：Context Optimization - 2025-11-08
  - [ ] Story-019: digest + Redaction
  - [ ] Story-020: Mermaid图导出
- [ ] 与Epic-001集成测试 - 2025-11-10
  - [ ] ExecutionPlan输出→safe_*执行→反馈闭环

#### Week 3: 工程化能力 (Day 11-16)
- [ ] Feature-012 完成：Budget & Admission Control - 2025-11-13
  - [ ] Story-021: 硬预算设定 + 阶段早停
  - [ ] Story-022: 失败签名去重 + 资源配额
- [ ] Feature-013 完成：Event Sourcing Reliability - 2025-11-15
  - [ ] Story-023: 幂等键 + 冲突检测
  - [ ] Story-024: WAL + checkpoint + 回放
- [ ] Feature-014 完成：Observability & Metrics - 2025-11-18
  - [ ] Story-025: 分支/会话级指标
  - [ ] Story-026: Token审计条 + 实时监控
- [ ] Feature-015 完成：Failure Taxonomy & Self-Healing - 2025-11-20
  - [ ] Story-027: 失败分类 + 策略库
  - [ ] Story-028: 策略匹配引擎 + 历史成功率
- [ ] 完整TPST基准对比 - 2025-11-22

### 演示场景
**英雄场景**：复杂重构任务
1. 用户: "重构整个auth模块，提取通用逻辑"
2. GoT: 识别为高复杂度任务，fork 4个分支
3. 并行评估：文本替换、AST重构、提取类、微服务化
4. 早停淘汰2个高风险方案
5. 最优方案通过validate，生成ExecutionPlan
6. safe_edit执行，feedback回写
7. 对比基线：从8次试错→首次成功，token减少65%

---

## 🛡️ 风险与对策

### 技术风险

| 风险 | 影响 | 概率 | 对策 | 负责人 |
|------|------|------|------|--------|
| **事件溯源复杂度** | High | Medium | 使用成熟库（SQLite+append-only） | Team |
| **并行调度开销** | Medium | Low | 限制并行数≤5，预算驱动 | Team |
| **Schema验证严格度** | Medium | Medium | 提供宽松模式（dev），生产严格 | Team |

### 用户体验风险

| 风险 | 影响 | 概率 | 对策 | 负责人 |
|------|------|------|------|--------|
| **思维过程不透明** | High | Medium | 提供Mermaid图可视化 | Team |
| **digest摘要信息丢失** | Medium | Medium | 允许展开查看完整事件 | Team |

---

## 🧪 测试策略

### 测试范围
- 事件溯源正确性（append-only, 冲突检测）
- 并行分支执行与聚合
- Schema验证准确性
- TPST对比基准测试

### 测试类型
- [x] 单元测试 - 每个MCP端点
- [x] 集成测试 - GoT → ExecutionPlan → safe_* 完整流程
- [x] 性能测试 - 并行分支调度延迟
- [x] TPST基准测试 - 对比SequentialThinking

### 测试覆盖率目标
- 核心模块: 95%
- 整体: 90%

---

## 📝 实现备注

### 设计决策

1. **为什么用图而不是链？**
   - 图支持分支、合流、回溯
   - 更自然地表达"同时思考多个方案"

2. **为什么限制content≤400字符？**
   - 强制简洁，避免长篇废话
   - 降低token消耗

3. **为什么需要digest？**
   - 完整事件图可能很大
   - 与LLM往返只传摘要，历史靠MCP拉取

4. **为什么使用append-only事件溯源？**
   - 避免"through id"问题
   - 完整历史可回放审计
   - 乐观并发控制（409冲突）

---

## 📚 相关文档

### 内部文档
- [Epic-001: 行为约束系统](../epic-001-behavior-constraints/README.md)
- [Epic-002: 项目规范即服务](../epic-002-project-standards/README.md)
- [产品定义 v1.0](../../definition/product-definition-v1.md)

### 外部参考
- [Graph-of-Thought Paper](https://arxiv.org/abs/2305.16582)
- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)
- [MCP Protocol](https://spec.modelcontextprotocol.io/)

---

## 🎯 下一步行动

### 立即行动（今天）
1. ✅ 创建Epic-003文档
2. 📋 制定三Epic协调开发计划
3. 📋 创建GoT Engine技术架构文档
4. 📋 更新整体产品路线图

### 短期行动（1周内）
1. 实现GoT Core Engine
2. 实现Parallel Thinking
3. 与Epic-001集成测试
4. TPST基准对比

### 问题待澄清
1. 是否优先Epic-003 > Epic-001？还是并行开发？
2. 事件存储使用SQLite还是LiteFS？
3. 并行分支默认数量（3-5个？）
4. 是否需要可视化UI？

---

**最后更新**: 2025-10-27
**更新人**: EvolvAI Team
