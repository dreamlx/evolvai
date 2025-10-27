# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## Architecture Overview

Serena is a semantic code analysis and editing toolkit that provides IDE-like capabilities to AI agents through the Model Context Protocol (MCP):

### Core Components

**1. SerenaAgent (`src/serena/agent.py`)**
- Central orchestrator managing projects, tools, and user interactions
- Coordinates language servers, memory persistence, and MCP server interface
- Manages tool registry and context/mode configurations

**2. SolidLanguageServer (`src/solidlsp/ls.py`)**  
- Unified wrapper around Language Server Protocol (LSP) implementations
- Provides language-agnostic interface for symbol operations
- Handles caching, error recovery, and multiple language server lifecycle

**3. Tool System (`src/serena/tools/`)**
- **file_tools.py** - File system operations, search, regex replacements
- **symbol_tools.py** - Language-aware symbol finding, navigation, editing
- **memory_tools.py** - Project knowledge persistence and retrieval
- **config_tools.py** - Project activation, mode switching
- **workflow_tools.py** - Onboarding and meta-operations
- **jetbrains_tools.py** - JetBrains IDE integration

**4. Configuration System (`src/serena/config/`)**
- **Contexts** - Define tool sets for different environments (desktop-app, agent, ide-assistant, codex)
- **Modes** - Operational patterns (planning, editing, interactive, one-shot, onboarding)
- **Projects** - Per-project settings and language server configs

**5. Language Server Infrastructure (`src/solidlsp/`)**
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

- **Markdown-based storage** in `.serena/memories/` directories
- **Project-specific knowledge** persistence across sessions
- **Contextual retrieval** based on relevance
- **Onboarding support** for new projects
- **Indexing system** for faster symbol discovery in large codebases

### MCP Integration

- **MCP Server** (`src/serena/mcp.py`) - Exposes tools via Model Context Protocol
- **Dashboard** (`src/serena/dashboard.py`) - Web-based log viewer and control interface
- **CLI** (`src/serena/cli.py`) - Command-line interface for project management and configuration

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

### Enforcement Rules

When working with documentation:
1. **Always check** `docs/.structure.md` first
2. **Always use** templates from `docs/templates/`
3. **Always follow** naming conventions
4. **Never create** random documentation files
5. **Always update** status markers
6. **Always link** related documents

**Violation Prevention**: If unsure about document placement, read `docs/.structure.md` completely before proceeding.