# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🧠 专家人格激活（强制执行）

**每次任务开始时必须先激活专家人格：**

### 人格激活加载流程
1. **读取人格文件**: `CLAUDE-PERSONA.md`
2. **激活思维模式**: 🧠 → 🎯 → ⚡
3. **建立行为偏好**: 系统性分析 > 直接行动

### Claude无法真正自我觉察，需要用户监督：

**用户触发词（有效机制）**
- "专家模式" → 强制重读 CLAUDE-PERSONA.md
- "深入思考" → 激活系统性分析，不立即修复
- "不对，有问题" → 暂停操作，重新评估
- "等一下" → 立即停止当前操作，思考操作并提问

### 自动读取人格文件的前置条件
- 遇到任何编译/TypeScript错误
- 准备创建新文件
- 用户表达不满意时

**激活标志**: 🧠 → 🎯 → ⚡

---

## 📚 Memory Bank Integration (Development Tool)

**⚠️ IMPORTANT**: Memory Bank MCP is an **EXTERNAL development tool** for managing project context during development. It is **NOT** a feature to be integrated into EvolvAI.

**What Memory Bank MCP is**:
- ✅ External MCP service (like Git, Docker, or npm)
- ✅ Development-time tool for AI session context
- ✅ Replacement for reading lengthy CLAUDE.md and docs/ on every session
- ✅ Already optimized - no TPST tracking needed for Memory Bank itself

**What Memory Bank MCP is NOT**:
- ❌ NOT an EvolvAI product feature
- ❌ NOT to be integrated into our codebase
- ❌ NOT something we optimize (it's already optimized)
- ❌ NOT part of our TPST metrics (measure EvolvAI tools instead)

**🚀 AUTOMATIC TRIGGERS - You MUST follow these**:

### 1. New Window Startup / Context Reset (AUTOMATIC)
**TRIGGER**:
- When you (Claude) start in a new conversation window
- After automatic context compression/truncation by Claude
**ACTION**: Ask Memory Bank MCP to "validate memory bank"

**Standard Protocol**:
```
Simply say: "Please validate memory bank for the 'serena' project."

Memory Bank MCP will automatically:
1. Pre-Flight Validation (check required files exist)
2. Hierarchical file loading:
   - projectbrief.md (project overview)
   - productContext.md (problem/solution context)
   - systemPatterns.md (architecture patterns, ADRs)
   - techContext.md (tech stack, commands)
   - activeContext.md (current focus, recent decisions)
   - progress.md (development status, roadmap)
   - .clinerules (project-specific behavioral rules)
3. Apply .clinerules adjustments
4. Return full context
```

**Token Savings**: 16-23K → ~4.5K (70% reduction) ✅

**UI Convenience**: `/memory-bank-load` slash command triggers this flow

### 2. Git Commit (AUTOMATIC)
**TRIGGER**: After every `git commit` command succeeds
**ACTION**: Ask Memory Bank MCP to "update memory bank"

**Standard Protocol**:
```
After git commit succeeds, immediately:
Say: "Please update the memory bank for the 'serena' project."

Provide context:
- Completed: [what was committed]
- Git status: [branch, commit message]
```

### 3. Manual Updates (ON DEMAND)
**TRIGGER**:
- ✅ After completing a Story/Task
- ✅ Before ending work session (user says "done" / "finished")
- ✅ After making important architectural decisions
- ✅ When project focus changes
- ✅ When user explicitly requests

**Standard Protocol**:
```
Say: "Please update the memory bank for the 'serena' project."

Provide context:
- Completed: [Story X.X, task description]
- New decisions: [List key decisions]
- Git status: [branch, recent commits]

Memory Bank MCP will automatically:
1. Analyze current state (Git, todos, conversation)
2. Update progress.md (always)
3. Update activeContext.md (if focus changed)
4. Update .clinerules (if new patterns discovered)
5. Update other files as needed
6. Report what was updated
```

**UI Convenience**: `/memory-bank-update` slash command triggers this flow

### Standard Memory Bank Files (camelCase naming)

Memory Bank MCP uses these standard files:
- **projectbrief.md** - Project overview and goals (static)
- **productContext.md** - Problem/solution context (rare updates)
- **systemPatterns.md** - Architecture patterns, ADRs (rare updates)
- **techContext.md** - Tech stack, commands (rare updates)
- **activeContext.md** - Current focus, recent decisions (frequent updates)
- **progress.md** - Development status, roadmap (frequent updates)
- **.clinerules** - Project-specific behavioral rules (updates as patterns discovered)

### Memory Bank as Development Tool

**Important Distinctions**:
- Memory Bank MCP = Development tool (like Git)
- No TPST tracking of Memory Bank itself
- Future EvolvAI internal memo = Product feature (Epic-002/003) for tracking AI execution and user habits
- Current goal: Use Memory Bank MCP correctly for session context

### Update Triggers

**DO update** when:
- Completing Story/Task
- Making important decisions
- Changing project focus
- Before ending work session
- After significant git commits

**DO NOT update** during:
- Minor code changes
- Exploratory work
- Temporary experiments
- Every single git commit

**Detailed Information**: Use Memory Bank MCP to read specific files as needed instead of loading all content from CLAUDE.md.

---

## Project Overview

**EvolvAI** is an AI behavior engineering platform that optimizes AI assistant efficiency through systematic behavior constraints and thinking optimization.

**Project History**: EvolvAI evolved from a fork of the Serena project (LSP-based code analysis toolkit) into an independent platform focused on AI behavior optimization rather than just code tooling. While we continue to leverage Serena's mature LSP infrastructure (25+ language support), EvolvAI's core innovation is the three-Epic architecture for reducing TPST (Tokens Per Solved Task).

**Core Metric**: **TPST (Tokens Per Solved Task)** = Total consumed tokens / Successfully solved tasks
- Target: Reduce TPST by 50-70% compared to unconstrained AI behavior

### Three-Epic Architecture

**Epic-001: Behavior Constraints System**
- Prevent AI from wasting tokens on inefficient behaviors
- Core tools: `safe_search`, `safe_edit`, `safe_exec` with ExecutionPlan validation
- Innovation: Constitutional system with batching strategies

**Epic-002: Project Standards as MCP Service**
- Reduce documentation rework and location correction token waste
- Core capability: `.project_standards.yml` specification with validation
- Innovation: 90% rules + 10% small-model architecture for cost optimization

**Epic-003: Graph-of-Thought Engine (GoT)**
- Reduce thinking token ratio from 40% to ≤20%
- Core technology: Event sourcing + parallel branching + early stopping
- Innovation: Replace sequential thinking chains with event-sourced parallel exploration

**Technical Foundation**: EvolvAI builds on Serena's LSP infrastructure (SolidLanguageServer, multi-language support, symbol operations) while adding the GoT engine and behavior constraint systems as new layers.

For detailed project history and positioning, use Memory Bank MCP to read `productContext.md` and `systemPatterns.md`

## Development Commands

**Essential Commands (use these exact commands):**
- `uv run poe format` - Format code (RUFF + BLACK) - ONLY allowed formatting command
- `uv run poe type-check` - Run mypy type checking - ONLY allowed type checking command
- `uv run poe test` - Run tests with default markers (excludes java/rust by default)
- `uv run poe test -m "python or go"` - Run specific language tests
- `uv run poe lint` - Check code style without fixing

**Test Markers:**
Available pytest markers for selective testing:
- `python`, `go`, `java`, `rust`, `typescript`, `php`, `perl`, `csharp`, `elixir`, `terraform`, `clojure`, `swift`, `bash`, `ruby`, `ruby_solargraph`
- `snapshot` - for symbolic editing operation tests

**Project Management:**
- `uv run serena-mcp-server` - Start MCP server from project root
- `uv run index-project` - Index project for faster tool performance

**Always run format, type-check, and test before completing any task.**

## 🔧 MCP Servers Configuration

This project has three MCP servers configured, each serving different purposes:

### Current Usage Strategy

**Memory Bank MCP** (Development Tool)
- Session context management (like Git for context)
- Standard protocol: "follow your custom instructions" / "update memory bank"
- No custom agents or TPST tracking needed
- Slash commands: `/memory-bank-load`, `/memory-bank-update`

**Serena MCP** (Codebase Operations - Being Phased Out)
- Mature LSP-based tools (will be integrated into EvolvAI)
- Symbol-level code operations (`find_symbol`, `replace_symbol_body`, `rename_symbol`)
- Semantic search and navigation
- **Memory system** - ❌ DEPRECATED by upstream, replaced by Memory Bank MCP
- **Note**: Serena upstream has shifted focus, we're evolving to EvolvAI MCP

**EvolvAI MCP** (Behavior Constraints - Under Development)
- Behavior constraint tools (Epic-001, under development)
- Batch editing with validation (`batch_edit`)
- Safe command execution with timeout (`safe_exec`)
- Constrained search results (`safe_search`)

### Memory and Documentation Strategy

**✅ RECOMMENDED - Use Memory Bank MCP + docs/**:
- **Memory Bank MCP** - Session context, current work state (按需加载)
  - Use `/memory-bank-load` for project context
  - Use `/memory-bank-update` to update current state
- **docs/** directory - Permanent knowledge, version-controlled
  - Architecture decisions → `docs/development/architecture/adrs/`
  - Lessons learned → `docs/knowledge/lessons/`
  - Project specs → `docs/product/`

**❌ DEPRECATED - Serena memory tools**:
- `.serena/memories/` - **Deprecated by upstream Serena project**
- Old tools: `read_memory`, `write_memory`, `list_memories`, `edit_memory` - DO NOT USE
- Replacement: Memory Bank MCP (dev time) + docs/ (permanent) + future EvolvAI memo (runtime)
- Reason: Upstream Serena shifted focus, no longer maintains memory system

**Migration Status**:
- Memory Bank integration: ✅ Complete (Phase 1)
- Core content migrated to Memory Bank
- Permanent knowledge should be in `docs/` for version control

### EvolvAI Dogfooding Guidelines

When developing EvolvAI features, **prioritize EvolvAI MCP tools** to:
1. **Validate tool efficiency**: Use `batch_edit`, `safe_exec`, `safe_search` in real development
2. **Collect TPST data**: Track token usage and execution performance
3. **Test behavior constraints**: Verify ExecutionPlan validation works correctly
4. **Identify improvements**: Document pain points and optimization opportunities

**Dogfooding Tools**:
- `batch_edit` - Regex-based batch file editing with preview
- `safe_exec` - Command execution with timeout and output limits
- `safe_search` - Pattern search with result constraints
- `propose_edit` + `apply_edit` - Two-phase editing workflow

**Goal**: Use EvolvAI to improve EvolvAI itself, demonstrating TPST reduction in practice.

### Tool Selection Quick Reference

| Task Type | Recommended MCP | Tool |
|-----------|----------------|------|
| Load project context | Memory Bank | "follow your custom instructions" |
| Update project state | Memory Bank | "update memory bank" |
| Symbol-level editing | Serena | `replace_symbol_body`, `insert_after_symbol` |
| Batch text replacement | EvolvAI | `batch_edit` |
| Run tests safely | EvolvAI | `safe_exec` |
| Search with limits | EvolvAI | `safe_search` |
| Code refactoring | Serena | `rename_symbol`, LSP tools |
| Learn coding patterns | EvolvAI | `analyze_coding_standards` |

### Evolution Roadmap

**Current State**: Dual MCP operation
- Serena MCP for LSP operations (being phased out)
- EvolvAI MCP for constrained operations (actively developing)

**Target State**: EvolvAI MCP replaces Serena completely
- Stage 1 (NOW): Dual operation, Epic-001 development
- Stage 2 (Q2 2025): Feature migration, Epic-002/003
- Stage 3 (Q3 2025): Full replacement, Serena retired

See: `docs/development/architecture/evolution-roadmap.md` for details

## Architecture Overview

**EvolvAI Architecture Stack**:
```
┌─────────────────────────────────────────┐
│   AI Agent (Claude, GPT, etc.)         │
└─────────────────┬───────────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────────┐
│  EvolvAI Platform (New Layers)          │
│  ┌───────────────────────────────────┐  │
│  │ Epic-003: GoT Engine              │  │ ← Event sourcing, parallel thinking
│  │ - Event Store + Session Mgmt      │  │
│  │ - Parallel branching + Early stop │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │ Epic-001: Behavior Constraints    │  │ ← Safe operations with validation
│  │ - ExecutionPlan validation        │  │
│  │ - safe_search/edit/exec           │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │ Epic-002: Project Standards MCP   │  │ ← Document validation
│  │ - .project_standards.yml          │  │
│  │ - 90% rules + 10% small model     │  │
│  └───────────────┬───────────────────┘  │
└──────────────────┼───────────────────────┘
                   │
┌──────────────────▼───────────────────────┐
│  Serena Infrastructure (Foundation)      │ ← Inherited from upstream
│  - SolidLanguageServer (LSP wrapper)     │
│  - Multi-language support (25+)          │
│  - Symbol operations & navigation        │
│  - Project memory system                 │
└──────────────────────────────────────────┘
```

### Core Components

**EvolvAI Components** (New):

**1. ToolExecutionEngine** (`src/evolvai/core/execution.py` - **✅ Phase 0 Complete**)
- Unified 4-phase execution system (PRE_VALIDATION → PRE_EXECUTION → EXECUTION → POST_EXECUTION)
- Complete audit trail for TPST (Tokens Per Solved Task) analysis
- Token tracking and performance monitoring (slow tools detection)
- Foundation for Epic-001 behavior constraints integration
- **Status**: Fully implemented and integrated into SerenaAgent (Story 0.1)

**2. Graph-of-Thought Engine** (`src/evolvai/got/` - *planned*)
- Event sourcing system for thinking traces
- Parallel branch management and early stopping
- Session checkpoint/restore capabilities
- Target: Reduce thinking tokens from 40% to ≤20%

**3. Behavior Constraints System** (`src/evolvai/constraints/` - *Phase 1-3 planned*)
- **Phase 0 Complete**: ToolExecutionEngine with execution_plan support
- **Phase 1 (Next)**: ExecutionPlan schema validation
- **Phase 2**: safe_search/safe_edit/safe_exec wrappers
- **Phase 3**: Batching strategies and constitutional constraints
- Target: Prevent wasteful token-burning behaviors

**4. Project Standards MCP** (`src/evolvai/standards/` - *planned*)
- .project_standards.yml specification parser
- Rule-based validators (location, structure, naming)
- Small-model principle scorer (cost-optimized)
- Target: Reduce documentation rework by 40%

**Serena Infrastructure Components** (Inherited):

**5. SerenaAgent** (`src/serena/agent.py`)
- Central orchestrator managing projects, tools, and user interactions
- Coordinates language servers, memory persistence, and MCP server interface
- Manages tool registry and context/mode configurations
- **New**: Integrated ToolExecutionEngine for unified tool execution and TPST tracking

**6. SolidLanguageServer** (`src/solidlsp/ls.py`)
- Unified wrapper around Language Server Protocol (LSP) implementations
- Provides language-agnostic interface for symbol operations
- Handles caching, error recovery, and multiple language server lifecycle

**7. Tool System** (`src/serena/tools/`)
- **file_tools.py** - File system operations, search, regex replacements
- **symbol_tools.py** - Language-aware symbol finding, navigation, editing
- **memory_tools.py** - Project knowledge persistence and retrieval
- **config_tools.py** - Project activation, mode switching
- **workflow_tools.py** - Onboarding and meta-operations
- **jetbrains_tools.py** - JetBrains IDE integration

**8. Configuration System** (`src/serena/config/`)
- **Contexts** - Define tool sets for different environments (desktop-app, agent, ide-assistant, codex)
- **Modes** - Operational patterns (planning, editing, interactive, one-shot, onboarding)
- **Projects** - Per-project settings and language server configs

**9. Language Server Infrastructure** (`src/solidlsp/`)
- **SolidLanguageServer** - Unified wrapper around LSP implementations
- **language_servers/** - Individual language server adapters for 25+ languages
- **Caching system** - Reduces language server overhead with intelligent caching
- **Error recovery** - Automatic restart of crashed language servers

### Language Support Architecture

Each supported language (25+ languages including Python, TypeScript, Go, Rust, Java, C#, etc.) has:
1. **Language Server Implementation** in `src/solidlsp/language_servers/`
2. **Runtime Dependencies** - Automatic language server downloads when needed
3. **Test Repository** in `test/resources/repos/<language>/`
4. **Test Suite** in `test/solidlsp/<language>/`

### Memory & Knowledge System

**Current System** (Memory Bank MCP + docs/):
- **Memory Bank MCP** - Session context managed through standard MCP protocol
  - Commands: "follow your custom instructions" (load), "update memory bank" (update)
  - Files: projectbrief.md, productContext.md, systemPatterns.md, techContext.md, activeContext.md, progress.md, .clinerules
- **docs/ directory** - Permanent knowledge under version control
  - Architecture decisions, lessons learned, project specs
- **Indexing system** - Faster symbol discovery in large codebases (via SerenaAgent)

**Legacy System** (DEPRECATED):
- `.serena/memories/` - Old Serena memory system, being phased out
- Tools: `read_memory`, `write_memory`, `list_memories`, `edit_memory` - Do NOT use

### MCP Integration

- **MCP Server** (`src/serena/mcp.py`) - Exposes tools via Model Context Protocol
- **Dashboard** (`src/serena/dashboard.py`) - Web-based log viewer and control interface
- **CLI** (`src/serena/cli.py`) - Command-line interface for project management and configuration

## 🚨 Development Mandatory Checkpoints

**CRITICAL**: These checkpoints prevent common development failures. **MUST** be followed for every task.

### Checkpoint 1: Before Starting Any Task

**Before writing any code, you MUST be able to answer**:

1. **Which Cycle is this Task in?**
   - Answer format: "Story X.X, Cycle Y: [Cycle name]"
   - Source: Story TDD Plan document (e.g., `story-1.2-tdd-plan.md`)
   - Cannot answer → **STOP** → Re-read Story TDD Plan

2. **Which test scenarios will this Task implement?**
   - List all test function names: `test_xxx`, `test_yyy`
   - Source: Red phase of the Cycle in Story TDD Plan
   - Cannot answer → **STOP** → Re-read Cycle definition

3. **Which acceptance criteria (DoD) does each test verify?**
   - Map each test → DoD standard (F1/Q1/P1/etc.)
   - Source: Story document verification section
   - Cannot answer → **STOP** → You're about to over-engineer

**Example Valid Answers**:
```
Task: Integrate PlanValidator into ToolExecutionEngine
Cycle: Story 1.2, Cycle 1 - Basic Integration Test
Tests: test_validator_called_when_plan_provided, test_validator_not_called_when_no_plan
DoD: F1 (PlanValidator must be called), Q1 (100% backward compatible)
```

### Checkpoint 2: Before Writing Each Test

**Every new test MUST have this docstring format**:

```python
def test_something(self):
    """[Brief test description in BDD style]

    Story: story-1.2-tdd-plan.md Cycle 3
    Scenario: "User can execute tool with valid plan"
    DoD: F1 - Functional completeness

    Given [precondition]
    When [action]
    Then [expected outcome]
    """
```

**Rules**:
- ❌ **Cannot find corresponding Story Scenario** → This is over-engineering → **DO NOT WRITE**
- ❌ **No DoD mapping** → This is testing implementation details → **DO NOT WRITE**
- ✅ **Clear Story/Scenario/DoD mapping** → Proceed with test

**Lesson Source**: Feature 2.2 had 40% test failures due to tests not mapping to actual requirements.

### Checkpoint 3: Before Implementation

**Before implementing functions/classes, you MUST**:

1. **Check test interface definition**:
   - Function name exactly as called in test
   - Parameter order exactly as in test
   - Parameter names exactly as in test

2. **Implement according to test interface**:
   - Do NOT modify function signature "to make it better"
   - Do NOT reorder parameters "for consistency"
   - Do NOT rename parameters "for clarity"

3. **If test interface is unreasonable**:
   - Fix the test FIRST
   - Then implement according to corrected test
   - Document why interface was changed

**Why This Matters**:
- Feature 2.2: 40% failures were interface mismatches
- Example: Test expected `func(file_path, backup_path)` but implemented `func(backup_path, file_path)`

### Checkpoint 4: Before Git Commit

**Before `git commit`, verify**:

1. **Every new function/class**:
   - Which test covers it? (Must have answer)
   - If no test → Why? (Must justify or delete)

2. **Every new test**:
   - Which DoD standard does it verify? (Must have answer)
   - If no DoD → Is this over-engineering? (Probably yes)

3. **Fixture usage check**:
   - Did you test something just because fixture exists?
   - Rule: **Fixture existence ≠ requirement to test**
   - Only test based on Story TDD Plan, not available fixtures

**Report to user if**:
- Found functions with no tests (except justified cases)
- Found tests with no DoD mapping (potential over-engineering)
- Need user confirmation before proceeding

### Key Lessons from Past Failures

**Feature 2.2 Post-Mortem** (52/65 tests passed, 80% pass rate):

1. **Interface Mismatches (40% of failures)**:
   - Cause: Implementation didn't follow test interface
   - Prevention: Checkpoint 3

2. **Missing Methods (25% of failures)**:
   - Cause: Tests assumed methods that weren't needed
   - Prevention: Checkpoint 1 & 2 (map to DoD)

3. **Mock Data Issues (20% of failures)**:
   - Cause: Over-complex mock setup
   - Prevention: BDD thinking + KISS principle

4. **Parameter Mismatches (15% of failures)**:
   - Cause: Required parameters without defaults
   - Prevention: Checkpoint 3

**Reference**: `docs/testing/standards/tdd-refactoring-guidelines.md` for detailed analysis and KISS principles.

### Emergency Stop Conditions

**STOP IMMEDIATELY if**:

- ❌ You cannot map current work to a Story document
- ❌ You are writing tests without corresponding DoD standards
- ❌ You are implementing features not in the Story TDD Plan
- ❌ You are testing "because the fixture exists"

**Then**:
1. Ask user: "I cannot find Story/DoD mapping for [X]. Should I stop or proceed?"
2. Document user's decision
3. If user says proceed → Add to Story document first

## Development Patterns

### Adding New Languages
1. Create language server class in `src/solidlsp/language_servers/`
2. Add to Language enum in `src/solidlsp/ls_config.py` 
3. Update factory method in `src/solidlsp/ls.py`
4. Create test repository in `test/resources/repos/<language>/`
5. Write test suite in `test/solidlsp/<language>/`
6. Add pytest marker to `pyproject.toml`

### Adding New Tools
1. Inherit from `Tool` base class in `src/serena/tools/tools_base.py`
2. Implement required methods and parameter validation
3. Register in appropriate tool registry
4. Add to context/mode configurations

### Testing Strategy
- Language-specific tests use pytest markers
- Symbolic editing operations have snapshot tests
- Integration tests in `test_serena_agent.py`
- Test repositories provide realistic symbol structures

## Configuration Hierarchy

Configuration is loaded from (in order of precedence):
1. Command-line arguments to `serena-mcp-server`
2. Project-specific `.serena/project.yml`
3. User config `~/.serena/serena_config.yml`
4. Active modes and contexts

## Key Implementation Notes

- **ToolExecutionEngine** - Unified 4-phase execution system for all tools with complete audit trail
  - All tool calls go through `SerenaAgent.execution_engine.execute(tool, **kwargs)`
  - Automatic TPST tracking: token estimation, duration, success/failure metrics
  - Audit log API: `get_audit_log()`, `analyze_tpst()`, `get_slow_tools()`
  - Foundation for Epic-001 behavior constraints (execution_plan parameter ready)
- **Symbol-based editing** - Uses LSP for precise code manipulation with semantic understanding
- **Caching strategy** - Multi-level caching reduces language server overhead and improves performance
- **Error recovery** - Automatic language server restart on crashes with graceful degradation
- **Multi-language support** - 25+ languages with LSP integration, unified through SolidLSP wrapper
- **MCP protocol** - Exposes tools to AI agents via Model Context Protocol for broad client compatibility
- **Async operation** - Non-blocking language server interactions with thread pool execution
- **Project activation** - Per-project configuration and language server management
- **Tool registry** - Dynamic tool discovery and registration based on context/mode configuration

## Working with the Codebase

- **Python 3.11** with `uv` for dependency management and reproducible environments
- **Strict typing** with mypy, formatted with ruff + black (ruff runs first for speed)
- **Language servers** run as separate processes with LSP communication through SolidLSP
- **Memory system** enables persistent project knowledge through markdown files
- **Context/mode system** allows workflow customization for different client environments
- **Testing strategy** uses pytest markers for language-specific tests and snapshot testing
- **Configuration hierarchy**: CLI args → project config → user config → defaults

## Documentation Organization

**IMPORTANT**: This project follows a strict documentation organization structure. Before creating, moving, or organizing any documentation files, you MUST consult:

📚 **Documentation Structure Reference**: `docs/.structure.md`
📋 **Sprint Workflow Guide**: `docs/development/workflow-checklist.md`

### Quick Rules for AI Assistants

**Document Creation**:
- ✅ Use templates from `docs/templates/`
- ✅ Follow naming conventions (epic-{num}-{name}, story-{num}-{desc}.md)
- ✅ Place in correct category (product/, development/, testing/, knowledge/)
- ❌ Never create docs in project root
- ❌ Never use Chinese directory/file names

**Document Organization**:
```
docs/
├── product/         # Product definitions, epics, specs, roadmap
├── development/     # Sprints, tasks, architecture, standards
├── testing/         # Test plans, benchmarks, reports
├── knowledge/       # Research, lessons learned
├── deployment/      # Setup guides, integration docs
├── api/             # API documentation
├── templates/       # Document templates (USE THESE!)
└── archive/         # Archived documents by date
```

**Finding Documents**:
- Product definition → `docs/product/definition/`
- Current sprint → `docs/development/sprints/current/`
- Architecture decisions → `docs/development/architecture/adrs/`
- Document templates → `docs/templates/`

**Status Markers**:
Use status tags in document titles: `[DRAFT]`, `[REVIEW]`, `[APPROVED]`, `[ACTIVE]`, `[DEPRECATED]`, `[ARCHIVED]`

### Key Workflow Checkpoints

**When working on Sprint tasks**:

1. **Before creating documents**:
   - Check `.structure.md` for correct location and naming
   - Temporary ideas/notes → `sprints/current/_inbox/`
   - Work items → `sprints/current/{work-item}/`

2. **During Sprint execution**:
   - Follow `workflow-checklist.md` for TDD cycles
   - Low-friction recording: use `_inbox/` for quick notes
   - Use timestamp naming: `YYYYMMDD-brief-desc.md`

3. **Sprint completion** (MANDATORY):
   - Execute **_inbox/ cleanup** (30-45 min)
     * Extract ADRs, Lessons, Research from temporary notes
     * Move personal notes outside project repo
     * Delete obsolete notes
   - Execute **5S6A archival** (30 min)
     * Archive completed work items
     * Generate Sprint summary
   
   **Full process**: See `workflow-checklist.md` Phase 5

**AI Behavior**:
- ✅ Remind user to clean up `_inbox/` when Sprint ends
- ❌ Never auto-clean `_inbox/` (user decides note value)
- ✅ Suggest categorization (ADR/Lesson/Research)
- ❌ Never auto-move files from `_inbox/`

### Enforcement Rules

When working with documentation:
1. **Always check** `docs/.structure.md` first
2. **Always use** templates from `docs/templates/`
3. **Always follow** naming conventions
4. **Never create** random documentation files
5. **Always update** status markers
6. **Always link** related documents

**Violation Prevention**: If unsure about document placement, read `docs/.structure.md` completely before proceeding.

## Git Workflow

EvolvAI follows standard Git practices with GitFlow workflow:
- **Remotes**: origin (dreamlx/evolvai) + upstream (oraios/serena)
- **Branches**: main/develop/feature/hotfix/archive types
- **Daily workflow**: Feature branches → develop → main
- **Upstream sync**: Selective cherry-pick from Serena

📖 Full workflow: docs/development/git-workflow.md

## Development Rules (Learned from Experience)