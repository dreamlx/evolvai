# Story 2.4 TDD Plan: Interactive Confirmation for High-Risk Operations

**Story**: Story 2.4 - Interactive Confirmation for High-Risk Operations
**Epic**: Epic-001 - Behavior Constraints System
**Phase**: Phase 2 - Safe Operations Tools
**Estimated Duration**: 2-3 days
**Target**: 18-20 tests

---

## 📋 Story Overview

**Goal**: Implement interactive confirmation mechanism for high-risk operations (wildcard deletes, current directory deletes, source directory deletes)

**Core Value**: Prevent AI reasoning failures from contextual misunderstandings while maintaining user control and flexibility

**Design Principle**: **Confirm, don't block** - User retains final decision authority

---

## 🎯 Definition of Done (DoD)

### Functional Acceptance
- **F1**: Detect wildcard delete operations (`rm -rf ./tmp_*`)
- **F2**: Detect current directory delete operations (`rm -rf .`)
- **F3**: Return `confirmation_required` result instead of blocking
- **F4**: Support `confirmed=True` parameter to skip second-time confirmation
- **F5**: MCP tool layer auto-prompts user for confirmation

### Quality Acceptance
- **Q1**: Test coverage ≥ 90%
- **Q2**: False positive rate < 5% (don't over-block normal operations)
- **Q3**: 100% backward compatible with Story 2.3

### Performance Acceptance
- **P1**: Precondition check still < 10ms
- **P2**: Confirmation logic doesn't impact non-high-risk operations

---

## 📅 Three-Day TDD Implementation Plan

### Day 1: Core Infrastructure

**Focus**: ExecutionResult extension + CONFIRMATION_REQUIRED_PATTERNS detection

**BDD Scenarios**:

#### Scenario 1.1: ExecutionResult has confirmation fields
```
Given a SafeExecWrapper instance
When a command requires confirmation
Then ExecutionResult should include:
  - confirmation_required: bool
  - confirmation_message: Optional[str]
  - risk_level: str ("low", "medium", "high")
```

#### Scenario 1.2: Wildcard delete detection
```
Given a command "rm -rf ./tmp_*"
When SafeExecWrapper.execute() is called
Then confirmation_required should be True
And confirmation_message should explain the risk
And risk_level should be "high"
```

#### Scenario 1.3: Current directory delete detection
```
Given a command "rm -rf ."
When SafeExecWrapper.execute() is called
Then confirmation_required should be True
And risk_level should be "high"
```

#### Scenario 1.4: Source directory delete detection
```
Given a command "rm -rf ./src"
When SafeExecWrapper.execute() is called
Then confirmation_required should be True
And risk_level should be "medium"
```

#### Scenario 1.5: Normal commands require no confirmation
```
Given a command "echo hello"
When SafeExecWrapper.execute() is called
Then confirmation_required should be False
And command executes normally
```

#### Scenario 1.6: Absurd commands still blocked
```
Given a command "rm -rf /"
When SafeExecWrapper.execute() is called
Then ConstraintViolationError is raised
(Story 2.3 behavior preserved)
```

**Red Phase Tests** (6-8 tests):
1. `test_execution_result_has_confirmation_fields` - DoD: F3
2. `test_execution_result_defaults_no_confirmation` - DoD: Q3
3. `test_detect_wildcard_delete_rm_rf` - DoD: F1
4. `test_detect_wildcard_delete_rm` - DoD: F1
5. `test_detect_delete_current_directory` - DoD: F2
6. `test_detect_delete_source_directory` - DoD: F1
7. `test_normal_commands_no_confirmation` - DoD: Q2
8. `test_absurd_commands_still_blocked` - DoD: Q3

**Green Phase Implementation**:
1. Extend `ExecutionResult` dataclass with confirmation fields
2. Define `CONFIRMATION_REQUIRED_PATTERNS` list
3. Implement `_check_confirmation_required()` method
4. Update `execute()` to call confirmation check
5. Set confirmation fields in ExecutionResult

**Refactor**:
- Extract risk level logic into helper function
- Ensure confirmation check is fast (< 1ms)

---

### Day 2: Confirmation Flow

**Focus**: `confirmed` parameter support + two-phase execution logic

**BDD Scenarios**:

#### Scenario 2.1: First execution returns confirmation request
```
Given a high-risk command "rm -rf ./tmp_*"
When SafeExecWrapper.execute() is called without confirmed flag
Then confirmation_required is True
And command is NOT executed
And stdout/stderr are empty
```

#### Scenario 2.2: Second execution with confirmed=True proceeds
```
Given a high-risk command "rm -rf ./tmp_*"
When SafeExecWrapper.execute(confirmed=True) is called
Then confirmation_required is False
And command executes normally
```

#### Scenario 2.3: confirmed flag only skips confirmation, not absurd checks
```
Given an absurd command "rm -rf /"
When SafeExecWrapper.execute(confirmed=True) is called
Then ConstraintViolationError is still raised
(Absurd commands cannot be confirmed away)
```

#### Scenario 2.4: Backward compatibility - no confirmed parameter
```
Given existing code calling execute(command, timeout)
When no confirmed parameter is provided
Then confirmation logic works normally
And no errors occur
```

**Red Phase Tests** (5-6 tests):
1. `test_first_execution_returns_confirmation_required` - DoD: F3
2. `test_first_execution_does_not_execute_command` - DoD: F3
3. `test_second_execution_with_confirmed_true_proceeds` - DoD: F4
4. `test_confirmed_only_skips_confirmation_not_absurd` - DoD: Q3
5. `test_backward_compatible_no_confirmed_param` - DoD: Q3
6. `test_confirmed_false_same_as_no_param` - DoD: Q3

**Green Phase Implementation**:
1. Add `confirmed: bool = False` parameter to `execute()`
2. Modify `_check_confirmation_required()` to accept `confirmed` flag
3. Implement early return logic when confirmation required
4. Ensure absurd command checks run regardless of `confirmed` flag
5. Return ExecutionResult with confirmation_required=True

**Refactor**:
- Ensure precondition check order is optimal
- Add docstring explaining two-phase execution flow

---

### Day 3: MCP Integration & Polish

**Focus**: SafeExecTool extension + integration testing

**BDD Scenarios**:

#### Scenario 3.1: SafeExecTool returns confirmation_required via JSON
```
Given SafeExecTool instance
When apply() is called with high-risk command
Then JSON response includes confirmation_required=true
And includes confirmation_message
And includes risk_level
```

#### Scenario 3.2: SafeExecTool accepts confirmed parameter
```
Given SafeExecTool instance
When apply() is called with confirmed=True
Then confirmation is skipped
And command executes normally
```

#### Scenario 3.3: MCP schema validation includes new fields
```
Given SafeExecTool schema
When inspected via MCP protocol
Then confirmed parameter is documented
And return type includes confirmation fields
```

**Red Phase Tests** (4-5 tests):
1. `test_safe_exec_tool_returns_confirmation_required_json` - DoD: F5
2. `test_safe_exec_tool_accepts_confirmed_param` - DoD: F4
3. `test_safe_exec_tool_json_includes_confirmation_fields` - DoD: F3
4. `test_safe_exec_tool_schema_has_confirmed_param` - DoD: F5
5. `test_integration_two_phase_execution_via_mcp` - DoD: F5

**Green Phase Implementation**:
1. Extend `SafeExecTool.apply()` to accept `confirmed` parameter
2. Update JSON serialization to include confirmation fields
3. Update docstring to document confirmation flow
4. Update pydantic schema for MCP protocol

**Refactor**:
- Clean up JSON formatting
- Ensure backward compatibility
- Add usage examples in docstring

---

## 🏗️ Technical Architecture

### CONFIRMATION_REQUIRED_PATTERNS

```python
# Priority-ordered patterns (check in this order)
CONFIRMATION_REQUIRED_PATTERNS = [
    # P0: Wildcard delete (highest risk)
    (r'rm\s+-rf?\s+.*\*', "wildcard_delete", "high",
     "Deleting with wildcard - please confirm exact targets"),

    # P1: Delete current directory
    (r'rm\s+-rf?\s+\./?$', "delete_current_dir", "high",
     "Deleting current directory - please confirm"),

    # P2: Delete source code directories
    (r'rm\s+-rf?\s+\./(src|lib|pkg|app|server|client)/?$',
     "delete_source_dir", "medium",
     "Deleting source code directory - please confirm"),
]
```

### ExecutionResult Extension

```python
@dataclass
class ExecutionResult:
    # Existing fields (Story 2.3)
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    precondition_passed: bool
    error_message: Optional[str] = None
    timeout_occurred: bool = False
    actual_duration_seconds: float = 0.0
    suggested_timeout: Optional[int] = None

    # Story 2.4: Confirmation fields
    confirmation_required: bool = False
    confirmation_message: Optional[str] = None
    risk_level: str = "low"  # "low", "medium", "high"
```

### Two-Phase Execution Flow

```python
def execute(
    self,
    command: str,
    timeout: int,
    execution_plan: Optional[ExecutionPlan] = None,
    confirmed: bool = False,  # Story 2.4: New parameter
) -> ExecutionResult:
    """Execute command with optional confirmation for high-risk operations.

    Two-phase execution:
    1. First call (confirmed=False): Returns confirmation_required=True if risky
    2. Second call (confirmed=True): Executes after user confirmation

    Note: Absurd commands (rm -rf /) are blocked regardless of confirmed flag.
    """
    # Check preconditions (absurd commands always checked)
    self._check_preconditions(command, timeout, execution_plan)

    # Check if confirmation required (unless already confirmed)
    if not confirmed:
        confirmation = self._check_confirmation_required(command)
        if confirmation:
            return ExecutionResult(
                success=False,
                exit_code=0,
                stdout="",
                stderr="",
                duration_ms=0.0,
                precondition_passed=True,
                confirmation_required=True,
                confirmation_message=confirmation["message"],
                risk_level=confirmation["risk_level"],
            )

    # Execute command (normal flow)
    ...
```

---

## 📊 Test Coverage Matrix

| DoD Standard | Tests | Coverage |
|--------------|-------|----------|
| F1: Wildcard detection | test_detect_wildcard_delete_* | ≥ 2 tests |
| F2: Current dir detection | test_detect_delete_current_directory | ≥ 1 test |
| F3: confirmation_required | test_execution_result_*, test_first_execution_* | ≥ 4 tests |
| F4: confirmed parameter | test_second_execution_*, test_*_confirmed_* | ≥ 3 tests |
| F5: MCP integration | test_safe_exec_tool_* | ≥ 3 tests |
| Q1: Coverage ≥ 90% | All tests | pytest-cov |
| Q2: False positive < 5% | test_normal_commands_no_confirmation | Manual review |
| Q3: Backward compatible | test_absurd_*, test_backward_compatible_* | ≥ 3 tests |
| P1: < 10ms | Performance assertion in tests | Timing checks |

**Total Expected Tests**: 18-20 tests

---

## 🎯 Success Criteria

### Functional Completeness
- ✅ All BDD scenarios passing
- ✅ 18-20 tests with 100% pass rate
- ✅ All DoD standards verified

### Code Quality
- ✅ Type-check: no issues
- ✅ Format: validated
- ✅ Mock complexity ≤ 3/10
- ✅ Every test maps to Story/Scenario/DoD

### Integration Quality
- ✅ Story 2.3 tests still passing (regression check)
- ✅ SafeExecTool tests passing
- ✅ Overall evolvai/tools test suite passing

---

## 🔗 Dependencies & Integration

### Input Dependencies
- ✅ Story 2.3: PreconditionChecker architecture
- ✅ Story 0.1: ToolExecutionEngine (for audit log)

### Output Deliverables
- ExecutionResult with confirmation fields
- SafeExecWrapper with two-phase execution
- SafeExecTool with MCP confirmation support
- Complete test suite (18-20 tests)

### Integration Points
- MCP protocol: Confirmation fields in JSON response
- ToolExecutionEngine: Audit log includes confirmation events
- Dashboard (future): Display confirmation requests

---

## 📚 Key Design Decisions

### 1. Two-Phase Execution vs. Blocking

**Decision**: Two-phase execution (confirm then execute)

**Rationale**:
- User retains control (KISS principle)
- Avoids false positives blocking valid operations
- TPST-friendly (one confirmation vs. multiple retries)

### 2. Risk Levels

**Decision**: Three levels - "low", "medium", "high"

**Rationale**:
- "high": Wildcard deletes, current directory deletes (immediate danger)
- "medium": Source directory deletes (recoverable via git)
- "low": Normal operations (no confirmation)

### 3. Absurd Commands Still Blocked

**Decision**: `confirmed=True` does NOT bypass absurd command checks

**Rationale**:
- `rm -rf /` is never intentional in AI context
- Prevents confirmation fatigue from reducing vigilance
- Clear separation: confirmation (contextual) vs. absurd (absolute)

---

## 🚀 Next Steps After Completion

1. **Milestone 1 Dogfooding**: Start using safe_exec with confirmation for EvolvAI development
2. **Collect Usage Data**: Track confirmation frequency, false positive rate
3. **Story 2.5**: Optimize patterns based on real usage data
4. **Story 2.6**: Smart wildcard expansion (show exact files to be deleted)

---

**Prepared by**: Claude Code
**Review Status**: Ready for Day 1 implementation
**Version**: 1.0 (Draft)
