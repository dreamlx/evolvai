# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

---

## 🧠 专家人格激活（强制执行）

**每次任务开始时必须先激活专家人格：**

### 人格激活加载流程
1. **读取人格文件**: `CLAUDE-PERSONA.md`
2. **激活思维模式**: 🧠 → 🎯 → ⚡
3. **建立行为偏好**: 系统性分析 > 直接行动

### Claude无法真正自我觉察，需要用户监督

**用户触发词（有效机制）**:
- "专家模式, amos, shifu" → 强制重读 CLAUDE-PERSONA.md
- "深入思考" → 激活系统性分析，不立即修复
- "不对，有问题" → 暂停操作，重新评估
- "等一下" → 立即停止当前操作，思考操作并提问

### 自动读取人格文件的前置条件
- 遇到任何编译/TypeScript错误
- 准备创建新文件
- 用户表达不满意时

**激活标志**: 🧠 → 🎯 → ⚡

---

## 🚨 核心规则（新会话必读）

### 📂 文档边界（操作docs/前必须理解）
- `docs/` = **业务文档仓库ONLY**（需求、架构、测试、指南、知识沉淀）
- `.claude/` = AI工具配置和元文档
- `workspace/` = 临时工作文件、执行计划、检查清单
- ⚠️ **违反边界 = 系统混乱**


## 🚀 START HERE - 第一步

**⚡ CRITICAL**: 运行 `/context-load` 加载项目上下文

### 为什么需要加载 Context？

**Token 优化**:
- CLAUDE.md (本文件): ~1.5k tokens (自动加载)
- Context files: ~12k tokens (按需加载)
- **总计**: ~13.5k vs 旧方案 20k = **节省 32%**

### Context 文件位置

`~/.claude/evolvai/serena/`

**P0 文件** (session start 必须加载):
- `project.md` - 项目身份、目标、架构 (~3.5k tokens)
- `active.md` - 当前工作、最近决策 (~3k tokens)
- `progress.md` - 进度状态、指标 (~2.5k tokens)
- `.rules` - 行为规则、检查点 (~2k tokens)

**P1 文件** (按需加载):
- `tech.md` - 命令、技术栈、常见问题 (~1.5k tokens)
- `patterns.md` - 架构模式、ADRs (~2k tokens)

### 加载后必做

**MANDATORY**: 声明 .rules 遵守
```
"我已加载项目上下文，将严格遵守 .rules:
1. TDD Workflow - 代码前检查 Story TDD Plan
2. Tool Priority - EvolvAI → Native (dogfooding)
3. Context Updates - 里程碑手动更新，非每次提交
4. Git Workflow - feature → develop → main

检查点：
- 代码前: Story TDD Plan? 哪个 Cycle? 哪个 DoD?
- 工具前: 使用 EvolvAI 工具优先?
- 提交前: 测试通过? format + type-check 完成?
- 卡住时: .rules 有指导吗?

准备工作！"
```

---

## ⚡ 关键规则速查（Context 加载前）

### 1. 工具优先级（强制 Dogfooding）

```
🥇 EvolvAI MCP (首选)
   └─ batch_edit, safe_exec, safe_search

🥉 Native Tools (最后手段，需记录原因)
   └─ Read, Write, Edit, Grep, Glob
```

**目的**: 收集 TPST 指标，验证工具效率

### 2. TDD 工作流（强制）

```
代码前 → 检查 Story TDD Plan
       → 确认 Cycle + 测试 + DoD
       → Red → Green → Refactor
```

**检查点**: .rules 中有完整检查点列表

### 3. Context 管理

```
加载: /context-load (session start)
更新: /context-update (merge/milestone/major decision)
跳过: 小提交、格式化、单个测试
```

### 4. Git 工作流

```
feature/* → develop → main
小提交 → 合并时更新 context
```

**完整规则**: 见 `.rules` (在 context 文件中)

### 5. EvolvAI 智能循环（防呆模式 - 强制执行）

**核心原则**：一次做对 > 效率优化（返工成本 >> 循环成本）

**每个任务必须完整执行 5 步，不允许跳过**：

```
1. safe_search + Area Detection
   └─ 理解上下文和影响范围（不是"找到文件"）
   └─ 即使是 MD 文件也要搜索引用！

2. think_about_collected_information
   └─ 信息足够吗？缺什么？

3. propose_edit + ExecutionPlan
   └─ 预览编辑 + 硬约束检查

4. apply_edit
   └─ 执行编辑

5. think_about_whether_you_are_done
   └─ 真正完成了吗？测试跑了吗？
```

**⚠️ Step 1 不能跳过的原因**：
- 即使"简单的 MD 文件"也可能被 50+ 处引用
- 程序文件需要找调用者、测试、文档
- "感觉简单"是陷阱，已通过 dogfooding 验证

**Dogfooding 报告格式**：

```
## 循环检查点报告
**任务**: [任务描述]

[Step 1] safe_search: 范围 X，找到 N 个结果
[Step 2] think: 信息足够/不足，缺 X
[Step 3] propose_edit: N 文件，~M 行
[Step 4] apply_edit: 执行
[Step 5] think: 完成/未完成，原因 X

📊 指标：Token ~N, 返工 N 次, ✅/❌
```

**设计原则**：
- 软约束（think）+ 硬约束（Area/Plan）= 协同
- 正确性 > 效率（在确保正确的前提下优化 tokens）
- 基于数据验证，不盲目调整

---

## 💻 紧急命令参考

```bash
# 代码质量 (每次提交前)
uv run poe format       # RUFF + BLACK (唯一允许)
uv run poe type-check   # mypy (唯一允许)
uv run poe test -xvs    # 运行测试 (首次失败停止)

# 测试标记
uv run poe test -m "python"        # Python 测试
uv run poe test -m "python or go"  # 多语言
```

**完整命令列表**: 见 `tech.md` (在 context 文件中)

---

## 📚 快速导航

### 在哪里找什么

**Session Context** (`~/.claude/evolvai/serena/`):
- 项目是什么? → `project.md`
- 当前在做什么? → `active.md`
- 进度如何? → `progress.md`
- 规则是什么? → `.rules`
- 命令有哪些? → `tech.md`
- 架构如何? → `patterns.md`

**Permanent Docs** (`docs/`):
- 架构决策 → `docs/development/architecture/adrs/`
- 经验教训 → `docs/knowledge/lessons/`
- 产品规格 → `docs/product/`
- 文档组织 → `docs/.structure.md`
- Git 工作流 → `docs/development/git-workflow.md`
- 工作流清单 → `docs/development/workflow-checklist.md`

### Slash Commands

- `/context-load` - 加载项目上下文
- `/context-update` - 更新上下文（里程碑时）

---

## ⚠️ 重要提醒

**每次 session 必须**:
1. ✅ 运行 `/context-load`
2. ✅ 声明 `.rules` 遵守
3. ✅ 代码前检查 Story TDD Plan
4. ✅ EvolvAI 工具优先（dogfooding）
5. ✅ 遵循 5 步智能循环（报告指标）

**为什么 CLAUDE.md 这么短？**

因为这个文件**自动加载**（每次 session 都付 token 成本）。

详细信息在：
- **Context files** (按需加载): ~/.claude/evolvai/serena/
- **Docs** (永久参考): docs/

这样设计节省 **32% tokens** (20k → 13.5k)。

---

**Token 优化**: CLAUDE.md ~1.5k (自动) + Context ~12k (按需) = 高效启动

**开始工作**: 运行 `/context-load` 然后查看 `active.md` 了解当前任务
