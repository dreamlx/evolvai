# Epic-005: EvolvAI 战略定位重评估

## 背景

上游 Serena 项目持续优化（231 commits），在缓存、LSP性能、符号检索等方面有显著改进。需要重新评估 EvolvAI 的差异化价值和战略定位。

## 核心发现

### 优化层次差异

| 层次 | Serena (上游) | EvolvAI |
|------|---------------|---------|
| 目标 | 执行效率 | 使用策略 |
| 优化点 | 每次调用更快 | 调用更少更精准 |
| 实现 | 缓存、LSP优化 | 约束系统、TPST |

### 差异化价值评估

| 能力 | 上游有无 | 差异化价值 | 决策 |
|------|----------|------------|------|
| 约束系统 (ExecutionPlan) | ❌ | ⭐⭐⭐ | 核心保持 |
| TPST 分析 | ❌ | ⭐⭐⭐ | 核心保持 |
| 区域检测 (Area Detection) | ❌ | ⭐⭐⭐ | 核心保持 |
| Propose/Apply 模式 | ❌ | ⭐⭐⭐ | 保持 |
| batch_edit | 部分重叠 | ⭐⭐ | 考虑重构 |

## 战略目标

### 重新定位

**从**: "AI 工具集"
**到**: "AI 工具使用策略引擎"

**核心价值主张**:
> "不是提供更多工具，而是让 AI 更聪明地使用现有工具"

### 目标成果

1. 明确 EvolvAI 与上游 Serena 的互补关系
2. 聚焦真正差异化的能力
3. 简化重叠功能，减少维护负担
4. 完善策略层文档和示例

## Features

### Feature 5.1: 约束系统可配置化

**目标**: 将约束系统作为可选功能，默认关闭，提供预设配置

**Stories**:
- [ ] Story 5.1.1: 添加 serena_config 配置项
- [ ] Story 5.1.2: 实现预设配置档位（conservative/balanced/permissive）
- [ ] Story 5.1.3: 更新文档说明使用场景

**DoD**:
- 配置项可通过 serena_config.yml 启用
- 三档预设配置可用
- 文档完整

### Feature 5.2: TPST Dashboard 集成

**目标**: 将 TPST 分析数据集成到 Dashboard

**Stories**:
- [ ] Story 5.2.1: 设计 TPST 可视化面板
- [ ] Story 5.2.2: 实现 audit_log 到 Dashboard 的数据桥接
- [ ] Story 5.2.3: 添加 token 效费比指标展示

**DoD**:
- Dashboard 可展示 TPST 数据
- 有 token 使用趋势图
- 能识别 token 浪费的工具

### Feature 5.3: batch_edit 重构评估

**目标**: 评估是否将 batch_edit 重构为 ReplaceContentTool + ExecutionPlan

**Stories**:
- [ ] Story 5.3.1: 分析 batch_edit 与 ReplaceContentTool 功能差异
- [ ] Story 5.3.2: 设计重构方案（如果决定重构）
- [ ] Story 5.3.3: 实现或保持现状（基于评估结果）

**DoD**:
- 有明确的决策记录 (ADR)
- 如重构，测试覆盖率保持
- 文档更新

### Feature 5.4: 差异化价值文档

**目标**: 撰写清晰的 EvolvAI 价值主张文档

**Stories**:
- [ ] Story 5.4.1: 撰写架构层次对比图
- [ ] Story 5.4.2: 撰写使用场景指南
- [ ] Story 5.4.3: 更新 README 和项目定位

**DoD**:
- 有清晰的架构图
- 有使用场景示例
- README 更新

## 成功指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 约束系统采用率 | 可配置 | 配置项使用统计 |
| TPST 识别效率 | 能识别 top 3 token 浪费 | Dashboard 展示 |
| 代码维护负担 | 减少 20% 重复代码 | LOC 对比 |
| 文档清晰度 | 用户理解定位 | 反馈收集 |

## 时间规划

| 阶段 | 内容 | 时间 |
|------|------|------|
| Phase 1 | Feature 5.1 约束系统配置化 | Week 1 |
| Phase 2 | Feature 5.3 batch_edit 评估 | Week 1-2 |
| Phase 3 | Feature 5.2 TPST Dashboard | Week 2-3 |
| Phase 4 | Feature 5.4 文档完善 | Week 3-4 |

## 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| 上游 API 持续变更 | 中 | 定期同步 + 兼容性测试 |
| 重构引入 bug | 中 | TDD + 高测试覆盖 |
| 用户不理解新定位 | 低 | 清晰文档 + 示例 |

## 相关资源

- [上游同步分析](../../../development/architecture/adrs/) - 待创建 ADR
- [约束系统设计](../../features/) - Epic-001 相关
- [TPST 分析设计](../../features/) - Epic-001 相关

---

**创建日期**: 2024-11-21
**状态**: Draft
**Owner**: TBD
