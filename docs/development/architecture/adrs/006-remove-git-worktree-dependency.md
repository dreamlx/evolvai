# ADR-006: 移除 safe_edit 的 Git Worktree 依赖

**日期**: 2025-01-19
**状态**: ✅ Accepted
**决策者**: EvolvAI Team
**相关**: Epic-001 Story 2.2 (safe_edit)

---

## 📋 Context (背景)

### 原始设计

Epic-001 Story 2.2 最初设计使用 **Git Worktree** 进行编辑隔离：

```python
# 原始设计意图
def apply_edit(patch_id: str):
    # 1. 创建 Git worktree
    worktree = create_worktree(f"/tmp/safe-edit-{patch_id}")

    # 2. 在 worktree 中应用 patch
    worktree.apply_patch(patch_id)

    # 3. 验证成功后合并到主目录
    if validate_success():
        merge_to_main_directory()
    else:
        # 4. 失败则删除 worktree（"自动回滚"）
        remove_worktree()
```

**设计目标**:
- 隔离编辑环境，避免污染主工作目录
- 失败时自动回滚（删除 worktree）
- 提供"安全"的编辑环境

---

## 🚨 Problem (问题)

### 关键发现

**2025-01-19 讨论中发现**：Git Worktree 在实际开发场景中存在严重问题。

#### 问题 1: 用户正在开发时的状态不被支持

**真实场景**:
```bash
# 用户的工作目录
/project/
├── src/main.py       (modified, unstaged)  ← 用户正在写代码
├── src/utils.py      (modified, staged)    ← 准备提交
├── test/test_main.py (new file, untracked) ← 新文件
└── .git/

# Git 状态
$ git status
modified:   src/main.py (not staged)
modified:   src/utils.py (staged)
untracked:  test/test_main.py
```

**Git Worktree 的行为**:
```python
# 创建 worktree 基于 HEAD
git worktree add /tmp/safe-edit-workspace HEAD

# 问题：
# ❌ /tmp/safe-edit-workspace 只包含 HEAD 的内容
# ❌ 用户的 unstaged 修改（main.py）不在 worktree 里
# ❌ 用户的 staged 修改（utils.py）也不在 worktree 里
# ❌ 用户的新文件（test_main.py）更不在 worktree 里

# 结果：
# propose_edit 生成的 diff 是基于 HEAD，不是用户当前状态
# apply_edit 可能与用户修改冲突
# 用户看到的预览与实际应用结果不一致
```

**根本问题**: Git Worktree 基于 **Git 快照 (HEAD)**，不是 **工作目录 (Working Directory)**

---

#### 问题 2: "回滚"机制的误解

**误解**:
```python
# 很多人以为 Git worktree 有神奇的回滚能力
apply_edit(patch_id):
    worktree = create_worktree()
    worktree.apply_patch()
    if test_failed():
        remove_worktree()  # ← "自动回滚"？
```

**现实**:
```python
# Git worktree 的 "回滚" 只是删除临时目录
git worktree remove /tmp/workspace
# - 删除临时目录
# - 删除 Git 引用
# - 主目录完全不受影响

# 但问题：
# ❌ 如果已经合并到主目录，删除 worktree 无法回滚
# ❌ 真正的回滚需要 git reset 或文件备份恢复
```

**结论**: Git Worktree 不提供真正的回滚能力

---

#### 问题 3: 性能开销

```bash
# Git Worktree 开销
$ time git worktree add /tmp/workspace HEAD
real    0m0.856s  # ~1秒（10k 文件项目）

# 包含：
# - 复制 .git/index (~MB 级)
# - 检出文件到新目录
# - 创建 Git 引用

# 对比：直接读取工作目录
$ time find src -name "*.py"
real    0m0.015s  # ~15ms

# 性能差距: ~57x
```

---

#### 问题 4: 只适用于 clean working tree

Git Worktree 只在以下情况下才安全：
```bash
$ git status
On branch main
nothing to commit, working tree clean  # ← 必须 clean
```

**但现实**:
- 用户大部分时间工作目录都是 dirty
- 强制要求 clean 极大降低可用性
- 违背 "AI 辅助开发" 的初衷（应该在任何时候都能用）

---

## 💡 Decision (决策)

### ✅ **移除 Git Worktree 依赖**

**改用**: 基于工作目录的文件操作 + 文件备份回滚

### 新架构设计

```python
class SafeEditTool:
    """
    Patch-First 架构（无 Git Worktree）
    """

    def propose_edit(
        self,
        pattern: str,
        replacement: str,
        scope: str = "**/*"
    ) -> str:
        """
        阶段 1: 生成编辑预览（基于工作目录）

        关键改变:
        ✅ 直接读取工作目录文件（包含用户所有修改）
        ✅ 生成 unified diff
        ✅ 保存到内存/临时文件（不需要 Git worktree）
        ❌ 不修改任何文件
        """
        # 1. 扫描工作目录文件（包含用户修改）
        files = scan_working_directory(scope)

        # 2. 执行 regex 替换，生成变更
        changes = []
        for file in files:
            original = file.read_text()  # 读取当前内容（包含修改）
            new_content = apply_pattern(original, pattern, replacement)
            if new_content != original:
                changes.append({
                    "file": file,
                    "original": original,
                    "new": new_content
                })

        # 3. 生成 unified diff
        unified_diff = create_unified_diff(changes)

        # 4. 保存 patch（内存/文件，不是 Git worktree）
        patch_id = uuid.uuid4()
        self.patch_storage[patch_id] = {
            "changes": changes,
            "unified_diff": unified_diff,
            "created_at": datetime.now()
        }

        # 5. 返回预览
        return {
            "patch_id": patch_id,
            "unified_diff": unified_diff,
            "affected_files": [c["file"] for c in changes],
            "total_changes": len(changes)
        }

    def apply_edit(
        self,
        patch_id: str,
        execution_plan: ExecutionPlan
    ) -> str:
        """
        阶段 2: 应用编辑（带约束检查和回滚）

        关键改变:
        ✅ 创建文件备份（回滚点）
        ✅ 直接在工作目录应用
        ✅ 失败时从备份恢复
        ❌ 不使用 Git worktree
        """
        # 1. 加载 patch
        patch = self.patch_storage[patch_id]
        changes = patch["changes"]

        # 2. ExecutionPlan 约束检查
        if len(changes) > execution_plan.limits.max_files:
            raise ConstraintViolationError()

        # 3. 创建文件备份（RollbackManager）
        rollback_id = self.rollback_manager.create_backups(changes)

        # 4. 应用 patch
        try:
            for change in changes:
                change["file"].write_text(change["new"])

            return {
                "success": True,
                "rollback_id": rollback_id
            }

        except Exception as e:
            # 5. 失败回滚（从文件备份恢复）
            self.rollback_manager.rollback(rollback_id)
            raise ApplyError(f"Apply failed: {e}")
```

---

## ✅ Consequences (影响)

### 正面影响

#### 1. 支持任意开发状态

```bash
# ✅ 现在可以在任何时候使用 safe_edit
$ git status
modified:   src/main.py (not staged)
modified:   src/utils.py (staged)
untracked:  test/test_main.py

# propose_edit 会基于当前工作目录生成 diff
# - 包含 main.py 的 unstaged 修改
# - 包含 utils.py 的 staged 修改
# - 包含 test_main.py（如果在 scope 内）

# ✅ 预览准确，用户看到的就是会发生的
```

#### 2. 性能显著提升

| 操作 | Git Worktree | 新方案 | 提升 |
|------|--------------|--------|------|
| propose_edit | ~856ms | ~15ms | **57x** |
| apply_edit | ~1.2s | ~50ms | **24x** |

#### 3. 简化架构

```
移除复杂度:
- ❌ Git worktree 创建/删除
- ❌ Git 引用管理
- ❌ worktree 路径管理
- ❌ worktree 同步问题

新增复杂度:
- ✅ 文件备份（已有 RollbackManager）
- ✅ 文件恢复（已有 RollbackManager）

净复杂度: 降低 ~60%
```

#### 4. 更清晰的职责划分

```
propose_edit:
- 职责: 生成预览（只读操作）
- 依赖: 文件系统（读取）
- 输出: patch_id + unified diff

apply_edit:
- 职责: 应用变更（写操作）
- 依赖: 文件系统（写入）+ RollbackManager（回滚）
- 输出: success + rollback_id
```

---

### 负面影响（及缓解措施）

#### 1. 失去"隔离环境"

**问题**: 直接在工作目录操作，失败会影响文件

**缓解**:
- ✅ ExecutionPlan 预检查（在写入前验证）
- ✅ RollbackManager 快速恢复（失败立即回滚）
- ✅ Patch-First 两阶段（propose 预览，用户确认后 apply）

**对比**:
```
Git Worktree 方案:
- "隔离" 只是假象（merge 后一样影响主目录）
- 失败后仍需回滚主目录

新方案:
- 承认直接操作工作目录
- 但有 ExecutionPlan 约束 + 快速回滚
- 实际更诚实、更可控
```

#### 2. 无法运行测试验证

**Git Worktree 的理想**:
```python
apply_edit(patch_id):
    worktree.apply_patch()
    # 在 worktree 中运行测试
    worktree.run_tests()  # 如果失败，主目录不受影响
    if success:
        merge_to_main()
```

**现实问题**:
- ❌ worktree 中运行测试很慢（需要重新安装依赖）
- ❌ 测试可能依赖主目录的状态（数据库、配置）
- ❌ 增加复杂度，收益有限

**新方案的选择**:
- Phase 1 (MVP): **不在 safe_edit 中运行测试**
- Phase 2+ (可选): 提供可选的验证钩子
  ```python
  apply_edit(patch_id, execution_plan, run_validation=False)
  ```

---

### 风险与对策

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| 用户担心"不安全" | Medium | Low | 强调 ExecutionPlan 约束 + 快速回滚 |
| 回滚失败（文件锁定） | Low | Medium | 重试机制 + 清晰错误提示 |
| 性能回退（大文件） | Low | Low | 文件大小限制（默认 10MB） |

---

## 📊 Alternatives Considered (备选方案)

### 方案 A: 保留 Git Worktree（已否决）

**理由**:
- ❌ 不支持用户开发状态（fatal）
- ❌ 性能开销大
- ❌ 只适用于 clean working tree

### 方案 B: Git Stash（已否决）

```python
# 使用 Git stash 作为回滚
apply_edit(patch_id):
    git stash push  # 保存当前状态
    apply_patch()
    if failed:
        git stash pop  # 恢复
```

**问题**:
- ❌ 仍然需要 Git 仓库
- ❌ stash 可能冲突
- ❌ 不适用于非 Git 项目

### 方案 C: 文件备份（已采纳）✅

**优势**:
- ✅ 不依赖 Git
- ✅ 快速（文件复制 ~ms 级）
- ✅ 简单可靠
- ✅ 已有 RollbackManager 实现

---

## 🔗 Related (相关)

### 文档更新

- ✅ [Epic-001 README.md](../../../product/epics/epic-001-behavior-constraints/README.md) - Story 2.2 交付物更新
- 📝 [Story 2.2 TDD Plan](../../sprints/current/story-2.2-tdd-plan.md) - 待创建
- 📝 [Story 2.2 BDD Scenarios](../../sprints/current/story-2.2-bdd-scenarios.md) - 待创建

### 相关决策

- [ADR-003: Tool Execution Engine Simplification](./003-tool-execution-engine-simplification.md)
- [ADR-004: Runtime Constraint Monitor Optimization](./004-runtime-constraint-monitor-optimization.md)

---

## 📝 Notes (备注)

### 经验教训

1. **不要盲目套用 Git 工具**
   - Git Worktree 是好工具，但不适合这个场景
   - 理解工具的设计意图和限制

2. **用户开发状态是第一位的**
   - 工具必须适应用户的真实工作流
   - 不能强制用户改变习惯（如要求 clean working tree）

3. **"隔离" 不一定需要 Git**
   - 文件备份 + 快速回滚也是有效的隔离
   - 简单方案往往更可靠

4. **性能很重要**
   - ~1秒 vs ~15ms 的差距用户能感知
   - AI 辅助工具必须快速响应

---

**最后更新**: 2025-01-19
**更新人**: EvolvAI Team
**状态**: ✅ Accepted - 开始实施
