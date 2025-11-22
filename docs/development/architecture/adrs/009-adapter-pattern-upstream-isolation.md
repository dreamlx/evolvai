# ADR-009: Adapter Pattern for Upstream Serena Isolation

## Status

**Accepted** - 2025-11-22

## Context

EvolvAI is built on top of Serena, which is rapidly evolving (231+ commits in a short period). This creates several challenges:

1. **Interface Drift**: Serena's internal APIs change frequently, breaking EvolvAI code
2. **Tight Coupling**: `ToolExecutionEngine` directly accessed `SerenaAgent` internals like `_active_project`, `serena_config.project_names`
3. **Maintenance Burden**: Each upstream change requires scattered fixes across EvolvAI codebase
4. **Testing Complexity**: Tests need to mock Serena's internal structure

### Specific Problem

`evolvai/core/execution.py` expected `SerenaAgent` to have:
- `is_language_server_running()` - did not exist
- `language_server` attribute - architecture uses `LanguageServerManager` instead
- `reset_language_server()` - did not exist

This caused MCP tools to fail with `AttributeError`.

## Decision

Implement the **Adapter Pattern** to isolate EvolvAI from Serena's internal implementation.

### Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  SerenaAgent    │ ──▶ │ SerenaAgentAdapter   │ ──▶ │ ToolExecutionEngine │
│  (Upstream)     │     │ (Isolation Layer)    │     │ (EvolvAI Core)      │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │   AgentProtocol      │
                        │   (Interface)        │
                        └──────────────────────┘
```

### Components

1. **`AgentProtocol`** (`evolvai/core/interfaces/agent_protocol.py`)
   - Defines the interface EvolvAI expects from an Agent
   - Uses Python's `typing.Protocol` for structural typing

2. **`SerenaAgentAdapter`** (`evolvai/adapters/serena_adapter.py`)
   - Adapts `SerenaAgent` to `AgentProtocol`
   - Encapsulates all Serena-specific implementation details
   - Single point of change when upstream architecture changes

3. **`ToolExecutionEngine`** (`evolvai/core/execution.py`)
   - Depends on `AgentProtocol`, not `SerenaAgent`
   - Automatically wraps raw `SerenaAgent` with Adapter

### Protocol Definition

```python
class AgentProtocol(Protocol):
    # LSP Management
    def is_using_language_server(self) -> bool: ...
    def is_language_server_running(self) -> bool: ...
    def reset_language_server(self) -> None: ...
    def save_lsp_caches(self) -> None: ...

    # Project Information
    def has_active_project(self) -> bool: ...
    def get_project_names(self) -> list[str]: ...
    def get_project_root(self) -> str | None: ...

    # Tool Management
    def get_active_tool_names(self) -> list[str]: ...
    def record_tool_usage(self, kwargs: dict, result: str, tool: Any) -> None: ...
    def tool_is_active(self, tool_name: str) -> bool: ...
```

## Consequences

### Positive

1. **Isolation**: EvolvAI core is protected from upstream Serena changes
2. **Single Point of Change**: Only `SerenaAgentAdapter` needs updating when Serena changes
3. **Clear Contract**: `AgentProtocol` documents exactly what EvolvAI needs
4. **Testability**: Tests can mock `AgentProtocol` without knowing Serena internals
5. **KISS Compliance**: Minimal adapter, no over-engineering

### Negative

1. **Indirection**: One more layer between EvolvAI and Serena
2. **Maintenance**: Adapter must be updated when upstream changes
3. **Performance**: Slight overhead from adapter method calls (negligible)

### Neutral

1. **Learning Curve**: Developers need to understand the adapter pattern
2. **Documentation**: Need to keep protocol and adapter documentation in sync

## Implementation

### Phase 1: Core Adapter (Completed)
- Created `AgentProtocol` interface
- Created `SerenaAgentAdapter`
- Modified `ToolExecutionEngine` to use adapter
- Updated all tests

### Phase 2: Future Enhancements (Optional)
- Add type stubs for better IDE support
- Create adapter for other Serena components if needed
- Automated compatibility testing with upstream releases

## Upstream Sync Strategy

### When to Update Adapter

1. **Breaking Changes**: When Serena changes method signatures or removes APIs
2. **New Features**: When EvolvAI wants to use new Serena capabilities
3. **Bug Fixes**: When Serena fixes bugs that affect adapter behavior

### Sync Workflow

```bash
# 1. Check upstream changes
git fetch upstream
git log upstream/main --oneline -20

# 2. Update adapter if needed
# Edit src/evolvai/adapters/serena_adapter.py

# 3. Run tests
uv run poe test test/evolvai/core -xvs

# 4. Commit adapter updates
git commit -m "chore: Update adapter for upstream Serena changes"
```

### Monitoring

- Watch Serena releases for breaking changes
- Set up CI to test against upstream main periodically
- Document known incompatibilities

## Alternatives Considered

### 1. Direct Patching (Rejected)
- Add missing methods directly to `SerenaAgent`
- **Problem**: Creates merge conflicts, hard to maintain

### 2. Fork and Modify (Rejected)
- Maintain a fork with EvolvAI-specific changes
- **Problem**: Difficult to sync 231+ commits, divergence risk

### 3. Monkey Patching (Rejected)
- Dynamically add methods at runtime
- **Problem**: Hidden dependencies, debugging nightmares

### 4. Multiple Adapters per Domain (Rejected)
- `LSPAdapter`, `ProjectAdapter`, `ToolAdapter`
- **Problem**: Over-engineering, violates YAGNI

## References

- [Adapter Pattern (GoF)](https://refactoring.guru/design-patterns/adapter)
- [Python Protocol (PEP 544)](https://peps.python.org/pep-0544/)
- Commit: `e2099f7` - Initial adapter implementation

## Review

- **Author**: Claude (AI Assistant)
- **Reviewer**: [Pending]
- **Date**: 2025-11-22
