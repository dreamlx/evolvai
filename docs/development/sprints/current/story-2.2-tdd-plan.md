# Story 2.2 TDD Plan: safe_edit 核心功能

**Story ID**: STORY-2.2
**创建日期**: 2025-01-19
**估算**: 5人天
**状态**: Ready for Implementation
**架构决策**: [ADR-006: 移除Git Worktree依赖](../../architecture/adrs/006-remove-git-worktree-dependency.md)

---

## 🎯 Story 目标

实现 Patch-First 架构的 safe_edit 工具，提供两阶段编辑流程：
1. **propose_edit**: 生成预览（基于工作目录，不修改文件）
2. **apply_edit**: 应用变更（带约束检查和回滚）

**核心价值**: 物理删除错误执行路径，强制预览-确认-应用流程

---

## 📋 TDD Cycles 概览

| Cycle | 功能 | 测试数 | 估算 | DoD |
|-------|------|--------|------|-----|
| **Cycle 1** | propose_edit 核心 | 6 | 1天 | D1: propose生成accurate diff |
| **Cycle 2** | apply_edit 核心 | 6 | 1天 | D2: apply只接受patch_id + 冲突检测 |
| **Cycle 3** | ExecutionPlan集成 | 4 | 0.5天 | D3: 约束检查生效 |
| **Cycle 4** | 回滚机制 | 4 | 0.5天 | D4: 失败自动回滚 |
| **Cycle 5** | MCP工具暴露 | 3 | 1天 | D5: MCP工具可用 |
| **Cycle 6** | 集成测试 | 5 | 1天 | D6: 端到端场景通过 |

**总计**: 28个测试，5人天

---

## 🔄 Cycle 1: propose_edit 核心功能

### 功能描述

实现 `propose_edit(pattern, replacement, scope)` 方法：
- 扫描工作目录文件（包含用户所有修改）
- 执行 regex 替换
- 生成 unified diff
- 保存 patch到内存
- 返回 patch_id + diff 预览

**关键点**: 不修改任何文件

---

### Test 1.1: 基础 propose 流程

```python
def test_propose_edit_basic_flow(tmp_path):
    """
    Given: 工作目录有1个文件
    When: propose_edit 替换文本
    Then: 返回 patch_id 和 unified diff，文件未修改
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("def old_func():\n    pass\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Execute
    result = tool.propose_edit(
        pattern="old_func",
        replacement="new_func",
        scope="**/*.py"
    )

    # Verify
    assert result["patch_id"] is not None
    assert "def old_func()" in result["unified_diff"]
    assert "def new_func()" in result["unified_diff"]

    # 关键: 文件未修改
    assert file.read_text() == "def old_func():\n    pass\n"
```

---

### Test 1.2: 基于工作目录（包含 unstaged 修改）

```python
def test_propose_based_on_working_directory(tmp_path, git_repo):
    """
    Given: Git 仓库，文件有 unstaged 修改
    When: propose_edit
    Then: diff 基于工作目录内容（不是 HEAD）
    """
    # Setup
    repo = git_repo(tmp_path)
    file = tmp_path / "main.py"

    # 1. 提交初始版本
    file.write_text("version = '1.0'\n")
    repo.add("main.py")
    repo.commit("Initial")

    # 2. 修改文件（unstaged）
    file.write_text("version = '2.0'\n")  # ← unstaged 修改

    tool = SafeEditTool(project_root=tmp_path)

    # Execute
    result = tool.propose_edit(
        pattern="version = '2.0'",
        replacement="version = '3.0'",
        scope="**/*.py"
    )

    # Verify: diff 基于工作目录（2.0 → 3.0），不是 HEAD（1.0）
    assert "version = '2.0'" in result["unified_diff"]  # from
    assert "version = '3.0'" in result["unified_diff"]  # to
    assert "version = '1.0'" not in result["unified_diff"]  # 不包含 HEAD
```

---

### Test 1.3: 多文件批量预览

```python
def test_propose_multiple_files(tmp_path):
    """
    Given: 多个文件需要修改
    When: propose_edit
    Then: 返回所有文件的 unified diff
    """
    # Setup
    (tmp_path / "a.py").write_text("name = 'old'\n")
    (tmp_path / "b.py").write_text("name = 'old'\n")
    (tmp_path / "c.txt").write_text("name = 'old'\n")  # 不匹配 scope

    tool = SafeEditTool(project_root=tmp_path)

    # Execute
    result = tool.propose_edit(
        pattern="old",
        replacement="new",
        scope="**/*.py"
    )

    # Verify
    assert result["affected_files"] == ["a.py", "b.py"]  # 不包含 c.txt
    assert result["total_changes"] == 2
    assert "a.py" in result["unified_diff"]
    assert "b.py" in result["unified_diff"]
```

---

### Test 1.4: 无匹配时返回空

```python
def test_propose_no_matches(tmp_path):
    """
    Given: 文件不匹配 pattern
    When: propose_edit
    Then: 返回空 patch
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("def func():\n    pass\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Execute
    result = tool.propose_edit(
        pattern="nonexistent",
        replacement="new",
        scope="**/*.py"
    )

    # Verify
    assert result["affected_files"] == []
    assert result["total_changes"] == 0
    assert result["unified_diff"] == ""
```

---

### Test 1.5: 复杂正则 pattern

```python
def test_propose_with_regex_pattern(tmp_path):
    """
    Given: 使用复杂正则 pattern
    When: propose_edit
    Then: 正则匹配和捕获组工作正常
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text('log.info("message")\nlog.debug("data")\n')

    tool = SafeEditTool(project_root=tmp_path)

    # Execute: 替换所有 log.X → logger.X
    result = tool.propose_edit(
        pattern=r'log\.(\w+)\("(.*)"\)',
        replacement=r'logger.\1("\2", extra={"timestamp": True})',
        scope="**/*.py"
    )

    # Verify
    assert 'logger.info("message"' in result["unified_diff"]
    assert 'logger.debug("data"' in result["unified_diff"]
    assert 'extra={"timestamp": True}' in result["unified_diff"]
```

---

### Test 1.6: Patch 存储和检索

```python
def test_patch_storage_and_retrieval(tmp_path):
    """
    Given: propose_edit 返回 patch_id
    When: 使用 patch_id 检索
    Then: 可以获取完整 patch 信息
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Execute
    result1 = tool.propose_edit("old", "new", "**/*.py")
    patch_id = result1["patch_id"]

    # Verify: 可以检索 patch
    patch = tool._get_patch(patch_id)
    assert patch is not None
    assert patch["unified_diff"] == result1["unified_diff"]
    assert patch["changes"][0]["file"] == file
    assert patch["changes"][0]["original"] == "old\n"
    assert patch["changes"][0]["new"] == "new\n"
```

---

### DoD 1: propose_edit 生成 accurate diff ✅

验收标准：
- ✅ 基于工作目录（包含 unstaged/staged/untracked）
- ✅ 生成 unified diff 格式
- ✅ 支持多文件批量预览
- ✅ 支持复杂正则 pattern
- ✅ patch_id 可检索
- ✅ 不修改任何文件

---

## 🔄 Cycle 2: apply_edit 核心功能

### 功能描述

实现 `apply_edit(patch_id, execution_plan)` 方法：
- 验证 patch_id 存在
- 应用 patch 到工作目录
- 返回 rollback_id

**关键点**: 只接受 patch_id，不接受 pattern/replacement

---

### Test 2.1: 基础 apply 流程

```python
def test_apply_edit_basic_flow(tmp_path):
    """
    Given: propose_edit 返回的 patch_id
    When: apply_edit
    Then: 文件被修改，返回 rollback_id
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    propose_result = tool.propose_edit("old", "new", "**/*.py")
    patch_id = propose_result["patch_id"]

    # Execute
    apply_result = tool.apply_edit(
        patch_id=patch_id,
        execution_plan=ExecutionPlan()
    )

    # Verify
    assert apply_result["success"] is True
    assert apply_result["rollback_id"] is not None
    assert file.read_text() == "new\n"  # 文件已修改
```

---

### Test 2.2: 无效 patch_id 拒绝

```python
def test_apply_invalid_patch_id(tmp_path):
    """
    Given: 无效的 patch_id
    When: apply_edit
    Then: 抛出 PatchNotFoundError
    """
    tool = SafeEditTool(project_root=tmp_path)

    with pytest.raises(PatchNotFoundError):
        tool.apply_edit(
            patch_id="invalid-uuid",
            execution_plan=ExecutionPlan()
        )
```

---

### Test 2.3: 不接受 pattern/replacement

```python
def test_apply_does_not_accept_pattern_replacement(tmp_path):
    """
    Given: apply_edit 只接受 patch_id
    When: 尝试传入 pattern/replacement
    Then: 类型错误（接口不允许）
    """
    tool = SafeEditTool(project_root=tmp_path)

    # Verify: apply_edit 签名只接受 patch_id 和 execution_plan
    import inspect
    sig = inspect.signature(tool.apply_edit)
    assert "patch_id" in sig.parameters
    assert "execution_plan" in sig.parameters
    assert "pattern" not in sig.parameters
    assert "replacement" not in sig.parameters
```

---

### Test 2.4: Patch 只能 apply 一次

```python
def test_patch_can_only_apply_once(tmp_path):
    """
    Given: patch_id 已经 applied
    When: 再次 apply 同一个 patch_id
    Then: 抛出 PatchAlreadyAppliedError
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    result = tool.propose_edit("old", "new", "**/*.py")
    patch_id = result["patch_id"]

    # First apply - OK
    tool.apply_edit(patch_id, ExecutionPlan())

    # Second apply - Error
    with pytest.raises(PatchAlreadyAppliedError):
        tool.apply_edit(patch_id, ExecutionPlan())
```

---

### Test 2.5: 多文件原子性应用

```python
def test_apply_multiple_files_atomic(tmp_path):
    """
    Given: patch 影响多个文件
    When: apply_edit
    Then: 所有文件同时修改（原子性）
    """
    # Setup
    file_a = tmp_path / "a.py"
    file_b = tmp_path / "b.py"
    file_a.write_text("old\n")
    file_b.write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    result = tool.propose_edit("old", "new", "**/*.py")

    # Apply
    tool.apply_edit(result["patch_id"], ExecutionPlan())

    # Verify: 两个文件都被修改
    assert file_a.read_text() == "new\n"
    assert file_b.read_text() == "new\n"
```

---

### Test 2.6: Patch 过期检测（文件变更冲突）

```python
def test_apply_detects_file_changes(tmp_path):
    """
    Given: propose_edit 生成 patch
    When: 文件在 propose 后被修改
    Then: apply_edit 检测冲突，拒绝应用
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("version = '1.0'\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Step 1: Propose
    result = tool.propose_edit("1.0", "2.0", "**/*.py")
    patch_id = result["patch_id"]

    # Step 2: 文件被修改（模拟用户或其他进程修改）
    file.write_text("version = '1.5'\n")  # 内容已变化

    # Step 3: Apply - 应该检测到冲突
    with pytest.raises(PatchOutdatedError) as exc:
        tool.apply_edit(patch_id, ExecutionPlan())

    assert "has changed since propose_edit" in str(exc.value)

    # Verify: 文件未被修改（保持用户的 1.5）
    assert file.read_text() == "version = '1.5'\n"
```

---

### DoD 2: apply_edit 只接受 patch_id ✅

验收标准：
- ✅ 验证 patch_id 有效性
- ✅ 应用 patch 到工作目录
- ✅ 不接受 pattern/replacement（物理删除错误路径）
- ✅ Patch 只能 apply 一次
- ✅ 多文件原子性应用
- ✅ 检测文件变更冲突（Patch 过期）

---

## 🔄 Cycle 3: ExecutionPlan 集成

### Test 3.1: max_files 约束

```python
def test_execution_plan_max_files_constraint(tmp_path):
    """
    Given: ExecutionPlan.max_files = 2
    When: patch 影响 3 个文件
    Then: apply 失败，抛出 ConstraintViolationError
    """
    # Setup
    for i in range(3):
        (tmp_path / f"file{i}.py").write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    result = tool.propose_edit("old", "new", "**/*.py")

    # Execute with constraint
    plan = ExecutionPlan(limits=ExecutionLimits(max_files=2))

    with pytest.raises(ConstraintViolationError) as exc:
        tool.apply_edit(result["patch_id"], plan)

    assert "max_files" in str(exc.value)

    # Verify: 文件未被修改（约束在写入前检查）
    assert (tmp_path / "file0.py").read_text() == "old\n"
```

---

### Test 3.2: max_changes 约束

```python
def test_execution_plan_max_changes_constraint(tmp_path):
    """
    Given: ExecutionPlan.max_changes = 5
    When: patch 有 10 处修改
    Then: apply 失败
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old " * 10)  # 10 occurrences

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    result = tool.propose_edit("old", "new", "**/*.py")

    # Execute with constraint
    plan = ExecutionPlan(limits=ExecutionLimits(max_changes=5))

    with pytest.raises(ConstraintViolationError):
        tool.apply_edit(result["patch_id"], plan)
```

---

### Test 3.3: timeout 约束

```python
def test_execution_plan_timeout_constraint(tmp_path):
    """
    Given: ExecutionPlan.timeout = 1s
    When: apply 超过 1s
    Then: 超时中止，回滚
    """
    # Setup: 创建大量文件模拟慢速写入
    for i in range(1000):
        (tmp_path / f"file{i}.py").write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    result = tool.propose_edit("old", "new", "**/*.py")

    # Execute with timeout
    plan = ExecutionPlan(limits=ExecutionLimits(timeout_seconds=1))

    with pytest.raises(TimeoutError):
        tool.apply_edit(result["patch_id"], plan)
```

---

### Test 3.4: dry_run 模式

```python
def test_execution_plan_dry_run_mode(tmp_path):
    """
    Given: ExecutionPlan.dry_run = True
    When: apply_edit
    Then: 不修改文件，但返回预期结果
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    result = tool.propose_edit("old", "new", "**/*.py")

    # Execute in dry_run mode
    plan = ExecutionPlan(dry_run=True)
    apply_result = tool.apply_edit(result["patch_id"], plan)

    # Verify
    assert apply_result["success"] is True
    assert apply_result["dry_run"] is True
    assert file.read_text() == "old\n"  # 文件未修改
```

---

### DoD 3: ExecutionPlan 约束检查生效 ✅

验收标准：
- ✅ max_files 约束执行
- ✅ max_changes 约束执行
- ✅ timeout 约束执行
- ✅ dry_run 模式支持
- ✅ 约束违规在写入前检查（不污染文件）

---

## 🔄 Cycle 4: 回滚机制

### Test 4.1: 基础回滚流程

```python
def test_apply_failure_triggers_rollback(tmp_path):
    """
    Given: apply 过程中发生错误
    When: 写入失败
    Then: 自动回滚，文件恢复原始内容
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    result = tool.propose_edit("old", "new", "**/*.py")

    # Mock 写入失败
    with patch.object(file, 'write_text', side_effect=IOError("Disk full")):
        with pytest.raises(ApplyError):
            tool.apply_edit(result["patch_id"], ExecutionPlan())

    # Verify: 文件被回滚
    assert file.read_text() == "old\n"
```

---

### Test 4.2: 手动回滚

```python
def test_manual_rollback(tmp_path):
    """
    Given: apply 成功完成
    When: 用户调用 rollback(rollback_id)
    Then: 文件恢复到 apply 前的状态
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Apply
    result = tool.propose_edit("old", "new", "**/*.py")
    apply_result = tool.apply_edit(result["patch_id"], ExecutionPlan())

    assert file.read_text() == "new\n"  # 已修改

    # Rollback
    tool.rollback(apply_result["rollback_id"])

    # Verify: 恢复原始内容
    assert file.read_text() == "old\n"
```

---

### Test 4.3: RollbackManager 集成

```python
def test_rollback_manager_integration(tmp_path):
    """
    Given: 使用 RollbackManager 创建备份
    When: apply_edit
    Then: RollbackManager 的 API 被正确调用
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    # Mock RollbackManager
    mock_rollback = Mock(spec=RollbackManager)
    mock_rollback.create_backup.return_value = "rollback-123"

    tool = SafeEditTool(project_root=tmp_path, rollback_manager=mock_rollback)

    # Execute
    result = tool.propose_edit("old", "new", "**/*.py")
    tool.apply_edit(result["patch_id"], ExecutionPlan())

    # Verify: RollbackManager 被调用
    mock_rollback.create_backup.assert_called_once()
```

---

### Test 4.4: 部分失败回滚

```python
def test_partial_failure_rollback(tmp_path):
    """
    Given: 多文件 apply，第二个文件失败
    When: 写入部分成功
    Then: 所有文件回滚（包括已成功的）
    """
    # Setup
    file_a = tmp_path / "a.py"
    file_b = tmp_path / "b.py"
    file_a.write_text("old\n")
    file_b.write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    result = tool.propose_edit("old", "new", "**/*.py")

    # Mock: file_b 写入失败
    original_write = file_b.write_text
    def failing_write(content):
        raise IOError("Permission denied")

    with patch.object(file_b, 'write_text', side_effect=failing_write):
        with pytest.raises(ApplyError):
            tool.apply_edit(result["patch_id"], ExecutionPlan())

    # Verify: 两个文件都回滚
    assert file_a.read_text() == "old\n"  # 已成功但被回滚
    assert file_b.read_text() == "old\n"  # 失败被回滚
```

---

### DoD 4: 失败自动回滚 ✅

验收标准：
- ✅ 写入失败自动回滚
- ✅ 手动回滚支持
- ✅ RollbackManager 集成
- ✅ 部分失败全部回滚（原子性）
- ✅ 回滚后文件内容完全恢复

---

## 🔄 Cycle 5: MCP 工具暴露

### Test 5.1: ProposeEditTool MCP 接口

```python
def test_propose_edit_mcp_tool(tmp_path):
    """
    Given: ProposeEditTool 暴露为 MCP 工具
    When: LLM 调用 mcp__evolvai__propose_edit
    Then: 返回 JSON 格式结果
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    tool = ProposeEditTool(project_root=tmp_path)

    # Execute (模拟 MCP 调用)
    result = tool.apply(
        pattern="old",
        replacement="new",
        scope="**/*.py"
    )

    # Verify: JSON 格式
    result_json = json.loads(result)
    assert "patch_id" in result_json
    assert "unified_diff" in result_json
    assert "affected_files" in result_json
```

---

### Test 5.2: ApplyEditTool MCP 接口

```python
def test_apply_edit_mcp_tool(tmp_path):
    """
    Given: ApplyEditTool 暴露为 MCP 工具
    When: LLM 调用 mcp__evolvai__apply_edit
    Then: 应用 patch 并返回结果
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    propose_tool = ProposeEditTool(project_root=tmp_path)
    apply_tool = ApplyEditTool(project_root=tmp_path)

    # Propose
    propose_result = json.loads(propose_tool.apply("old", "new", "**/*.py"))
    patch_id = propose_result["patch_id"]

    # Apply (模拟 MCP 调用)
    apply_result = apply_tool.apply(
        patch_id=patch_id,
        execution_plan={
            "limits": {"max_files": 10, "max_changes": 50}
        }
    )

    # Verify
    result_json = json.loads(apply_result)
    assert result_json["success"] is True
    assert file.read_text() == "new\n"
```

---

### Test 5.3: MCP 服务器注册

```python
def test_mcp_server_registration():
    """
    Given: EvolvAI MCP 服务器启动
    When: 列出可用工具
    Then: propose_edit 和 apply_edit 在列表中
    """
    from serena.mcp import get_mcp_tools

    tools = get_mcp_tools()
    tool_names = [t.name for t in tools]

    assert "mcp__evolvai__propose_edit" in tool_names
    assert "mcp__evolvai__apply_edit" in tool_names
```

---

### DoD 5: MCP 工具可用 ✅

验收标准：
- ✅ ProposeEditTool 暴露为 MCP 工具
- ✅ ApplyEditTool 暴露为 MCP 工具
- ✅ 返回 JSON 格式结果
- ✅ MCP 服务器正确注册
- ✅ LLM 可调用（端到端测试）

---

## 🔄 Cycle 6: 集成测试和端到端场景

### Test 6.1: 完整编辑流程

```python
def test_end_to_end_edit_flow(tmp_path):
    """
    Scenario: 用户重构代码
    Given: 项目有多个文件
    When: propose → 预览 → apply
    Then: 代码被正确重构
    """
    # Setup
    (tmp_path / "main.py").write_text("def old_func():\n    pass\n")
    (tmp_path / "utils.py").write_text("from main import old_func\n")
    (tmp_path / "test.py").write_text("old_func()\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Step 1: Propose
    propose_result = tool.propose_edit(
        pattern="old_func",
        replacement="new_func",
        scope="**/*.py"
    )

    # Verify preview
    assert propose_result["affected_files"] == ["main.py", "utils.py", "test.py"]

    # Step 2: Apply
    apply_result = tool.apply_edit(
        propose_result["patch_id"],
        ExecutionPlan(limits=ExecutionLimits(max_files=10))
    )

    # Verify
    assert (tmp_path / "main.py").read_text() == "def new_func():\n    pass\n"
    assert (tmp_path / "utils.py").read_text() == "from main import new_func\n"
```

---

### Test 6.2: 用户修改冲突处理

```python
def test_user_modification_conflict(tmp_path):
    """
    Scenario: propose 后用户修改了文件
    Given: propose_edit 生成 patch
    When: 用户修改文件后 apply
    Then: 检测冲突，拒绝 apply
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("version = '1.0'\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Step 1: Propose
    result = tool.propose_edit("1.0", "2.0", "**/*.py")

    # Step 2: 用户修改文件
    file.write_text("version = '1.5'\n")  # 用户改成 1.5

    # Step 3: Apply - 应该检测冲突
    with pytest.raises(ConflictError) as exc:
        tool.apply_edit(result["patch_id"], ExecutionPlan())

    assert "file modified after propose" in str(exc.value)
```

---

### Test 6.3: 大规模重构

```python
def test_large_scale_refactor(tmp_path):
    """
    Scenario: 重构 100+ 文件
    Given: 大型项目
    When: propose → apply
    Then: 性能符合预期（<1s）
    """
    # Setup: 创建 100 个文件
    for i in range(100):
        (tmp_path / f"file{i}.py").write_text(f"id = {i}\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose
    start = time.time()
    result = tool.propose_edit(r"id = (\d+)", r"identifier = \1", "**/*.py")
    propose_time = time.time() - start

    # Apply
    start = time.time()
    tool.apply_edit(result["patch_id"], ExecutionPlan())
    apply_time = time.time() - start

    # Verify performance
    assert propose_time < 0.5  # <500ms
    assert apply_time < 1.0    # <1s
```

---

### Test 6.4: ExecutionPlan 约束保护

```python
def test_execution_plan_prevents_runaway(tmp_path):
    """
    Scenario: 防止 AI 失控修改
    Given: LLM 尝试修改 1000 个文件
    When: ExecutionPlan.max_files = 50
    Then: 被拒绝，未修改任何文件
    """
    # Setup
    for i in range(1000):
        (tmp_path / f"file{i}.py").write_text("data\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Propose (1000 files)
    result = tool.propose_edit("data", "info", "**/*.py")
    assert result["total_changes"] == 1000

    # Apply with constraint
    plan = ExecutionPlan(limits=ExecutionLimits(max_files=50))

    with pytest.raises(ConstraintViolationError):
        tool.apply_edit(result["patch_id"], plan)

    # Verify: 所有文件未被修改
    assert all(
        (tmp_path / f"file{i}.py").read_text() == "data\n"
        for i in range(1000)
    )
```

---

### Test 6.5: 回滚后重新 propose

```python
def test_rollback_and_repropose(tmp_path):
    """
    Scenario: Apply 后发现问题，回滚，重新 propose
    Given: apply 完成
    When: rollback → 修改 pattern → repropose
    Then: 新 patch 基于回滚后的内容
    """
    # Setup
    file = tmp_path / "main.py"
    file.write_text("old\n")

    tool = SafeEditTool(project_root=tmp_path)

    # Step 1: First attempt
    result1 = tool.propose_edit("old", "wrong", "**/*.py")
    apply_result = tool.apply_edit(result1["patch_id"], ExecutionPlan())

    assert file.read_text() == "wrong\n"

    # Step 2: Rollback
    tool.rollback(apply_result["rollback_id"])
    assert file.read_text() == "old\n"

    # Step 3: Repropose with correct replacement
    result2 = tool.propose_edit("old", "correct", "**/*.py")
    tool.apply_edit(result2["patch_id"], ExecutionPlan())

    assert file.read_text() == "correct\n"
```

---

### DoD 6: 端到端场景通过 ✅

验收标准：
- ✅ 完整编辑流程（propose → apply）
- ✅ 用户修改冲突检测
- ✅ 大规模重构性能达标
- ✅ ExecutionPlan 约束保护生效
- ✅ 回滚后可重新 propose

---

## 📊 测试覆盖率目标

| 模块 | 目标覆盖率 | 关键路径 |
|------|-----------|---------|
| `propose_edit()` | 100% | 文件扫描、diff 生成、patch 存储 |
| `apply_edit()` | 100% | patch 验证、约束检查、文件写入 |
| `rollback()` | 100% | 备份恢复、错误处理 |
| ExecutionPlan 集成 | 100% | 所有约束类型 |
| MCP 工具 | 100% | JSON 序列化、参数验证 |

**总体目标**: ≥95% 行覆盖率，100% 分支覆盖率（核心路径）

---

## 🚀 实施顺序

### Day 1: Cycle 1 (propose_edit)
- 8:00-10:00: Test 1.1-1.3 (基础 + 多文件)
- 10:00-12:00: Test 1.4-1.6 (边界 + 存储)
- 13:00-15:00: 实现 propose_edit 核心逻辑
- 15:00-17:00: DoD 1 验收

### Day 2: Cycle 2 (apply_edit)
- 8:00-10:00: Test 2.1-2.3 (基础 + 验证)
- 10:00-12:00: Test 2.4-2.5 (约束 + 原子性)
- 13:00-15:00: 实现 apply_edit 核心逻辑
- 15:00-17:00: DoD 2 验收

### Day 3 (上午): Cycle 3 (ExecutionPlan)
- 8:00-10:00: Test 3.1-3.2 (max_files + max_changes)
- 10:00-12:00: Test 3.3-3.4 (timeout + dry_run)
- 12:00-12:30: DoD 3 验收

### Day 3 (下午): Cycle 4 (回滚)
- 13:00-14:30: Test 4.1-4.2 (自动 + 手动)
- 14:30-16:00: Test 4.3-4.4 (集成 + 部分失败)
- 16:00-17:00: DoD 4 验收

### Day 4: Cycle 5 (MCP 集成)
- 8:00-10:00: Test 5.1-5.2 (MCP 工具接口)
- 10:00-12:00: Test 5.3 + MCP 服务器配置
- 13:00-15:00: MCP docstring 优化
- 15:00-17:00: DoD 5 验收

### Day 5: Cycle 6 (集成测试)
- 8:00-10:00: Test 6.1-6.2 (端到端 + 冲突)
- 10:00-12:00: Test 6.3-6.4 (性能 + 保护)
- 13:00-14:00: Test 6.5 (回滚场景)
- 14:00-16:00: 完整回归测试
- 16:00-17:00: DoD 6 验收 + 文档更新

---

## 📝 Notes

### 复用现有组件

1. **RollbackManager** (来自 batch_edit):
   ```python
   # src/evolvai/core/rollback_manager.py
   rollback_manager.create_file_backup(file_path)
   rollback_manager.rollback_file_backup(rollback_hash, file_path)
   ```

2. **ExecutionPlan** (来自 Phase 0):
   ```python
   # src/evolvai/core/execution_plan.py
   ExecutionPlan(
       limits=ExecutionLimits(max_files=10, max_changes=50, timeout_seconds=30),
       dry_run=False
   )
   ```

3. **unified diff 生成** (标准库):
   ```python
   import difflib
   difflib.unified_diff(original_lines, new_lines, ...)
   ```

### 不实现的功能（YAGNI）

- ❌ Git stash 集成（Phase 1 MVP 不需要）
- ❌ 测试验证钩子（可选，Phase 2+）
- ❌ 冲突自动解决（过于复杂）
- ❌ UI 预览界面（MCP 客户端负责）

---

**最后更新**: 2025-01-19
**创建人**: EvolvAI Team
**状态**: Ready for Implementation
**预计开始**: TBD
