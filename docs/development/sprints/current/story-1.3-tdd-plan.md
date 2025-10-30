# Story 1.3 TDD Plan - Runtime Constraint Monitoring

**Story ID**: STORY-1.3
**Date**: 2025-10-30
**Status**: [DRAFT]
**Priority**: [P1]
**Estimated Effort**: 2.5 person-days (optimized from 3 person-days)

---

## 📋 Story Overview

### Objective
Implement integrated runtime constraint monitoring to enforce ExecutionPlan limits during actual tool execution, providing critical infrastructure for Safe Tools and Constitutional Constraints.

### Strategic Context
**Critical Infrastructure**: This story is essential for:
- **Phase 2 Safe Tools**: Runtime enforcement of execution limits
- **Phase 4 Constitutional Constraints**: Runtime environment for rule engine
- **TPST Optimization**: Early failure to reduce token waste

### Architecture Decision
Based on [ADR-004: RuntimeConstraintMonitor Optimization](../../architecture/adrs/004-runtime-constraint-monitor-optimization.md), we're using an integrated design rather than standalone component.

---

## 🎯 Acceptance Criteria

### Functional Requirements
1. ✅ **File Count Monitoring**: Track and enforce `ExecutionPlan.limits.max_files`
2. ✅ **Change Count Monitoring**: Track and enforce `ExecutionPlan.limits.max_changes`
3. ✅ **Timeout Monitoring**: Track and enforce `ExecutionPlan.limits.timeout_seconds`
4. ✅ **Exception Handling**: Raise specific exceptions for each constraint violation
5. ✅ **Audit Integration**: Record violations in existing audit log
6. ✅ **Early Failure**: Stop execution immediately when limits exceeded

### Non-Functional Requirements
1. ✅ **Performance**: <2ms overhead for all runtime checks
2. ✅ **Integration**: Seamless integration with existing ToolExecutionEngine
3. ✅ **Backward Compatibility**: No impact on existing tool calls
4. ✅ **Maintainability**: Clean, testable, extensible design

---

## 🔄 TDD Cycles (Optimized: 4 cycles)

### 🔴 Cycle 1: ExecutionContext Runtime Tracking Fields

**Duration**: 0.5 day
**Focus**: Add runtime tracking infrastructure to ExecutionContext

#### Red Phase - Write Tests
```python
class TestExecutionContextRuntimeTracking:
    """Test ExecutionContext runtime tracking capabilities."""

    def test_files_processed_tracking_initialization(self):
        """Test that files_processed starts at 0."""
        ctx = ExecutionContext(tool_name="test", kwargs={})
        assert ctx.files_processed == 0

    def test_changes_made_tracking_initialization(self):
        """Test that changes_made starts at 0."""
        ctx = ExecutionContext(tool_name="test", kwargs={})
        assert ctx.changes_made == 0

    def test_increment_files_processed(self):
        """Test files_processed increment."""
        ctx = ExecutionContext(tool_name="test", kwargs={})
        ctx.files_processed += 1
        assert ctx.files_processed == 1
```

#### Green Phase - Implementation
```python
# In src/evolvai/core/execution.py
@dataclass
class ExecutionContext:
    # ... existing fields ...

    # Runtime tracking fields (NEW)
    files_processed: int = 0
    changes_made: int = 0

    def check_limits(self) -> None:
        """Check runtime constraints against execution plan limits."""
        if self.execution_plan is None:
            return

        limits = self.execution_plan.limits

        if self.files_processed > limits.max_files:
            raise FileLimitExceededError(
                f"File limit exceeded: {self.files_processed} > {limits.max_files}"
            )

        if self.changes_made > limits.max_changes:
            raise ChangeLimitExceededError(
                f"Change limit exceeded: {self.changes_made} > {limits.max_changes}"
            )
```

#### Refactor Phase
- Code formatting and type checking
- Add docstrings
- Ensure no regressions

---

### 🔴 Cycle 2: FileLimitExceededError Implementation

**Duration**: 0.5 day
**Focus**: File count constraint enforcement

#### Red Phase - Write Tests
```python
def test_file_limit_exceeded_when_max_files_reached(self):
    """Test FileLimitExceededError when max_files limit exceeded."""
    # Setup ExecutionContext with execution plan having max_files=1
    ctx = ExecutionContext(tool_name="test", kwargs={})
    ctx.execution_plan = ExecutionPlan(
        limits=ExecutionLimits(max_files=1)
    )

    # Process 2 files
    ctx.files_processed = 2

    # Should raise FileLimitExceededError
    with pytest.raises(FileLimitExceededError) as exc_info:
        ctx.check_limits()

    assert "File limit exceeded" in str(exc_info.value)
    assert "2 > 1" in str(exc_info.value)

def test_no_exception_when_file_limit_not_exceeded(self):
    """Test no exception when within file limit."""
    ctx = ExecutionContext(tool_name="test", kwargs={})
    ctx.execution_plan = ExecutionPlan(
        limits=ExecutionLimits(max_files=10)
    )

    ctx.files_processed = 5

    # Should not raise exception
    ctx.check_limits()  # Should pass silently
```

#### Green Phase - Implementation
```python
# In src/evolvai/core/constraint_exceptions.py
class FileLimitExceededError(Exception):
    """Raised when file processing exceeds execution plan limits."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
```

#### Refactor Phase
- Add comprehensive error message formatting
- Ensure exception is serializable
- Add logging support

---

### 🔴 Cycle 3: ChangeCountLimitError Implementation

**Duration**: 0.5 day
**Focus**: Change count constraint enforcement

#### Red Phase - Write Tests
```python
def test_change_limit_exceeded_when_max_changes_reached(self):
    """Test ChangeLimitExceededError when max_changes limit exceeded."""
    ctx = ExecutionContext(tool_name="test", kwargs={})
    ctx.execution_plan = ExecutionPlan(
        limits=ExecutionLimits(max_changes=5)
    )

    # Make 6 changes
    ctx.changes_made = 6

    # Should raise ChangeLimitExceededError
    with pytest.raises(ChangeLimitExceededError) as exc_info:
        ctx.check_limits()

    assert "Change limit exceeded" in str(exc_info.value)
    assert "6 > 5" in str(exc_info.value)

def test_multiple_constraints_violation_reporting(self):
    """Test that first violation is reported (file limit takes precedence)."""
    ctx = ExecutionContext(tool_name="test", kwargs={})
    ctx.execution_plan = ExecutionPlan(
        limits=ExecutionLimits(max_files=1, max_changes=1)
    )

    # Exceed both limits
    ctx.files_processed = 2
    ctx.changes_made = 3

    # Should report file limit first (checked first)
    with pytest.raises(FileLimitExceededError):
        ctx.check_limits()
```

#### Green Phase - Implementation
```python
# In src/evolvai/core/constraint_exceptions.py
class ChangeLimitExceededError(Exception):
    """Raised when change count exceeds execution plan limits."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
```

#### Refactor Phase
- Consistent error message formatting with FileLimitExceededError
- Add structured error data for audit logging
- Ensure proper exception chaining

---

### 🔴 Cycle 4: TimeoutError and Integration Testing

**Duration**: 1.0 day
**Focus**: Timeout enforcement and full ToolExecutionEngine integration

#### Red Phase - Write Tests
```python
def test_timeout_checking_integration(self):
    """Test timeout checking in actual execution context."""
    # Create mock agent
    mock_agent = Mock()
    mock_agent._active_project = Mock()
    mock_agent.is_using_language_server = Mock(return_value=False)

    # Create tool
    tool = Mock()
    tool.get_name = Mock(return_value="test_tool")
    tool.is_active = Mock(return_value=True)
    apply_fn = Mock(return_value="success")
    tool.get_apply_fn = Mock(return_value=apply_fn)

    # Create execution plan with timeout
    plan = ExecutionPlan(
        limits=ExecutionLimits(timeout_seconds=1)  # Very short timeout
    )

    # Create execution engine
    engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

    # Mock time passage (simulate execution taking too long)
    with patch('time.time') as mock_time:
        mock_time.side_effect = [0, 2]  # Start at 0, end at 2 seconds

        try:
            engine.execute(tool, execution_plan=plan)
            assert False, "Should have raised TimeoutError"
        except TimeoutError:
            pass  # Expected

def test_audit_log_records_runtime_violations(self):
    """Test that runtime violations are recorded in audit log."""
    mock_agent = Mock()
    mock_agent._active_project = Mock()
    mock_agent.is_using_language_server = Mock(return_value=False)

    tool = Mock()
    tool.get_name = Mock(return_value="test_tool")
    tool.is_active = Mock(return_value=True)
    apply_fn = Mock(return_value="success")
    tool.get_apply_fn = Mock(return_value=apply_fn)

    plan = ExecutionPlan(
        limits=ExecutionLimits(max_files=1)
    )

    engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

    # Simulate file limit violation during execution
    def simulate_execution_with_violation(tool, ctx):
        ctx.files_processed = 2  # Exceeds limit
        ctx.check_limits()  # Should raise exception

    with patch.object(engine, '_execute_tool', side_effect=simulate_execution_with_violation):
        try:
            engine.execute(tool, execution_plan=plan)
        except FileLimitExceededError:
            pass  # Expected

    # Verify audit log records the violation
    audit_log = engine.get_audit_log()
    assert len(audit_log) == 1
    assert audit_log[0]["success"] is False
    assert audit_log[0]["tool"] == "test_tool"
```

#### Green Phase - Implementation
```python
# Extend ExecutionContext.check_limits() with timeout checking
def check_limits(self) -> None:
    """Check runtime constraints against execution plan limits."""
    if self.execution_plan is None:
        return

    limits = self.execution_plan.limits

    # Check file count
    if self.files_processed > limits.max_files:
        raise FileLimitExceededError(
            f"File limit exceeded: {self.files_processed} > {limits.max_files}"
        )

    # Check change count
    if self.changes_made > limits.max_changes:
        raise ChangeLimitExceededError(
            f"Change limit exceeded: {self.changes_made} > {limits.max_changes}"
        )

    # Check timeout
    current_time = time.time()
    elapsed_time = current_time - self.start_time
    if elapsed_time > limits.timeout_seconds:
        raise TimeoutError(
            f"Execution timeout: {elapsed_time:.1f}s > {limits.timeout_seconds}s"
        )

# In ToolExecutionEngine.execute() - Add runtime checking in EXECUTION phase
def execute(self, tool: "Tool", **kwargs: Any) -> str:
    # ... existing PRE_VALIDATION and PRE_EXECUTION phases ...

    try:
        # Phase 3: Execution
        ctx.phase = ExecutionPhase.EXECUTION

        # NEW: Check runtime constraints before execution
        ctx.check_limits()

        ctx.result = self._execute_tool(tool, ctx)

        # NEW: Check runtime constraints after execution
        ctx.check_limits()

        # ... rest of method ...
```

#### Refactor Phase
- Performance optimization (<2ms target)
- Exception handling cleanup
- Integration test coverage

---

## 📊 Quality Standards

### Testing Requirements
- **Unit Test Coverage**: ≥95% for new code
- **Integration Tests**: Full ToolExecutionEngine integration scenarios
- **Performance Tests**: <2ms runtime checking overhead
- **Exception Testing**: All error paths covered

### Code Quality
- **Type Safety**: 100% mypy strict compliance
- **Formatting**: RUFF + BLACK compliance
- **Documentation**: Comprehensive docstrings for new methods
- **Error Handling**: Clear, actionable error messages

---

## 🎯 Success Metrics

### Functional Metrics
- ✅ 3 runtime constraint rules implemented
- ✅ All constraints properly enforced during execution
- ✅ Clear exception messages for each violation type
- ✅ Audit log properly records runtime violations

### Performance Metrics
- ✅ <2ms overhead for runtime constraint checking
- ✅ Zero impact when no execution_plan provided
- ✅ No memory leaks in constraint checking logic

### Integration Metrics
- ✅ Seamless integration with existing ToolExecutionEngine
- ✅ Zero regression in existing tests
- ✅ Backward compatibility maintained
- ✅ Foundation ready for Phase 2 Safe Tools

---

## 📝 Implementation Notes

### Integration Points
1. **ExecutionContext.check_limits()**: Core constraint checking logic
2. **ToolExecutionEngine.execute()**: Integration points in EXECUTION phase
3. **Exception Handling**: Integration with existing audit and error systems

### Performance Considerations
- Inline checking minimizes method call overhead
- Early exit on first violation
- Minimal memory footprint (just integer counters)

### Extensibility
- Easy to add new constraint types
- Foundation for Phase 4 Constitutional Constraints
- Configurable checking order (file → change → timeout)

---

## 🔄 Development Workflow

### Pre-Development
1. ✅ Create this TDD plan
2. ✅ Update Phase 1 implementation plan
3. ✅ Update Epic-001 README
4. Create feature branch: `feature/epic1-story1.3-runtime-constraints`

### Development Process
1. Follow TDD cycles exactly as specified
2. Commit after each cycle completion
3. Run full test suite after each cycle
4. Performance test after Cycle 4

### Post-Development
1. Integration testing with existing tools
2. Performance benchmarking
3. Documentation updates
4. Merge to develop branch

---

## 📚 Related Documents

- **ADR-004**: RuntimeConstraintMonitor Optimization Decision
- **Phase 1 Implementation Plan**: Overall phase context
- **Epic-001 README**: Strategic goals and timeline
- **Story 1.1 TDD Plan**: Static validation reference

---

**Document Status**: [DRAFT] - Ready for review and approval
**Last Updated**: 2025-10-30
**Next Review**: Before Story 1.3 development kickoff