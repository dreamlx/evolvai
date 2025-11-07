# Sprint {编号}: {Sprint名称}

**Sprint ID**: SPRINT-{编号}
**开始日期**: YYYY-MM-DD
**结束日期**: YYYY-MM-DD
**Sprint目标**: {Sprint的核心目标}
**状态**: [PLANNING/ACTIVE/REVIEW/COMPLETED]

---

## 🎯 Sprint目标

### 主要目标
{这个Sprint要实现的主要目标}

### 成功标准
- [ ] {成功标准1}
- [ ] {成功标准2}
- [ ] {成功标准3}

---

## 📋 Sprint Backlog

### High Priority Stories
| Story ID | 描述 | 估算 | 负责人 | 状态 |
|----------|------|------|--------|------|
| STORY-{编号} | {简短描述} | {X}SP | {负责人} | [TODO/IN_PROGRESS/DONE] |

### Medium Priority Stories
| Story ID | 描述 | 估算 | 负责人 | 状态 |
|----------|------|------|--------|------|
| STORY-{编号} | {简短描述} | {X}SP | {负责人} | [TODO/IN_PROGRESS/DONE] |

### Low Priority Stories (Stretch Goals)
| Story ID | 描述 | 估算 | 负责人 | 状态 |
|----------|------|------|--------|------|
| STORY-{编号} | {简短描述} | {X}SP | {负责人} | [TODO/IN_PROGRESS/DONE] |

---

## 📊 Sprint容量

### 团队容量
- **总可用人天**: {X}人天
- **计划Story Points**: {X}SP
- **实际完成Story Points**: {X}SP
- **速率 (Velocity)**: {X}SP

### 团队成员
| 成员 | 可用时间 | 承诺Story Points |
|------|----------|------------------|
| {成员1} | {X}天 | {X}SP |
| {成员2} | {X}天 | {X}SP |

---

## 📅 每日进度

### Day 1 (YYYY-MM-DD)
**完成的工作**:
- {完成项1}
- {完成项2}

**遇到的阻塞**:
- {阻塞项1}

**下一步计划**:
- {计划项1}

### Day 2 (YYYY-MM-DD)
**完成的工作**:
- {完成项1}

**遇到的阻塞**:
- {阻塞项1}

**下一步计划**:
- {计划项1}

---

## 🛡️ 风险与问题

### 活跃风险
| 风险 | 影响 | 概率 | 对策 | 负责人 |
|------|------|------|------|--------|
| {风险描述} | H/M/L | H/M/L | {对策} | {负责人} |

### 已解决问题
| 问题 | 解决方案 | 解决日期 |
|------|----------|----------|
| {问题描述} | {解决方案} | YYYY-MM-DD |

---

## 📈 Sprint燃尽图

### Story Points燃尽
```
Day  | Remaining SP
-----|-------------
Day 1| {X}
Day 2| {X}
...  | ...
```

### 任务燃尽
```
Day  | Remaining Tasks
-----|----------------
Day 1| {X}
Day 2| {X}
...  | ...
```

---

## 🔍 Sprint Review

### Demo内容
- [ ] {Demo项1}
- [ ] {Demo项2}

### 完成的Story
- STORY-{编号}: {Story名称}
- STORY-{编号}: {Story名称}

### 未完成的Story
- STORY-{编号}: {Story名称} - {未完成原因}

### Stakeholder反馈
{Stakeholder的反馈内容}

---

## 🔄 Sprint Retrospective

### 做得好的地方 (What Went Well)
- {正面经验1}
- {正面经验2}

### 需要改进的地方 (What Could Be Improved)
- {改进点1}
- {改进点2}

### 行动项 (Action Items)
- [ ] {行动项1} - 负责人: {负责人}
- [ ] {行动项2} - 负责人: {负责人}

### 学到的经验 (Lessons Learned)
- {经验1}
- {经验2}

---

## 📊 指标总结

### 质量指标
- **测试覆盖率**: {X}%
- **Bug数量**: {X}
- **代码审查完成率**: {X}%

### 效率指标
- **计划完成率**: {X}%
- **平均Story完成时间**: {X}天
- **代码提交频率**: {X}次/天

---

## ✅ Sprint完成清单

### 代码和测试
- [ ] 所有代码已合并到develop分支
- [ ] 所有测试通过（`uv run poe test`）
- [ ] 代码格式化和类型检查通过

### 文档归档
- [ ] **🗂️ 执行5S6A文档整理**（参考：[docs-5s6a-analysis.md](../../development/tasks/docs-5s6a-analysis.md)）
  - [ ] 检查current/目录，归档已完成Story文档到completed/
  - [ ] 检查命名规范（story-X.X格式）
  - [ ] 移动分析文档到knowledge/research/
  - [ ] 清理临时测试文件
- [ ] Sprint文档移动到completed/sprint-{编号}/

### Sprint Review和Retrospective
- [ ] Sprint Review完成
- [ ] Sprint Retrospective完成
- [ ] 行动项记录到下一个Sprint

---

## 📚 相关文档

- [Sprint Planning Notes](./sprint-{编号}-planning.md)
- [Sprint Review Slides](./sprint-{编号}-review.pdf)
- [Sprint Retrospective](../../knowledge/lessons-learned/sprint-retrospectives/sprint-{编号}-retro.md)
- [5S6A文档整理指南](../../development/tasks/docs-5s6a-analysis.md)

---

**创建日期**: YYYY-MM-DD
**最后更新**: YYYY-MM-DD
**下一个Sprint**: [Sprint {编号+1}](./sprint-{编号+1}.md)
