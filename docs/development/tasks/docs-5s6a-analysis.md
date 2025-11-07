# docs/ 目录5S6A整理分析

**分析日期**: 2025-11-07
**分析方法**: 5S6A精益管理原则
**参照标准**: docs/.structure.md v1.0

---

## 🎯 6A框架分析

### 1️⃣ Aim (目标)

**整理目标**:
- 符合docs/.structure.md规范要求
- 清晰的文档层级和命名
- 及时归档已完成的Story/Phase文档
- 减少查找时间，提高文档可维护性

**成功标准**:
- ✅ 所有命名符合规范（无feature-X.X，统一story-X.X）
- ✅ 已完成Story文档移至completed/
- ✅ 已完成Phase文档移至archive/
- ✅ knowledge/目录结构清晰（analysis → research/）
- ✅ 无冗余或错误目录

---

### 2️⃣ Analyze (分析)

#### 📊 当前状态 vs 规范要求

**1. 命名不一致问题**

| 实际文件 | 规范要求 | 问题 |
|---------|---------|------|
| `feature-2.1-safe-search-tdd-plan.md` | `story-2.1-tdd-plan.md` | Feature vs Story混用 |
| `feature-2.3-safe-exec-tdd-plan.md` | `story-2.3-tdd-plan.md` | Feature vs Story混用 |

**根因**: Phase 2文档创建时未遵循Story命名规范

---

**2. 未归档的已完成文档**

| 文件位置 | 状态 | 应该在 |
|---------|------|--------|
| `sprints/current/story-0.1-tdd-plan.md` | Phase 0 完成 (2025-10-28) | `archive/2025-10/phase-0/` |
| `sprints/current/story-0.2-tdd-plan.md` | Phase 0 完成 (2025-10-28) | `archive/2025-10/phase-0/` |
| `sprints/current/story-0.3-tdd-plan.md` | Phase 0 完成 (2025-10-28) | `archive/2025-10/phase-0/` |
| `archive/2025-10/phase-0-completion-report.md` | ✅ 已归档 | 正确位置 |

**根因**: Phase 0完成后未执行文档归档流程

---

**3. 目录结构问题**

```
实际:
docs/knowledge/
├── critical-analysis-feature-2.2.md          # ❌ 应该在research/
├── preventive-analysis-safe-search.md        # ❌ 应该在research/
└── research/
    ├── baseline-testing-strategy.md          # ✅ 正确
    ├── gpt5-lesson-guard-discussion.md       # ✅ 正确
    └── ...

规范:
docs/knowledge/
├── research/                                  # 研究和分析文档
│   ├── critical-analysis-feature-2.2.md
│   ├── preventive-analysis-safe-search.md
│   └── baseline-testing-strategy.md
└── lessons-learned/                           # 经验教训
    └── sprint-retrospectives/
```

**根因**: 创建时未遵循规范的二级目录结构

---

**4. Git未跟踪文件**

```bash
Untracked files:
  backend/                                      # ❌ 不应该在docs/下
  docs/knowledge/research/gpt5-lesson-guard-discussion.md
  docs/knowledge/research/reflection-as-product-feature.md
  docs/product/definition/evolvai-positioning-with-lesson-guard.md
  docs/product/epics/epic-001-behavior-constraints/decision-lesson-guard-positioning.md
  docs/product/roadmap/single-person-reality-check.md
  docs/templates/bdd-test-template.md
  docs/templates/story-tdd-plan-template.md
```

**问题分析**:
- `backend/` 目录: 错误创建，应该删除或移到项目根目录外
- research/文档: 新创建但未提交
- 模板文件: 新创建但未提交

---

**5. Sprint/Story文档完整性检查**

| Story | TDD Plan | Completion Summary | 状态 |
|-------|----------|-------------------|------|
| Story 0.1 | ✅ current/ | ❌ 缺失 | Phase 0完成，应归档 |
| Story 0.2 | ✅ current/ | ❌ 缺失 | Phase 0完成，应归档 |
| Story 0.3 | ✅ current/ | ❌ 缺失 | Phase 0完成，应归档 |
| Story 1.1 | ✅ completed/sprint-001/ | ✅ completed/sprint-001/ | ✅ 正确归档 |
| Story 1.2 | ✅ current/ | ❌ 缺失 | 进行中 |
| Story 1.3 | ✅ current/ | ❌ 缺失 | 计划中 |

---

### 3️⃣ Arrange (整理方案)

#### 📋 整理任务清单

**Priority 1: 命名规范化** (5分钟)
```bash
# 重命名Feature → Story
git mv docs/development/sprints/current/feature-2.1-safe-search-tdd-plan.md \
       docs/development/sprints/current/story-2.1-tdd-plan.md

git mv docs/development/sprints/current/feature-2.3-safe-exec-tdd-plan.md \
       docs/development/sprints/current/story-2.3-tdd-plan.md
```

**Priority 2: 归档Phase 0文档** (10分钟)
```bash
# 创建Phase 0归档目录
mkdir -p docs/archive/2025-10/phase-0

# 移动Phase 0 Story文档
git mv docs/development/sprints/current/story-0.1-tdd-plan.md \
       docs/archive/2025-10/phase-0/

git mv docs/development/sprints/current/story-0.2-tdd-plan.md \
       docs/archive/2025-10/phase-0/

git mv docs/development/sprints/current/story-0.3-tdd-plan.md \
       docs/archive/2025-10/phase-0/

# phase-0-completion-report.md 已经在正确位置
```

**Priority 3: 重组knowledge/目录** (5分钟)
```bash
# 移动分析文档到research/
git mv docs/knowledge/critical-analysis-feature-2.2.md \
       docs/knowledge/research/critical-analysis-feature-2.2.md

git mv docs/knowledge/preventive-analysis-safe-search.md \
       docs/knowledge/research/preventive-analysis-safe-search.md
```

**Priority 4: 处理未跟踪文件** (10分钟)
```bash
# 检查backend/目录（可能是误创建）
ls -la backend/
# 如果不需要: rm -rf backend/

# 提交新的research文档和模板
git add docs/knowledge/research/gpt5-lesson-guard-discussion.md
git add docs/knowledge/research/reflection-as-product-feature.md
git add docs/product/definition/evolvai-positioning-with-lesson-guard.md
git add docs/product/epics/epic-001-behavior-constraints/decision-lesson-guard-positioning.md
git add docs/product/roadmap/single-person-reality-check.md
git add docs/templates/bdd-test-template.md
git add docs/templates/story-tdd-plan-template.md
```

**Priority 5: 创建缺失的Completion Summary** (可选，15分钟)
```bash
# 为Phase 0 Stories创建简单的completion summary
# 或者在Phase 0归档时添加统一的phase-0-stories-summary.md
```

---

### 4️⃣ Act (执行)

**执行顺序**:
1. ✅ Priority 1: 命名规范化（影响最小，立即执行）
2. ✅ Priority 2: 归档Phase 0（清理current/目录）
3. ✅ Priority 3: 重组knowledge/（规范目录结构）
4. ⚠️ Priority 4: 处理未跟踪文件（需要确认backend/）
5. ⏭️ Priority 5: 补充文档（可延后）

**执行时间**: 约30分钟

---

### 5️⃣ Audit (审计)

**审计检查表**:
- [ ] 所有文件命名符合docs/.structure.md规范
- [ ] current/目录只包含活跃的Story文档
- [ ] completed/目录包含近期完成的Sprint文档
- [ ] archive/按年月组织历史文档
- [ ] knowledge/目录使用二级分类（research/, lessons-learned/）
- [ ] 无冗余或错误的目录
- [ ] 所有新文档已提交到git

**审计工具**:
```bash
# 检查命名规范
find docs/development/sprints/current -name "feature-*.md"

# 检查未归档文档
grep -r "Phase 0" docs/development/sprints/current/

# 检查未跟踪文件
git status --short | grep "^??"

# 检查目录结构
tree docs -L 3 -I '__pycache__|*.pyc'
```

---

### 6️⃣ Advance (改进)

**持续改进措施**:

1. **文档生命周期自动化**
   - 创建git hooks检查文档命名
   - Sprint完成时自动提醒归档

2. **文档质量检查**
   - 添加docs-lint脚本检查规范
   - CI/CD集成文档结构验证

3. **模板强制使用**
   - 更新CLAUDE.md明确要求使用模板
   - 添加模板检查到PR review

4. **定期维护提醒**
   - 每周检查current/目录
   - 每月归档completed/到archive/

---

## 📊 5S分析

### 1S: Seiri (整理/Sort)

**需要保留**:
- ✅ 活跃的Story文档（1.2, 1.3, 2.2）
- ✅ Phase 1实施计划
- ✅ 所有templates/
- ✅ 所有product/epics/

**需要移除/归档**:
- ❌ Phase 0 Story文档 → archive/2025-10/phase-0/
- ❌ backend/目录 → 删除或移到项目根外
- ❌ documentation-review-2025-10-27.md → archive/2025-10/

### 2S: Seiton (整顿/Set in order)

**有序放置规则**:
- 📂 **sprints/current/** - 只放活跃Story（Phase 1+）
- 📂 **sprints/completed/** - 近1-3个月完成的Sprint
- 📂 **archive/** - 3个月前的历史文档
- 📂 **knowledge/research/** - 所有研究分析文档

### 3S: Seiso (清扫/Shine)

**清洁检查**:
- 🧹 删除backend/目录（误创建）
- 🧹 移除重复文档
- 🧹 统一文件命名格式

### 4S: Seiketsu (清洁/Standardize)

**标准化措施**:
- 📏 强制使用docs/.structure.md规范
- 📏 Story命名: story-{phase}.{number}-tdd-plan.md
- 📏 归档规则: 完成后7天内归档

### 5S: Shitsuke (素养/Sustain)

**维持机制**:
- 🔄 每周Sprint会议检查文档状态
- 🔄 Story完成时立即创建completion summary
- 🔄 Phase完成后统一归档
- 🔄 使用docs-lint工具自动检查

---

## 🎯 立即行动项

### 今日必做 (30分钟)
1. ✅ 重命名feature-2.x → story-2.x
2. ✅ 归档Phase 0文档到archive/2025-10/phase-0/
3. ✅ 移动analysis文档到knowledge/research/
4. ⚠️ 检查并处理backend/目录

### 本周待办
- [ ] 为Phase 0创建统一的stories-summary.md
- [ ] 提交所有未跟踪的新文档
- [ ] 创建docs-lint脚本
- [ ] 更新CLAUDE.md增强文档规范要求

### 长期改进
- [ ] 添加git hooks验证文档命名
- [ ] CI/CD集成文档结构检查
- [ ] 创建文档归档自动化脚本

---

## 📝 执行记录

**执行人**: Claude + User
**执行日期**: 2025-11-07
**执行状态**: 🟡 待执行

**预期效果**:
- 文档查找时间减少50%
- 文档命名100%符合规范
- current/目录文件数减少40%
- 新团队成员文档导航效率提升

---

**参考文档**:
- [文档组织结构规范](../../../.structure.md)
- [GitFlow工作流](../../standards/git-workflow.md)
- [文档模板集](../../../templates/)
