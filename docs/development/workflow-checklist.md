# EvolvAI 开发和文档管理工作流 Checklist

**版本**: 1.1
**创建日期**: 2025-11-07
**更新日期**: 2025-11-14
**状态**: [ACTIVE]
**基于**: 实际执行的Phase 0-2流程总结

---

## 🎯 工作流概览

```
Epic规划 → Story拆分 → TDD开发 → Git提交 → Sprint完成 → 5S6A整理
   ↓          ↓          ↓         ↓          ↓           ↓
  产品层    开发层     代码层    版本控制    交付层      维护层
```

---

## 📋 Phase 1: Epic/Story规划

### Epic创建
- [ ] 使用模板：`cp docs/templates/epic-template.md docs/product/epics/epic-XXX/README.md`
- [ ] 定义业务价值和成功指标
- [ ] 拆分Phase（0-5个Phase）
- [ ] 拆分Story（每个Phase 3-5个Story）
- [ ] 估算工作量（人天）
- [ ] 识别依赖和风险

**关键文件**：
- `docs/product/epics/epic-XXX/README.md`
- `docs/product/definition/product-definition-vX.md`

**常见陷阱**：
- ❌ Phase拆分过细（<3人天/Phase）或过粗（>20人天/Phase）
- ❌ Story没有明确验收标准
- ❌ 忘记定义TPST等成功指标

---

### Story拆分和TDD计划

- [ ] 使用模板：`cp docs/templates/story-tdd-plan-template.md docs/development/sprints/current/story-X.X-tdd-plan.md`
- [ ] 定义Story验收标准（AC）
- [ ] 映射到DoD标准（F1/Q1/P1等）
- [ ] 拆分TDD Cycles（3-5个Cycle）
- [ ] 每个Cycle定义：Red（测试）→ Green（实现）→ Refactor（重构）
- [ ] 估算每个Cycle工作量

**关键原则**：
- ✅ 每个测试必须映射到DoD标准（否则是过度工程）
- ✅ 测试先于实现（TDD Red-Green-Refactor）
- ✅ Cycle粒度：半天到1天（不要太细或太粗）

**常见陷阱**：
- ❌ 写测试时没有对应的DoD标准（Feature 2.2: 40%失败）
- ❌ 实现时修改测试接口（接口不匹配）
- ❌ 因为有fixture就写测试（fixture存在 ≠ 需要测试）

---

## 📋 Phase 2: TDD开发循环

### 开发前检查（Checkpoint 1）

**必须能回答的问题**：
- [ ] 这是Story X.X的哪个Cycle？
- [ ] 这个Cycle要实现哪些测试场景（test_xxx）？
- [ ] 每个测试验证哪个DoD标准？

**无法回答 → STOP → 重新阅读Story TDD Plan**

---

### Red Phase：写测试

- [ ] 创建测试文件（test_xxx.py）
- [ ] 写测试docstring（必须格式）：
  ```python
  def test_something(self):
      """[简短描述]

      Story: story-X.X-tdd-plan.md Cycle Y
      Scenario: "用户场景描述"
      DoD: F1/Q1/P1 - 标准描述

      Given [前置条件]
      When [操作]
      Then [预期结果]
      """
  ```
- [ ] 运行测试（应该失败：Red）
- [ ] 检查：测试是否映射到Story Scenario和DoD？

**常见陷阱**：
- ❌ 没有docstring（无法追溯到Story）
- ❌ 测试没有对应的DoD标准（过度工程）
- ❌ 测试依赖执行顺序（应该独立）

---

### Green Phase：实现功能

- [ ] **按测试接口实现**（不要改接口！）
- [ ] 检查测试中的函数签名：
  - 参数名称
  - 参数顺序
  - 返回值类型
- [ ] 实现最简单的让测试通过的代码
- [ ] 运行测试（应该通过：Green）

**关键原则**：
- ✅ 实现必须**完全匹配**测试接口（Feature 2.2: 40%失败是接口不匹配）
- ✅ 不要"优化"测试接口（先让Green，再Refactor）
- ✅ 如果接口不合理，先修改测试，再实现

**常见陷阱**：
- ❌ 实现时"顺手"改了参数顺序
- ❌ 觉得接口不好就直接改（应该先改测试）
- ❌ 实现比测试要求的复杂（YAGNI违反）

---

### Refactor Phase：重构

- [ ] 消除代码重复（DRY）
- [ ] 提取公共函数/类
- [ ] 优化命名和结构
- [ ] 运行测试（仍然通过：保持Green）
- [ ] 代码格式化：`uv run poe format`
- [ ] 类型检查：`uv run poe type-check`

**何时跳过Refactor**：
- ✅ MVP阶段，代码量小
- ✅ 第一次实现，还看不出重复模式
- ❌ 已经看到明显重复（必须重构）

---

### Cycle完成检查（Checkpoint 2）

- [ ] 所有测试通过（`uv run poe test`）
- [ ] 代码格式化和类型检查通过
- [ ] 每个新函数/类都有对应测试
- [ ] 每个新测试都映射到DoD标准

**发现问题 → 修复问题 → 重新检查（不要带着问题进入下一Cycle）**

---

## 📋 Phase 3: Git提交流程

### 本地开发分支

- [ ] 检查当前分支：`git branch`（不应该在main/master）
- [ ] 如果在main → 创建feature分支：`git checkout -b feature/story-X.X-xxx`
- [ ] 查看变更：`git status`
- [ ] 查看diff：`git diff`

**分支命名**：
- `feature/story-X.X-description`：新功能
- `fix/issue-description`：Bug修复
- `docs/description`：纯文档变更
- `refactor/description`：重构

---

### 提交代码

- [ ] 暂存变更：`git add <files>`
- [ ] **写有意义的commit message**：
  ```
  type: 简短描述（50字内）

  - 详细说明1
  - 详细说明2

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
- [ ] Commit类型：
  - `feat:` 新功能
  - `fix:` Bug修复
  - `docs:` 文档变更
  - `refactor:` 重构
  - `test:` 测试相关
  - `chore:` 构建/工具变更

**常见陷阱**：
- ❌ Commit message太简单："fix", "update"
- ❌ 一个Commit包含多个不相关变更
- ❌ 忘记运行format/type-check就提交

---

### 合并到develop

- [ ] 切换到develop：`git checkout develop`
- [ ] 拉取最新：`git pull origin develop`
- [ ] 合并feature分支：`git merge feature/story-X.X-xxx`
- [ ] 解决冲突（如果有）
- [ ] 运行测试：`uv run poe test`
- [ ] 推送：`git push origin develop`

**何时推送到远程**：
- ✅ Story Cycle完成
- ✅ 需要备份代码
- ✅ 需要CI/CD运行
- ❌ 代码未测试（不要推送broken code）

---

## 📋 Phase 4: Story完成

### Story级验收

- [ ] 所有Cycle完成
- [ ] 所有测试通过
- [ ] 覆盖率达标（核心 ≥90%, 整体 ≥85%）
- [ ] 所有DoD标准满足
- [ ] 代码已合并到develop

---

### 创建Story完成总结

- [ ] 创建：`docs/development/sprints/current/story-X.X-completion-summary.md`
- [ ] 记录：
  - 实际工作量 vs 估算
  - 遇到的问题和解决方案
  - 技术债务（如果有）
  - 经验教训

**常见陷阱**：
- ❌ 跳过completion summary（经验丢失）
- ❌ 只记录成功，不记录问题（无法改进）

---

## 📋 Phase 5: Sprint完成和文档整理

⚠️ **重要提醒**: Sprint 结束时必须完成两个整理环节：
1. **_inbox/ 整理** - 提炼临时笔记为长期知识（30-45分钟）
2. **5S6A 归档** - 归档工作区文档（30分钟）

**不整理的后果**：
- _inbox/ 堆积大量文件，无法区分有价值笔记
- 临时想法丢失，重复踩坑
- 知识无法沉淀，经验无法传承

---

### Sprint Review和Retrospective

- [ ] Sprint Review：演示完成的Story
- [ ] Sprint Retrospective：
  - 做得好的地方
  - 需要改进的地方
  - 行动项
  - 经验教训

---

### _inbox/ 整理流程（批量处理临时笔记）

**目标**: 将 Sprint 执行中的临时笔记提炼为长期知识，清空 _inbox/

**预期时间**: 30-45分钟/Sprint

---

#### Step 1: 列出所有临时笔记

```bash
# 查看_inbox目录内容
ls -1 docs/development/sprints/current/_inbox/

# 统计文件数量
ls -1 docs/development/sprints/current/_inbox/ | wc -l
# 预期：<30个文件/Sprint（如果>50个，说明记录过于碎片化）
```

- [ ] 列出所有 _inbox/ 文件
- [ ] 检查文件数量（预期 <30个/Sprint）

---

#### Step 2: 逐个文件决策归宿

**决策树（对每个文件）**：

```
1. 是否有长期价值？
   ├─ NO → 删除（临时协调笔记、过时讨论）
   └─ YES → 继续判断

2. 价值类型是什么？
   ├─ 架构决策
   │  └─ 提炼为 ADR → docs/architecture/adrs/
   │
   ├─ 开发教训
   │  └─ 提炼为 Lesson → docs/knowledge/lessons-learned/
   │
   ├─ 技术研究
   │  └─ 整理为 Research → docs/knowledge/research/
   │
   ├─ 未来想法
   │  └─ 移动到 → docs/product/backlog/future-ideas/
   │
   ├─ 重要讨论记录
   │  └─ 保留到 → completed/sprint-XXX/_discussions/（可选）
   │
   └─ 个人跨项目笔记
      └─ 移动到个人管理系统（不在项目仓库）

3. 需要重写吗？
   ├─ 需要 → 使用模板创建正式文档，删除原始笔记
   └─ 不需要 → 直接移动并重命名
```

---

#### Step 3: 操作示例（Checklist）

**案例 1: 架构决策**

```bash
# 文件：20251115-pydantic-performance-discussion.md
# 内容：讨论了Pydantic vs dataclass性能差异和选型理由

# 判断：有长期价值 + 架构决策
# 操作：提炼为ADR

# 1. 使用ADR模板
cp docs/templates/adr-template.md \
   docs/architecture/adrs/003-pydantic-validation.md

# 2. 从原始笔记提炼内容填入ADR
# （手动编辑003-pydantic-validation.md）

# 3. 删除原始笔记
rm docs/development/sprints/current/_inbox/20251115-pydantic-performance-discussion.md
```

- [ ] 提炼为 ADR（如有架构决策讨论）

---

**案例 2: 开发教训**

```bash
# 文件：20251116-feature2.2-test-failure-investigation.md
# 内容：40%测试失败的调查过程和根因分析

# 判断：有长期价值 + 开发教训
# 操作：提炼为Lesson文档

# 1. 移动并重命名
mv docs/development/sprints/current/_inbox/20251116-feature2.2-test-failure-investigation.md \
   docs/knowledge/lessons-learned/2025-11-feature2.2-test-failures.md

# 2. 编辑格式化（添加标题、整理结构）
# （手动编辑文档，使其结构清晰）

# 3. 更新lessons-learned/index.md
# （可选：添加到索引中，按标签分类）
```

- [ ] 提炼为 Lesson（如有踩坑经验）

---

**案例 3: 技术研究**

```bash
# 文件：20251117-got-event-sourcing-research.md
# 内容：调研了GoT引擎的事件溯源方案

# 判断：有长期价值 + 技术研究
# 操作：整理为Research文档

mv docs/development/sprints/current/_inbox/20251117-got-event-sourcing-research.md \
   docs/knowledge/research/got-event-sourcing-analysis.md

# 编辑格式化
```

- [ ] 整理为 Research（如有技术调研）

---

**案例 4: 未来想法**

```bash
# 文件：20251114-epic-003-actor-model-idea.md
# 内容：Epic 003可以考虑Actor模型实现并发

# 判断：有长期价值 + 未来想法
# 操作：移动到产品backlog

mv docs/development/sprints/current/_inbox/20251114-epic-003-actor-model-idea.md \
   docs/product/backlog/future-ideas/epic-003-actor-model.md
```

- [ ] 移动到 future-ideas（如有未来想法）

---

**案例 5: 个人笔记**

```bash
# 文件：20251118-cross-project-refactor-pattern.md
# 内容：这个重构模式可以用到我的CyanEagle项目

# 判断：有价值，但不属于本项目
# 操作：移动到个人管理系统

# 移动到个人笔记目录（项目仓库外）
mv docs/development/sprints/current/_inbox/20251118-cross-project-refactor-pattern.md \
   ~/Documents/PersonalNotes/
```

- [ ] 移动到个人管理（如为跨项目笔记）

---

**案例 6: 临时笔记（删除）**

```bash
# 文件：20251119-standup-meeting-notes.md
# 内容：每日站会的进度同步

# 判断：无长期价值（问题已解决，笔记过时）
# 操作：删除

rm docs/development/sprints/current/_inbox/20251119-standup-meeting-notes.md
```

- [ ] 删除无价值笔记

---

#### Step 4: 验证 _inbox/ 清空

```bash
# 检查_inbox是否清空
ls docs/development/sprints/current/_inbox/

# 预期结果：空目录，或只有新Sprint的笔记
```

- [ ] 确认 _inbox/ 已清空
- [ ] knowledge/ 已更新（新增 Lesson/Research）
- [ ] architecture/adrs/ 已更新（如有新 ADR）
- [ ] product/backlog/future-ideas/ 已更新（如有新想法）

---

### 5S6A文档整理（关键！）

**参考**：`docs/development/tasks/docs-5s6a-analysis.md`

#### 1️⃣ Seiri（整理）- 识别需要归档的文档

- [ ] 列出current/目录所有文件：`ls docs/development/sprints/current/`
- [ ] 识别已完成Story文档（查看Story状态）
- [ ] 识别已完成Phase文档（查看Epic README）

---

#### 2️⃣ Seiton（整顿）- 归档到正确位置

**已完成Story文档**：
```bash
# 为本Sprint创建completed目录
mkdir -p docs/development/sprints/completed/sprint-XXX

# 移动Story文档
git mv docs/development/sprints/current/story-X.X-tdd-plan.md \
       docs/development/sprints/completed/sprint-XXX/

git mv docs/development/sprints/current/story-X.X-completion-summary.md \
       docs/development/sprints/completed/sprint-XXX/
```

**已完成Phase文档**：
```bash
# 创建archive目录（按年月）
mkdir -p docs/archive/YYYY-MM/phase-X

# 移动Phase相关文档
git mv docs/development/sprints/current/story-X.X-tdd-plan.md \
       docs/archive/YYYY-MM/phase-X/
```

**分析文档**：
```bash
# 移动到knowledge/research/
git mv docs/knowledge/xxx-analysis.md \
       docs/knowledge/research/
```

---

#### 3️⃣ Seiso（清扫）- 清理临时文件

- [ ] 检查根目录：`ls -la | grep -E "test|temp|debug"`
- [ ] 删除临时目录：`rm -rf backend/ temp/ debug/`
- [ ] 检查未跟踪文件：`git status --short | grep "^??"`

---

#### 4️⃣ Seiketsu（清洁）- 检查规范

**命名规范检查**：
```bash
# 检查是否有feature-命名（应该是story-）
find docs/development/sprints/current -name "feature-*.md"

# 检查knowledge/目录结构
tree docs/knowledge -L 2
```

- [ ] 所有Story文档使用`story-X.X-xxx.md`格式
- [ ] knowledge/使用二级目录（research/, lessons-learned/）
- [ ] 无临时测试文件在根目录

---

#### 5️⃣ Shitsuke（素养）- 提交整理结果

```bash
# 查看整理变更
git status

# 提交整理
git add .
git commit -m "docs: Sprint-XXX 5S6A文档整理

- 归档已完成Story文档到completed/sprint-XXX/
- 移动Phase-X文档到archive/YYYY-MM/
- 规范knowledge/目录结构
- 清理临时测试文件
"
```

---

#### 6️⃣ Audit（审计）- 验证整理效果

**审计检查清单**：
```bash
# 1. current/目录应该只有活跃Story（下一Sprint的）
ls docs/development/sprints/current/
# 预期：<10个文件

# 2. completed/目录包含本Sprint文档
ls docs/development/sprints/completed/sprint-XXX/
# 预期：本Sprint的所有Story文档

# 3. archive/目录包含已完成Phase
ls docs/archive/YYYY-MM/
# 预期：phase-X/目录

# 4. knowledge/目录结构规范
tree docs/knowledge -L 2
# 预期：research/, lessons-learned/

# 5. 无未跟踪临时文件
git status --short | grep "^??"
# 预期：只有新的合法文档（如果有）
```

- [ ] 所有检查通过
- [ ] 文档查找测试：能在30秒内找到任何Story文档

---

## 📋 Phase 6: 下一Sprint准备

### 创建下一Sprint

- [ ] 使用模板：`cp docs/templates/sprint-template.md docs/development/sprints/current/sprint-XXX.md`
- [ ] 移动未完成Story到下一Sprint Backlog
- [ ] 更新Epic README进度
- [ ] 更新ACTION_PLAN.md

---

## 🔍 关键检查点总结

### Checkpoint 1: 开发前（防止过度工程）
**问题**：这是哪个Story的哪个Cycle？测试验证哪个DoD？
**无法回答 → STOP**

### Checkpoint 2: 测试前（防止接口不匹配）
**问题**：测试接口（参数名/顺序）是否和Story一致？
**不一致 → 先改测试，再实现**

### Checkpoint 3: 提交前（防止代码质量问题）
```bash
uv run poe format      # 必须通过
uv run poe type-check  # 必须通过
uv run poe test        # 必须通过
```

### Checkpoint 4: Story完成前（防止遗漏）
**问题**：所有DoD标准都满足了吗？
**有遗漏 → 补充测试或实现**

### Checkpoint 5: Sprint完成前（防止文档混乱）
**问题**：执行5S6A整理了吗？
**没有 → 按checklist执行（30分钟）**

---

## 📊 工作流指标

### 时间估算（单人开发）

| 阶段 | 活动 | 时间 |
|------|------|------|
| 规划 | Epic拆分 + Story TDD计划 | 0.5-1天/Story |
| 开发 | TDD Cycle（Red-Green-Refactor） | 0.5-1天/Cycle |
| 提交 | Git commit + merge | 5-10分钟 |
| 完成 | Story summary | 15-30分钟 |
| 整理 | 5S6A文档整理 | 30分钟/Sprint |

### 质量指标

| 指标 | 目标 | 实际（Phase 0-2） |
|------|------|------------------|
| 测试覆盖率 | ≥85% | Story 1.1: 100%, Story 0.2: 95% |
| 首次测试通过率 | ≥80% | Story 1.1: 100%, Feature 2.2: 20%（教训！） |
| 文档命名规范符合率 | 100% | 整理前: 85%, 整理后: 100% |
| Sprint文档归档及时率 | 100% | Phase 0延迟（已改进） |

---

## 🚨 常见错误和教训

### Feature 2.2的教训（89%测试失败）

**根本原因**：
1. ❌ 测试未映射到DoD标准（40%失败）
2. ❌ 实现接口与测试不匹配（40%失败）
3. ❌ 因为有fixture就写测试（20%失败）

**预防措施**：
- ✅ Checkpoint 1: 开发前必须确认DoD映射
- ✅ Checkpoint 2: 测试前必须确认接口一致
- ✅ 只基于Story TDD Plan写测试，不基于fixture

---

### Phase 0文档归档延迟

**问题**：Phase 0完成后，文档滞留在current/目录

**解决方案**：
- ✅ Sprint模板添加5S6A提醒
- ✅ Definition of Done添加文档归档标准
- ✅ 创建docs-5s6a-analysis.md详细指南

---

### 命名规范不一致

**问题**：feature-2.X 和 story-2.X 混用

**解决方案**：
- ✅ 统一使用story-X.X命名
- ✅ .structure.md明确规范
- ✅ 5S6A整理时检查

---

## 📚 参考文档

### 规范文档
- [文档组织结构规范](../../.structure.md)
- [Definition of Done](./definition-of-done.md)
- [TDD重构指南](../../testing/standards/tdd-refactoring-guidelines.md)
- [Git工作流](../git-workflow.md)

### 模板文档
- [Epic模板](../../templates/epic-template.md)
- [Story TDD计划模板](../../templates/story-tdd-plan-template.md)
- [Sprint模板](../../templates/sprint-template.md)
- [BDD测试模板](../../templates/bdd-test-template.md)

### 分析文档
- [5S6A整理分析](../tasks/docs-5s6a-analysis.md)
- [Feature 2.2 Critical Analysis](../../knowledge/research/critical-analysis-feature-2.2.md)
- [基准测试策略](../../knowledge/research/baseline-testing-strategy.md)

---

## 🎯 下一步优化方向

### 已验证有效（继续保持）
- ✅ TDD Red-Green-Refactor循环
- ✅ Story TDD Plan强制映射DoD
- ✅ 5S6A定期文档整理
- ✅ Checkpoint机制防止错误

### 待验证改进（Phase 2实施）
- ⏭️ BDD场景驱动TDD（Story 2.2试点）
- ⏭️ 通用基准测试框架（Story 2.4）
- ⏭️ Patch-First架构模式（Story 2.2）

### 不做（避免过度工程）
- ❌ docs-lint自动化脚本
- ❌ pre-commit hooks验证
- ❌ 复杂的工作流管理系统

---

**创建日期**: 2025-11-07
**维护者**: EvolvAI Team
**基于**: Phase 0-2 实际执行经验
**下次更新**: Phase 2完成后（2025-11-19）