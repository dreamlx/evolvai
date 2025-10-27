# [ACTIVE] Epic 001: 行为约束系统

**Epic ID**: EPIC-001
**创建日期**: 2025-10-26
**负责人**: EvolvAI Team
**状态**: [ACTIVE]
**优先级**: [P0]

---

## 📋 Epic概述

### 业务价值
通过**物理删除错误执行路径**而非依赖提示词约束，从根本上改变AI助手的行为模式。让AI无法绕过约束，而是从接口层面就只能看到"正确的选项"。

核心理念：**行为工程 > 提示词工程**

### 目标用户
- AI编程助手（Claude Code, Cursor, Roo Code等）
- MCP客户端开发者
- 需要可控AI工具的开发团队

### 成功指标
- **TPST降低**: 相比原生工具降低30%以上（MVP目标）
- **首次成功率**: >75%的任务首次执行成功
- **工具调用准确率**: >90%的工具调用符合约束
- **Token浪费率**: <10%的token用于错误尝试

---

## 🎯 Epic目标

### 主要目标
1. **ExecutionPlan宪法系统**: 用JSON Schema强制约束工具行为
2. **三大safe工具**: safe_search, safe_edit, safe_exec实现物理路径删除
3. **可验证性**: 所有操作可预览、验证、回滚
4. **MCP集成**: 通过MCP协议暴露给AI助手

### 次要目标
- 建立TPST基线测试套件
- 生成可复现的英雄场景演示
- 为Phase 2的索引系统奠定基础

---

## 📦 包含的Features

### Feature 1: ExecutionPlan Schema
- **Feature ID**: FEATURE-001
- **描述**: 实现ExecutionPlan Pydantic模型，包含dry_run、validation、rollback等强制字段
- **优先级**: [P0]
- **估算**: 2人天
- **状态**: [In Progress]

### Feature 2: safe_search Wrapper
- **Feature ID**: FEATURE-002
- **描述**: 智能协调ripgrep/ugrep/grep，自动选择最佳工具并提供统一JSON输出
- **优先级**: [P0]
- **估算**: 2人天
- **状态**: [Backlog]

### Feature 3: safe_edit Patch-First
- **Feature ID**: FEATURE-003
- **描述**: 使用difflib生成统一diff，git apply应用，propose和apply阶段保持一致
- **优先级**: [P0]
- **估算**: 3人天
- **状态**: [Backlog]

### Feature 4: safe_exec Process Management
- **Feature ID**: FEATURE-004
- **描述**: 使用os.setsid和os.killpg管理进程组，确保timeout时完全清理
- **优先级**: [P1]
- **估算**: 1.5人天
- **状态**: [Backlog]

---

## 📊 时间线

### 预计时间
- **开始日期**: 2025-10-27
- **结束日期**: 2025-11-02
- **总工作量**: 8.5人天 (约1周，MVP Week 1)

### 里程碑
- [x] Product Definition完成 - 2025-10-26
- [ ] ExecutionPlan Schema实现 - 2025-10-28
- [ ] safe_search实现 - 2025-10-29
- [ ] safe_edit Patch-First实现 - 2025-10-31
- [ ] safe_exec实现 - 2025-11-01
- [ ] MCP集成测试 - 2025-11-02

---

## 🔗 依赖关系

### 依赖的Epic
无 - 这是第一个Epic

### 被依赖的Epic
- EPIC-002: MCP集成与TPST审计 - 需要本Epic提供的safe工具

---

## 🎯 验收标准

### Epic级验收标准
- [ ] ExecutionPlan Schema用Pydantic定义，包含所有强制字段
- [ ] safe_search可自动选择ripgrep/ugrep/grep并返回JSON格式
- [ ] safe_edit使用Patch-First架构，propose和apply一致
- [ ] safe_exec可正确管理进程组，timeout时完全清理
- [ ] 所有工具通过MCP暴露给AI助手
- [ ] 基线测试通过（pytest, fastapi, superset三个repo）

---

## 🛡️ 风险与对策

### 技术风险
| 风险 | 影响 | 概率 | 对策 |
|------|------|------|------|
| difflib性能问题（大文件） | Medium | Low | 限制单次编辑文件大小<10MB |
| git apply冲突处理复杂 | High | Medium | 使用--3way模式，提供冲突解决指导 |
| 进程killpg权限问题 | Medium | Low | 文档说明需要的权限，提供sudo方案 |
| ripgrep不可用时降级 | Low | Low | 提供grep fallback，文档说明依赖 |

### 业务风险
| 风险 | 影响 | 概率 | 对策 |
|------|------|------|------|
| TPST改进不达30% | High | Medium | 严格测量baseline，识别优化点 |
| MCP客户端兼容性 | Medium | Medium | 先支持Claude Code，逐步扩展 |

---

## 📝 备注

### 设计原则
1. **接口层约束 > 提示词约束**: 物理删除错误路径
2. **Patch-First**: propose和apply阶段必须使用同一个diff
3. **Git Worktree隔离**: 每个任务独立worktree，避免污染主目录
4. **Fair Baseline**: 使用git ls-files确保grep和rg对比公平

### 技术栈
- Python 3.11
- Pydantic for schemas
- subprocess for command execution
- difflib for unified diff generation
- MCP protocol for tool exposure

---

## 📚 相关文档

- [产品定义 v1.0](../../definition/product-definition-v1.md)
- [讨论总结 2025-10-26](../../definition/discussion-summary-2025-10-26.md)
- [ADR-001: Patch-First架构](../../../development/architecture/adrs/001-patch-first.md)
- [ADR-002: Git Worktree策略](../../../development/architecture/adrs/002-git-worktree.md)
- [Sprint-001: MVP Week 1](../../../development/sprints/current/sprint-001-mvp-week1.md)

---

**最后更新**: 2025-10-26
**更新人**: EvolvAI Team
