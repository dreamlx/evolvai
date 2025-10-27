# EvolvAI三大Epic关系与协作分析

**文档类型**: Product Roadmap Analysis
**创建日期**: 2025-10-27
**状态**: [APPROVED]

---

## 📋 执行摘要

EvolvAI的核心价值通过**三个互补的Epic**实现：

| Epic | 核心 | 约束对象 | 产出 | TPST影响 |
|------|------|----------|------|----------|
| **Epic-003** | 思维层 | AI推理过程 | ExecutionPlan/DocPlan | -40% |
| **Epic-001** | 执行层 | 代码操作 | safe_search/safe_edit结果 | -30% |
| **Epic-002** | 规范层 | 文档结构 | 规范验证通过/修正建议 | -40% |
| **累加效果** | **完整闭环** | **想→做→写** | **可验证行为** | **-70%** |

---

## 🏗️ 三层架构

### 架构图

```
┌─────────────────────────────────────────────────┐
│           用户请求 & AI助手交互                  │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  Epic-003: 思维层 (Graph-of-Thought Engine)    │
│  ┌──────────────────────────────────────────┐  │
│  │  动态拆解: "重构auth" → 4种策略分支       │  │
│  │  并行推演: 同时评估风险与收益             │  │
│  │  验证收敛: Schema校验 → 选最优方案        │  │
│  └──────────────────────────────────────────┘  │
│  产出: ExecutionPlan/DocPlan (可执行计划)      │
└────────────────────┬────────────────────────────┘
                     │ Plan
┌────────────────────▼────────────────────────────┐
│  Epic-001: 执行层 (Behavior Constraints)       │
│  ┌──────────────────────────────────────────┐  │
│  │  物理约束: 禁止直接执行，必须先预览      │  │
│  │  safe_search: 强制limit + timeout        │  │
│  │  safe_edit: Patch-First + dry_run        │  │
│  └──────────────────────────────────────────┘  │
│  产出: 代码变更结果 + 验证反馈                 │
└────────────────────┬────────────────────────────┘
                     │ Results + Validation
┌────────────────────▼────────────────────────────┐
│  Epic-002: 规范层 (Project Standards as MCP)   │
│  ┌──────────────────────────────────────────┐  │
│  │  位置验证: 文档是否在正确目录             │  │
│  │  结构验证: 必填章节是否完整               │  │
│  │  原则评分: 是否符合项目规范               │  │
│  └──────────────────────────────────────────┘  │
│  产出: ✅ 规范通过 / ❌ 修正建议               │
└─────────────────────────────────────────────────┘
```

---

## 🔄 完整协作流程

### 场景：复杂重构任务

```
用户请求: "重构auth模块，提取通用逻辑，更新相关文档"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: 思维层（Epic-003）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. GoT: session.start("重构auth模块")
2. GoT: 识别高复杂度 → fork 4个分支
   ├─ branch_1: 纯重命名（风险低，收益低）
   ├─ branch_2: 提取函数（平衡）
   ├─ branch_3: 提取类（复杂度中）
   └─ branch_4: 微服务化（风险高）

3. GoT: parallel.run(aggregator=best)
   ├─ 评分: branch_1=0.4, branch_2=0.8, branch_3=0.7, branch_4=0.3
   └─ 早停: 淘汰branch_1, branch_4

4. GoT: 对比branch_2 vs branch_3
   ├─ branch_2: 影响文件少，测试覆盖好
   └─ winner: branch_2

5. GoT: validate.plan(ExecutionPlan)
   ├─ ✅ 包含dry_run, rollback, limits
   ├─ ✅ risk_score=0.3（可接受）
   └─ ✅ 通过

6. GoT: 输出ExecutionPlan
   {
     "dry_run": true,
     "rollback": {"strategy": "git_revert"},
     "limits": {"max_files": 15, "max_changes": 200},
     "validation": {
       "pre_conditions": ["所有测试通过", "无未提交变更"],
       "expected_outcomes": ["auth_utils.py创建", "3个文件重构"]
     }
   }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 2: 执行层（Epic-001）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7. safe_edit: 接收ExecutionPlan
8. safe_edit: 检查pre_conditions
   ├─ run tests → ✅ 全部通过
   └─ git status → ✅ 工作区干净

9. safe_edit: dry_run模式
   ├─ 生成unified diff
   ├─ 展示预览：
   │   - 创建auth_utils.py (+150行)
   │   - 修改login.py (-50行 +20行)
   │   - 修改register.py (-30行 +15行)
   └─ 等待确认

10. 用户: 确认执行

11. safe_edit: 应用变更
    ├─ git apply --3way
    ├─ run tests → ✅ 全部通过
    └─ 验证expected_outcomes → ✅ 符合

12. safe_edit: 反馈结果
    {
      "status": "success",
      "changes_applied": 3,
      "tests_passed": true,
      "validation_matched": true
    }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 3: 规范层（Epic-002）- 文档更新
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

13. GoT: critic角色
    "代码重构成功，需要更新架构文档"

14. GoT: 生成DocPlan
    {
      "doc_type": "architecture",
      "title": "Auth模块重构说明",
      "location": "docs/development/architecture/auth-refactor-2025-10.md"
    }

15. doc.validate(DocPlan)
    ├─ ❌ 位置错误: 应该在architecture/refactoring/
    ├─ ❌ 命名不规范: 应该是auth-module-refactoring.md
    └─ 返回修正建议

16. GoT: 修订DocPlan
    {
      "location": "docs/development/architecture/refactoring/auth-module-refactoring.md",
      "required_sections": ["重构背景", "变更说明", "影响范围", "测试验证"]
    }

17. doc.validate(修订后)
    ✅ 通过

18. AI创建文档 → pre-commit守卫验证 → ✅ 允许提交

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 4: 闭环反馈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

19. GoT: 接收Epic-001和Epic-002的成功反馈
20. GoT: critic评估
    "✅ 任务完成，无需修订"
21. GoT: digest
    {
      "summary": "成功重构auth模块，提取通用逻辑到auth_utils.py，所有测试通过",
      "token_used": 850,
      "baseline_tokens": 2400,
      "reduction": "65%"
    }
```

---

## 📊 TPST累加效应

> 📊 **权威指标定义**: 详见 [Metrics Reference](../specs/metrics-reference.md#完整版目标-week-6)
> ⚠️  **注意**: 以下为假设性估算，需实验验证协同效应

### 单独效应

| Epic | 优化点 | TPST降低（估算） | 适用场景 |
|------|--------|----------|----------|
| Epic-003 | 减少思考冗长、并行探索 | -30% | 复杂任务拆解、方案选择 |
| Epic-001 | 减少盲目重试、首次成功 | -15% | 代码搜索、编辑操作 |
| Epic-002 | 减少文档返工、位置纠正 | -10% | 文档创建、结构验证 |

### 累加效应

**基线场景**（无约束）：
```
总token: 3000
├─ 思考: 1200 tokens (5次试错)
├─ 代码操作: 1200 tokens (3次返工)
└─ 文档: 600 tokens (2次纠正)
```

**优化后**（三Epic完整闭环）：
```
总token: 900 (-70%)
├─ 思考: 480 tokens (-60%, Epic-003)
├─ 代码操作: 300 tokens (-75%, Epic-001+003协同)
└─ 文档: 120 tokens (-80%, Epic-002+003协同)
```

**为什么累加效应>单独相加？**
1. **思维优化放大执行效率**：GoT产出更准确的Plan → safe_*首次成功率更高
2. **执行反馈改进思维**：safe_*的验证结果 → GoT的critic学习
3. **规范前置减少返工**：Doc规范在GoT阶段就被考虑 → 创建时直接符合

---

## 🎯 开发优先级建议

### 方案A：顺序开发（保守）

```
Month 1: Epic-003 (2周MVP + 2周打磨)
Month 2: Epic-001 (2周MVP + 2周集成)
Month 3: Epic-002 (2周MVP + 2周集成)

总耗时: 3个月
优势: 风险最低，逐步验证
劣势: 完整价值延迟3个月才体现
```

### 方案B：混合并行（推荐）⭐

```
Week 1: Epic-003 Core (GoT引擎基础)
Week 2: Epic-003 + Epic-001 集成开始
  ├─ GoT产出ExecutionPlan
  └─ safe_search/safe_edit实现

Week 3: Epic-001完成 + Epic-002准备
  ├─ GoT ↔ safe_* 闭环验证
  └─ Epic-002架构设计

Week 4: Epic-002 Core + 三Epic初步集成
Week 5-6: 完整闭环打磨与TPST验证

总耗时: 6周
优势: 渐进式验证，快速闭环
劣势: 需要更强的协调能力
```

### 方案C：Epic-003优先，其他并行

```
Week 1-2: Epic-003 MVP（全力投入）
Week 3-4: Epic-001 + Epic-002 并行（Epic-003已稳定）
Week 5: 三Epic集成与验证

总耗时: 5周
优势: 思维层先行，为后续铺路
劣势: Week 3-4压力较大
```

---

## 🔗 单一来源真相（Single Source of Truth）

### 设计原则

**核心理念**: Plan和证据链是唯一权威来源，跨层同步与追踪必须通过结构化数据流

**三个SSOT层次**:

```
┌─────────────────────────────────────────────────┐
│  SSOT-1: 思维图谱（Epic-003 Event Store）       │
│  ├─ 所有思维事件（append-only）                 │
│  ├─ 分支决策与评分历史                          │
│  └─ 证据链：Plan → 执行 → 验证 → 反馈          │
├─────────────────────────────────────────────────┤
│  SSOT-2: ExecutionPlan（Epic-003 → Epic-001）  │
│  ├─ 可执行计划的唯一定义                        │
│  ├─ 预期结果与验证条件                          │
│  └─ 回滚策略与限制约束                          │
├─────────────────────────────────────────────────┤
│  SSOT-3: 规范库（Epic-002 .project_standards） │
│  ├─ 项目级规范的唯一定义                        │
│  ├─ 位置、命名、结构规则                        │
│  └─ 豁免记录与修订历史                          │
└─────────────────────────────────────────────────┘
```

### 数据一致性保证

#### 1. Plan版本控制

```python
class ExecutionPlanExtended(BaseModel):
    plan_id: str = Field(..., description="唯一计划ID: plan_{uuid}")
    version: int = Field(default=1, description="版本号")
    derived_from_event: str = Field(..., description="来源思维事件ID")

    # 一致性字段
    checksum: str = Field(..., description="Plan内容的SHA256校验和")
    created_at: datetime
    expires_at: Optional[datetime] = None  # Plan有效期

    # 溯源字段
    session_id: str = Field(..., description="来源会话ID")
    branch_id: str = Field(..., description="来源分支ID")
```

**校验机制**:
```python
def validate_plan_integrity(
    plan: ExecutionPlanExtended,
    event_store: EventStore
) -> bool:
    """验证Plan与思维图谱一致性"""
    # 1. 检查来源事件是否存在
    event = event_store.get_event(plan.derived_from_event)
    if not event:
        raise ValueError(f"来源事件{plan.derived_from_event}不存在")

    # 2. 检查checksum
    computed = compute_checksum(plan)
    if computed != plan.checksum:
        raise ValueError("Plan内容校验失败（可能被篡改）")

    # 3. 检查有效期
    if plan.expires_at and datetime.utcnow() > plan.expires_at:
        raise ValueError("Plan已过期，需重新生成")

    return True
```

#### 2. 证据链追踪

```python
class EvidenceChain(BaseModel):
    """完整证据链（SSOT）"""
    chain_id: str = Field(..., description="证据链ID")
    session_id: str
    initiated_at: datetime

    # 证据节点
    nodes: List[EvidenceNode] = Field(default_factory=list)

    # 当前状态
    status: Literal["in_progress", "completed", "failed"] = "in_progress"

class EvidenceNode(BaseModel):
    """证据链节点"""
    node_id: str
    layer: Literal["thought", "execution", "validation"]
    event_id: str  # 指向事件存储的ID

    # 节点内容
    operation: str  # "plan_step", "safe_edit", "doc.validate"
    input_data: dict  # 输入数据快照
    output_data: dict  # 输出数据快照
    status: Literal["pending", "success", "failure"]

    # 时间戳
    started_at: datetime
    completed_at: Optional[datetime] = None

    # 关联
    parent_node_id: Optional[str] = None  # 父节点（用于构建树）
```

**证据链构建**:
```
思维图谱事件 ─┬─> ExecutionPlan ──> Evidence(plan_generated)
             │
             └─> safe_edit ──────────> Evidence(execution_started)
                     │
                     ├─> dry_run ───> Evidence(diff_generated)
                     │
                     ├─> apply ─────> Evidence(changes_applied)
                     │
                     └─> tests ─────> Evidence(tests_passed)
                             │
                             └─> GoT critic ──> Evidence(task_completed)
```

#### 3. 跨层同步协议

**同步规则**:
1. **Epic-003 → Epic-001**: Plan必须通过validate，才能传递给Epic-001
2. **Epic-001 → Epic-003**: 执行结果必须写入Evidence事件，GoT才能感知
3. **Epic-002 → Epic-003**: 规范校验结果写入Evidence事件，影响后续Plan生成

**同步接口**:
```python
@mcp_tool
def sync_plan_to_execution(
    plan: ExecutionPlanExtended
) -> dict:
    """同步Plan到执行层（Epic-003 → Epic-001）"""
    # 1. 验证Plan完整性
    validate_plan_integrity(plan, event_store)

    # 2. 创建Evidence节点
    evidence = EvidenceNode(
        node_id=f"evidence_{uuid4()}",
        layer="thought",
        event_id=plan.derived_from_event,
        operation="plan_generated",
        input_data={"goal": plan.goal},
        output_data=plan.dict(),
        status="success"
    )

    # 3. 添加到证据链
    chain.add_node(evidence)

    # 4. 返回执行句柄
    return {
        "execution_handle": f"exec_{uuid4()}",
        "plan_id": plan.plan_id,
        "evidence_node": evidence.node_id
    }

@mcp_tool
def sync_execution_result_to_thought(
    execution_handle: str,
    result: dict
) -> dict:
    """同步执行结果到思维层（Epic-001 → Epic-003）"""
    # 1. 查找证据链
    chain = evidence_store.get_chain_by_handle(execution_handle)

    # 2. 创建执行结果Evidence节点
    evidence = EvidenceNode(
        node_id=f"evidence_{uuid4()}",
        layer="execution",
        event_id=result["event_id"],  # Epic-001的事件ID
        operation=result["tool"],  # safe_edit/safe_search
        input_data=result["input"],
        output_data=result["output"],
        status="success" if result["success"] else "failure",
        parent_node_id=chain.nodes[-1].node_id  # 链接到上一节点
    )

    # 3. 添加到证据链
    chain.add_node(evidence)

    # 4. 写回GoT Event Store（作为evidence事件）
    got_event = ThinkEvent(
        id=f"evt_{uuid4()}",
        session_id=chain.session_id,
        idempotency_key=f"{chain.session_id}:evidence:{evidence.node_id}",
        type="evidence",
        parent_ids=[chain.nodes[0].event_id],  # 链接到原始Plan事件
        role="tester",
        content=f"执行{'成功' if result['success'] else '失败'}: {result['summary'][:300]}",
        score={
            "success": result["success"],
            "tests_passed": result.get("tests_passed", 0),
        },
        status="done"
    )
    event_store.append_event(got_event)

    return {
        "evidence_node": evidence.node_id,
        "got_event_id": got_event.id,
        "chain_status": chain.status
    }
```

### 失败传播与恢复

#### 失败分类

```python
class FailureType(Enum):
    # 思维层失败
    PLAN_INVALID = "plan_invalid"           # Plan未通过Schema校验
    BRANCH_EARLY_STOPPED = "branch_early_stopped"  # 分支早停
    BUDGET_EXCEEDED = "budget_exceeded"     # 预算耗尽

    # 执行层失败
    EXECUTION_FAILED = "execution_failed"   # safe_*执行失败
    TESTS_FAILED = "tests_failed"           # 测试失败
    ROLLBACK_FAILED = "rollback_failed"     # 回滚失败

    # 规范层失败
    VALIDATION_FAILED = "validation_failed" # 规范校验失败
    PLACEMENT_WRONG = "placement_wrong"     # 文档位置错误
```

#### 失败传播规则

```
┌─────────────────────────────────────────┐
│ Epic-003 (思维层)                        │
│ Plan生成失败 ──> 触发修订 ──> 重试      │
│ 预算耗尽 ──────> 早停收敛 ──> 返回最优  │
└────────────┬────────────────────────────┘
             │ Plan
             ▼
┌─────────────────────────────────────────┐
│ Epic-001 (执行层)                        │
│ dry_run失败 ─> 拒绝执行 ─> Evidence失败 │
│ apply失败 ──> 自动回滚 ──> Evidence失败 │
│ tests失败 ──> 回滚 ─────> Evidence失败  │
└────────────┬────────────────────────────┘
             │ Evidence(failure)
             ▼
┌─────────────────────────────────────────┐
│ Epic-003 (思维层 - critic)               │
│ 接收失败Evidence                         │
│ 分析失败原因                             │
│ 生成修订Plan ────> 重新提交Epic-001     │
└─────────────────────────────────────────┘
```

#### 恢复策略

```python
RECOVERY_STRATEGIES = {
    FailureType.PLAN_INVALID: {
        "action": "revise_plan",
        "fallback": "ask_user",
        "max_retries": 3
    },
    FailureType.EXECUTION_FAILED: {
        "action": "rollback_and_revise",
        "fallback": "report_to_user",
        "max_retries": 2
    },
    FailureType.TESTS_FAILED: {
        "action": "rollback",
        "then": "analyze_test_failure",
        "max_retries": 1
    },
    FailureType.VALIDATION_FAILED: {
        "action": "apply_suggestions",  # Epic-002提供的修正建议
        "fallback": "ask_user",
        "max_retries": 2
    },
}
```

---

## 🔗 技术依赖关系

### 共享基础设施

| 基础设施 | Epic-003 | Epic-001 | Epic-002 |
|---------|----------|----------|----------|
| **Pydantic模型** | ThinkEvent, Session | ExecutionPlan | ProjectStandards, DocPlan |
| **MCP服务框架** | GoT端点 | safe_*端点 | doc.*端点 |
| **验证引擎** | validate.plan | pre_conditions校验 | doc.validate |
| **审计日志** | 事件溯源 | 执行记录 | 规范豁免 |

### 数据流动

```
GoT → ExecutionPlan/DocPlan → safe_*/doc.* → Results → GoT critic
  ↑                                                        ↓
  └────────────────────────────────────────────────────────┘
                      反馈闭环
```

---

## 🛡️ 协调风险与缓解

### 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **Schema不兼容** | High | Week 1设计评审，统一Schema定义 |
| **接口变更** | Medium | 使用版本化API，保持向后兼容 |
| **性能开销** | Low | 事件异步处理，批量操作优化 |

### 协调风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **开发进度不同步** | High | 每周对齐会议，设置检查点 |
| **优先级冲突** | Medium | 明确Epic-003基础优先 |
| **代码冲突** | Low | 清晰模块边界，不同目录 |

---

## 📈 预期收益时间线

### MVP阶段（Week 6）
- Epic-003: 思维优化 -40%
- Epic-001: 执行优化 -30%
- Epic-002: 文档优化 -40%
- **累加效果**: -70% TPST（理论）
- **实际预期**: -50% TPST（保守）

### 成熟阶段（Month 3）
- 三Epic深度集成优化
- 闭环学习效应
- **实际目标**: -70% TPST

---

## 🎯 决策建议

### 推荐：方案B（混合并行）

**理由**：
1. ✅ **渐进式验证**：每周都能看到进展和效果
2. ✅ **快速闭环**：Week 3就能验证GoT → safe_* 集成
3. ✅ **风险可控**：Epic-003先行2周，为后续铺路
4. ✅ **团队效率**：2人团队可实现（一人主Epic-003，一人主Epic-001/002）

**前提条件**：
- 2人团队可用
- Epic-003 Week 1-2 MVP稳定
- 每周协调机制到位

### 关键里程碑

| 里程碑 | 日期 | 验收标准 |
|--------|------|----------|
| **Epic-003 MVP** | Week 2 | GoT引擎可产出ExecutionPlan |
| **Epic-003+001集成** | Week 3 | GoT → safe_* 闭环运行 |
| **三Epic初步集成** | Week 4 | 完整流程跑通 |
| **TPST验证达标** | Week 6 | 实测TPST降低≥50% |

---

**决策**: ✅ **批准方案B（混合并行开发）**

**决策人**: EvolvAI Team
**决策日期**: 2025-10-27
**审查周期**: 每周评审，Week 2和Week 4重新评估

---

**最后更新**: 2025-10-27
**更新人**: EvolvAI Team
