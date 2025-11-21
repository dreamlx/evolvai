# Documentation Structure Optimization - 2025-10-28

## 背景 Context

基于与用户的深入讨论，优化了 EvolvAI 项目的文档组织结构，解决了文档分类不清、命名不统一、生命周期管理模糊等问题。

## 核心决策 Key Decisions

### 方案选择: 方案2 (Hybrid Approach)
- **决策文档组织**: 按领域就近放置 + `decision-` 前缀 + frontmatter 标记
- **理由**: Shell 友好（避免 `[]` 特殊字符），AI 可搜索，维护成本低

### 共识要点 Consensus Points
1. ✅ **TDD 计划 = 执行文档**：放在 `development/sprints/current/`
2. ✅ **development = "开发活动"**：宽泛定义，包含 sprints、architecture、standards
3. ✅ **Story 完成处理**：移动所有相关文档到 `sprints/completed/{sprint-id}/`
4. ✅ **决策文档命名**：`decision-{topic}.md` + frontmatter（type, category, status, date）

## 实施内容 Implementation

### Phase 1: .structure.md 更新 ✅
**Commit**: 229480e (325 insertions, 15 deletions)

**7 个主要改进**:
1. **目录结构详细说明** (lines 11-112)
   - `sprints/current/` 内容明确：Sprint 总览、Phase 计划、Story TDD 计划、完成总结
   - `knowledge/research/` 用途：研究和分析文档
   - 决策文档分布指南：按领域分布（product/、development/、knowledge/）

2. **命名规范扩展** (lines 152-209)
   - Decision docs: `decision-{topic}.md` + frontmatter
   - Story docs: `story-{num}-tdd-plan.md`, `story-{num}-completion-summary.md`
   - Phase docs: `phase-{num}-implementation-plan.md`, `phase-{num}-completion-report.md`

3. **Frontmatter 元数据规范** (NEW section, lines 213-263)
   - Decision metadata: type, category, status, date
   - Story metadata: epic, story, phase, status, start_date, completion_date
   - 使用场景: 搜索、统计、关联、过滤

4. **生命周期管理细化** (lines 295-345)
   - Story/Sprint/Phase/Epic/Decision 各自的归档规则
   - `completed/` (1-3 months) vs `archive/` (3+ months)
   - 永不归档列表: ADRs, decision docs, Epic READMEs, product definitions

5. **快速查找指南增强** (lines 320-335)
   - 决策文档搜索: `./scripts/find-decisions.sh` 或 find 命令
   - 研究文档路径: `docs/knowledge/research/`
   - 已完成 Story: `docs/development/sprints/completed/{sprint-id}/`

6. **AI 助手规则扩展** (lines 438-458)
   - Rule 5: 创建决策文档（prefix, frontmatter, 领域放置, 使用模板）
   - Rule 6: Story 完成处理（创建总结，移动到 completed/，更新链接）
   - Rule 7: Frontmatter 使用（必需 vs 建议字段，YAML 格式）

7. **更新版本信息**
   - 版本: 1.0 → 保持（增量改进）
   - 更新日期: 2025-10-26 → 2025-10-28

### Phase 2: 模板和工具创建 ✅

**新文件 1**: `docs/templates/decision-template.md` (956 bytes)
- Frontmatter 元数据模板
- 完整决策文档结构: Status, Context, Decision, Rationale, Alternatives, Pros/Cons, Consequences, Implementation, References
- 状态变更历史追踪

**新文件 2**: `scripts/find-decisions.sh` (executable)
- 功能: 搜索所有决策文档（decision-*.md + ADRs）
- 过滤选项:
  - `all`: 列出所有决策文档
  - `architecture|technical|product|process`: 按类别过滤
  - `approved|proposed|deprecated`: 按状态过滤
- 测试结果: ✅ 成功找到 decision-template.md + 3 个 ADRs

### Phase 3: 现有文档迁移 ✅ (User Completed)

用户已完成现有文档的迁移和规范化工作：
- ✅ 为现有决策文档添加 frontmatter
- ✅ 重命名不符合规范的文档
- ✅ 整理 sprints/completed/ 目录

## 技术细节 Technical Details

### Frontmatter Schema

**Decision Documents**:
```yaml
---
type: decision                    # 必需
category: architecture|technical|product|process  # 必需
status: proposed|approved|deprecated              # 必需
date: YYYY-MM-DD                 # 必需
decision_id: ADR-001             # 可选（ADR 必需）
supersedes: ADR-000              # 可选
related: [ADR-002, ADR-003]      # 可选
---
```

**Story Documents**:
```yaml
---
epic: epic-001-behavior-constraints    # 必需
story: story-1.1                       # 必需
phase: phase-1                         # 必需
status: planning|in-progress|completed|archived  # 必需
start_date: 2025-10-26                # 必需
completion_date: 2025-10-28           # 可选
---
```

### Shell-Friendly Design

**问题**: `[]` 方括号是 shell 特殊字符，需要转义
**解决**: 使用 `decision-` 前缀，无需转义，直接可搜索：
```bash
find docs -name "decision-*.md"     # ✅ 有效
grep -rl "category: architecture" docs/  # ✅ 有效
```

## 文档组织原则 Organization Principles

### 按领域分布 Domain-Distributed Approach
- **product/definition/**: 产品决策 (decision-tpst-as-core-metric.md)
- **development/architecture/**: 技术选型决策 (decision-pydantic-rationale.md)
- **development/standards/**: 流程决策 (decision-strict-tdd-methodology.md)
- **knowledge/research/**: 研究型决策 (decision-parallel-development.md)

### 生命周期管理 Lifecycle Management

**Active Documents** (sprints/current/):
- Sprint 总览、Phase 计划、Story TDD 计划、完成总结、每日更新

**Recent Completed** (sprints/completed/, 1-3 months):
- Sprint 及其所有 Story 文档
- 便于快速查阅近期工作

**Long-term Archive** (archive/{year-month}/, 3+ months):
- 旧的 Sprint 文档
- Phase 完成报告
- 过时的产品文档

**Never Archive** (永久保留):
- ADRs (architecture/adrs/)
- 其他决策文档（原位，更新 status）
- Epic README（原位，更新 status）
- 产品定义（原位，创建新版本）

## 使用指南 Usage Guide

### For AI Assistants

**创建决策文档**:
1. 使用模板: `cp docs/templates/decision-template.md docs/{domain}/decision-{topic}.md`
2. 填写 frontmatter（type, category, status, date）
3. 按领域就近放置（不是统一的 decisions/ 目录）

**Story 完成处理**:
1. 创建 `story-{num}-completion-summary.md`
2. 移动所有相关文档到 `sprints/completed/{sprint-id}/`
3. 包括: TDD plan, completion summary, 执行文档
4. 更新 Sprint 文档的链接

**搜索决策文档**:
```bash
# 所有决策文档
./scripts/find-decisions.sh all

# 架构决策
./scripts/find-decisions.sh architecture

# 已批准的决策
./scripts/find-decisions.sh approved

# 使用 grep 搜索特定内容
grep -rl "category: technical" docs/
```

### For Developers

**文档创建检查清单**:
- [ ] 使用正确的模板（templates/）
- [ ] 遵循命名规范（epic-, feature-, story-, decision-, phase-）
- [ ] 添加必需的 frontmatter 元数据
- [ ] 放在正确的目录（按领域，不是按类型）
- [ ] 更新状态标记 ([DRAFT], [REVIEW], [APPROVED], etc.)

**文档归档检查清单**:
- [ ] 更新文档状态（Done → Completed）
- [ ] 根据文档类型选择归档位置（completed/ vs archive/）
- [ ] 更新相关文档的链接和引用
- [ ] 对于决策文档，更新 status 字段（不要移动）

## Git 历史 Git History

```
229480e docs: Enhance documentation structure with decision document framework
fca3166 docs: Reorganize documentation structure according to .structure.md
d7723fe Merge feature/epic1-story1-plan-validator into develop
fbcbc26 docs(epic1-story1.1): Add Story 1.1 completion summary
0365ca4 feat(epic1-story1.1-cycle6): Add performance optimization and integration tests
```

## 经验教训 Lessons Learned

### What Worked Well ✅

1. **讨论驱动的设计**: 与用户充分讨论后再实施，确保方案符合实际需求
2. **Shell 友好优先**: 考虑命令行使用场景，避免特殊字符（如 `[]`）
3. **混合方案平衡**: 既保持领域分布（易维护），又提供统一标记（易搜索）
4. **Frontmatter 元数据**: 结构化元数据使得自动化工具开发变得简单
5. **渐进式实施**: Phase 1-2-3 分阶段实施，每阶段可独立验证

### Challenges and Solutions

**Challenge 1**: 决策文档组织方式（统一 vs 分布）
- **Solution**: 混合方案 - 领域分布 + decision- 前缀 + frontmatter
- **Rationale**: 平衡可维护性和可搜索性

**Challenge 2**: 文件名标记与 shell 兼容性
- **Solution**: 使用简单前缀（decision-）而非特殊字符（`[DECISION]`）
- **Rationale**: Shell 友好，无需转义，直接可用于 find/grep

**Challenge 3**: completed/ vs archive/ 区分不清
- **Solution**: 明确时间范围（1-3 months vs 3+ months）和内容类型
- **Rationale**: 近期工作需要快速访问，长期归档用于存档

### Future Improvements

1. **自动化工具**: 开发文档质量检查工具（lint-docs）
2. **文档生成**: 自动生成文档索引和关系图
3. **模板扩展**: 根据使用反馈扩展更多模板
4. **多语言支持**: 未来国际化时创建纯英文版本模板

## 影响范围 Impact

### Immediate Benefits
- ✅ 清晰的文档组织规则（AI 和开发者都能理解）
- ✅ Shell 友好的搜索和过滤（find, grep 直接可用）
- ✅ 结构化元数据支持自动化工具开发
- ✅ 明确的生命周期管理（避免文档混乱）

### Long-term Benefits
- 📈 降低文档维护成本（规则清晰，执行简单）
- 📈 提高文档可发现性（搜索脚本 + frontmatter）
- 📈 支持文档自动化（元数据驱动的工具开发）
- 📈 减少 AI 助手的 token 浪费（明确的文档位置和规则）

## References

- **Commit**: 229480e
- **Discussion Date**: 2025-10-28
- **Files Changed**: 3 (1 modified, 2 created)
- **Lines Changed**: +325 / -15
- **Status**: ✅ All Phases Complete (1, 2, 3)

---

**Created**: 2025-10-28
**Last Updated**: 2025-10-28
**Status**: [COMPLETE]
