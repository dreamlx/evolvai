# AI Development Rules for EvolvAI

This file contains detailed case studies, lessons learned, and best practices for AI assistants working on the EvolvAI project. These rules are derived from actual development experience and should be consulted before starting any significant task.

**Last Updated**: 2025-11-02
**Version**: 1.0

---

## 🎯 Meta Rule: When to Check These Rules

**Always check before**:
- ✅ Writing TDD plans or test strategies
- ✅ Creating architecture designs or epic breakdowns
- ✅ Implementing >50 lines of code
- ✅ Starting a new Phase or Story

**Check if**:
- ⚠️ Test pass rate <80%
- ⚠️ Refactoring needed in TDD Green Phase
- ⚠️ Test/Code ratio >1:10
- ⚠️ Feeling uncertain about approach

---

## 📚 Rule 1: KISS Principle (Phase 2 Feature 2.2 Lesson)

### Case Study: Feature 2.2 Safe Edit Wrapper

**Problem**: Initial implementation with 13 tests had only 8% pass rate

**Root Causes**:
1. **Over-mocking**: Complex mock setups that tested implementation details
2. **Framework Testing**: Testing Pydantic serialization (framework's responsibility)
3. **YAGNI Violations**: Implementing features not needed yet
4. **Over-testing Edge Cases**: Testing concurrency, permissions before core functionality

**Solution**: KISS Refactoring
- Reduced 13 tests → 6 tests
- Focused on behavior verification (what, not how)
- Trusted frameworks (Pydantic, pathlib, etc.)
- Test/Code ratio improved to 1:21

**Outcome**: 100% pass rate, maintainable tests, faster implementation

### Application Checklist

When creating TDD plans or tests, ask:

**❌ Red Flags (Avoid)**:
- [ ] Am I testing the framework? (Pydantic, FastAPI, pathlib, etc.)
- [ ] Am I mocking more than 3 levels deep?
- [ ] Am I implementing features not in the current Story?
- [ ] Am I testing edge cases before core functionality works?
- [ ] Is my test/code ratio >1:10?
- [ ] Do I need >10 words to explain what this test verifies?

**✅ Green Lights (Do This)**:
- [ ] Testing behavior, not implementation details
- [ ] Each test verifies one clear outcome
- [ ] Using real objects when possible (avoid unnecessary mocks)
- [ ] Core functionality tests first, edge cases later
- [ ] Test name clearly describes expected behavior

### Quick Self-Check

If you answer "yes" to any of these, simplify your approach:
1. "This test will break if I change implementation details" → ❌ Implementation testing
2. "I need to explain how the code works to understand this test" → ❌ Too coupled
3. "I'm testing that Pydantic validates correctly" → ❌ Framework testing

---

## 📐 Rule 2: Test/Code Ratio Guidelines

### Best Practice Examples

**Feature 2.1: Safe Search Wrapper** (Best Practice)
- Test/Code Ratio: **1:21**
- Tests: 6
- Code: ~126 statements
- Pass Rate: 100%
- Outcome: Gold standard for EvolvAI

**Feature 2.2: Safe Edit Wrapper** (After KISS)
- Test/Code Ratio: **1:21**
- Tests: 6
- Code: ~126 statements
- Pass Rate: 100%
- Outcome: Recovered after refactoring

**Phase 2.5 Story 2.5.1: TPST Framework** (Current)
- Test/Code Ratio: **1:4.2**
- Tests: 10
- Code: 42 statements
- Pass Rate: 100%
- Note: Data models have higher test/code ratios (acceptable)

### Target Ranges by Component Type

| Component Type | Target Ratio | Reasoning |
|----------------|--------------|-----------|
| Business Logic | 1:15 to 1:25 | Feature 2.1/2.2 standard |
| Data Models | 1:3 to 1:6 | Validation-heavy, less logic |
| API Wrappers | 1:20 to 1:30 | Thin wrappers, trust frameworks |
| Complex Algorithms | 1:10 to 1:15 | Need more edge case coverage |

### Red Flags

- **Ratio >1:10 for business logic**: Over-testing or under-implementing
- **Ratio <1:30**: Under-testing or god object anti-pattern

---

## 🔴 Rule 3: TDD Red-Green-Refactor Methodology

### The Three Phases (Strict)

**🔴 Red Phase**:
1. Write the test for ONE behavior
2. Run the test
3. **Verify it fails with the expected error** (ModuleNotFoundError, AttributeError, etc.)
4. If it passes → Something is wrong, test is not actually testing anything

**🟢 Green Phase**:
1. Write **minimal** code to make the test pass
2. Run all tests
3. **All tests pass** (if KISS applied correctly, first try)
4. If tests fail → Implementation bug, fix it
5. If you need complex refactoring → Planning failed, KISS not applied

**🔵 Refactor Phase**:
1. Improve code quality WITHOUT changing behavior
2. Run all tests after each refactor
3. **If KISS applied correctly, this phase should be rare or unnecessary**

### Phase 2.5 Story 2.5.1 Example

**Cycle 1: TPSTRecord**
- 🔴 Red: 4 tests created → ModuleNotFoundError ✅
- 🟢 Green: 15-statement Pydantic model → 4/4 pass ✅
- 🔵 Refactor: Not needed (KISS made it right first time) ✅

**Cycle 2: TPSTTracker.record()**
- 🔴 Red: 3 tests created → AttributeError ✅
- 🟢 Green: 13-statement method → 3/3 pass ✅
- 🔵 Refactor: Not needed ✅

**Cycle 3: TPSTTracker.load()**
- 🔴 Red: 3 tests created → AttributeError ✅
- 🟢 Green: 24-statement method → 3/3 pass ✅
- 🔵 Refactor: Only docstring formatting (trivial) ✅

**Key Insight**: KISS principle made all 3 Cycles pass first try, no real refactoring needed.

---

## 🌳 Rule 4: GitFlow Workflow

### Branch Strategy

```
main (production)
└── develop (integration)
    └── feature/{epic}-{story}-{description}
        └── Individual commits per Cycle/Story
```

### Branch Naming Convention

**Pattern**: `feature/{epic-num}-{story-num}-{short-desc}`

**Examples**:
- ✅ `feature/phase-2.5-tpst-framework`
- ✅ `feature/epic1-story1.3-runtime-constraints`
- ❌ `feature/tpst` (too vague)
- ❌ `tpst-implementation` (missing prefix)

### Commit Message Convention

**Format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, test, chore

**Example**:
```
feat(phase-2.5): Implement TPST data collection framework (Cycle 1+2)

## Phase 2.5: TPST数据收集框架
实施Story 2.5.1的前2个Cycle，建立TPST(Tokens Per Solved Task)数据收集基础设施。

### Cycle 1: TPSTRecord数据模型 ✅
- Add TPSTRecord Pydantic model (15 statements, 100% coverage)
...

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Commit Frequency

**Rule**: Commit after each completed unit of work

**Examples**:
- ✅ After each TDD Cycle completion (Red-Green-Refactor done)
- ✅ After each Story completion
- ✅ Before risky operations (major refactoring)
- ❌ At end of day (too late, risky)
- ❌ After entire Phase (too large, hard to review)

---

## 📊 Rule 5: Quality Gates

### Pre-Completion Checklist

Before marking any task as "complete":

**Testing**:
- [ ] All tests passing (100% pass rate)
- [ ] Coverage ≥90% for core modules (100% preferred)
- [ ] No skipped tests (`@pytest.mark.skip` removed)
- [ ] No commented-out tests

**Code Quality**:
- [ ] `uv run poe type-check` → 0 errors
- [ ] `uv run poe format` → No changes (already formatted)
- [ ] No TODO comments in production code
- [ ] No debug print statements

**Git**:
- [ ] Working on feature branch (not main/develop)
- [ ] All changes committed
- [ ] Commit message follows conventional commits
- [ ] No untracked files (except temp/logs)

**Documentation**:
- [ ] Docstrings for all public functions/classes
- [ ] TDD plan updated if approach changed
- [ ] Lessons learned documented (if applicable)

---

## 🧠 Rule 6: Memory System Usage

### Before Starting Tasks

**Check these memories**:
1. `.serena/memories/project-overview.md` - Project context
2. `.serena/memories/phase-{N}-lessons.md` - Phase-specific lessons
3. `.serena/memories/lessons-learned.md` - All cumulative lessons

**Tools to use**:
- `mcp__serena__list_memories` - List available memories
- `mcp__serena__read_memory` - Read specific memory file

### After Completing Tasks

**Document lessons in**:
1. `.claude/AI_RULES.md` - If it's a reusable pattern/rule
2. `.serena/memories/lessons-learned.md` - If it's project-specific insight
3. Completion reports (`docs/development/sprints/completed/`) - Phase summaries

**Format**:
```markdown
## Lesson: [Title]

**Context**: [What was the situation?]
**Problem**: [What went wrong?]
**Analysis**: [Why did it happen?]
**Solution**: [What fixed it?]
**Outcome**: [What was the result?]
**Rule Created**: [What rule should prevent this in the future?]
```

---

## 🎯 Rule 7: Planning Validation

### TDD Plan Validation Checklist

Before implementing a TDD plan, validate against:

**Scope Check**:
- [ ] Are all Cycles necessary? (YAGNI test)
- [ ] Can any Cycles be merged? (KISS simplification)
- [ ] Are we testing frameworks? (Trust frameworks)

**Ratio Check**:
- [ ] Estimated test/code ratio in target range? (1:15 to 1:25 for logic)
- [ ] Total test count reasonable? (<15 tests for typical Story)

**Complexity Check**:
- [ ] Any mocks >3 levels deep? (Simplify)
- [ ] Any tests requiring >10 words to explain? (Clarify or split)

**KISS Review**:
- [ ] Review against Phase 2.2 lesson checklist
- [ ] Identify potential over-engineering
- [ ] Simplify before implementation

---

## 📈 Rule 8: Continuous Improvement

### After Each Phase

**Reflection Questions**:
1. What worked well? (Keep doing)
2. What didn't work? (Stop doing)
3. What should we try? (Start doing)
4. What rules should we add? (Document)

**Update These Files**:
- `.claude/AI_RULES.md` - New rules or case studies
- `.serena/memories/lessons-learned.md` - Project-specific insights
- Completion reports - Phase summaries with metrics

### Metrics to Track

**Quality Metrics**:
- Test pass rate (target: 100%)
- Code coverage (target: ≥90%)
- Test/code ratio (target: 1:15 to 1:25)
- Type check errors (target: 0)

**Efficiency Metrics**:
- Cycles needed vs. planned
- Refactoring frequency (target: rare with KISS)
- First-time-right rate (target: ≥80%)

---

## 📋 Rule 9: Project Management Workflow

### Three-Layer Architecture

EvolvAI uses a systematic approach to capture and process ideas:

```
Layer 1: BACKLOG.md → Quick capture
Layer 2: Git Issues → Formal tracking
Layer 3: docs/planning/ → Epic/Sprint planning
```

**Full Documentation**: `docs/development/workflows/project-management-workflow.md`

### When to Use Each Layer

**BACKLOG.md** (Layer 1):
- Quick idea capture
- Bug discoveries
- Research topics
- Documentation improvements
- No formal structure needed yet

**Git Issues** (Layer 2):
- Formal requirements (>2 hours work)
- Need team collaboration
- Require commit/PR tracking
- Have clear acceptance criteria

**docs/planning/** (Layer 3):
- Epic definitions
- Sprint planning
- Roadmap management
- Completion reports

### AI Assistant Triggers

**Trigger 1: Idea Mention**
When user mentions improvement/idea/bug without formal tracking:
```
💡 Suggestion: Should this go in BACKLOG.md?

Options:
1. Add to BACKLOG.md now
2. Create Git Issue (formal tracking)
3. Note for later
```

**Trigger 2: Weekly Review (Friday)**
If Friday + no recent BACKLOG.md review:
```
📅 Weekly Reminder: BACKLOG.md Review Time!

Tasks:
1. Review High Priority ideas
2. Convert ready items to Git Issues
3. Archive processed items

Last review: [date]
Pending items: [count]
```

**Trigger 3: Bi-weekly Sprint (Every 2 weeks)**
If sprint cycle detected:
```
🎯 Sprint Planning Reminder!

Tasks:
1. Review current Sprint progress
2. Write completion report (if done)
3. Select next Sprint stories
4. Update sprint-goals.md

Current Sprint: [date]
Completion: [date]
```

**Trigger 4: Extended Discussion**
If same BACKLOG item discussed >5 messages:
```
📋 Suggestion: This idea has evolved significantly!

Consider creating Git Issue for:
- Better tracking and collaboration
- Commit/PR linking
- Historical reference

Shall I create the issue?
```

### Integration Points

**BACKLOG.md Location**: Project root
**Review Frequency**: Weekly (Friday)
**Archive Location**: `docs/planning/backlog-archive/YYYY-MM.md`
**Sprint Cadence**: Bi-weekly

### Best Practices

**✅ Do This**:
- Capture all ideas immediately in BACKLOG.md
- Weekly review and processing
- Use templates for consistency
- Link BACKLOG → Issue → Epic
- Archive completed items

**❌ Avoid This**:
- Creating Issues for every small idea
- Letting BACKLOG grow unbounded
- Skipping weekly reviews
- Mixing informal/formal tracking

---

## 🔗 Related Resources

**Project Documentation**:
- `CLAUDE.md` - Project overview and quick rules
- `.serena/memories/` - Project-specific knowledge
- `docs/development/sprints/completed/` - Phase completion reports

**Development Guides**:
- `docs/development/tdd-methodology.md` - TDD best practices
- `docs/development/architecture/adrs/` - Architecture decisions
- `docs/.structure.md` - Documentation organization

---

## 📝 Version History

**v1.1 (2025-11-02)**:
- Added Rule 9: Project Management Workflow
  - Three-layer architecture (BACKLOG → Issues → Planning)
  - AI assistant triggers and reminders
  - Integration with BACKLOG.md and weekly review cadence

**v1.0 (2025-11-02)**:
- Initial creation with Phase 2 lessons
- Rule 1: KISS Principle (Feature 2.2 case study)
- Rule 2: Test/Code Ratio guidelines
- Rule 3: TDD methodology
- Rule 4: GitFlow workflow
- Rule 5: Quality gates
- Rule 6: Memory system usage
- Rule 7: Planning validation
- Rule 8: Continuous improvement
