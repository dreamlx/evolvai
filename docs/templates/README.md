# EvolvAI Documentation Templates

**版本**: 1.0
**更新日期**: 2025-10-26

---

## 📝 可用模板

### 产品管理模板
- `epic-template.md` - Epic文档模板
- `feature-template.md` - Feature文档模板 ✅
- `story-template.md` - User Story文档模板
- `task-template.md` - Task文档模板 ✅
- `sprint-template.md` - Sprint计划与总结模板

### 技术决策模板
- `adr-template.md` - Architecture Decision Record模板

### 其他模板（待添加）
- `test-plan-template.md` - 测试计划模板

---

## 🚀 使用方法

### 1. 复制模板
```bash
# 创建新Epic
cp docs/templates/epic-template.md docs/product/epics/epic-001-behavior-constraints/README.md

# 创建新Story
cp docs/templates/story-template.md docs/product/epics/epic-001/story-001-execution-plan.md

# 创建新ADR
cp docs/templates/adr-template.md docs/development/architecture/adrs/001-patch-first-architecture.md

# 创建新Sprint
cp docs/templates/sprint-template.md docs/development/sprints/current/sprint-001-mvp-week1.md
```

### 2. 填写内容
- 将所有`{占位符}`替换为实际内容
- 更新状态标记 `[DRAFT]` → `[APPROVED]` → `[ACTIVE]`
- 删除不适用的章节
- 添加项目特定的内容

### 3. 链接相关文档
- 更新相关Epic/Story/Task的链接
- 添加到产品路线图
- 关联到Sprint backlog

---

## 📋 模板使用场景

### Epic模板
**何时使用**:
- 启动新的大型功能开发
- 规划产品季度/半年路线图
- 需要跨Sprint的重大功能

**包含内容**:
- 业务价值和目标用户
- 成功指标和验收标准
- Features分解
- 时间线和里程碑
- 风险评估

### Story模板
**何时使用**:
- 分解Epic到可执行的用户故事
- 定义Sprint backlog
- 明确验收标准

**包含内容**:
- 用户故事格式
- 验收标准
- 技术任务分解
- 测试用例

### ADR模板
**何时使用**:
- 做出重要技术架构决策
- 需要记录技术权衡
- 团队需要达成共识

**包含内容**:
- 决策背景
- 考虑的方案
- 决策权衡
- 后果和度量

### Sprint模板
**何时使用**:
- Sprint计划会议
- 每日站会记录
- Sprint回顾会议

**包含内容**:
- Sprint目标
- Sprint backlog
- 每日进度
- Review和Retrospective

---

## ✅ 质量检查清单

### 创建文档时检查
- [ ] 使用了正确的模板
- [ ] 所有`{占位符}`已替换
- [ ] 状态标记正确
- [ ] 文件命名符合规范
- [ ] 文件放在正确目录
- [ ] 添加了相关文档链接

### 更新文档时检查
- [ ] 更新了状态标记
- [ ] 更新了最后修改日期
- [ ] 添加了更新说明
- [ ] 通知了相关人员

---

## 🎨 自定义模板

### 如何扩展模板
1. 复制最接近的现有模板
2. 添加项目特定的章节
3. 保持一致的格式风格
4. 更新此README文档

### 模板规范
- 使用Markdown格式
- 使用emoji增强可读性 🎯📋✅
- 保持清晰的标题层级
- 包含示例内容
- 提供填写指导

---

## 📚 参考资源

- [文档组织结构](../.structure.md)
- [GitFlow工作流](../development/standards/git-workflow.md)
- [敏捷开发流程](../development/standards/agile-workflow.md)

---

## 🤝 贡献模板

如果你创建了有价值的新模板：
1. 确保模板质量和完整性
2. 添加使用说明
3. 更新此README
4. 提交Pull Request

---

**维护者**: EvolvAI Team
**反馈**: GitHub Issues
