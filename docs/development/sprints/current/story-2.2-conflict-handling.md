# Story 2.2 冲突处理机制详解

**状态**: [DESIGN]
**创建时间**: 2025-01-07
**相关Story**: story-2.2-bdd-scenarios.md Scenario 5-6

## 1. 什么是冲突？

在Patch-First架构中，**冲突**指的是：

> **当propose阶段生成的patch无法正确应用到apply阶段的文件状态时，产生的不一致情况。**

### 1.1 冲突产生的时间线

```
时间线：
T1: propose_edit() → 扫描文件A → 生成patch_123
T2: （中间时刻）→ 文件A被外部修改
T3: apply_edit(patch_123) → 尝试应用到文件A → 冲突！
```

### 1.2 为什么会有冲突？

Patch-First架构的核心特点是**分离提案和执行**：

- **propose_edit()**: 基于**当前文件状态**生成patch
- **apply_edit()**: 在**未来某个时刻**应用patch
- **时间差**: T1到T3之间，文件可能已被修改

---

## 2. 冲突的类型

### 类型1: Pattern不存在冲突

**场景**: Pattern在propose时存在，apply时已被删除

```python
# T1: propose时的文件
def getUserData():
    return "user"

# T2: 中间修改（外部IDE或其他工具）
def fetchUserData():  # 已经改名了！
    return "user"

# T3: apply时尝试替换 getUserData → fetchUserData
# 结果: Pattern "getUserData" 不存在 → 冲突！
```

**影响**:
- `re.sub(pattern, replacement, content)` 无法找到匹配
- 替换后内容与原内容相同
- 文件未发生变化

### 类型2: Pattern多次匹配冲突

**场景**: Pattern在propose时匹配1次，apply时匹配多次

```python
# T1: propose时的文件
def getUserData():
    return "user"

# T2: 中间修改（新增了重复代码）
def getUserData():
    return "user"

def getUserDataBackup():
    data = getUserData()
    return data

# T3: apply时替换 getUserData → fetchUserData
# 结果: 替换了2处，但patch只记录了1处的变化 → 行为不一致！
```

**影响**:
- `re.sub()` 会替换所有匹配
- 但unified_diff只反映propose时的1处变化
- 产生意外的多处修改

### 类型3: 文件结构变化冲突

**场景**: 文件在propose时存在，apply时被删除或移动

```python
# T1: propose扫描到 src/user.go
patch_content.affected_files = ["src/user.go"]

# T2: 中间修改（文件被移动）
src/user.go → deleted
pkg/user.go → created

# T3: apply时尝试读取 src/user.go
# 结果: FileNotFoundError → 冲突！
```

**影响**:
- `src_file.read_text()` 抛出异常
- 无法完成替换操作

### 类型4: 内容基准漂移冲突

**场景**: Pattern虽然存在，但周围上下文已变化

```python
# T1: propose时的文件
def getUserData():
    return "user"

def getUser():
    return getUserData()

# T2: 中间修改（上下文改变）
def getUserData():
    return "user"

def getUser():
    # Deprecated: use fetchUserData
    return getUserData()

# T3: apply时替换 getUserData → fetchUserData
# 结果: 注释中的提示与实际函数名不匹配 → 语义冲突！
```

**影响**:
- Pattern匹配成功，但语义不一致
- 可能产生误导性代码

---

## 3. 当前简化实现的冲突处理

### 3.1 当前架构

```python
def apply_edit(self, patch_id: str):
    """当前简化实现（Day 3完成）"""

    # 1. 读取原始文件
    original_content = src_file.read_text()

    # 2. 应用替换
    new_content = re.sub(pattern, replacement, original_content)

    # 3. 直接写回主目录
    src_file.write_text(new_content)
```

### 3.2 自然处理的冲突类型

| 冲突类型 | 当前行为 | 是否安全 |
|---------|---------|---------|
| **类型1: Pattern不存在** | `re.sub()` 返回原内容不变，文件未修改 | ✅ 安全 |
| **类型2: Pattern多次匹配** | 替换所有匹配，可能产生意外修改 | ⚠️ 半安全 |
| **类型3: 文件不存在** | `FileNotFoundError` 异常，跳过该文件 | ✅ 安全 |
| **类型4: 上下文变化** | Pattern匹配成功，但可能语义错误 | ❌ 不安全 |

### 3.3 当前的"隐式安全机制"

**机制1: 跳过无变化文件**

```python
# propose_edit中已有检查
if new_content == original_content:
    continue  # 不生成diff，不加入affected_files
```

**机制2: 异常时跳过文件**

```python
# apply_edit中的异常处理
try:
    original_content = src_file.read_text()
except (UnicodeDecodeError, PermissionError):
    continue  # 跳过该文件
```

**机制3: 临时目录隔离**

```python
# apply_edit中先在临时目录验证
temp_file.write_text(new_content)
# 只有成功才复制回主目录
shutil.copy2(temp_file, src_file)
```

### 3.4 当前未处理的风险

| 风险 | 描述 | 影响 |
|-----|------|------|
| **多次匹配** | 替换了比预期更多的地方 | 可能产生意外修改 |
| **语义冲突** | Pattern匹配但上下文已变 | 代码可能逻辑错误 |
| **部分成功** | 10个文件中5个成功5个失败 | 不一致状态 |

---

## 4. 完整冲突处理机制（Scenario 5-6）

如果实施Scenario 5-6，应该包含以下机制：

### 4.1 Scenario 5: 主动冲突检测

**目标**: 在apply前检测冲突，失败时回滚

```python
def apply_edit_with_conflict_detection(self, patch_id: str):
    """完整实现（Scenario 5）"""

    # Phase 1: 预检测（在临时目录）
    conflicts = []
    for file in affected_files:
        # 1.1 文件存在性检查
        if not file.exists():
            conflicts.append({
                "file": file,
                "type": "FILE_NOT_FOUND",
                "message": "File was deleted or moved"
            })
            continue

        # 1.2 Pattern匹配次数检查
        original_content = file.read_text()
        match_count_now = len(re.findall(pattern, original_content))
        match_count_expected = patch_metadata["match_count"]

        if match_count_now == 0:
            conflicts.append({
                "file": file,
                "type": "PATTERN_NOT_FOUND",
                "message": f"Pattern '{pattern}' no longer exists"
            })
        elif match_count_now > match_count_expected:
            conflicts.append({
                "file": file,
                "type": "MULTIPLE_MATCHES",
                "message": f"Pattern matches {match_count_now} times, expected {match_count_expected}"
            })

        # 1.3 上下文完整性检查（可选）
        if not self._verify_context(file, patch_metadata["context_lines"]):
            conflicts.append({
                "file": file,
                "type": "CONTEXT_CHANGED",
                "message": "Surrounding context has changed"
            })

    # Phase 2: 冲突处理决策
    if conflicts:
        # 2.1 抛出详细的冲突报告
        raise PatchConflictError(
            patch_id=patch_id,
            conflicts=conflicts,
            resolution_strategies=["abort", "force", "interactive"]
        )

    # Phase 3: 无冲突则正常执行
    return self._execute_in_worktree(patch_id)
```

**关键改进**:
1. **预检测**: 在真正修改文件前检测所有潜在冲突
2. **详细报告**: 冲突类型、位置、原因一目了然
3. **原子性**: 要么全部成功，要么全部失败（不留部分成功状态）

### 4.2 Scenario 6: 隔离验证机制

**目标**: 在临时环境中先验证，通过后才合并

```python
def apply_edit_with_validation(self, patch_id: str, validation_config: dict):
    """完整实现（Scenario 6）"""

    # Phase 1: 在worktree中执行
    worktree_path = self._create_worktree()
    try:
        # 1.1 在worktree中应用patch
        self._apply_in_worktree(worktree_path, patch_id)

        # Phase 2: 执行验证步骤
        validation_results = []

        # 2.1 语法验证（可选）
        if validation_config.get("check_syntax"):
            result = self._run_syntax_check(worktree_path)
            validation_results.append(result)

        # 2.2 类型检查（可选）
        if validation_config.get("check_types"):
            result = self._run_type_check(worktree_path)
            validation_results.append(result)

        # 2.3 测试运行（可选）
        if validation_config.get("run_tests"):
            result = self._run_tests(worktree_path)
            validation_results.append(result)

        # 2.4 自定义验证脚本（可选）
        if validation_script := validation_config.get("custom_script"):
            result = self._run_custom_validation(worktree_path, validation_script)
            validation_results.append(result)

        # Phase 3: 验证结果决策
        if all(r["success"] for r in validation_results):
            # 3.1 验证通过 → 合并到主目录
            self._merge_from_worktree(worktree_path)
            return ApplyResult(success=True, validation_passed=True)
        else:
            # 3.2 验证失败 → 丢弃worktree，返回失败
            failed_checks = [r for r in validation_results if not r["success"]]
            raise ValidationError(
                patch_id=patch_id,
                failed_checks=failed_checks
            )

    finally:
        # Phase 4: 清理worktree
        self._cleanup_worktree(worktree_path)
```

**关键改进**:
1. **隔离验证**: 在临时环境中运行所有检查
2. **多重验证**: 语法、类型、测试、自定义脚本
3. **安全合并**: 只有全部验证通过才修改主目录

---

## 5. 冲突检测策略矩阵

| 检测阶段 | 检测项 | 简化实现 | 完整实现（S5-6） | 成本 |
|---------|-------|---------|-----------------|-----|
| **预检测** | 文件存在性 | ❌ | ✅ | 低 |
| **预检测** | Pattern匹配次数 | ❌ | ✅ | 低 |
| **预检测** | 上下文完整性 | ❌ | ✅ | 中 |
| **应用中** | 异常捕获 | ✅ | ✅ | 低 |
| **应用后** | 语法验证 | ❌ | ✅ | 中 |
| **应用后** | 类型检查 | ❌ | ✅ | 中 |
| **应用后** | 测试运行 | ❌ | ✅ | 高 |

---

## 6. 冲突解决策略

### 6.1 Abort策略（默认）

```python
if conflicts:
    raise PatchConflictError(conflicts)
    # 不做任何修改，返回错误
```

**适用场景**: MVP阶段，保守安全

### 6.2 Force策略（高级）

```python
if conflicts:
    # 忽略冲突，强制应用
    # 用户自行承担风险
    warnings.warn(f"Forced apply with {len(conflicts)} conflicts")
    return self._force_apply(patch_id)
```

**适用场景**: 用户明确知道风险，需要强制执行

### 6.3 Interactive策略（未来）

```python
if conflicts:
    # 逐个冲突询问用户
    for conflict in conflicts:
        action = self._ask_user_resolution(conflict)
        if action == "skip":
            continue
        elif action == "edit":
            self._interactive_edit(conflict)
        elif action == "abort":
            raise PatchConflictError([conflict])
```

**适用场景**: IDE集成，图形化冲突解决

---

## 7. 实施建议

### 7.1 MVP阶段（当前）

**策略**: "乐观执行 + 自然失败"

- ✅ 依赖`re.sub()`的自然行为（Pattern不存在时不修改）
- ✅ 依赖临时目录隔离（失败不影响主目录）
- ✅ 依赖异常机制跳过问题文件

**优点**:
- 实现简单（已完成）
- 大部分场景安全
- 符合KISS原则

**缺点**:
- 没有主动冲突检测
- 没有详细的冲突报告
- 多次匹配可能产生意外修改

### 7.2 Phase 2阶段（可选）

**如果遇到以下情况，考虑实施Scenario 5-6**:

1. **用户反馈**: 频繁遇到意外修改问题
2. **生产需求**: 需要严格的变更控制
3. **合规要求**: 需要完整的变更审计轨迹
4. **协作场景**: 多人同时编辑同一项目

**实施顺序**:
1. **先实施Scenario 5**: 主动冲突检测（成本低，收益高）
2. **再实施Scenario 6**: 隔离验证机制（成本高，但提供最强保证）

### 7.3 成本效益分析

| 方案 | 实施成本 | 运行成本 | 安全性 | 推荐场景 |
|-----|---------|---------|-------|---------|
| **简化实现** | 低（已完成） | 低 | 中 | MVP、原型、个人项目 |
| **+Scenario 5** | 中（2-3天） | 低 | 高 | 团队协作、生产环境 |
| **+Scenario 6** | 高（4-5天） | 高 | 极高 | 关键系统、合规要求 |

---

## 8. 测试场景示例

### 8.1 测试Scenario 5的用例

```python
def test_apply_patch_conflict_rollback(self, tmp_path):
    """测试冲突检测和回滚机制"""

    # Arrange - 准备初始状态
    test_file = tmp_path / "user.go"
    test_file.write_text('func getUserData() { return "user" }')

    editor = PatchEditor(project_root=tmp_path)
    proposal = editor.propose_edit(
        pattern="getUserData",
        replacement="fetchUserData"
    )

    # Act - 模拟文件被外部修改（制造冲突）
    test_file.write_text('func getUser() { return "user" }')  # getUserData已被删除

    # Assert - 验证冲突检测
    with pytest.raises(PatchConflictError) as exc_info:
        editor.apply_edit(patch_id=proposal.patch_id)

    # 验证冲突详情
    conflict = exc_info.value.conflicts[0]
    assert conflict["type"] == "PATTERN_NOT_FOUND"
    assert conflict["file"] == "user.go"

    # 验证回滚：主目录未被修改
    assert test_file.read_text() == 'func getUser() { return "user" }'
```

### 8.2 测试Scenario 6的用例

```python
def test_apply_with_isolated_validation(self, tmp_path):
    """测试隔离验证机制"""

    # Arrange
    test_file = tmp_path / "calc.py"
    test_file.write_text('def add(a, b): return a + b')

    editor = PatchEditor(project_root=tmp_path)
    proposal = editor.propose_edit(
        pattern="add",
        replacement="sum"
    )

    # Act - 配置验证规则
    validation_config = {
        "check_syntax": True,
        "run_tests": False  # 简化测试
    }

    result = editor.apply_edit(
        patch_id=proposal.patch_id,
        validation_config=validation_config
    )

    # Assert
    assert result.success is True
    assert result.validation_passed is True
    assert 'def sum(a, b)' in test_file.read_text()
```

---

## 9. 决策记录

### 9.1 为什么当前MVP不实施Scenario 5-6？

**决策**: 降级为可选功能

**理由**:
1. **KISS原则**: 简化实现已提供基本安全性
2. **成本考虑**: 完整冲突检测需额外2-3天开发
3. **需求不明确**: 未获得用户反馈证实需要
4. **可延迟**: 可根据实际使用情况再决定

### 9.2 什么时候应该实施？

**触发条件**:
1. 用户报告意外修改问题 > 3次
2. 团队协作场景需要严格变更控制
3. 生产环境部署需要合规审计
4. 与CI/CD流程集成需要验证钩子

### 9.3 替代方案

**方案1**: 限制使用场景
- 只在"确定文件未被修改"时使用propose → apply
- 对于可能被修改的文件，直接使用safe_edit

**方案2**: 缩短时间窗口
- propose后立即apply，减少中间修改风险
- 提供`propose_and_apply()`快捷方法

**方案3**: 增强用户提示
- apply前显示affected_files，让用户确认
- apply后显示diff，让用户验证结果

---

## 10. 总结

### 当前状态（MVP）

```
冲突处理 = 自然失败 + 临时目录隔离 + 异常跳过
```

**安全性**: ⭐⭐⭐☆☆（60% 安全）
**复杂度**: ⭐☆☆☆☆（极简）
**成本**: ⭐☆☆☆☆（已完成）

### 完整实施（Scenario 5-6）

```
冲突处理 = 主动检测 + 详细报告 + 隔离验证 + 原子回滚
```

**安全性**: ⭐⭐⭐⭐⭐（95% 安全）
**复杂度**: ⭐⭐⭐⭐☆（较复杂）
**成本**: ⭐⭐⭐⭐☆（4-5天）

### 建议

**现阶段**: 使用MVP实现，收集用户反馈
**下一阶段**: 根据反馈决定是否实施Scenario 5-6
**长期**: 考虑与ExecutionPlan集成，提供可配置的冲突策略
