# Reflection Persistence as Product Feature - 研究文档

**创建日期**: 2025-11-06
**状态**: [APPROVED] - 定位为 Epic-001 Phase 5
**类型**: 产品构想
**优先级**: P1（高优先级）
**决策文档**: [Decision: Lesson Guard Positioning](../../product/epics/epic-001-behavior-constraints/decision-lesson-guard-positioning.md)

---

## 🎯 核心洞察

### 问题发现

**当前痛点**：
- Feature 2.2测试失败率20%，主要原因是重复已知错误（接口不匹配40%、过度设计25%等）
- 手动创建的反思持久化机制（CLAUDE.md检查点、模板、Memory）依赖AI主动阅读和遵守
- 每个新会话可能重复相同的错误，造成token浪费

**关键发现**：
> **反思如果不能被强制执行，就是浪费。**
>
> 我们手动创建的反思持久化机制，正是EvolvAI应该提供的核心功能之一！

---

## 💡 产品化机会

### 价值主张

**独特卖点（USP）**：
> 市场上第一个"AI从自己的错误中学习并主动防护"的开发工具

**核心能力**：
1. **自动学习** - AI从每次失败中自动提取教训
2. **主动防护** - 在犯错前就阻止，不是事后补救
3. **持续优化** - 使用越久，保护越强（网络效应）

### 与EvolvAI定位的完美契合

**EvolvAI三大Epic**：
- Epic-001: Behavior Constraints - 防止当前低效行为
- Epic-002: Project Standards - 减少文档返工
- Epic-003: GoT Engine - 优化思考效率

**新功能定位**：
- **Epic-001 Feature 1.4: Lesson-Based Constraints** - 防止重复历史错误

**协同效应**：
```
当前约束（safe_search/edit/exec） → 防止"正在做的坏事"
教训约束（lesson-based） → 防止"曾经做过的坏事"
═══════════════════════════════════════════════════════
合力：全方位TPST优化
```

---

## 🏗️ 产品架构概念

### 核心组件（概念层）

#### 1. Lesson（教训）
单个失败经验的结构化表示：
- 失败模式描述
- 检测规则（如何识别违反）
- 防护措施（如何避免）
- 严重程度和触发条件

#### 2. LessonLibrary（教训库）
集中管理所有教训：
- 从Serena Memory加载
- 按检查点类型分类
- 支持模式匹配和规则检查
- 统计和分析能力

#### 3. LessonEnforcement（强制执行）
集成到ExecutionPlan：
- 指定检查点类型
- 配置严格程度（警告/阻止）
- 自动记录新教训
- 审计日志记录

#### 4. CheckpointSystem（检查点系统）
四大关键检查点：
- **Task Start** - 验证Story/DoD映射
- **Test Write** - 验证Story/Scenario/DoD标注
- **Implementation** - 验证接口一致性
- **Commit** - 验证无过度设计

### 集成点

**与现有架构集成**：
```
ToolExecutionEngine
  ├── PRE_VALIDATION: ExecutionPlan schema validation ✅ 已完成
  ├── PRE_EXECUTION: PlanValidator + LessonEnforcer ← NEW
  ├── EXECUTION: Tool execution
  └── POST_EXECUTION: Audit logging + Lesson recording ← NEW
```

**复用现有基础设施**：
- ExecutionPlan框架
- ToolExecutionEngine hooks
- Serena Memory系统
- 审计日志系统

---

## 📋 三阶段实施计划

### Phase 1: 只读检查工具（MVP）
**时间**: 2周
**目标**: 验证产品价值

**核心能力**：
- `check_lessons()` MCP工具
- 从Memory读取教训并返回相关警告
- 不改变现有架构

**使用场景**：
```
AI在Task开始时调用check_lessons()
→ 系统返回相关教训和警告
→ AI获得提醒但不强制执行
```

**成功标准**：
- 能够检索Feature 2.2教训
- AI主动使用该工具
- 用户反馈正面

---

### Phase 2: 主动验证检查
**时间**: 4周
**目标**: 实现主动防护

**核心能力**：
- `validate_against_lessons()` 工具
- 解析和验证具体内容（如测试代码）
- 检测违反教训的具体情况

**使用场景**：
```
AI写测试前调用validate_against_lessons()
→ 系统解析测试代码
→ 检查是否有Story/Scenario/DoD标注
→ 返回违规列表
→ AI根据反馈修正
```

**成功标准**：
- 能够检测40%的接口不匹配
- 能够识别缺失的DoD映射
- 减少测试返工率

---

### Phase 3: ExecutionPlan强制约束
**时间**: 6周
**目标**: 完全系统化防护

**核心能力**：
- LessonEnforcement集成到ExecutionPlan
- pre_execution阶段自动检查
- 违反时抛出LessonViolationError
- 自动记录新教训

**使用场景**：
```
用户配置ExecutionPlan.lessons
→ ToolExecutionEngine自动执行检查
→ 违反教训时阻止执行
→ 记录违规到审计日志
→ 失败时自动提取新教训
```

**成功标准**：
- 完全集成Epic-001架构
- 测试失败率降至<5%
- 自动教训积累工作正常

---

## 💰 商业价值分析

### ROI估算

**开发投入**：
- 总计12周（约3个月）
- 复用现有基础设施，开发成本可控

**收益预测**：

| 项目规模 | 防止失败 | Token节省 | 年化价值 |
|---------|---------|----------|---------|
| 小型（10 Stories） | 20% | 100K tokens | $200 |
| 中型（50 Stories） | 20% | 500K tokens | $1,000 |
| 大型（200 Stories） | 20% | 2M tokens | $4,000 |

**注**: 以Claude Sonnet价格估算（$3/M input tokens）

### 独特市场价值

**差异化优势**：
1. ✅ 市场第一个"AI自学习"开发工具
2. ✅ 网络效应：用户越多，教训库越丰富
3. ✅ 持续价值：不是一次性功能，而是持续优化系统

**竞争壁垒**：
- 需要完整的ExecutionPlan框架（竞争对手难以复制）
- 需要项目memory系统（跨会话持久化）
- 需要行为约束理念（不是所有AI助手都有）

---

## 🎯 关键决策点（待讨论）

### 决策1: 产品定位

**选项A**: Epic-001 Feature 1.4
- 优点：自然延伸，复用现有框架
- 缺点：可能显得不够重要

**选项B**: 独立Epic-004
- 优点：突出重要性，独立品牌
- 缺点：增加复杂度，可能失焦

**建议**: 选项A（作为Epic-001的核心能力）

---

### 决策2: MVP范围

**选项A**: 只读工具（Phase 1）
- 优点：快速验证，风险低
- 缺点：价值有限，可能无法充分证明

**选项B**: 主动验证（Phase 2）
- 优点：价值明确，用户体验更好
- 缺点：开发时间6周，风险较高

**建议**: 选项A，快速迭代验证

---

### 决策3: 教训来源

**选项A**: 手动编写教训
- 优点：质量可控，立即可用
- 缺点：维护成本高

**选项B**: 自动提取教训
- 优点：扩展性好，长期价值高
- 缺点：AI准确性问题，短期难实现

**选项C**: 混合模式
- 优点：兼顾两者优点
- 缺点：系统复杂度增加

**建议**: Phase 1&2用选项A，Phase 3引入选项C

---

### 决策4: 强制程度

**选项A**: 仅警告（Soft）
- 优点：不影响工作流，用户接受度高
- 缺点：防护力度弱

**选项B**: 完全阻止（Hard）
- 优点：防护力度强
- 缺点：可能过度约束，影响灵活性

**选项C**: 可配置（Configurable）
- 优点：灵活性高
- 缺点：配置复杂度增加

**建议**: Phase 1用选项A，Phase 3支持选项C

---

## 📊 成功指标定义

### 产品指标

**Phase 1 (MVP)**:
- ✅ `check_lessons()`工具被AI主动调用率 > 80%
- ✅ 用户满意度评分 ≥ 4/5
- ✅ 相关警告被采纳率 > 50%

**Phase 2**:
- ✅ 检测出的违规准确率 > 90%
- ✅ 误报率 < 10%
- ✅ 测试返工率降低 > 30%

**Phase 3**:
- ✅ 测试失败率从20% → <5%
- ✅ 接口不匹配从40% → <5%
- ✅ 过度设计从25% → <5%
- ✅ 自动教训提取准确率 > 70%

### 业务指标

**TPST降低**:
- 目标：整体TPST降低10-20%（通过减少失败返工）

**用户留存**:
- 目标：活跃用户使用率 > 60%

**网络效应**:
- 目标：教训库每月增长 > 10条

---

## 🔗 相关资源

### 现有实现（手动机制）
- [CLAUDE.md](../../CLAUDE.md) - 强制检查点（Layer 1）
- [BDD测试模板](../../docs/templates/bdd-test-template.md) - 强制标注（Layer 3）
- [Story TDD模板](../../docs/templates/story-tdd-plan-template.md) - Task检查清单（Layer 2）
- [Feature 2.2教训](../../.serena/memories/feature-2.2-tdd-lessons-learned) - 教训沉淀（Layer 5）

### 相关Epic/Feature
- [Epic-001: Behavior Constraints](../../docs/product/epics/epic-001-behavior-constraints/) - 父Epic
- [ToolExecutionEngine](../../src/evolvai/core/execution.py) - 集成点
- [ExecutionPlan](../../src/evolvai/core/execution_plan.py) - 扩展点

---

## 💭 未解答的问题

1. **教训的粒度**：应该多细？（功能级 vs 模式级）
2. **跨项目共享**：是否需要公共教训库？
3. **AI准确性**：如何确保AI正确理解和应用教训？
4. **性能影响**：Lesson检查对执行性能的影响？
5. **用户体验**：如何平衡防护力度和开发流畅性？

---

## 📅 下一步行动

### 立即行动
- [ ] 创建专门讨论的任务窗口
- [ ] 邀请相关stakeholder讨论
- [ ] 决策产品定位和优先级

### 讨论议程（待专门会议）
1. 是否立即启动产品化（GO/NO-GO决策）
2. 如果GO，确定MVP范围和时间表
3. 关键技术决策（4个决策点）
4. 资源分配和里程碑规划

### 如果决定GO
1. 创建Feature 1.4完整文档（Epic/Feature/Story）
2. 更新产品路线图
3. 启动Story 1.4.1（Phase 1 MVP）TDD计划

---

## 🎨 营销概念（初步）

**产品名称候选**：
- "Lesson Guard" - 教训守卫
- "Failure Shield" - 失败防护
- "Smart Memory" - 智能记忆
- "Learn & Lock" - 学习与锁定

**Slogan候选**：
- "Let AI learn from its mistakes, so you don't have to repeat them."
- "Turn every failure into a permanent safeguard."
- "The more you use, the smarter it gets."

**核心消息**：
> EvolvAI不仅约束AI当前行为，更让AI从历史中学习。
> 每个项目的失败都变成未来的防护，Token浪费越来越少。

---

## 📝 文档版本历史

**v1.0 (2025-11-06)**:
- 初始创建
- 记录核心洞察和产品化方案
- 定义三阶段实施计划
- 识别关键决策点

**v2.0 (2025-11-06)**:
- ✅ 决策确认：定位为 Epic-001 Phase 5
- 与 GPT-5 建议对比分析
- KISS 原则简化设计
- 明确实施路径和依赖关系

---

## 🎉 决策结果（2025-11-06）

### ✅ 最终定位

**Lesson Guard 作为 Epic-001 Phase 5**

**理由**：
1. 需要稳定的基础设施（ExecutionPlan、Safe Tools、Constitutional Constraints）
2. 与 Phase 4 形成"规则系统双子星"
3. 可复用 Phase 4 的规则系统经验
4. 不打乱当前路线图（Phase 1-3 按计划进行）
5. 手动机制（CLAUDE.md、模板）在 Phase 5 前继续发挥作用

### 📋 实施计划（KISS 版本）

**总估算**: 6 人天（约 1.5 周）

**Story 5.1**: Lesson Library 核心实现（2 人天）
- Lesson dataclass（5字段）
- 复用 Serena Memory（Markdown 存储）
- 简单的 Python 函数规则匹配

**Story 5.2**: MCP 工具接口（2 人天）
- 3 个 MCP 工具：check_lessons, list_lessons, validate_against_lessons
- 只支持 MCP（不做 CLI/IDE/CI）

**Story 5.3**: ExecutionPlan 集成和验收（2 人天）
- ToolExecutionEngine pre-execution hook
- 审计日志
- 端到端测试

### 🎯 关键简化（相比 GPT-5 建议）

| 维度 | GPT-5 建议 | KISS 版本 | 简化率 |
|------|-----------|-----------|--------|
| 文件数量 | 8 个组件 | 2 个文件 | -75% |
| 数据字段 | 15+ 字段 | 5 字段 | -67% |
| 存储方案 | SQLite | Serena Memory | 复用现有 |
| 规则系统 | YAML DSL | Python 函数 | 无 DSL |
| 平台支持 | 6 个平台 | MCP only | -83% |

### 📅 时间表

- **Phase 4 完成**: 2025-12-02
- **Phase 5 开始**: 2025-12-03
- **Phase 5 完成**: 2025-12-05
- **Epic-001 收尾**: 2025-12-09

---

**状态**: [APPROVED] - 已确认为 Epic-001 Phase 5
**负责人**: EvolvAI Team
**完整决策**: 见 [Decision: Lesson Guard Positioning](../../product/epics/epic-001-behavior-constraints/decision-lesson-guard-positioning.md)
