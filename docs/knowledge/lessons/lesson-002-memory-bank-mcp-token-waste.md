# Lesson 002: Memory Bank MCP Token Waste Problem

**Date**: 2025-11-19
**Severity**: High
**Category**: Architecture, TPST Optimization
**Status**: Confirmed

---

## Problem Statement

Memory Bank MCP, designed to **reduce** session startup tokens, actually **increases** token consumption by 5x due to MCP client architecture.

### Expected vs Actual

| Metric | Expected | Actual | Waste |
|--------|----------|--------|-------|
| Memory content | ~12k | ~12k | ✅ OK |
| MCP overhead | 0k | **+46.8k** | ❌ **5x waste** |
| **Total** | ~12k | **~59k** | **390% overhead** |

---

## Root Cause Analysis

### What Memory Bank MCP Actually Is

```yaml
Memory Bank MCP:
  Core: File system wrapper (read/write/list)
  Rules: Naming conventions (camelCase)
  Intelligence: None (just file I/O)

Equivalent to:
  - Read ~/.claude/memory-bank/serena/*.md
  - Write ~/.claude/memory-bank/serena/*.md
  - Glob ~/.claude/memory-bank/serena/*.md
```

**Conclusion**: Memory Bank MCP is NOT a special technology, just file management + conventions.

### Why Token Waste Occurs

**Claude Code MCP Client Behavior**:
1. User calls ANY MCP tool
2. Claude Code connects to ALL configured MCP servers
3. ALL tool definitions loaded into context
4. Result: 46.8k tokens for Serena + EvolvAI MCP tools

**Verification**:
```
Before /memory-bank-load:
  MCP tools: 7.5k tokens (only Memory Bank)

After /memory-bank-load:
  MCP tools: 54.3k tokens
  ├─ Serena MCP: ~23k (32 tools × ~720 tokens)
  ├─ EvolvAI MCP: ~23k (31 tools × ~740 tokens)
  └─ Memory Bank: 5.5k (5 tools × ~1.1k tokens)
```

---

## Why This Violates Memory Bank's Purpose

Memory Bank MCP was created to **reduce TPST** by:
- Replacing 16-23k (CLAUDE.md + docs/)
- With ~4.5k (hierarchical loading)
- **Target**: 60-70% token reduction

**Actual Result**:
- CLAUDE.md + docs/: ~16-23k
- Memory Bank MCP: **~59k** (content + MCP overhead)
- **Result**: 157-268% **increase**, not reduction!

---

## Solution: Direct File Reading

### Why Direct Files Win

| Aspect | Memory Bank MCP | Direct Files | Winner |
|--------|----------------|--------------|--------|
| Token cost | 59k | 12k | ✅ Direct (79% cheaper) |
| Functionality | read/write/list | Read/Write/Glob | ✅ Equivalent |
| Reliability | MCP connection | File system | ✅ Direct |
| Complexity | MCP server | Native tools | ✅ Direct |
| Performance | MCP protocol | Direct I/O | ✅ Direct |

### Implementation

**Replace**:
```bash
# Old approach (59k tokens)
/memory-bank-load
  → Calls Memory Bank MCP tools
  → Triggers ALL MCP connections
  → Loads 46.8k tool definitions
```

**With**:
```bash
# New approach (12k tokens)
/context-load
  → Read ~/.claude/memory-bank/serena/projectbrief.md
  → Read ~/.claude/memory-bank/serena/activeContext.md
  → Read ~/.claude/memory-bank/serena/progress.md
  → Read ~/.claude/memory-bank/serena/.clinerules
  → Total: ~12k tokens (content only)
```

**Token Savings**: 59k → 12k = **79% reduction** ✅

---

## Key Insight: MCP is Not Always the Answer

### When to Use MCP

✅ **Use MCP when**:
- Tool provides actual computation (LSP, search, validation)
- Tool has server-side state
- Tool requires special protocols/authentication
- Tool offers functionality beyond file I/O

### When NOT to Use MCP

❌ **Avoid MCP when**:
- Simple file read/write operations
- No server-side processing needed
- Native tools are sufficient
- MCP overhead > actual value

### Memory Bank Case

```
Memory Bank MCP = File I/O + Conventions
                ≠ Special technology

Therefore: Use native file tools instead
```

---

## Action Items

### Immediate (Today)

- [x] Document this lesson
- [ ] Create `/context-load` slash command using direct files
- [ ] Update CLAUDE.md to remove Memory Bank MCP references
- [ ] Test token savings

### Short-term (This Week)

- [ ] Migrate all Memory Bank usage to direct files
- [ ] Remove Memory Bank MCP from project config
- [ ] Update documentation (productContext.md, systemPatterns.md)
- [ ] Measure actual TPST improvement

### Long-term (Future)

- [ ] Share this finding with Memory Bank MCP maintainers
- [ ] Consider: Does EvolvAI need internal memo as MCP? (Probably NO)
- [ ] Pattern: "File system + conventions" > "MCP wrapper"

---

## Related Decisions

- **ADR-005** (to be created): Use direct file I/O for session context
- **Deprecation**: Memory Bank MCP in EvolvAI project
- **Pattern**: Prefer native tools over MCP for simple operations

---

## Metrics

**Before (Memory Bank MCP)**:
- Session startup: 80k → 139k tokens (+59k)
- MCP tools overhead: 46.8k tokens
- Actual content: 12k tokens
- **Efficiency**: 20% (12k useful / 59k total)

**After (Direct Files)** (projected):
- Session startup: 80k → 92k tokens (+12k)
- MCP tools overhead: 0k tokens
- Actual content: 12k tokens
- **Efficiency**: 100% (12k useful / 12k total)

**Improvement**: 79% token reduction, 5x efficiency gain

---

## Quotes

> "Memory Bank MCP 的本质是文件管理系统,通过文件系统来存储和管理记忆库文件,使用规则来约定更新修改方式。那么我们应该采用方案 A: 直接读取文件,抛弃掉 memory bank。"
> — User insight, 2025-11-19

This perfectly captures the core insight: **Don't use MCP to wrap what file systems already do well.**

---

## References

- Context usage analysis: 80k → 139k tokens
- MCP tools breakdown: 7.5k → 54.3k tokens
- Memory Bank MCP repo: (upstream project)
- EvolvAI TPST optimization goals: 50-70% reduction
