# Story 2.2: safe_edit 核心功能 - BDD Scenarios

**Story ID**: STORY-2.2
**Epic**: EPIC-001 (行为约束系统)
**创建日期**: 2025-01-19
**负责人**: EvolvAI Team
**架构决策**: [ADR-006: 移除 Git Worktree 依赖](../../architecture/adrs/006-remove-git-worktree-dependency.md)
**TDD Plan**: [story-2.2-tdd-plan.md](./story-2.2-tdd-plan.md)

---

## 📋 文档目的

本文档定义 Story 2.2 (safe_edit) 的**用户故事级验收场景**，采用 BDD Given-When-Then 格式。

**与 TDD Plan 的关系**:
- **TDD Plan**: 27 个技术测试用例 (单元/集成级别)
- **BDD Scenarios**: 8 个用户场景 (验收测试级别)

---

## 🎯 核心场景概览

| 场景 ID | 场景名称 | 用户价值 | TDD Cycle |
|---------|---------|---------|-----------|
| **S1** | 预览基于工作目录 | 看到准确预览，含所有开发中修改 | Cycle 1 |
| **S2** | 只接受 patch_id | 安全应用，不能绕过预览 | Cycle 2 |
| **S3** | 约束保护 | 防止意外大规模修改 | Cycle 3 |
| **S4** | 失败自动回滚 | 编辑失败不影响项目 | Cycle 4 |
| **S5** | 多文件批量编辑 | 一次性修改多个文件 | Cycle 1-2 |
| **S6** | Patch 过期检测 | 防止应用过时 Patch | Cycle 2 |
| **S7** | MCP 工具集成 | AI 助手安全调用 | Cycle 5 |
| **S8** | 端到端工作流 | 完整预览→应用→验证流程 | Cycle 6 |

---

## 📝 BDD Scenarios

### S1: 预览基于工作目录 (not Git HEAD)

```
Given: src/main.py unstaged: "version = '2.0'" (HEAD: "version = '1.0'")
When:  propose_edit(pattern="version = '2.0'", replacement="version = '3.0'")
Then:  diff shows "2.0 → 3.0" (NOT "1.0 → 3.0")
       文件未被修改 (仍是 "version = '2.0'")
```

**验证点**: ✅ 预览基于工作目录 ✅ 不基于 Git HEAD ✅ propose 不修改文件

**TDD测试**: `test_propose_based_on_working_directory` (Cycle 1)

---

### S2: 只接受 patch_id 应用

```
Given: propose_edit → patch_id="abc-123"
When:  apply_edit(patch_id="abc-123", execution_plan={max_files:10})
Then:  success=true, modified_files=["src/main.py"], rollback_id 已生成
       文件被修改，RollbackManager 已创建备份
```

**验证点**: ✅ 只接受 patch_id ✅ 文件修改 ✅ 回滚点创建

**TDD测试**: `test_apply_requires_patch_id`, `test_apply_success_workflow` (Cycle 2)

---

### S3: 约束保护 (ExecutionPlan)

```
Given: patch 会修改 15 个文件
When:  apply_edit(execution_plan={max_files:10})
Then:  抛出 ConstraintViolationError: "Exceeds max_files: 15 > 10"
       没有文件被修改，未创建备份 (预检查失败)
```

**验证点**: ✅ max_files 约束 ✅ 预检查拒绝 ✅ 零副作用

**TDD测试**: `test_apply_exceeds_max_files` (Cycle 3)

---

### S4: 失败自动回滚

```
Given: patch 修改 3 个文件: file1.py ✅, file2.py ✅, file3.py ❌ (磁盘满)
When:  apply_edit(patch_id)
Then:  抛出 ApplyError: "Apply failed: [disk full error]"
       RollbackManager 自动回滚 file1.py, file2.py
       项目状态恢复到 apply_edit 调用前
```

**验证点**: ✅ 失败触发回滚 ✅ 所有文件恢复 ✅ 无部分应用

**TDD测试**: `test_apply_failure_auto_rollback` (Cycle 4)

---

### S5: 多文件批量编辑

```
Given: src/utils.py: "def old_function(): pass"
       src/main.py: "from utils import old_function; old_function()"
When:  propose_edit(pattern="old_function", replacement="new_function")
       然后 apply_edit(patch_id)
Then:  两个文件都正确修改为 "new_function"
```

**验证点**: ✅ 跨文件批量修改 ✅ 一致性保证

**TDD测试**: `test_propose_multiple_files`, `test_apply_multiple_files` (Cycle 1-2)

---

### S6: Patch 过期检测

```
Given: propose_edit → patch_id (基于 main.py: "version = '1.0'")
When:  另一进程修改 main.py 为 "version = '1.5'"
       然后 apply_edit(patch_id)
Then:  抛出 PatchOutdatedError: "File has changed since propose_edit"
       建议 "Please re-run propose_edit"
       没有文件被修改
```

**验证点**: ✅ 检测文件变化 ✅ 拒绝过期 Patch ✅ 重新生成建议

**TDD测试**: `test_apply_detects_file_changes` (Cycle 2)

---

### S7: MCP 工具集成

```
Given: AI 助手通过 MCP 连接到 EvolvAI 服务器
When:  调用 mcp__evolvai__propose_edit(pattern, replacement, scope)
Then:  返回 JSON: {patch_id, unified_diff, affected_files, statistics}
       AI 可以向用户展示预览

When:  调用 mcp__evolvai__apply_edit(patch_id, max_files, max_changes)
Then:  返回 JSON: {success, modified_files, rollback_id}
```

**验证点**: ✅ MCP 协议兼容 ✅ JSON 响应正确 ✅ AI 可解析

**TDD测试**: `test_mcp_propose_edit`, `test_mcp_apply_edit` (Cycle 5)

---

### S8: 端到端工作流

```
Given: Python 项目，需要重命名变量 "old_var" → "new_var"

Step 1 预览:  propose_edit() → patch_id + unified_diff
Step 2 确认:  检查 diff，确认无误
Step 3 应用:  apply_edit(patch_id) → success + modified_files
Step 4 验证:  pytest tests/ 通过，git diff 显示正确变更
```

**验证点**: ✅ 完整工作流 ✅ propose → apply 衔接 ✅ 结果可验证

**TDD测试**: `test_end_to_end_edit_flow` (Test 6.1, Cycle 6)

---

## 📊 BDD → TDD 映射表

| BDD | TDD Cycle | 测试用例 | 估算 |
|-----|-----------|---------|------|
| S1 | Cycle 1 | `test_propose_based_on_working_directory` (Test 1.2) | 0.3天 |
| S2 | Cycle 2 | `test_apply_edit_basic_flow` (Test 2.1), `test_apply_invalid_patch_id` (Test 2.2) | 0.3天 |
| S3 | Cycle 3 | `test_execution_plan_max_files_constraint` (Test 3.1) | 0.5天 |
| S4 | Cycle 4 | `test_apply_failure_triggers_rollback` (Test 4.1), `test_partial_failure_rollback` (Test 4.4) | 0.5天 |
| S5 | Cycle 1-2 | `test_propose_multiple_files` (Test 1.3), `test_apply_multiple_files_atomic` (Test 2.5) | 0.2天 |
| S6 | Cycle 2 | `test_apply_detects_file_changes` (Test 2.6) | 0.2天 |
| S7 | Cycle 5 | `test_propose_edit_mcp_tool` (Test 5.1), `test_apply_edit_mcp_tool` (Test 5.2) | 1天 |
| S8 | Cycle 6 | `test_end_to_end_edit_flow` (Test 6.1), `test_user_modification_conflict` (Test 6.2) | 1天 |

**总计**: 8 BDD Scenarios → 28 TDD 测试 → 5 人天

---

## ✅ 验收标准

### 文档级验收
- [x] 8 个场景定义完整
- [x] Given-When-Then 格式规范
- [x] BDD → TDD 映射清晰
- [x] 与 ADR-006 一致

### 实施级验收 (未来)
- [ ] 所有 BDD 场景对应的 TDD 测试通过
- [ ] 端到端场景 (S8) 在真实项目中验证
- [ ] MCP 工具 (S7) 在 Claude Code/Cursor 中测试

---

## 🔗 相关文档

- [ADR-006: 移除 Git Worktree](../../architecture/adrs/006-remove-git-worktree-dependency.md)
- [Story 2.2 TDD Plan](./story-2.2-tdd-plan.md)
- [Epic-001 README](../../../product/epics/epic-001-behavior-constraints/README.md)

---

## 📝 设计原则

1. **用户视角优先**: 不暴露实现细节
2. **所见即所得**: propose预览 = apply结果
3. **安全第一**: 约束保护 + 自动回滚
4. **渐进式验证**: propose → 确认 → apply → 测试

**与 ADR-006 一致性**:
- ✅ 基于工作目录操作 (不是 Git HEAD)
- ✅ 包含 unstaged/staged/untracked 修改
- ✅ 文件备份回滚 (不是 Git worktree)
- ✅ Patch-First 两阶段架构

---

**最后更新**: 2025-01-19
**更新人**: EvolvAI Team
**更新内容**: 重新设计 BDD Scenarios，移除 Git worktree 架构
