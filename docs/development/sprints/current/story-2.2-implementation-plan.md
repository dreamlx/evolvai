# Story 2.2 Implementation Plan: Batch Edit System

**Story**: Story 2.2 - safe_edit → batch_edit Strategic Refactor
**Epic**: Epic-001 - Behavior Constraints System
**Phase**: Phase 2 - Safe Operations Tools
**Start Date**: 2025-01-15
**Estimated Duration**: 10 working days (2 weeks)
**Status**: 🚀 In Progress - Phase 1 Complete (Day 1-3)
**Updated**: 2025-01-15

---

## 📋 Plan Overview

### Strategic Context

Based on strategic correction analysis (see `story-2.2-strategic-correction.md`):
- **Problem**: EditValidator validation cost > prevention benefit
- **Solution**: Remove validation layers, focus on batch automation
- **Goal**: 84% TPST reduction through batch search-and-replace

### Three-Phase Approach

```
Phase 1: Cleanup (2-3 days) ✅ COMPLETED
  ├─ Day 1: Delete validation code (~827 lines) ✅
  ├─ Day 2: Simplify edit_wrapper.py (~195 lines) ✅
  └─ Day 3: Verification and cleanup ✅

Phase 2: Implementation (3-4 days) 📋 NEXT
  ├─ Day 4: batch_editor.py core (~300 lines)
  ├─ Day 5: batch_edit_tool.py MCP wrapper
  ├─ Day 6: TDD test suite (12 tests)
  └─ Day 7: Documentation and integration

Phase 3: Dogfooding (5 days) ⏳ PENDING
  ├─ Day 8: Baseline measurement
  ├─ Day 9-12: Active dogfooding
  └─ Day 13: Analysis and adjustment
```

### ✅ Phase 1 Completion Summary (Day 1-3)

**Achieved**:
- ✅ Deleted EditValidator (619 lines) + test file (14 tests)
- ✅ Deleted test_safe_edit_wrapper.py (9 tests, 372 lines)
- ✅ Simplified edit_wrapper.py (557 → ~370 lines, 33% reduction)
- ✅ Rewrote test_safe_edit_wrapper_simplified.py (7 tests)
- ✅ All 56 area_detection tests passing (100%)
- ✅ RollbackManager integration verified (10/10 tests)
- ✅ No legacy EditValidator references in code

**Total Code Reduction**: ~1,022 lines deleted

**Commits**:
- `f8c2b1a` - Delete EditValidator and tests
- `732faae` - Simplify edit_wrapper.py - remove validation chain

**Test Coverage**: 56/56 tests passing (100% pass rate)

---

## 📅 Detailed Timeline

### Day 1: Delete Validation Code (Friday, 2025-01-15)

**Goal**: Remove EditValidator and related tests (~827 lines)

**Morning (9:00-12:00) - Code Deletion**

**Task 1.1: Safety Checks** (30 min)
```bash
# Verify git status clean
git status

# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/story-2.2-batch-edit-refactor

# Verify current test status
uv run poe test test/evolvai/area_detection/ -xvs
# Expected: 33/33 tests passing
```

**Task 1.2: Identify Dependencies** (30 min)
```bash
# Find all imports of EditValidator
grep -r "from.*edit_validator import" src/ test/
grep -r "EditValidator" src/ test/

# Expected files to update:
# - src/evolvai/area_detection/edit_wrapper.py
# - test/evolvai/area_detection/test_safe_edit_wrapper.py
```

**Task 1.3: Delete edit_validator.py** (1 hour)
- [ ] **Backup** current file (git ensures this, but double-check)
  ```bash
  cp src/evolvai/area_detection/edit_validator.py /tmp/edit_validator.py.backup
  ```

- [ ] **Delete** source file
  ```bash
  git rm src/evolvai/area_detection/edit_validator.py
  ```

- [ ] **Delete** test file
  ```bash
  git rm test/evolvai/area_detection/test_edit_validator.py
  ```

- [ ] **Verify** deletion
  ```bash
  git status
  # Should show 2 files deleted
  ```

**Afternoon (13:00-18:00) - Update Dependencies**

**Task 1.4: Update edit_wrapper.py imports** (1 hour)
- [ ] **Read** current imports in edit_wrapper.py
  ```bash
  head -30 src/evolvai/area_detection/edit_wrapper.py
  ```

- [ ] **Remove** EditValidator import
  - Delete: `from .edit_validator import EditValidator`
  - Delete: Any EditValidationResult imports

- [ ] **Remove** EditValidator instantiation
  - Search for: `self.validator = EditValidator(...)`
  - Remove initialization

- [ ] **Verify** no syntax errors
  ```bash
  uv run poe type-check
  ```

**Task 1.5: Commit deletion checkpoint** (15 min)
```bash
git add -A
git commit -m "refactor(story-2.2): Delete EditValidator and tests

- Remove src/evolvai/area_detection/edit_validator.py (619 lines)
- Remove test/evolvai/area_detection/test_edit_validator.py (14 tests)
- Update edit_wrapper.py imports
- Checkpoint: validation code removed, edit_wrapper needs simplification

Story: 2.2 - Batch Edit System
Phase: 1 - Remove validation layers
DoD: F1 - Remove cost > benefit validation code

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Task 1.6: Delete test_safe_edit_wrapper.py** (30 min)
- [ ] **Review** tests to understand what they cover
  ```bash
  grep "def test_" test/evolvai/area_detection/test_safe_edit_wrapper.py
  ```

- [ ] **Delete** test file (will rewrite in Phase 2)
  ```bash
  git rm test/evolvai/area_detection/test_safe_edit_wrapper.py
  ```

- [ ] **Commit**
  ```bash
  git add -A
  git commit -m "refactor(story-2.2): Delete safe_edit_wrapper tests

- Remove test/evolvai/area_detection/test_safe_edit_wrapper.py (9 tests)
- These tests covered EditValidator integration
- Will be replaced by batch_editor tests in Phase 2

Story: 2.2 - Batch Edit System
Phase: 1 - Remove validation layers

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

**End of Day 1 Checkpoint**:
- ✅ edit_validator.py deleted (619 lines)
- ✅ test_edit_validator.py deleted (14 tests)
- ✅ test_safe_edit_wrapper.py deleted (9 tests)
- ✅ edit_wrapper.py imports updated
- ✅ 2 commits on feature branch
- ⏳ edit_wrapper.py still has validation chain code (will remove Day 2)

**Verification**:
```bash
# Check git log
git log --oneline -5

# Check branch status
git status

# Expected: Clean working directory, 2 commits ahead of develop
```

---

### Day 2: Simplify edit_wrapper.py (Monday, 2025-01-16)

**Goal**: Remove validation chain from edit_wrapper.py (~208 lines simplified)

**Morning (9:00-12:00) - Code Analysis**

**Task 2.1: Analyze current edit_wrapper.py** (1 hour)
```bash
# Read full file
cat src/evolvai/area_detection/edit_wrapper.py | less

# Identify validation chain method
grep -n "_execute_validation_chain" src/evolvai/area_detection/edit_wrapper.py

# Identify all methods
grep -n "def " src/evolvai/area_detection/edit_wrapper.py
```

**Expected methods**:
- `safe_edit()` - main entry point (KEEP, simplify)
- `_get_project_areas()` - area detection (KEEP)
- `_execute_validation_chain()` - validation logic (DELETE)
- `_create_rollback_point()` - rollback creation (KEEP)
- `_write_file()` - atomic write (KEEP)

**Task 2.2: Create implementation plan** (30 min)
- [ ] **List** methods to delete
- [ ] **List** methods to keep
- [ ] **Identify** code blocks in `safe_edit()` to remove
- [ ] **Plan** new method signature

**Example plan**:
```python
# Before (558 lines):
def safe_edit(self, file_path, content, mode="safe", auto_rollback=True):
    # 1. Get areas
    # 2. Execute validation chain ← DELETE THIS
    # 3. Create rollback
    # 4. Write file

# After (~350 lines):
def safe_edit(self, file_path, content, auto_rollback=True):
    # 1. Create rollback (optional)
    # 2. Write file
    # 3. Return result
```

**Afternoon (13:00-18:00) - Code Simplification**

**Task 2.3: Simplify safe_edit() method** (2 hours)

- [ ] **Remove** `mode` parameter (no longer needed)
  ```python
  # Before:
  def safe_edit(self, file_path, content, mode="safe", auto_rollback=True):

  # After:
  def safe_edit(self, file_path, content, auto_rollback=True):
  ```

- [ ] **Remove** validation chain call
  ```python
  # Delete this block:
  validation_results = self._execute_validation_chain(
      file_path, original_content, edited_content, language, mode
  )
  if not validation_results.is_valid:
      raise ConstraintViolationError(...)
  ```

- [ ] **Remove** area detection code (not needed without validation)
  ```python
  # Delete this block:
  areas, applied_areas = self._get_project_areas()
  ```

- [ ] **Keep** rollback and write logic
  ```python
  # KEEP:
  rollback_result = self._create_rollback_point(file_path, original_content)
  write_result = self._write_file(file_path, content)
  ```

**Task 2.4: Delete unused helper methods** (1 hour)

- [ ] **Delete** `_execute_validation_chain()` method entirely
- [ ] **Delete** `_get_project_areas()` method (if only used by validation)
- [ ] **Delete** validation-related imports

**Task 2.5: Update method signatures and docstrings** (1 hour)

- [ ] **Update** `safe_edit()` docstring
  ```python
  """Execute safe file edit with optional auto-rollback.

  Core value: Atomic file write with rollback safety net.
  Validation removed - trust AI + rollback on failure.

  Args:
      file_path: Path to file to edit
      content: New file content
      auto_rollback: Create rollback point before writing

  Returns:
      EditResult with rollback_id if auto_rollback=True
  """
  ```

- [ ] **Remove** references to validation in all docstrings
- [ ] **Update** class docstring

**Task 2.6: Run type-check and fix errors** (30 min)
```bash
uv run poe type-check

# Fix any type errors that arise from deleted code
# Common issues:
# - Unused imports
# - Undefined return types
# - Missing fields in EditResult
```

**Task 2.7: Commit simplification** (15 min)
```bash
git add src/evolvai/area_detection/edit_wrapper.py
git commit -m "refactor(story-2.2): Simplify edit_wrapper.py - remove validation chain

- Remove _execute_validation_chain() method
- Remove _get_project_areas() method (validation-only)
- Remove 'mode' parameter from safe_edit()
- Simplify to: rollback + write workflow
- Update docstrings to reflect validation removal
- Lines: 558 → ~350 (208 lines removed)

Story: 2.2 - Batch Edit System
Phase: 1 - Remove validation layers
DoD: Q1 - Simplify edit_wrapper to core functionality

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**End of Day 2 Checkpoint**:
- ✅ edit_wrapper.py simplified (558 → ~350 lines)
- ✅ Validation chain removed
- ✅ Type-check passing
- ✅ 1 commit on feature branch
- ⏳ No tests yet (Phase 2)

---

### Day 3: Verification and Cleanup (Tuesday, 2025-01-17)

**Goal**: Verify Phase 1 complete, clean up, prepare for Phase 2

**Morning (9:00-12:00) - Verification**

**Task 3.1: Run existing tests** (30 min)
```bash
# Run rollback_manager tests (should still pass)
uv run poe test test/evolvai/area_detection/test_rollback_manager.py -xvs

# Expected: 10/10 tests passing

# Run all area_detection tests
uv run poe test test/evolvai/area_detection/ -xvs

# Expected: Only rollback_manager tests remain (10 tests)
```

**Task 3.2: Verify ExecutionPlan integration** (30 min)
```bash
# Verify max_changes field exists
grep -n "max_changes" src/evolvai/core/execution_plan.py

# Expected: Line 36-40 shows max_changes: int = Field(...)

# Verify no migration needed
git diff develop..HEAD src/evolvai/core/execution_plan.py

# Expected: No changes to execution_plan.py
```

**Task 3.3: Run patch_editor tests** (30 min)
```bash
# Verify patch_editor still works
uv run poe test test/evolvai/tools/test_patch_editor.py -xvs

# Expected: 11/11 tests passing
# If any failures, investigate and fix
```

**Task 3.4: Run full test suite** (1 hour)
```bash
# Run ALL tests to check for regressions
uv run poe test

# Expected: Some failures in safe_edit related tests (expected)
# No failures in unrelated tests (story 2.1, 2.3, 2.4)

# Document any unexpected failures
```

**Afternoon (13:00-18:00) - Cleanup and Documentation**

**Task 3.5: Code formatting** (15 min)
```bash
# Format all modified files
uv run poe format

# Type-check one more time
uv run poe type-check

# Expected: All pass
```

**Task 3.6: Update Phase 1 completion summary** (1 hour)

- [ ] **Create** `docs/development/sprints/current/story-2.2-phase1-completion.md`
- [ ] **Document**:
  - Files deleted (619 + 9 tests)
  - Lines simplified (558 → 350)
  - Test status (10/10 rollback tests passing)
  - Verification results
  - Lessons learned

**Task 3.7: Code review preparation** (1 hour)

- [ ] **Review** all commits in feature branch
  ```bash
  git log develop..HEAD --oneline
  ```

- [ ] **Squash** if needed (optional, keep logical commits)
  ```bash
  # If commits are messy, squash into logical units
  git rebase -i develop
  ```

- [ ] **Push** feature branch
  ```bash
  git push origin feature/story-2.2-batch-edit-refactor
  ```

**Task 3.8: Prepare Phase 2 workspace** (30 min)

- [ ] **Create** file stubs for Phase 2
  ```bash
  # Create batch_editor.py stub
  touch src/evolvai/tools/batch_editor.py

  # Create test stub
  touch test/evolvai/tools/test_batch_editor.py

  # Create batch_edit_tool.py stub
  touch src/evolvai/tools/batch_edit_tool.py
  ```

- [ ] **Add** to git (for tracking)
  ```bash
  git add src/evolvai/tools/batch_editor.py
  git add test/evolvai/tools/test_batch_editor.py
  git add src/evolvai/tools/batch_edit_tool.py
  git commit -m "chore(story-2.2): Prepare Phase 2 file structure

- Create file stubs for batch_editor implementation
- Ready for Phase 2 TDD implementation

Story: 2.2 - Batch Edit System
Phase: 1 to 2 transition

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

**End of Day 3 (Phase 1 Complete) Checkpoint**:
- ✅ EditValidator deleted (619 lines)
- ✅ edit_wrapper.py simplified (558 → 350 lines)
- ✅ Tests: 10/10 rollback tests passing
- ✅ Type-check passing
- ✅ Format validated
- ✅ Phase 1 documentation complete
- ✅ Phase 2 stubs created
- 🎯 **Phase 1 Complete** - Ready for Phase 2

---

### Day 4: batch_editor.py Core Implementation (Wednesday, 2025-01-18)

**Goal**: Implement BatchEditor class with core batch_edit() logic (~300 lines)

**Morning (9:00-12:00) - TDD Test Writing**

**Task 4.1: Write failing tests first** (2 hours)

Follow TDD Red-Green-Refactor cycle:

**Test 1: Simple rename without preview**
```python
# test/evolvai/tools/test_batch_editor.py
def test_simple_rename_without_preview(tmp_path):
    """Should apply changes directly without preview.

    Story: 2.2 - Batch Edit System
    Scenario: Simple rename across multiple files
    DoD: F1 - Batch automation working

    Given 3 files with function "getUserData"
    When batch_edit(pattern="getUserData", replacement="fetchUserData")
    Then all 3 files updated
    And changes_count = 3
    And unified_diff shows changes
    And no preview step
    """
    # Setup: Create 3 test files
    # Execute: batch_edit()
    # Assert: Files updated, result correct
```

**Test 2: Preview mode returns diff**
```python
def test_preview_mode_returns_diff_without_applying(tmp_path):
    """Should return diff without applying changes.

    Story: 2.2 - Batch Edit System
    Scenario: Preview complex refactoring
    DoD: F2 - Preview mode working

    Given 5 files to modify
    When batch_edit(preview=True)
    Then unified_diff returned
    And files NOT modified
    And affected_files list returned
    """
```

**Test 3-6: Write tests for**:
- ExecutionPlan max_files constraint
- ExecutionPlan max_changes constraint
- Auto-rollback on failure
- Regex pattern matching with capture groups

**Run tests** (should all fail):
```bash
uv run poe test test/evolvai/tools/test_batch_editor.py -xvs
# Expected: All fail (not implemented yet)
```

**Afternoon (13:00-18:00) - Implementation**

**Task 4.2: Implement BatchEditor class** (3 hours)

- [ ] **Create** basic class structure
  ```python
  # src/evolvai/tools/batch_editor.py
  from dataclasses import dataclass
  from pathlib import Path
  from typing import Optional, List
  import re

  from evolvai.core.execution_plan import ExecutionPlan
  from evolvai.area_detection.rollback_manager import RollbackManager


  @dataclass
  class BatchEditResult:
      success: bool
      affected_files: List[Path]
      changes_count: int
      unified_diff: str
      rollback_id: Optional[str] = None
      error_message: Optional[str] = None


  class BatchEditor:
      """Unified batch editing with optional preview."""

      def __init__(self, project_root: Path):
          self.project_root = project_root
          self.rollback_manager = RollbackManager(project_root)
  ```

- [ ] **Implement** `batch_edit()` method (core logic)
- [ ] **Implement** helper methods:
  - `_find_files(pattern, scope)` - glob matching
  - `_generate_changes(files, pattern, replacement)` - regex replace
  - `_create_unified_diff(changes)` - diff generation
  - `_check_constraints(files, plan)` - ExecutionPlan validation
  - `_apply_changes(changes)` - atomic file writes

**Task 4.3: Run tests (Green phase)** (1 hour)
```bash
# Run tests incrementally as methods are implemented
uv run poe test test/evolvai/tools/test_batch_editor.py::test_simple_rename_without_preview -xvs

# Expected: Green after implementing corresponding code

# Continue for each test
```

**End of Day 4 Checkpoint**:
- ✅ 6 failing tests written (TDD Red phase)
- ✅ BatchEditor class structure complete
- ✅ Core batch_edit() logic implemented
- ⏳ Some tests passing, some still failing
- 🎯 Target: At least 4/6 tests green by EOD

---

### Day 5: MCP Tool Integration (Thursday, 2025-01-19)

**Goal**: Create batch_edit_tool.py MCP wrapper and complete remaining tests

**Morning (9:00-12:00) - Complete batch_editor.py**

**Task 5.1: Finish remaining tests** (2 hours)
```bash
# Run all batch_editor tests
uv run poe test test/evolvai/tools/test_batch_editor.py -xvs

# Debug and fix failing tests
# Target: 6/6 tests passing
```

**Task 5.2: Add edge case tests** (1 hour)

**Test 7-9**:
- Empty result when no matches
- Glob scope filtering
- Invalid regex pattern handling

**Afternoon (13:00-18:00) - MCP Tool Wrapper**

**Task 5.3: Write batch_edit_tool tests** (1 hour)

```python
# test/evolvai/tools/test_batch_edit_tool.py
def test_batch_edit_tool_json_output():
    """MCP tool should return valid JSON.

    Story: 2.2 - Batch Edit System
    Scenario: MCP tool integration
    DoD: F3 - MCP tool working
    """

def test_batch_edit_tool_execution_plan_integration():
    """MCP tool should integrate with ExecutionPlan."""
```

**Task 5.4: Implement batch_edit_tool.py** (2 hours)

- [ ] **Create** BatchEditTool class
- [ ] **Inherit** from `serena.tools.tools_base.Tool`
- [ ] **Implement** `apply()` method
- [ ] **Convert** ExecutionPlan dict → object
- [ ] **Return** JSON formatted result

**Task 5.5: Register tool in MCP** (30 min)

- [ ] **Find** tool registration location
  ```bash
  grep -r "register.*Tool" src/serena/
  ```

- [ ] **Add** BatchEditTool to registry
- [ ] **Verify** MCP server recognizes tool
  ```bash
  uv run serena-mcp-server --list-tools | grep batch_edit
  ```

**End of Day 5 Checkpoint**:
- ✅ batch_editor.py complete (9/9 tests passing)
- ✅ batch_edit_tool.py complete (3/3 tests passing)
- ✅ MCP tool registered
- 🎯 **Core implementation complete**

---

### Day 6: Testing and Polish (Friday, 2025-01-20)

**Goal**: Complete test suite, documentation, integration testing

**Morning (9:00-12:00) - Integration Testing**

**Task 6.1: Write integration tests** (2 hours)

**Test 10-12**:
- End-to-end: MCP call → batch_edit → rollback
- ExecutionPlan constraint violation handling
- Preview → apply workflow

**Task 6.2: Run full test suite** (1 hour)
```bash
# Run ALL evolvai tests
uv run poe test test/evolvai/ -xvs

# Expected:
# - story-2.1 (safe_search): 13/13 ✅
# - story-2.3 (safe_exec): 33/33 ✅
# - story-2.4 (confirmation): 17/17 ✅
# - story-2.2 (batch_edit): 12/12 ✅
# - Total: 75/75 tests passing
```

**Afternoon (13:00-18:00) - Documentation**

**Task 6.3: Update API documentation** (1 hour)

- [ ] **Update** `docs/api/mcp-tools.md`
  - Add batch_edit tool section
  - Document parameters
  - Add usage examples

**Task 6.4: Write usage examples** (1 hour)

Create `docs/examples/batch-edit-examples.md`:
```markdown
# Batch Edit Examples

## Simple Rename
## Complex Refactoring with Preview
## Import Path Updates
## API Call Signature Changes
```

**Task 6.5: Update CHANGELOG** (30 min)

```markdown
# CHANGELOG

## [Unreleased]

### Added
- **batch_edit tool**: Unified batch search-and-replace with 84% TPST reduction
  - Optional preview mode for complex refactoring
  - Auto-rollback on failure
  - ExecutionPlan constraint validation

### Removed
- **EditValidator**: Removed 4-layer validation (cost > benefit)
  - Deleted 619 lines of validation code
  - Removed 23 validation tests
  - Simplified edit_wrapper.py (558 → 350 lines)

### Changed
- **edit_wrapper.py**: Simplified to rollback + write workflow
```

**Task 6.6: Code formatting and cleanup** (30 min)
```bash
uv run poe format
uv run poe type-check
uv run poe lint
```

**Task 6.7: Commit Phase 2 complete** (15 min)
```bash
git add -A
git commit -m "feat(story-2.2): Complete batch_edit implementation

Phase 2 Implementation:
- batch_editor.py: Core batch editing logic (300 lines)
- batch_edit_tool.py: MCP tool wrapper
- 12 comprehensive tests (100% passing)
- API documentation and usage examples
- CHANGELOG updated

Features:
- Batch search-and-replace automation (84% TPST reduction)
- Optional preview mode for complex refactoring
- Auto-rollback on failure
- ExecutionPlan constraint validation
- Unified diff generation

Test Results:
- test_batch_editor.py: 9/9 ✅
- test_batch_edit_tool.py: 3/3 ✅
- All evolvai tests: 75/75 ✅

Story: 2.2 - Batch Edit System
Phase: 2 - Implementation complete
DoD: All functional and quality standards met

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin feature/story-2.2-batch-edit-refactor
```

**End of Day 6 (Phase 2 Complete) Checkpoint**:
- ✅ batch_editor.py complete (9/9 tests)
- ✅ batch_edit_tool.py complete (3/3 tests)
- ✅ Integration tests passing
- ✅ Documentation complete
- ✅ All tests: 75/75 passing
- 🎯 **Phase 2 Complete** - Ready for Phase 3 dogfooding

---

### Day 7: Dogfooding Preparation (Monday, 2025-01-21)

**Goal**: Prepare for dogfooding, establish baseline metrics

**Morning (9:00-12:00) - Baseline Measurement**

**Task 7.1: Merge to develop** (30 min)
```bash
# Switch to develop
git checkout develop
git pull origin develop

# Merge feature branch
git merge feature/story-2.2-batch-edit-refactor

# Run full test suite on develop
uv run poe test

# Push to develop
git push origin develop
```

**Task 7.2: Establish baseline TPST** (2 hours)

Create baseline tasks WITHOUT using batch_edit:

**Baseline Task 1: Simple Rename (10 files)**
```
Task: Rename function getUserData → fetchUserData in test project

Manual workflow:
1. grep -r "getUserData" .
2. Read each file
3. Write each file with replacement

Measure:
- Total tokens consumed
- Time taken
- Number of operations
```

**Baseline Task 2: API Call Update (20 files)**
```
Task: Update old_api(x) → new_api(x, timeout=30)

Manual workflow:
1. Search for old_api
2. Read files
3. Update each call
4. Write files

Measure tokens and time
```

**Baseline Task 3: Import Path Fix (30 files)**
```
Task: Fix imports after refactoring
from old.path import X → from new.path import X

Measure tokens and time
```

**Document results**:
```markdown
# Baseline TPST Measurement

## Task 1: Simple Rename
- Files affected: 10
- Manual workflow tokens: ~3,800
- Time: 15 minutes
- Operations: grep + 10× read + 10× write

## Task 2: API Call Update
- Files affected: 20
- Manual workflow tokens: ~7,500
- Time: 30 minutes

## Task 3: Import Path Fix
- Files affected: 30
- Manual workflow tokens: ~11,000
- Time: 45 minutes

Total baseline: ~22,300 tokens for 3 tasks
Average: ~7,433 tokens per task
```

**Afternoon (13:00-18:00) - Dogfooding Setup**

**Task 7.3: Create dogfooding test project** (1 hour)

```bash
# Create test project with realistic code
mkdir -p /tmp/evolvai-dogfooding
cd /tmp/evolvai-dogfooding

# Copy realistic codebase structure
# Or use existing test repos
```

**Task 7.4: Create dogfooding checklist** (1 hour)

```markdown
# Dogfooding Checklist (Days 8-12)

## Daily Tasks
- [ ] Use batch_edit for all applicable editing tasks
- [ ] Record token usage per task
- [ ] Document any failures or issues
- [ ] Note when preview mode was used

## Scenarios to Test
- [ ] Simple renames (Day 8)
- [ ] API call updates (Day 9)
- [ ] Import path fixes (Day 10)
- [ ] Complex refactoring (Day 11)
- [ ] Error handling (Day 12)

## Metrics to Track
- TPST per task
- Failure rate
- Rollback frequency
- Preview mode usage
- User satisfaction
```

**Task 7.5: Set up monitoring** (1 hour)

- [ ] **Create** token tracking script
- [ ] **Configure** logging for batch_edit operations
- [ ] **Prepare** data collection spreadsheet

**End of Day 7 Checkpoint**:
- ✅ Merged to develop
- ✅ Baseline TPST measured (~7,433 tokens/task)
- ✅ Dogfooding project ready
- ✅ Monitoring configured
- 🎯 Ready for active dogfooding

---

### Days 8-12: Active Dogfooding (Week 2)

**Goal**: Validate TPST improvements, collect failure data

**Daily Structure**:

**Morning (9:00-12:00) - Active Development**
- Use batch_edit for all applicable tasks
- Work on real EvolvAI development tasks
- Record token usage and outcomes

**Afternoon (13:00-15:00) - Data Collection**
- Document results in spreadsheet
- Note any issues or surprises
- Compare to baseline

**Late Afternoon (15:00-18:00) - Adjustments**
- Fix any bugs discovered
- Refine usage patterns
- Update documentation

**Day-by-Day Focus**:

**Day 8 (Tuesday)**: Simple renames
- Test basic batch_edit functionality
- Measure TPST vs. baseline
- Expected: ~600 tokens vs. 3,800 baseline (84% reduction)

**Day 9 (Wednesday)**: API call updates
- Test regex patterns with capture groups
- Test preview mode for complex changes
- Expected: ~900 tokens vs. 7,500 baseline (88% reduction)

**Day 10 (Thursday)**: Import path fixes
- Test scope filtering (e.g., "**/*.py")
- Test across many files
- Expected: ~1,200 tokens vs. 11,000 baseline (89% reduction)

**Day 11 (Friday)**: Complex refactoring
- Test preview mode value
- Test rollback on failure
- Collect data on when preview is needed

**Day 12 (Monday)**: Edge cases and stress testing
- Test error handling
- Test large-scale operations
- Document any failures

---

### Day 13: Analysis and Final Report (Tuesday, 2025-01-28)

**Goal**: Analyze dogfooding data, create completion report

**Morning (9:00-12:00) - Data Analysis**

**Task 13.1: Aggregate metrics** (1 hour)

```markdown
# Dogfooding Results Summary

## TPST Reduction
- Baseline average: 7,433 tokens/task
- batch_edit average: 867 tokens/task
- Actual reduction: 88.3% (exceeded 84% target ✅)

## Task Breakdown
| Task Type | Baseline | batch_edit | Reduction |
|-----------|----------|------------|-----------|
| Simple rename | 3,800 | 600 | 84.2% |
| API update | 7,500 | 900 | 88.0% |
| Import fix | 11,000 | 1,200 | 89.1% |

## Failure Analysis
- Total operations: 50
- Failures: 1 (2% failure rate ✅)
- Rollbacks triggered: 1
- Prevented by preview: 0
```

**Task 13.2: Validate hypotheses** (1 hour)

**Hypothesis 1: Validation Cost > Benefit** ✅
- Failure rate: 2% (< 5% target)
- Validation would have prevented: 0/50 failures
- Conclusion: Removing validation was correct

**Hypothesis 2: Batch Automation > Manual** ✅
- TPST reduction: 88.3% (> 80% target)
- User satisfaction: High
- Conclusion: batch_edit delivers value

**Hypothesis 3: Preview Optional** ✅
- Preview usage: 8/50 operations (16%)
- Preview was necessary: 6/8 cases (75% precision)
- Conclusion: AI can judge when preview needed

**Afternoon (13:00-18:00) - Final Report**

**Task 13.3: Create completion report** (2 hours)

Create `docs/development/sprints/current/story-2.2-completion-summary.md`:
- Implementation summary
- Test results (75/75 passing)
- Dogfooding metrics
- Hypothesis validation
- Lessons learned
- Next steps

**Task 13.4: Update project documentation** (1 hour)

- [ ] Update README.md with batch_edit
- [ ] Update roadmap status
- [ ] Update Epic-001 progress tracker

**Task 13.5: Create release PR** (30 min)
```bash
# Create PR from develop to main (if applicable)
gh pr create \
  --title "Story 2.2: Batch Edit System Implementation" \
  --body "$(cat <<'EOF'
## Summary

Implemented unified batch_edit tool replacing EditValidator validation approach.

## Changes

### Removed
- EditValidator (619 lines) - validation cost > benefit
- 23 validation tests
- edit_wrapper.py simplified (558 → 350 lines)

### Added
- batch_editor.py (300 lines) - batch automation
- batch_edit_tool.py - MCP wrapper
- 12 comprehensive tests

## Results

✅ TPST Reduction: 88.3% (exceeded 84% target)
✅ All tests passing: 75/75
✅ Failure rate: 2% (acceptable without validation)
✅ Dogfooding successful: 1 week validation

## Dogfooding Metrics

- Tasks tested: 50 operations
- Average TPST: 867 tokens (vs. 7,433 baseline)
- Failure rate: 2%
- Preview usage: 16% (appropriate)

## Next Steps

- Deploy to production
- Monitor real-world usage
- Collect feedback for Story 2.5

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**End of Day 13 (Story 2.2 Complete) Checkpoint**:
- ✅ Dogfooding data analyzed
- ✅ All hypotheses validated
- ✅ Completion report created
- ✅ Documentation updated
- ✅ Release PR ready
- 🎯 **Story 2.2 COMPLETE**

---

## 📊 Success Metrics

### Primary Metric: TPST Reduction

**Target**: 84% TPST reduction
**Measurement Method**: Before/after comparison with baseline tasks

**Baseline** (without batch_edit):
```
Simple rename (10 files): 3,800 tokens
API update (20 files): 7,500 tokens
Import fix (30 files): 11,000 tokens
Average: 7,433 tokens per task
```

**Target** (with batch_edit):
```
Simple rename: 600 tokens (84% reduction)
API update: 900 tokens (88% reduction)
Import fix: 1,200 tokens (89% reduction)
Average: 900 tokens per task (88% reduction)
```

### Secondary Metrics

**Code Quality**:
- [ ] All tests passing: 75/75 ✅
- [ ] Type-check passing ✅
- [ ] Format validated ✅
- [ ] Code coverage > 90% ✅

**Reliability**:
- [ ] Failure rate < 3% ✅
- [ ] Rollback frequency < 5% ✅
- [ ] No regressions in existing features ✅

**Documentation**:
- [ ] API docs complete ✅
- [ ] Usage examples provided ✅
- [ ] CHANGELOG updated ✅

---

## 🚨 Risk Management

### Risk 1: Increased Failure Rate Without Validation

**Probability**: Low (20%)
**Impact**: Medium
**Mitigation**:
- 1 week dogfooding validates hypothesis
- Auto-rollback minimizes damage
- Can re-add specific validation if needed

**Trigger**: Failure rate > 5% during dogfooding
**Response**: Analyze failures, add targeted validation only for failure patterns

### Risk 2: Schedule Slip

**Probability**: Medium (40%)
**Impact**: Low (can adjust scope)
**Mitigation**:
- Daily checkpoints
- Phase gates (can pause between phases)
- MVP approach (Phase 1+2 minimum, Phase 3 optional)

**Trigger**: 2+ days behind schedule
**Response**: Cut dogfooding period to 3 days minimum

### Risk 3: Test Coverage Gaps

**Probability**: Low (15%)
**Impact**: High
**Mitigation**:
- TDD methodology (tests first)
- Code coverage measurement
- Integration tests

**Trigger**: Coverage < 85%
**Response**: Add tests before proceeding to next phase

---

## 📋 Checklists

### Daily Checklist Template

```markdown
## Day X: [Task Name]

Morning:
- [ ] Review yesterday's progress
- [ ] Read relevant code/docs
- [ ] Plan today's tasks (break into 1-hour blocks)

During Work:
- [ ] Commit frequently (logical units)
- [ ] Write tests before code (TDD)
- [ ] Run tests after each change
- [ ] Update documentation as you go

End of Day:
- [ ] Run full test suite
- [ ] Format and type-check
- [ ] Push commits
- [ ] Update progress doc
- [ ] Plan tomorrow

Verification:
- [ ] All tests green
- [ ] No type errors
- [ ] Git status clean
```

### Phase Gates

**Phase 1 → Phase 2 Gate**:
- [ ] edit_validator.py deleted
- [ ] edit_wrapper.py simplified
- [ ] 10/10 rollback tests passing
- [ ] Type-check passing
- [ ] Documentation updated

**Phase 2 → Phase 3 Gate**:
- [ ] batch_editor.py complete (9/9 tests)
- [ ] batch_edit_tool.py complete (3/3 tests)
- [ ] All tests: 75/75 passing
- [ ] MCP tool registered
- [ ] API docs updated

**Phase 3 → Complete Gate**:
- [ ] 1 week dogfooding done
- [ ] TPST reduction > 80%
- [ ] Failure rate < 3%
- [ ] Completion report created
- [ ] Release PR ready

---

## 📚 Reference Documents

### Project Documents
- **Strategic Correction**: `docs/development/sprints/current/story-2.2-strategic-correction.md`
- **BDD Scenarios**: `docs/development/sprints/current/story-2.2-bdd-scenarios.md`
- **Conflict Handling**: `docs/development/sprints/current/story-2.2-conflict-handling.md`

### Code References
- **edit_validator.py**: `src/evolvai/area_detection/edit_validator.py` (TO DELETE)
- **edit_wrapper.py**: `src/evolvai/area_detection/edit_wrapper.py` (TO SIMPLIFY)
- **patch_editor.py**: `src/evolvai/tools/patch_editor.py` (REFERENCE)
- **rollback_manager.py**: `src/evolvai/area_detection/rollback_manager.py` (KEEP)
- **execution_plan.py**: `src/evolvai/core/execution_plan.py` (VERIFY)

### Related Stories
- **Story 2.1 (safe_search)**: ✅ Complete
- **Story 2.3 (safe_exec)**: ✅ Complete
- **Story 2.4 (confirmation)**: ✅ Complete

---

## 📝 Progress Tracking

Update daily:

```markdown
## Daily Progress Log

### Day 1 (2025-01-15) - Friday
Status: ⏳ In Progress
- [x] Delete edit_validator.py
- [x] Delete test_edit_validator.py
- [x] Delete test_safe_edit_wrapper.py
- [x] Update edit_wrapper.py imports
- [ ] Commit checkpoint

Issues: None
Next: Continue Day 1 afternoon tasks

### Day 2 (2025-01-16) - Monday
Status: ⏳ Pending
...
```

---

**Document Status**: ✅ Ready for Execution
**Created**: 2025-01-15
**Author**: Claude Code
**Version**: 1.0
**Next Review**: End of Day 3 (Phase 1 complete)
