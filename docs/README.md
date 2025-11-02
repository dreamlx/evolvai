# EvolvAI 文档中心

**版本**: 1.0
**更新日期**: 2025-10-27
**项目状态**: ✅ MVP实施阶段

---

## 🎯 快速导航

### 🚀 新手入门
- 想了解项目定位？→ [产品定义](./product/definition/product-definition-v1.md)
- 想看讨论总结？→ [讨论总结](./product/definition/discussion-summary-2025-10-26.md)
- 想了解产品路线图？→ [路线图](./product/roadmap/)
- 想创建新文档？→ [文档模板](./templates/)

### 📋 产品团队
- **产品定义**: [product/definition/](./product/definition/)
- **产品路线图**: [product/roadmap/](./product/roadmap/)
- **Epic管理**: [product/epics/](./product/epics/)
- **产品规格**: [product/specs/](./product/specs/)

### 🏗️ 开发团队
- **当前Sprint**: [development/sprints/current/](./development/sprints/current/)
- **任务管理**: [development/tasks/](./development/tasks/)
- **架构文档**: [development/architecture/](./development/architecture/)
- **开发规范**: [development/standards/](./development/standards/)

### 🧪 测试团队
- **测试计划**: [testing/plans/](./testing/plans/)
- **测试标准**: [testing/standards/](./testing/standards/)
- **性能基准**: [testing/benchmarks/](./testing/benchmarks/)
- **测试报告**: [testing/reports/](./testing/reports/)

### 📚 知识管理
- **技术研究**: [knowledge/research/](./knowledge/research/)
- **经验总结**: [knowledge/lessons-learned/](./knowledge/lessons-learned/)

---

## 📚 核心文档索引

### 产品定义文档
| 文档 | 描述 | 状态 |
|------|------|------|
| [产品定义 v1.0](./product/definition/product-definition-v1.md) | 完整产品定义，包含定位、架构、路线图 | ✅ APPROVED |
| [讨论总结](./product/definition/discussion-summary-2025-10-26.md) | 2025-10-26项目讨论成果总结 | ✅ APPROVED |

### Epic和Feature文档
| 文档 | 描述 | 状态 |
|------|------|------|
| [Epic-003: Graph-of-Thought引擎](./product/epics/epic-003-graph-of-thought/README.md) | **思维层**约束（并行推理、可验证计划） | ✅ ACTIVE |
| [Epic-001: 行为约束系统](./product/epics/epic-001-behavior-constraints/README.md) | **执行层**约束（safe_search, safe_edit） | ✅ ACTIVE |
| [Epic-002: 项目规范即服务](./product/epics/epic-002-project-standards/README.md) | **规范层**约束（文档位置、结构、原则） | ✅ ACTIVE |
| [三Epic关系分析](./product/roadmap/three-epics-relationship.md) | 三层架构协作与TPST累加效应 | ✅ APPROVED |
| [Feature-001: ExecutionPlan Schema](./product/epics/epic-001-behavior-constraints/feature-001-execution-plan.md) | Epic-001核心Schema定义 | ✅ IN_PROGRESS |
| [Story-001: ExecutionPlan核心Schema](./product/epics/epic-001-behavior-constraints/story-001-execution-plan-schema.md) | ExecutionPlan详细实现 | ✅ IN_PROGRESS |

### 技术架构文档
| 文档 | 描述 | 状态 |
|------|------|------|
| [行为工程架构](./development/architecture/behavior-engineering.md) | 行为约束系统架构设计 | 🔄 TODO |
| [Project Standards MCP Service](./development/architecture/project-standards-mcp-service.md) | 项目规范MCP服务技术架构 | ✅ DRAFT |
| [ADR-001: Patch-First](./development/architecture/adrs/001-patch-first.md) | Patch-First架构决策记录 | 🔄 TODO |
| [ADR-002: Git Worktree](./development/architecture/adrs/002-git-worktree.md) | Git Worktree策略决策记录 | 🔄 TODO |
| [ADR-003: TPST指标](./development/architecture/adrs/003-tpst-metrics.md) | TPST指标体系决策记录 | 🔄 TODO |

### Sprint文档
| Sprint | 描述 | 状态 |
|--------|------|------|
| [并行开发分析](./development/sprints/parallel-development-analysis.md) | Epic-001 & Epic-002并行开发可行性 | ✅ APPROVED |
| [Sprint 001](./development/sprints/current/sprint-001-mvp-week1.md) | MVP Week 1 - 核心约束层 | 🔄 TODO |
| [Sprint 002](./development/sprints/current/sprint-002-mvp-week2.md) | MVP Week 2 - MCP集成演示 | 🔄 TODO |

---

## 📝 文档规范

### 必读文档
1. **[文档组织结构](./.structure.md)** - 文档目录规范和命名约定
2. **[文档模板](./templates/)** - 标准化文档模板
3. **[CLAUDE.md](../CLAUDE.md)** - AI助手遵守规则

### 文档状态标记
| 标记 | 含义 | 使用场景 |
|------|------|----------|
| `[DRAFT]` | 草稿 | 文档初创阶段 |
| `[REVIEW]` | 审查中 | 等待团队审查 |
| `[APPROVED]` | 已批准 | 正式批准使用 |
| `[ACTIVE]` | 活跃使用 | 正在使用的文档 |
| `[DEPRECATED]` | 已废弃 | 不再推荐使用 |
| `[ARCHIVED]` | 已归档 | 已移至archive/ |

### 文档命名规范
```
Epic:    epic-{编号}-{名称}/
Feature: feature-{编号}-{名称}.md
Story:   story-{编号}-{描述}.md
Task:    task-{编号}.{子编号}-{描述}.md
ADR:     {编号}-{决策标题}.md
Sprint:  sprint-{编号}-{描述}.md
```

---

## 🔄 文档工作流

### 创建新文档
```bash
# 1. 选择合适的模板
cd docs/templates/

# 2. 复制到目标位置
cp epic-template.md ../product/epics/epic-003-new-feature/README.md

# 3. 填写内容
# 替换所有{占位符}
# 更新状态为[DRAFT]

# 4. 提交审查
git add .
git commit -m "docs: add epic-003 draft"
```

### 更新现有文档
```bash
# 1. 修改文档内容
# 2. 更新状态标记
# 3. 更新"最后更新"日期
# 4. 提交变更
git commit -m "docs: update epic-001 status to ACTIVE"
```

### 归档文档
```bash
# 1. 标记文档为[ARCHIVED]
# 2. 移动到archive/{年月}/
mv docs/product/epics/epic-001/ docs/archive/2025-10/
# 3. 更新相关链接
# 4. 提交归档变更
git commit -m "docs: archive epic-001 (completed)"
```

---

## 🎯 MVP阶段文档计划

### Week 1 (核心约束层)
- [ ] Epic-001: 行为约束系统
- [ ] Story-001: ExecutionPlan Schema
- [ ] Story-002: safe_search包装器
- [ ] Story-003: safe_edit Patch-First
- [ ] ADR-001: Patch-First架构
- [ ] ADR-002: Git Worktree策略

### Week 2 (MCP集成演示)
- [ ] Epic-002: MCP集成
- [ ] Story-004: MCP服务端点
- [ ] Story-005: TPST审计系统
- [ ] Story-006: 英雄场景演示
- [ ] ADR-003: TPST指标体系
- [ ] Sprint-001 Retrospective

---

## 📊 文档统计

### 当前文档统计
- ✅ 产品定义文档: 2篇
- ✅ 模板文档: 6篇 (epic, feature✅, story, task✅, adr, sprint)
- ✅ Epic文档: 3篇 (Epic-003思维层, Epic-001执行层, Epic-002规范层)
- ✅ 路线图分析: 1篇 (三Epic关系与协作)
- ✅ Feature文档: 1篇 (Feature-001示例)
- ✅ Story文档: 1篇 (Story-001示例)
- ✅ 架构文档: 1篇 (Project Standards MCP Service)
- ✅ 开发分析: 1篇 (并行开发分析)
- 🔄 ADR文档: 0篇 (待创建)
- 🔄 Sprint文档: 0篇 (待创建)

### 目标文档统计 (MVP完成时)
- Epic文档: 2篇
- Story文档: 6篇
- ADR文档: 3篇
- Sprint文档: 2篇
- 测试文档: 3篇

---

## 🤖 AI助手使用指南

### Claude Code必须遵守
1. **创建文档前**: 检查[.structure.md](./.structure.md)
2. **使用模板**: 从[templates/](./templates/)复制
3. **遵守命名**: 使用规范的命名约定
4. **更新索引**: 在本README中添加新文档

### 快速命令
```bash
# 查看文档结构
cat docs/.structure.md

# 列出所有模板
ls docs/templates/

# 查找特定文档
find docs/ -name "*execution*"

# 检查文档状态
grep -r "\[DRAFT\]" docs/
```

---

## 📚 相关资源

### 内部资源
- [项目README](../README.md)
- [CLAUDE.md](../CLAUDE.md)
- [开发指南](./development/standards/)

### 外部参考
- [Architecture Decision Records](https://adr.github.io/)
- [Agile Documentation Best Practices](https://www.agilealliance.org/agile101/agile-glossary/)
- [Markdown Guide](https://www.markdownguide.org/)

---

## 🤝 贡献文档

### 如何贡献
1. 遵守[.structure.md](./.structure.md)规范
2. 使用[templates/](./templates/)模板
3. 保持文档简洁清晰
4. 及时更新文档状态
5. 提交Pull Request

### 文档质量标准
- ✅ 使用清晰的标题层级
- ✅ 包含目录导航
- ✅ 链接相关文档
- ✅ 保持简洁明了
- ✅ 定期更新状态

---

## 📞 联系方式

- **维护团队**: EvolvAI Team
- **反馈渠道**: GitHub Issues
- **讨论论坛**: GitHub Discussions

---

**最后更新**: 2025-10-26
**文档版本**: 1.0
**维护者**: EvolvAI Team
