# Lesson 003: batch_edit Tool Capability Boundaries

**Date**: 2025-11-17
**Status**: APPROVED
**Context**: Dogfooding batch_edit tool for EvolvAI codebase improvements
**Related**: Story 2.2 (BatchEditor implementation)

---

## Executive Summary

Through dogfooding the batch_edit tool on the EvolvAI codebase, we discovered critical insights about tool capability boundaries and appropriate use cases. The key finding: **batch_edit is a Level 1 (regex-based) tool and should not attempt to handle Level 2 (AST) or Level 3 (semantic) operations**.

**Core Principle**: Good tools are not universal tools—they excel in specific scenarios and gracefully decline tasks beyond their capabilities.

---

## Background

### Initial Dogfooding Plan

We attempted to use batch_edit for three tasks:

1. **Import order standardization** - Unify Python import statements to PEP 8
2. **Test docstring unification** - Convert simple Chinese docstrings to BDD format
3. **Deprecated API updates** - Find and update deprecated API calls

### Tool Capability Taxonomy

During dogfooding, we identified three distinct tool capability levels:

| Level | Capability | Tool Examples | Operation Type |
|-------|-----------|--------------|----------------|
| **Level 1** | Pattern matching + Text replacement | `sed`, `awk`, `batch_edit` | String operations |
| **Level 2** | Syntax understanding + Structural modification | `isort`, `black`, `ruff` | AST operations |
| **Level 3** | Semantic analysis + Intelligent refactoring | LSP tools, IDE refactoring | Cross-file semantic analysis |

---

## What Happened

### Task 1: Import Order Standardization ❌

**Initial Assumption**: batch_edit can add blank lines between import groups

**Reality Check**:
```
Task: "Insert blank line between stdlib and third-party imports"

What regex can do:
  Match pattern → Replace with new pattern

What's needed:
  Understand import semantics → Identify group boundaries → Insert at boundary

Gap:
  "Group boundary" is a structural concept that regex cannot understand
```

**Outcome**: Used `isort` (Level 2 tool) instead—the correct tool for this task.

**Lesson**: Import ordering requires AST understanding (stdlib vs. third-party vs. local), which is beyond regex capabilities.

---

### Task 2: Test Docstring Unification ❌

**Initial Assumption**: This is a text replacement task

**Reality Check**:
```python
# Current state (simple):
"""测试执行报告生成"""

# Target state (BDD format):
"""Test execution report generation.

Story: story-1.2-tdd-plan.md Cycle 3
Scenario: "User can generate execution report"
DoD: F1 - Functional completeness

Given a successful tool execution
When generating report
Then report contains all execution details
"""
```

**What's needed to transform**:
1. Infer corresponding Story document ❌ (semantic understanding)
2. Infer Scenario from test code ❌ (business logic analysis)
3. Infer DoD standards ❌ (requirement mapping)
4. Generate Given-When-Then ❌ (test logic analysis)

**Outcome**: Abandoned—this is a Level 3 task requiring semantic analysis.

**Lesson**: Even though both are "docstrings," the transformation requires understanding test intent, not just pattern matching.

---

### Task 3: Finding Appropriate Use Cases ⚠️

**Search Results**:
- TODO comments: Only 1 found (no batch operation needed)
- Exception class duplicates: Found 3 `ConstraintViolationError` definitions
  - But they have **incompatible interfaces** (requires refactoring, not simple replacement)
- Docstring style: Already consistent across codebase

**Outcome**: No obvious batch_edit use cases found in current codebase.

**Lesson**: Well-maintained codebases may not have many Level 1 batch replacement opportunities. This doesn't mean the tool is useless—it means the tool's value appears **when needed**, not by forcing usage.

---

## Key Insights

### 1. Tool Selection Matrix

**When to use batch_edit (Level 1)**:

✅ **Appropriate scenarios**:
- Cross-file renaming (API names, variable names, constants)
- String format unification (log formats, comment styles)
- Bulk version number updates, URL changes, config value updates
- Simple code pattern replacements (e.g., `getUserData` → `fetchUserData`)

❌ **Inappropriate scenarios**:
- Operations requiring code structure understanding (import sorting, code reorganization)
- Operations requiring semantic inference (documentation generation, test generation)
- Operations requiring refactoring (interface unification, architecture changes)

### 2. The "Tool Seeking Task" Anti-pattern

**Problem**: "We have batch_edit, let's find something to use it on"

**Why it's wrong**:
- Valuable tools emerge naturally when problems arise
- Forcing tool usage leads to misapplication
- Indicates tool-market fit issues

**Correct approach**: "We have a renaming task, batch_edit is the perfect tool"

### 3. Graceful Degradation > False Capability

From user feedback (KISS/YAGNI principles):

> "我觉得保持 KISS和YAGNI原则，我们只需要返回告知ai 调用不能处理，无法定位。这样可能更好"

**Translation**: Tools should return clear error messages like "cannot locate semantic position" rather than attempting operations beyond their capabilities.

**Benefits**:
- Honest about limitations
- Guides users to appropriate tools
- Maintains trust through transparency

---

## Recommendations

### 1. Documentation Improvements

**batch_edit_tool.py docstring should include**:

```python
"""Batch file editing tool for regex-based pattern replacement.

IMPORTANT - Tool Capability Boundaries:

This is a LEVEL 1 tool (regex-based string operations).

✅ Appropriate for:
  - Cross-file renaming (functions, variables, constants)
  - String format unification (logs, comments, URLs)
  - Simple pattern replacements without semantic understanding

❌ NOT appropriate for:
  - Import ordering (use: isort)
  - Code formatting (use: black, ruff)
  - Semantic refactoring (use: LSP tools, IDE refactoring)
  - Operations requiring code structure understanding

When batch_edit encounters patterns it cannot semantically locate,
it will return a clear error message suggesting appropriate alternatives.
"""
```

### 2. Error Message Enhancement

**Current behavior**: Fails silently or with generic "pattern not found"

**Proposed behavior**: Detect semantic operation patterns and provide helpful guidance

```python
# Example enhanced error:
{
  "success": false,
  "error_type": "SemanticOperationDetected",
  "summary": "Cannot locate: This operation requires semantic understanding",
  "fix_suggestion": "Use these alternatives:\n"
                    "- Import ordering: isort\n"
                    "- Code formatting: black, ruff\n"
                    "- Semantic refactoring: LSP tools",
  "pattern_attempted": "Insert blank line between import groups"
}
```

### 3. Tool Selection Guide

Create a decision tree document:

```
Need to modify code across multiple files?
├─ Simple text pattern replacement? → batch_edit
├─ Code structure/formatting? → black, ruff, isort
└─ Semantic refactoring? → LSP tools, IDE
```

---

## Success Metrics

**This dogfooding was successful because**:

1. ✅ **Identified tool boundaries** - Clear Level 1/2/3 taxonomy
2. ✅ **Fixed circular import** - Discovered and resolved integration issues
3. ✅ **Configured isort** - Set up proper dependency ordering
4. ✅ **Validated KISS principle** - Tools should have clear, focused capabilities
5. ✅ **Prevented feature creep** - Resisted making batch_edit "do everything"

**Not successful at**:
- ❌ Using batch_edit extensively (but this is not the goal!)
- Goal was validation, not forced usage

---

## Future Dogfooding Opportunities

**Wait for organic needs**:
- API renaming across codebase (e.g., `safe_search` → `search_with_constraints`)
- Configuration value updates (e.g., timeout values, version strings)
- Log format standardization (when expanding logging)
- Deprecation notices (when marking APIs as deprecated)

**Don't force**:
- Searching for tasks just to use the tool
- Applying batch_edit to inappropriate scenarios

---

## Related Decisions

- **ADR-004**: Tool-level rollback principle (tools should only rollback their own changes)
- **KISS/YAGNI**: Simple, focused tools over complex, universal tools
- **Unix Philosophy**: Each tool does one thing well

---

## Conclusion

The greatest value from this dogfooding was **not** extensive tool usage, but rather **clarity about tool boundaries**. batch_edit is valuable precisely because it:

1. Excels at Level 1 (regex) operations
2. Refuses Level 2/3 operations gracefully
3. Guides users to appropriate alternatives

**Quote from user**: "保持 KISS和YAGNI原则" (Keep KISS and YAGNI principles)

This captures the essence: Good engineering is knowing what NOT to build, not just what to build.
