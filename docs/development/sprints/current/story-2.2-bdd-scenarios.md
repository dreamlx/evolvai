# Story 2.2: safe_edit Patch-First Architecture - BDD Scenarios

**Story ID**: STORY-2.2
**创建日期**: 2025-11-07
**状态**: [APPROVED] - 基于方案A重新设计
**决策**: 放弃旧实现，按Patch-First架构重新实现

---

## 📋 Story概述

**用户故事**:
> 作为AI编程助手，我需要在修改代码前先看到diff预览，确认无误后再应用，这样可以避免错误修改并保证可回滚性。

**核心价值**:
- ✅ 预览修改影响（diff）
- ✅ 分离propose和apply操作
- ✅ Git worktree隔离验证
- ✅ 原子性和可回滚性

**反模式**（故意不做的）:
- ❌ 直接修改文件
- ❌ 没有预览的编辑
- ❌ 文件复制式backup
- ❌ 批量操作（Phase 3再考虑）

---

## 🎯 验收标准（Definition of Done）

### 功能完整性 (F)

**F1: propose_edit生成unified diff**
- propose_edit()可以扫描文件、执行替换、生成diff
- 返回patch_id和完整的unified diff内容
- 不修改任何文件

**F2: apply_edit只接受patch_id**
- apply_edit(patch_id)验证patch存在
- 在Git worktree中隔离执行
- 使用git apply应用patch

**F3: Git worktree隔离验证**
- 每次apply创建临时worktree
- 失败自动清理worktree
- 成功才合并到主目录

**F4: 原子性和回滚**
- apply要么全成功，要么全失败
- 失败自动git reset回滚
- 记录审计日志

**F5: MCP工具暴露**
- propose_edit暴露为MCP工具
- apply_edit暴露为MCP工具
- AI助手可以调用

### 质量标准 (Q)

**Q1: 测试覆盖率 ≥ 90%**
- 所有BDD场景有对应测试
- 边界情况和错误处理覆盖

**Q2: 性能标准**
- propose_edit: < 2s (单文件)
- apply_edit: < 5s (Git操作)
- patch存储: < 100MB内存

**Q3: 代码质量**
- 通过format/type-check/lint
- 符合KISS原则
- 无过度设计

### 性能标准 (P)

**P1: 响应时间**
- propose: < 2s (单文件)
- apply: < 5s (含Git操作)

**P2: 资源使用**
- 内存: < 100MB
- 临时文件: 自动清理

---

## 🎬 BDD场景定义

### Scenario 1: 预览单文件编辑影响 (propose)

**优先级**: P0 - 核心功能
**DoD映射**: F1

```gherkin
Feature: 预览编辑影响
  作为AI助手，我想在修改文件前先看到diff
  这样我可以确认修改是否正确

Scenario: 成功生成单文件diff
  Given 项目目录 "/test-project"
    And 文件 "src/user.go" 内容为:
      """
      package main
      func getUserData() string { return "user" }
      """
  When 我调用 propose_edit:
    | pattern      | replacement     |
    | getUserData  | fetchUserData   |
  Then 返回成功结果
    And 生成patch_id格式 "patch_<timestamp>_<hash>"
    And unified diff包含:
      """
      --- a/src/user.go
      +++ b/src/user.go
      @@ -1,1 +1,1 @@
      -func getUserData() string { return "user" }
      +func fetchUserData() string { return "user" }
      """
    And 原文件未被修改
    And patch保存到内存
```

**测试函数名**: `test_propose_single_file_edit_success`

---

### Scenario 2: 预览多文件跨域编辑

**优先级**: P0
**DoD映射**: F1

```gherkin
Scenario: 扫描多文件生成完整patch
  Given 项目有以下文件:
    | path              | content                    |
    | backend/user.go   | func getUserData() {...}   |
    | backend/auth.go   | user := getUserData()      |
    | frontend/api.ts   | const data = getUserData() |
  When 我调用 propose_edit:
    | pattern      | replacement     | scope        |
    | getUserData  | fetchUserData   | backend/**   |
  Then 扫描到2个文件 (只backend)
    And unified diff包含两个文件的修改
    And patch_id对应完整的multi-file patch
    And 前端文件未被扫描
```

**测试函数名**: `test_propose_multi_file_edit_with_scope`

---

### Scenario 3: 应用已验证的补丁 (apply)

**优先级**: P0
**DoD映射**: F2, F3

```gherkin
Feature: 应用补丁
  作为AI助手，我想应用已确认的patch
  这样可以保证修改的原子性和可回滚性

Scenario: 成功应用单文件patch
  Given 已有patch_id "patch_1234_abc"
    And patch内容为单文件diff
  When 我调用 apply_edit(patch_id="patch_1234_abc")
  Then 创建临时Git worktree
    And 在worktree中执行 git apply
    And git apply成功
    And 将worktree变更合并到主目录
    And 清理临时worktree
    And 返回成功结果
    And 审计日志记录操作
```

**测试函数名**: `test_apply_single_file_patch_success`

---

### Scenario 4: patch_id验证失败

**优先级**: P0
**DoD映射**: F2

```gherkin
Scenario: patch_id不存在
  Given 不存在patch_id "invalid_patch"
  When 我调用 apply_edit(patch_id="invalid_patch")
  Then 抛出异常 PatchNotFoundError
    And 错误消息: "Patch 'invalid_patch' not found"
    And 未创建worktree
    And 未修改任何文件
```

**测试函数名**: `test_apply_invalid_patch_id`

---

### Scenario 5: Git apply冲突处理

**优先级**: P0
**DoD映射**: F3, F4

```gherkin
Scenario: patch与当前代码冲突
  Given 已有patch_id "patch_1234_abc"
    And patch基于旧版本文件
    And 主目录文件已被修改（冲突）
  When 我调用 apply_edit(patch_id="patch_1234_abc")
  Then 创建临时Git worktree
    And 执行 git apply
    And git apply失败（冲突）
    And 自动清理worktree
    And 抛出异常 PatchConflictError
    And 错误消息包含冲突详情
    And 主目录未被修改
```

**测试函数名**: `test_apply_patch_conflict_rollback`

---

### Scenario 6: 隔离环境验证通过

**优先级**: P1
**DoD映射**: F3

```gherkin
Scenario: 在worktree中验证后才合并
  Given 已有patch_id "patch_1234_abc"
    And 配置了post_apply_validation=True
  When 我调用 apply_edit(patch_id="patch_1234_abc")
  Then 创建临时Git worktree
    And 在worktree中apply patch
    And 运行验证脚本（如果配置）
    And 验证通过
    And 将worktree变更合并到主目录
    And 清理worktree
```

**测试函数名**: `test_apply_with_isolated_validation`

---

### Scenario 7: ExecutionPlan集成

**优先级**: P1
**DoD映射**: F2, Phase 1集成

```gherkin
Scenario: apply遵守ExecutionPlan约束
  Given 已有patch_id "patch_1234_abc"
    And ExecutionPlan定义:
      | max_changes | timeout_seconds | rollback_strategy |
      | 50          | 30              | GIT_REVERT        |
  When 我调用 apply_edit(patch_id, execution_plan)
  Then 执行引擎检查约束
    And 如果patch修改 > 50行，抛出ConstraintViolationError
    And 如果超时 > 30s，自动取消并回滚
    And 失败时使用GIT_REVERT策略
```

**测试函数名**: `test_apply_with_execution_plan_constraints`

---

### Scenario 8: MCP接口调用

**优先级**: P0
**DoD映射**: F5

```gherkin
Scenario: AI助手通过MCP调用propose
  Given AI助手连接到EvolvAI MCP服务器
  When AI助手调用MCP工具:
    """
    {
      "tool": "propose_edit",
      "arguments": {
        "pattern": "getUserData",
        "replacement": "fetchUserData",
        "scope": "backend/**/*.go"
      }
    }
    """
  Then 返回JSON结果:
    """
    {
      "success": true,
      "patch_id": "patch_1234_abc",
      "affected_files": ["backend/user.go", "backend/auth.go"],
      "unified_diff": "...",
      "statistics": {
        "files_scanned": 10,
        "files_matched": 2,
        "total_changes": 3
      }
    }
    """
```

**测试函数名**: `test_mcp_propose_edit_integration`

---

## 🚫 反场景（明确不做的）

### Anti-Scenario 1: 直接编辑（违反Patch-First）

```gherkin
Scenario: 尝试直接写入文件
  When 我调用任何直接写入文件的API
  Then 应该没有这样的API存在
    Because "物理删除错误路径"是核心设计原则
```

### Anti-Scenario 2: 批量操作（Phase 3功能）

```gherkin
Scenario: 批量apply多个patch
  Given 多个patch_id
  When 我尝试批量apply
  Then 当前版本不支持
    Because 批量操作是Phase 3的内容
    And MVP专注核心流程
```

### Anti-Scenario 3: 模式系统（YAGNI）

```gherkin
Scenario: conservative/aggressive模式
  When 我调用propose或apply时指定mode参数
  Then 不接受mode参数
    Because 产品定义未要求
    And 增加不必要的复杂度
```

---

## 📊 场景优先级矩阵

| 场景 | 优先级 | DoD | 估算 | 风险 |
|------|--------|-----|------|------|
| Scenario 1: propose单文件 | P0 | F1 | 1天 | 低 |
| Scenario 2: propose多文件 | P0 | F1 | 0.5天 | 低 |
| Scenario 3: apply成功 | P0 | F2,F3 | 1.5天 | 中 |
| Scenario 4: patch验证 | P0 | F2 | 0.5天 | 低 |
| Scenario 5: 冲突处理 | P0 | F3,F4 | 1天 | 高 |
| Scenario 6: 隔离验证 | P1 | F3 | 0.5天 | 中 |
| Scenario 7: ExecutionPlan | P1 | F2 | 0.5天 | 低 |
| Scenario 8: MCP集成 | P0 | F5 | 0.5天 | 低 |
| **总计** | | | **6人天** | |

---

## 🔧 技术实现要点

### propose_edit实现要点

```python
def propose_edit(
    pattern: str,
    replacement: str,
    scope: str = "**/*",
    language: Optional[str] = None,
    **kwargs
) -> ProposalResult:
    """
    生成编辑提案，不修改文件

    Returns:
        ProposalResult:
            - patch_id: str
            - unified_diff: str
            - affected_files: List[str]
            - statistics: Dict
    """
    # 1. 使用rg/ugrep扫描文件
    # 2. 读取匹配文件内容
    # 3. 执行替换生成新内容
    # 4. difflib.unified_diff生成patch
    # 5. 保存到内存: patch_store[patch_id] = patch_content
    # 6. 返回proposal结果（不修改文件）
```

### apply_edit实现要点

```python
def apply_edit(
    patch_id: str,
    execution_plan: Optional[ExecutionPlan] = None,
    **kwargs
) -> ApplyResult:
    """
    应用已验证的patch

    Returns:
        ApplyResult:
            - success: bool
            - modified_files: List[str]
            - worktree_path: str (临时路径)
            - audit_log_id: str
    """
    # 1. 验证patch_id存在
    # 2. 创建Git worktree: git worktree add /tmp/evolvai_<uuid>
    # 3. 在worktree中: git apply <patch_file>
    # 4. 如果失败: 清理worktree，抛出异常
    # 5. 如果成功: 复制变更到主目录
    # 6. 清理worktree: git worktree remove
    # 7. 记录审计日志
```

### patch存储设计

```python
# 简单的内存存储（MVP）
patch_store: Dict[str, PatchContent] = {}

@dataclass
class PatchContent:
    patch_id: str
    unified_diff: str
    affected_files: List[str]
    created_at: datetime
    metadata: Dict[str, Any]
```

---

## 🧪 测试策略

### 单元测试（80%覆盖）

- `test_propose_*`: 测试propose_edit各种情况
- `test_apply_*`: 测试apply_edit各种情况
- `test_patch_*`: 测试patch存储和验证

### 集成测试（关键路径）

- `test_propose_apply_workflow`: 完整propose→apply流程
- `test_git_worktree_isolation`: Git worktree隔离
- `test_conflict_rollback`: 冲突回滚

### 端到端测试（真实项目）

- 在当前项目测试propose/apply
- 验证TPST改进
- dogfooding验证

---

## 📝 实施计划

### Day 1: propose_edit核心（Scenario 1-2）
- [ ] 实现文件扫描（rg/ugrep）
- [ ] 实现内容替换
- [ ] 实现unified_diff生成
- [ ] 实现patch_store
- [ ] 单元测试

### Day 2: apply_edit基础（Scenario 3-4）
- [ ] 实现patch_id验证
- [ ] 实现Git worktree创建
- [ ] 实现git apply执行
- [ ] 实现worktree清理
- [ ] 单元测试

### Day 3: 冲突和回滚（Scenario 5-6）
- [ ] 实现git apply错误处理
- [ ] 实现自动回滚
- [ ] 实现隔离验证
- [ ] 集成测试

### Day 4: ExecutionPlan集成（Scenario 7）
- [ ] 集成到ToolExecutionEngine
- [ ] 实现约束检查
- [ ] 审计日志记录
- [ ] 集成测试

### Day 5: MCP集成和端到端（Scenario 8）
- [ ] 创建MCP工具定义
- [ ] 注册到工具系统
- [ ] 端到端测试
- [ ] Dogfooding验证

### Day 6: 清理和文档
- [ ] 删除旧实现
- [ ] 删除过度设计代码
- [ ] 更新文档
- [ ] 准备演示

---

## 🗑️ 需要删除的代码

### 旧实现文件
- [ ] `src/evolvai/area_detection/edit_wrapper.py` (大部分重写)
- [ ] `test/evolvai/area_detection/test_safe_edit_wrapper.py` (全部重写)

### 过度设计功能
- [ ] `safe_edit_batch()` - Phase 3再考虑
- [ ] `conservative/aggressive` 模式 - YAGNI
- [ ] `safe_edit_mcp()` - 误解MCP集成方式
- [ ] 过度复杂的区域感知逻辑 - 简化

---

## ✅ 成功指标

### 功能指标
- [ ] 8个BDD场景100%通过
- [ ] propose_edit可用
- [ ] apply_edit可用
- [ ] MCP集成可用

### 质量指标
- [ ] 测试覆盖率 ≥ 90%
- [ ] 无过度设计代码
- [ ] format/type-check/lint通过

### 用户价值指标
- [ ] 可以预览diff
- [ ] 可以安全apply
- [ ] 可以自动回滚
- [ ] AI助手可以调用

---

**最后更新**: 2025-11-07
**创建人**: EvolvAI Team
**状态**: [APPROVED] - Ready for Implementation
