# BDD思维测试模板

**版本**: 1.0
**创建日期**: 2025-11-06
**适用范围**: 所有新测试编写和测试重构
**状态**: [ACTIVE]

---

## 📋 模板概述

本模板采用**轻量级BDD思维**，在保持pytest框架的同时，引入Given-When-Then结构化思维，提升测试可读性和维护性。

**核心原则**：
- ✅ 使用pytest，不引入额外BDD工具
- ✅ 采用Given-When-Then注释结构
- ✅ 行为驱动命名：`test_[角色]_can_[动作]_when_[条件]`
- ✅ 测试代码即可执行的用户手册

---

## 🚨 强制标注要求（MANDATORY）

**所有测试都必须在docstring中包含以下三项标注**：

```python
def test_something(self):
    """[测试描述]

    Story: story-X.X-[name].md Cycle Y    ← 必须：指定Story文档和Cycle
    Scenario: "[BDD场景名称]"              ← 必须：对应Story中的场景
    DoD: [验收标准编号]                    ← 必须：如F1/Q1/P1

    Given [前置条件]
    When [动作]
    Then [期望结果]
    """
```

**强制检查规则**：
1. ❌ **找不到Story文档对应** → 这是过度设计 → 不要写
2. ❌ **找不到BDD场景对应** → 这是测试实现细节 → 不要写
3. ❌ **找不到DoD标准对应** → 这是自己发明需求 → 不要写

**来源**：`CLAUDE.md` - Development Mandatory Checkpoints

**教训**：Feature 2.2 测试失败率20% → 原因是测试没有映射到实际需求

---

## 🎯 测试命名规范

### 基本模式

```python
test_[user_role]_can_[action]_when_[condition]
test_[user_role]_cannot_[action]_when_[condition]
test_[system]_[behavior]_when_[trigger]
```

### 命名示例

| 场景类型 | 技术命名（避免） | BDD命名（推荐） |
|---------|----------------|----------------|
| 成功场景 | `test_valid_plan_passes` | `test_user_can_execute_with_valid_plan` |
| 失败场景 | `test_invalid_plan_raises_error` | `test_execution_blocked_when_plan_invalid` |
| 边界条件 | `test_max_files_limit` | `test_operation_fails_when_exceeding_file_limit` |
| 回滚场景 | `test_rollback_on_failure` | `test_changes_reverted_when_operation_fails` |
| 集成场景 | `test_validator_integration` | `test_validator_prevents_invalid_operations` |

---

## 📝 基础测试模板

### 模板1：成功路径测试

```python
def test_user_can_[action]_when_[condition](self):
    """[简短描述用户能做什么]

    Story: story-X.X-[name].md Cycle Y
    Scenario: [具体场景名称]
    DoD: [验收标准编号，如F1/Q1/P1]

    Given [前置条件1]
    And [前置条件2]
    When [用户执行动作]
    Then [期望结果1]
    And [期望结果2]
    """
    # Given: [前置条件1的描述]
    # ... 设置代码

    # And: [前置条件2的描述]
    # ... 更多设置

    # When: [用户执行动作的描述]
    result = # ... 执行代码

    # Then: [期望结果1的描述]
    assert # ... 断言1

    # And: [期望结果2的描述]
    assert # ... 断言2
```

**🚨 强制标注说明**：
- **Story**: 必须指定Story文档和Cycle编号（从Story TDD计划中查找）
- **Scenario**: 必须是Story文档中定义的BDD场景名称
- **DoD**: 必须映射到Definition of Done的验收标准
- **找不到映射 → 这是过度设计 → 不要写这个测试**

**完整示例**：

```python
def test_user_can_execute_tool_with_valid_plan(self):
    """User can execute tool operation when providing valid execution plan.

    Story: story-1.2-integration.md Cycle 2
    Scenario: "Execute tool with valid rollback strategy"
    DoD: F1 - PlanValidator integration functional

    Given a tool that performs file operations
    And a valid execution plan with git revert strategy
    When user executes the tool
    Then tool operation succeeds
    And result is returned to user
    """
    # Given: a tool that performs file operations
    tool = Mock()
    tool.name = "file_operation_tool"
    tool.apply = Mock(return_value="operation_success")

    # And: a valid execution plan with git revert strategy
    plan = ExecutionPlan(
        rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
    )
    engine = ToolExecutionEngine()

    # When: user executes the tool
    result = engine.execute(tool, execution_plan=plan)

    # Then: tool operation succeeds
    tool.apply.assert_called_once()

    # And: result is returned to user
    assert result == "operation_success"
```

---

### 模板2：失败路径测试

```python
def test_user_cannot_[action]_when_[condition](self):
    """[简短描述什么操作会被阻止]

    Story: story-X.X-[name].md Cycle Y
    Scenario: [具体失败场景]
    DoD: [验收标准编号，如Q1/F2]

    Given [会导致失败的前置条件]
    When [用户尝试执行动作]
    Then [操作被阻止]
    And [用户收到清晰的错误消息]
    """
    # Given: [会导致失败的前置条件]
    # ... 设置代码

    # When: [用户尝试执行动作]
    with pytest.raises(ExpectedException) as exc_info:
        # ... 执行代码

    # Then: [操作被阻止]
    assert # ... 验证异常类型

    # And: [用户收到清晰的错误消息]
    assert # ... 验证错误消息内容
```

**完整示例**：

```python
def test_execution_blocked_when_plan_invalid(self):
    """Execution is blocked when execution plan validation fails.

    Story: story-1.2-integration.md Cycle 3
    Scenario: "Execution blocked when plan invalid"
    DoD: F1 - Invalid plan blocks execution

    Given an execution plan with empty precondition string
    When user attempts to execute the tool
    Then execution is blocked
    And user receives clear error message about validation failure
    """
    # Given: an execution plan with empty precondition string
    from evolvai.core.exceptions import ConstraintViolationError

    plan = ExecutionPlan(
        rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
        validation=ValidationConfig(
            pre_conditions=["test", ""],  # Empty string - invalid!
            expected_outcomes=["success"],
        ),
    )

    tool = Mock()
    tool.name = "test_tool"
    engine = ToolExecutionEngine()

    # When: user attempts to execute the tool
    with pytest.raises(ConstraintViolationError) as exc_info:
        engine.execute(tool, execution_plan=plan)

    # Then: execution is blocked
    assert exc_info.value.validation_result.is_valid is False
    tool.apply.assert_not_called()

    # And: user receives clear error message about validation failure
    error_message = str(exc_info.value)
    assert "validation failed" in error_message.lower()
    assert "empty string" in error_message.lower()
```

---

### 模板3：边界条件测试

```python
def test_[system]_[behavior]_when_at_[boundary](self):
    """[描述边界条件下的行为]

    Scenario: [边界场景]
      Given [边界条件设置]
      When [触发边界情况]
      Then [系统按预期响应]
    """
    # Given: [边界条件设置]
    # ... 设置代码

    # When: [触发边界情况]
    result = # ... 执行代码

    # Then: [系统按预期响应]
    assert # ... 边界断言
```

**完整示例**：

```python
def test_operation_fails_when_exceeding_file_limit(self):
    """Operation fails gracefully when file count exceeds plan limit.

    Scenario: Exceed maximum file limit
      Given an execution plan with max_files limit of 10
      When user attempts to edit 11 files
      Then operation is rejected
      And error message indicates file limit exceeded
    """
    # Given: an execution plan with max_files limit of 10
    plan = ExecutionPlan(
        limits=ExecutionLimits(max_files=10, max_changes=100, timeout_seconds=60),
    )

    # When: user attempts to edit 11 files
    tool = Mock()
    tool.name = "multi_file_edit"
    tool.get_affected_files = Mock(return_value=[f"file{i}.py" for i in range(11)])

    engine = ToolExecutionEngine()

    # Then: operation is rejected
    with pytest.raises(ConstraintViolationError) as exc_info:
        engine.execute(tool, file_count=11, execution_plan=plan)

    # And: error message indicates file limit exceeded
    error = exc_info.value
    assert "file limit" in str(error).lower()
    assert "10" in str(error)  # Shows the limit
```

---

### 模板4：状态变化测试

```python
def test_[state]_changes_to_[new_state]_when_[trigger](self):
    """[描述状态转换]

    Scenario: [状态转换场景]
      Given [初始状态]
      When [触发事件]
      Then [状态已变更]
      And [副作用已发生]
    """
    # Given: [初始状态]
    # ... 初始化代码

    # When: [触发事件]
    # ... 触发代码

    # Then: [状态已变更]
    assert # ... 状态断言

    # And: [副作用已发生]
    assert # ... 副作用断言
```

**完整示例**：

```python
def test_audit_log_records_validation_when_plan_provided(self):
    """Audit log records validation result when execution plan is provided.

    Scenario: Execute with valid plan and check audit trail
      Given a valid execution plan
      And an empty audit log
      When tool is executed with the plan
      Then audit log contains new entry
      And entry includes validation status
      And entry includes validation duration
    """
    # Given: a valid execution plan
    plan = ExecutionPlan(
        rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT),
    )

    # And: an empty audit log
    engine = ToolExecutionEngine()
    assert len(engine.get_audit_log()) == 0

    tool = Mock()
    tool.name = "test_tool"
    tool.apply = Mock(return_value="success")

    # When: tool is executed with the plan
    result = engine.execute(tool, execution_plan=plan)

    # Then: audit log contains new entry
    audit_log = engine.get_audit_log()
    assert len(audit_log) == 1

    # And: entry includes validation status
    entry = audit_log[0]
    assert entry["execution_plan_validation"] == "passed"

    # And: entry includes validation duration
    assert "validation_duration_ms" in entry
    assert entry["validation_duration_ms"] < 10  # Fast validation
```

---

### 模板5：集成测试

```python
def test_[component_a]_integrates_with_[component_b]_when_[scenario](self):
    """[描述组件集成行为]

    Scenario: [集成场景]
      Given [组件A设置]
      And [组件B设置]
      When [触发集成操作]
      Then [组件A行为正确]
      And [组件B行为正确]
      And [整体结果符合预期]
    """
    # Given: [组件A设置]
    # ... 组件A设置

    # And: [组件B设置]
    # ... 组件B设置

    # When: [触发集成操作]
    result = # ... 集成操作

    # Then: [组件A行为正确]
    assert # ... A的断言

    # And: [组件B行为正确]
    assert # ... B的断言

    # And: [整体结果符合预期]
    assert # ... 整体断言
```

**完整示例**：

```python
def test_validator_integrates_with_engine_when_validating_plans(self):
    """PlanValidator integrates with ToolExecutionEngine during pre-execution.

    Scenario: Validator detects violations during execution
      Given a PlanValidator instance
      And a ToolExecutionEngine instance
      And an invalid execution plan
      When engine attempts to execute
      Then validator is invoked
      And violations are detected
      And execution is halted
      And violations are recorded in audit log
    """
    # Given: a PlanValidator instance (implicitly created by engine)
    # And: a ToolExecutionEngine instance
    engine = ToolExecutionEngine()

    # And: an invalid execution plan
    plan = ExecutionPlan(
        validation=ValidationConfig(pre_conditions=[""]),  # Invalid
    )

    tool = Mock()
    tool.name = "test_tool"

    # When: engine attempts to execute
    with pytest.raises(ConstraintViolationError):
        engine.execute(tool, execution_plan=plan)

    # Then: validator is invoked (implicit - via exception)
    # And: violations are detected (via exception)
    # And: execution is halted
    tool.apply.assert_not_called()

    # And: violations are recorded in audit log
    audit_log = engine.get_audit_log()
    assert len(audit_log) == 1
    assert audit_log[0]["execution_plan_validation"] == "failed"
    assert "constraint_violations" in audit_log[0]
```

---

## 🔧 Mock策略 (KISS原则)

### 原则：最小化Mock复杂度

```python
# ❌ 避免：复杂的mock链
with patch('os.path.exists') as mock_exists, \
     patch('shutil.copy2') as mock_copy, \
     patch('time.time') as mock_time:
    mock_exists.return_value = True
    mock_copy.return_value = None
    mock_time.return_value = 1234567890
    # ... 复杂的测试逻辑

# ✅ 推荐：专注行为验证
def test_backup_creates_copy_of_original_file(self):
    """Backup operation creates a timestamped copy of the original file.

    Given an original file
    When backup is created
    Then a copy exists with .backup suffix
    """
    # Given: an original file
    manager = RollbackManager()

    # When: backup is created
    result = manager.create_backup("/test/file.txt")

    # Then: a copy exists with .backup suffix
    assert result.success
    assert result.backup_path.endswith(".backup")
    # 不关心内部调用了哪些具体方法
```

---

## 📊 测试组织结构

### 测试类组织

```python
class TestUserWorkflows:
    """Test user-facing workflows and behaviors."""

    def test_user_can_create_backup(self):
        """User workflow: Create backup."""
        # ...

    def test_user_can_restore_from_backup(self):
        """User workflow: Restore from backup."""
        # ...


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_graceful_failure_when_file_missing(self):
        """Error handling: Missing file."""
        # ...

    def test_clear_error_message_when_permission_denied(self):
        """Error handling: Permission denied."""
        # ...


class TestPerformance:
    """Test performance requirements."""

    def test_validation_completes_within_5ms(self):
        """Performance: Fast validation."""
        # ...


class TestBackwardCompatibility:
    """Test backward compatibility guarantees."""

    def test_existing_calls_work_without_execution_plan(self):
        """Compatibility: Legacy calls unchanged."""
        # ...
```

---

## 🎯 场景类型快速参考

| 场景类型 | 命名模式 | 重点验证 |
|---------|---------|---------|
| **成功路径** | `test_user_can_[action]_when_[condition]` | 功能完成、返回正确结果 |
| **失败路径** | `test_user_cannot_[action]_when_[condition]` | 操作阻止、错误消息清晰 |
| **边界条件** | `test_[system]_[behavior]_at_[boundary]` | 边界处理、极限情况 |
| **状态变化** | `test_[state]_changes_to_[new_state]_when_[event]` | 状态转换、副作用 |
| **集成** | `test_[A]_integrates_with_[B]_when_[scenario]` | 组件协作、端到端流程 |
| **性能** | `test_[operation]_completes_within_[time]` | 响应时间、资源使用 |
| **兼容性** | `test_[feature]_works_with_[legacy]` | 向后兼容、零回归 |

---

## ✅ 最佳实践检查清单

### 测试编写前
- [ ] 理解用户故事和验收标准
- [ ] 确定测试场景类型
- [ ] 选择合适的命名模式
- [ ] 规划Given-When-Then结构

### 测试编写时
- [ ] 使用行为驱动的命名
- [ ] 添加清晰的Scenario描述
- [ ] 使用Given-When-Then注释
- [ ] 最小化Mock复杂度
- [ ] 验证行为而非实现

### 测试编写后
- [ ] 测试名称清晰表达意图
- [ ] 注释和代码一致
- [ ] 断言验证用户关心的行为
- [ ] 错误消息清晰可操作
- [ ] 测试可作为文档阅读

---

## 📚 相关资源

- [TDD重构指南](../testing/standards/tdd-refactoring-guidelines.md) - KISS原则和重构策略
- [Definition of Done](../development/standards/definition-of-done.md) - 完成标准
- [Story模板](story-template.md) - Story级别的开发计划

---

## 💡 快速开始

1. **选择场景类型**：从上表选择最匹配的场景类型
2. **复制对应模板**：从本文档复制模板代码
3. **填充业务逻辑**：替换占位符为实际业务代码
4. **运行测试**：`uv run poe test -k "your_test_name"`
5. **检查清单**：使用最佳实践检查清单验证

---

**维护者**: EvolvAI Team
**反馈渠道**: GitHub Issues
**最后更新**: 2025-11-06
