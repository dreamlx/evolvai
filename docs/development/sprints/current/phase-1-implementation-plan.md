# Phase 1 Implementation Plan - ExecutionPlan Validation Framework

**Status**: [DRAFT]
**Date**: 2025-10-28
**Epic**: Epic-001 Behavior Constraints System
**Phase**: Phase 1 - ExecutionPlan Validation Framework

---

## Executive Summary

Phase 1 focuses on implementing the **ExecutionPlan validation framework** that will enforce behavior constraints at the pre-execution phase. With ExecutionPlan schema already completed in Story 0.2, Phase 1 will build the validation logic and integrate it into ToolExecutionEngine.

**⚡ TPST Optimization Focus**: This phase follows the principle of avoiding redundant validation to support Epic-001's goal of reducing TPST by 30%. PlanValidator focuses on business rules that Pydantic cannot validate, rather than duplicating boundary checks.

### Key Objectives
1. Implement PlanValidator for ExecutionPlan business rule checking (not boundary duplication)
2. Integrate validation into ToolExecutionEngine's pre-execution phase
3. Implement runtime constraint monitoring for actual execution limits
4. Enable dry-run mode and rollback strategy framework

### Success Criteria
- ✅ PlanValidator validates all business rule constraints (no Pydantic duplication)
- ✅ Invalid plans rejected before execution
- ✅ Runtime constraints monitored during execution
- ✅ Zero validation overhead when constraints disabled
- ✅ <5ms total validation overhead (contributes to TPST reduction)
- ✅ 100% test coverage for validation logic
- ✅ Clear error messages for constraint violations
- ✅ TPST optimization: Zero redundant validation cycles

---

## Phase 1 Architecture

### Component Stack
```
┌─────────────────────────────────────────┐
│   AI Agent (Claude, GPT, etc.)         │
└─────────────────┬───────────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────────┐
│  ToolExecutionEngine                    │
│  ┌───────────────────────────────────┐  │
│  │ PRE_VALIDATION Phase              │  │ ← Tool/project checks
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │ PRE_EXECUTION Phase               │  │ ← NEW: PlanValidator integration
│  │ - Validate ExecutionPlan          │  │
│  │ - Check constraint rules          │  │
│  │ - Verify rollback strategy        │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │ EXECUTION Phase                   │  │ ← Original tool logic
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │ POST_EXECUTION Phase              │  │ ← Audit + statistics
│  └───────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### New Components

**1. PlanValidator** (`src/evolvai/core/plan_validator.py`)
- Validates ExecutionPlan reasonableness
- Checks constraint consistency
- Verifies rollback strategy requirements
- Returns validation result with detailed errors

**2. ConstraintChecker** (`src/evolvai/core/constraint_checker.py`)
- Basic constraint rule evaluation
- Resource limit enforcement
- Scope restriction validation
- Foundation for Phase 4 constitutional constraints

**3. ValidationResult** (Data class in `plan_validator.py`)
- Validation status (passed/failed)
- List of violations with detailed messages
- Suggested fixes or adjustments

---

## Phase 1 Stories

### Story 1.1: PlanValidator Core Implementation

**Priority**: [P0]
**Estimated Effort**: 3 person-days (optimized from 4 person-days)
**Status**: [Backlog]

**Objective**: Implement comprehensive ExecutionPlan business rule validation with TDD approach, focusing on rules that Pydantic cannot validate.

**⚡ TPST Optimization**: Avoids duplicate boundary validation (already handled by Pydantic), focusing only on business logic that requires semantic understanding.

**Deliverables**:
- `src/evolvai/core/validation_result.py` - ValidationResult and ValidationViolation classes
- `src/evolvai/core/plan_validator.py` - PlanValidator class (business rule focus)
- `test/evolvai/core/test_plan_validator.py` - Comprehensive test suite
- 📄 **Detailed TDD Plan**: [Story 1.1 TDD Plan](story-1.1-tdd-plan.md)

**Validation Rules** (Business Logic Only):

1. **Rollback Strategy Business Rules**:
   - Suspicious command detection (INFO-level warnings, not security)
   - Command syntax basic validation
   - ⚠️ Note: MANUAL requires commands is validated by Pydantic

2. **Validation Config Semantic Checks**:
   - Empty strings in pre_conditions/expected_outcomes (ERROR)
   - Duplicate conditions/outcomes (WARNING)
   - String content validation (not just type checking)

3. **Cross-Field Business Rules** (Core TPST Optimization):
   - batch=True with low limits warning
   - High limits with short timeout warning
   - dry_run + rollback strategy consistency
   - Business logic constraints that span multiple fields

**NOT Validated** (Pydantic Already Handles):
- ❌ Limits boundaries (max_files: 1-100, already in Field)
- ❌ Required fields (rollback required, already in schema)
- ❌ Type checking (already handled by Pydantic)

**TDD Cycles**:
- Cycle 1: ValidationResult data class (Red → Green → Refactor)
- Cycle 2: PlanValidator framework (simplified, 5 tests)
- Cycle 3: Rollback strategy rules (4 tests, INFO-level warnings)
- Cycle 4: Validation config consistency (5 tests)
- Cycle 5: Cross-field validation rules (6 tests)
- Cycle 6: Performance optimization and integration (10 tests)

**Success Criteria**:
- ✅ 20-25 tests with 100% coverage (optimized from 36+)
- ✅ All business rules implemented (no Pydantic duplication)
- ✅ Performance: <1ms per validation
- ✅ Clear error messages for each violation type
- ✅ Zero redundant validation overhead

---

### Story 1.2: ToolExecutionEngine Integration

**Priority**: [P0]
**Estimated Effort**: 3 person-days
**Status**: [Backlog]

**Objective**: Integrate PlanValidator into ToolExecutionEngine's pre-execution phase.

**Deliverables**:
- Update `src/evolvai/core/execution.py` - Add validation to _pre_execution_with_constraints()
- Update `test/evolvai/core/test_execution.py` - Integration tests (NEW FILE)
- Update `src/serena/agent.py` - execution_plan propagation if needed

**Integration Points**:
1. **ExecutionEngine._pre_execution_with_constraints()**:
   ```python
   def _pre_execution_with_constraints(self, tool: "Tool", ctx: ExecutionContext) -> None:
       if ctx.execution_plan is None:
           return  # No plan to validate

       validator = PlanValidator()
       result = validator.validate(ctx.execution_plan)

       if not result.is_valid:
           ctx.constraint_violations = result.violations
           raise ConstraintViolationError(result)
   ```

2. **Error Handling**:
   - New exception: `ConstraintViolationError`
   - Include validation errors in audit log
   - Clear user-facing error messages

3. **Backward Compatibility**:
   - If execution_plan is None, skip validation (100% compatible)
   - If constraints_enabled=False, skip validation
   - No impact on existing tool calls

**TDD Cycles**:
- Cycle 1: Basic integration test (plan validation called)
- Cycle 2: Valid plan passes through successfully
- Cycle 3: Invalid plan raises ConstraintViolationError
- Cycle 4: Violations recorded in audit log
- Cycle 5: Backward compatibility verification
- Cycle 6: Error handling and user messages

**Success Criteria**:
- ✅ PlanValidator called in pre-execution phase
- ✅ Invalid plans rejected before execution
- ✅ Violations recorded in audit trail
- ✅ Zero regression in existing tests
- ✅ 100% backward compatible

---

### Story 1.3: Runtime Constraint Monitoring

**Priority**: [P1]
**Estimated Effort**: 2.5 person-days (optimized from 3 person-days)
**Status**: [Backlog]
**📄 Decision**: [ADR-004: RuntimeConstraintMonitor Optimization](../../../development/architecture/adrs/004-runtime-constraint-monitor-optimization.md)

**Objective**: Implement integrated runtime constraint monitoring to enforce ExecutionPlan limits during actual tool execution, providing critical infrastructure for Safe Tools and Constitutional Constraints.

**⚠️ Key Distinction**:
- **Story 1.1 (PlanValidator)**: Validates the ExecutionPlan itself before execution (static validation)
- **Story 1.3 (RuntimeConstraintMonitor)**: Monitors actual execution against plan limits (dynamic monitoring)

**🎯 Strategic Importance**:
- **Critical Infrastructure**: Essential for Phase 2 Safe Tools enforcement
- **Phase 4 Foundation**: Provides runtime environment for Constitutional Constraints  
- **TPST Core**: Enables early failure to reduce token waste

**Deliverables**:
- Enhance `src/evolvai/core/execution.py` -集成运行时跟踪到 ExecutionContext
- `src/evolvai/core/constraint_exceptions.py` - Runtime constraint violation exceptions
- `test/evolvai/core/test_runtime_constraints.py` - Test suite

**Runtime Constraints** (Integrated Monitoring):

1. **File Count Monitoring**:
   - Track actual files processed via ExecutionContext.files_processed
   - Raise FileLimitExceededError when limit breached
   - Record violation in existing audit log

2. **Change Count Monitoring**:
   - Track actual changes made via ExecutionContext.changes_made  
   - Raise ChangeLimitExceededError when limit breached
   - Allow graceful rollback using existing mechanisms

3. **Timeout Monitoring**:
   - Track elapsed execution time via ExecutionContext timing
   - Raise TimeoutError when limit breached
   - Ensure clean process termination

**Optimized Integration with ToolExecutionEngine**:
```python
# In ExecutionContext (enhanced)
class ExecutionContext:
    files_processed: int = 0  # NEW: Runtime tracking
    changes_made: int = 0     # NEW: Runtime tracking
    
    def check_limits(self) -> None:
        """Integrated runtime constraint checking"""
        if self.execution_plan:
            limits = self.execution_plan.limits
            if self.files_processed > limits.max_files:
                raise FileLimitExceededError(...)
            if self.changes_made > limits.max_changes:
                raise ChangeLimitExceededError(...)

# In ToolExecutionEngine.execute() - EXECUTION phase
# Inline constraint checking during tool execution
ctx.check_limits()  # Integrated calls
```

**Architecture Optimization**:
- ✅ **Integrated Design**: Leverage existing ToolExecutionEngine architecture
- ✅ **Reuse Infrastructure**: Built on ExecutionContext and audit log system
- ✅ **Minimal Overhead**: Inline checking with <2ms performance target
- ✅ **Extensible**: Foundation for Phase 4 Constitutional Constraints

**TDD Cycles** (Optimized from 6 to 4 cycles):
- Cycle 1: ExecutionContext runtime tracking fields
- Cycle 2: FileLimitExceededError implementation  
- Cycle 3: ChangeCountLimitError implementation
- Cycle 4: TimeoutError and integration testing

**Success Criteria**:
- ✅ 3 runtime constraint rules implemented with integrated design
- ✅ Clean integration with existing ToolExecutionEngine flow
- ✅ Graceful handling of violations (reuse existing rollback support)
- ✅ Violations recorded in existing audit log
- ✅ 100% test coverage with 4 TDD cycles
- ✅ Performance: <2ms for all runtime checks
- ✅ Foundation ready for Phase 2 Safe Tools and Phase 4 Constitutional Constraints

**Why Optimization Matters**:
- **Strategic Efficiency**: Maintains critical infrastructure while reducing complexity
- **Architecture Alignment**: Leverages existing 4-phase execution flow
- **Development Velocity**: Reduced from 3 to 2.5 person-days
- **Maintainability**: Integrated design reduces component boundaries

---

## Timeline and Dependencies

### Estimated Timeline
- **Story 1.1**: 3 person-days (TDD: 1.5 days test + 1.5 days implementation)
- **Story 1.2**: 3 person-days (TDD: 1.5 days test + 1.5 days implementation)
- **Story 1.3**: 3 person-days (TDD: 1.5 days test + 1.5 days implementation)
- **Total**: 9 person-days (~2 weeks)

### Dependencies
```
Story 0.2 (ExecutionPlan Schema) ✅
    ↓
Story 1.1 (PlanValidator) ⏳
    ↓
Story 1.2 (Integration) ⏳
    ↓
Story 1.3 (Basic Constraints) ⏳
    ↓
Phase 2 (Safe Operations) 🔜
```

### Milestones
- [ ] Story 1.1 Complete: PlanValidator implemented and tested
- [ ] Story 1.2 Complete: Validation integrated into execution engine
- [ ] Story 1.3 Complete: Basic constraint rules foundation ready
- [ ] Phase 1 Complete: Full validation framework operational

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Validation overhead too high | Medium | Low | Performance testing in each TDD cycle |
| Constraint rules too complex | Medium | Medium | Start with simple rules, iterate |
| Error messages unclear | High | Medium | User-facing message testing in each story |
| Backward compatibility break | High | Low | Comprehensive regression testing |

### Process Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| TDD discipline not followed | High | Low | Strict cycle enforcement, code review |
| Scope creep to Phase 4 | Medium | Medium | Clear story boundaries, defer advanced features |
| Integration issues with existing tools | Medium | Low | Early integration testing |

---

## Quality Standards

### Testing Requirements
- **Unit Test Coverage**: ≥95% for all new code
- **Integration Tests**: Full ToolExecutionEngine integration scenarios
- **Performance Tests**: <5ms total overhead for validation
- **Regression Tests**: Zero new failures in existing test suite

### Code Quality
- **Type Safety**: 100% mypy strict compliance
- **Formatting**: RUFF + BLACK compliance
- **Documentation**: Comprehensive docstrings for all public APIs
- **Code Review**: All PRs reviewed before merge

### Performance Targets
- ValidationResult instantiation: <0.1ms
- PlanValidator.validate(): <1ms
- Full pre-execution with validation: <5ms
- Zero overhead when constraints disabled

---

## Development Workflow

### GitFlow Process
```
develop
    ↓
feature/epic1-story1-plan-validator (Story 1.1)
    ↓ merge
develop
    ↓
feature/epic1-story2-validation-integration (Story 1.2)
    ↓ merge
develop
    ↓
feature/epic1-story3-basic-constraints (Story 1.3)
    ↓ merge
develop
```

### TDD Workflow (Per Story)
1. **Red Phase**: Write failing tests for next functionality
2. **Green Phase**: Implement minimum code to pass tests
3. **Refactor Phase**: Improve code quality without changing behavior
4. **Integration**: Ensure existing tests still pass
5. **Commit**: Commit after each cycle completion
6. **Review**: Code review before story completion

### Commit Message Format
```
feat(epic1-storyX-cycleY): Brief description

- Detailed change 1
- Detailed change 2
- Test coverage: X tests added

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Documentation Deliverables

### Per Story
- **TDD Plan**: Detailed cycle-by-cycle plan before starting
- **Cycle Reports**: Brief report after each TDD cycle
- **Story Completion Report**: Summary of deliverables and outcomes

### Phase 1 Completion
- **Phase 1 Completion Report**: Comprehensive summary similar to Phase 0
- **Architecture Decision Record**: If significant design decisions made
- **Performance Benchmarks**: Validation overhead measurements
- **Integration Guide**: How to use ExecutionPlan validation in tools

---

## Success Metrics

### Functional Metrics
- ✅ 100% of validation rules implemented
- ✅ Zero false positives in validation
- ✅ Clear actionable error messages for all violations
- ✅ All invalid plans rejected before execution

### Performance Metrics
- ✅ <5ms total validation overhead
- ✅ <1ms PlanValidator execution time
- ✅ Zero overhead when constraints disabled
- ✅ No memory leaks in validation logic

### Quality Metrics
- ✅ ≥95% test coverage for new code
- ✅ Zero regression in existing tests
- ✅ 100% mypy type check passing
- ✅ 100% RUFF + BLACK formatting compliance

### Process Metrics
- ✅ All stories follow TDD workflow
- ✅ Each story completed within estimated time ±20%
- ✅ All code reviewed before merge
- ✅ Documentation complete and up-to-date

---

## Next Steps

### Immediate Actions (Now)
1. ✅ Create Phase 1 Implementation Plan (this document)
2. ⏳ Write Story 1.1 TDD Plan (detailed cycle plan)
3. ⏳ Update Epic-001 README (adjust Phase 1 Features)

### Story 1.1 Kickoff (Next)
1. Review Story 1.1 TDD Plan
2. Create feature branch: `feature/epic1-story1-plan-validator`
3. Start Cycle 1: ValidationResult data class (Red phase)

### Phase 1 Completion (2 weeks target)
1. All 3 stories completed and merged to develop
2. Phase 1 Completion Report generated
3. Performance benchmarks validated
4. Ready to start Phase 2: Safe Operations

---

**Document Status**: [DRAFT] - Awaiting review and approval
**Last Updated**: 2025-10-28
**Next Review**: Before Story 1.1 kickoff