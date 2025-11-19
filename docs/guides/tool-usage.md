# EvolvAI Tool Usage Guide

**Purpose**: Educational guide for understanding tool capabilities and selection strategies.

**For**: Human developers and AI assistants learning the EvolvAI tool ecosystem.

---

## Tool Selection Framework

### Understanding Tool Capability Levels

Tools are categorized by capability level, which determines what operations they can handle:

### Level 1: Pattern-Based Text Operations

**Tools**: `batch_edit`, sed, awk, grep

**What they can do:**
- Match text patterns using regular expressions
- Replace matched text with new text (including capture groups)
- Process files as plain text without understanding code structure

**What they CANNOT do:**
- Understand code syntax or structure
- Identify semantic boundaries (like "between import groups")
- Analyze cross-file dependencies
- Perform intelligent refactoring

**Perfect for:**
- Renaming variables/functions across files: `getUserData` → `fetchUserData`
- Updating version strings: `v1.0.0` → `v2.0.0`
- Standardizing string formats: `"error:"` → `"ERROR:"`
- Batch comment modifications: `# TODO` → `# TODO(author)`
- Simple API migrations: `oldAPI()` → `newAPI()`

**NOT suitable for:**
- Import statement reorganization (use isort instead)
- Code formatting (use black/ruff instead)
- Adding missing docstrings (requires semantic understanding)
- Complex refactoring (use LSP-based tools instead)

### Level 2: Syntax-Aware Structural Operations

**Tools**: isort, black, ruff, prettier

**What they can do:**
- Parse code into Abstract Syntax Trees (AST)
- Understand code structure (imports, functions, classes)
- Perform syntax-aware transformations
- Maintain code validity during modifications

**Use these when:**
- Sorting/organizing import statements → isort
- Formatting code to standards → black
- Fixing linting issues → ruff --fix
- Adding/removing trailing commas → black

### Level 3: Semantic Refactoring Operations

**Tools**: LSP tools (find_symbol, rename_symbol), IDE refactoring

**What they can do:**
- Analyze code semantics and meaning
- Track references across files
- Understand type systems and interfaces
- Perform complex refactoring operations

**Use these when:**
- Extracting methods/functions (IDE refactoring)
- Renaming with cross-file reference updates (LSP rename)
- Changing function signatures (IDE refactoring)
- Interface/protocol modifications (requires semantic analysis)

---

## Decision Tree: Which Tool Should I Use?

```
Q: Is this a simple text pattern replacement?
   YES → batch_edit (Level 1) ✅
   NO  → Continue below

Q: Do I need to understand code structure?
   NO  → batch_edit (Level 1) ✅
   YES → Continue below

Q: Does it involve import statements or code formatting?
   YES → isort/black/ruff (Level 2) ✅
   NO  → Continue below

Q: Do I need to understand code meaning/semantics?
   NO  → black/isort/ruff (Level 2) ✅
   YES → LSP tools/IDE (Level 3) ✅

Q: Does it require analyzing code logic or cross-file dependencies?
   YES → LSP tools/IDE (Level 3) ✅
   NO  → batch_edit might work (Level 1) ⚠️
```

---

## Common Mistakes and Solutions

### ❌ MISTAKE: Using batch_edit to "add blank line between import groups"
**✅ SOLUTION**: Use isort - it understands import structure

**Why**: batch_edit sees text, not code structure. It cannot distinguish between stdlib imports, third-party imports, and local imports.

### ❌ MISTAKE: Using batch_edit to "update all function signatures"
**✅ SOLUTION**: Use LSP rename or IDE refactoring - they track references

**Why**: Changing a function signature requires updating all call sites, which requires semantic analysis.

### ❌ MISTAKE: Using batch_edit to "format code consistently"
**✅ SOLUTION**: Use black/ruff - they understand Python syntax

**Why**: Code formatting requires understanding syntax (indentation levels, expression boundaries, etc.)

### ❌ MISTAKE: Using batch_edit for "extracting common code to function"
**✅ SOLUTION**: Use IDE refactoring - requires semantic understanding

**Why**: Extraction requires analyzing variable scopes, dependencies, and side effects.

---

## When batch_edit Should Gracefully Decline

If you encounter these error messages, it means you're trying to use a Level 1 tool for a Level 2/3 task:

- **"Cannot locate semantic boundary"** → Need Level 2+ tool
- **"No matches found"** (but you know the code exists) → Pattern too complex
- **"Would affect X files"** (unexpectedly high) → Pattern too broad

In these cases, batch_edit will provide suggestions for better tools.

---

## Real-World Examples from EvolvAI Dogfooding

### ✅ SUCCESS: Organizing imports with isort (not batch_edit)

**Task**: Sort imports according to PEP 8

**Why batch_edit failed**: Needs to understand stdlib vs third-party

**Solution**: Used isort with proper configuration

**Result**: All imports correctly organized

**Lesson**: Import organization is Level 2 (syntax-aware), not Level 1

### ❌ ATTEMPTED: Standardizing test docstrings with batch_edit

**Task**: Convert triple-quoted Chinese descriptions to BDD format with Story/Scenario/DoD

**Why batch_edit failed**: Requires understanding test logic to extract Story/Scenario

**Why it seemed possible**: Looked like text transformation

**Lesson**: Adding semantic content (mapping code to requirements) requires Level 3 understanding

### ⚠️ DISCOVERED: Duplicate exception classes across modules

**Task**: Unify ConstraintViolationError imports

**Why batch_edit failed**: Exceptions have incompatible interfaces (different __init__ signatures)

**Required solution**: Manual refactoring (Level 3) with interface unification

**Lesson**: Structural issues need architectural decisions, not automated text replacement

---

## batch_edit Deep Dive

### What Makes batch_edit Powerful

1. **Cross-file operations**: Modify hundreds of files in one operation
2. **Regex capture groups**: Preserve and transform matched content
3. **Preview mode**: See changes before applying
4. **ExecutionPlan constraints**: Prevent runaway operations
5. **Atomic rollback**: File-level precision, no collateral damage

### Safety Features

- **File-level rollback**: Each file gets independent backup ID
- **Only modified files restored on failure**: User's other uncommitted work remains untouched
- **Atomic file writes**: Using temp file + replace pattern
- **No dependency on git**: Works in any environment
- **ExecutionPlan validation**: max_files, max_changes limits

### Design Principle (ADR-004)

**Tool-level rollback > System-level rollback**

Development tools must only rollback their own changes:
- ✅ batch_edit: Restores only files it modified
- ❌ git reset --hard: Destroys ALL uncommitted work (dangerous!)

---

## Summary: Know Your Tool's Boundaries

batch_edit is a powerful Level 1 tool that excels at pattern-based text transformations across multiple files. It is NOT a universal refactoring tool.

Understanding these boundaries helps you:

1. **Choose the right tool for the job**
2. **Avoid wasting time on impossible tasks**
3. **Achieve better results faster**
4. **Maintain code quality and safety**

**When in doubt, remember:**
- Simple text patterns → batch_edit ✅
- Everything else → Consider Level 2/3 tools

---

## Quick Reference

| Task | Tool | Level |
|------|------|-------|
| Rename variable across files | batch_edit | 1 |
| Update version strings | batch_edit | 1 |
| Organize imports | isort | 2 |
| Format code | black/ruff | 2 |
| Rename with LSP | rename_symbol | 3 |
| Extract function | IDE refactoring | 3 |
| Change signatures | LSP + IDE | 3 |

---

**Last Updated**: 2025-11-19
**Maintainer**: EvolvAI Team
