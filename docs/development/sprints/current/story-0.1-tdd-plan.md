# Story 0.1 TDD 开发计划：实现 ToolExecutionEngine

**Story ID**: STORY-0.1
**Epic**: Epic-001 (Phase 0: 工具调用链路简化)
**工期**: 5 人天
**风险**: 🟡 中等
**状态**: [PLANNING]

---

## 📋 Story 目标

实现统一的 ToolExecutionEngine，作为所有工具执行的唯一入口，提供完整的审计能力和 TPST 分析基础。

**交付物**：
1. `ExecutionPhase` 枚举 - 执行阶段定义
2. `ExecutionContext` 数据类 - 完整审计信息
3. `ToolExecutionEngine` 类 - 4 阶段执行流程
4. 审计日志接口 - 记录和查询执行历史
5. TPST 分析接口 - token 消耗分析

---

## 🧪 TDD 开发策略

### Red-Green-Refactor 循环计划

采用**垂直切片**策略，每个循环完成一个完整的功能切片：

```
Cycle 1: ExecutionPhase + ExecutionContext (基础数据结构)
  Red → Green → Refactor → Commit

Cycle 2: ToolExecutionEngine 核心框架 (4 阶段流程)
  Red → Green → Refactor → Commit

Cycle 3: Pre-validation 阶段实现
  Red → Green → Refactor → Commit

Cycle 4: Execution 阶段实现
  Red → Green → Refactor → Commit

Cycle 5: Post-execution 阶段实现
  Red → Green → Refactor → Commit

Cycle 6: 审计日志接口
  Red → Green → Refactor → Commit

Cycle 7: TPST 分析接口
  Red → Green → Refactor → Commit
```

---

## 📁 测试文件结构

```
test/evolvai/
├── __init__.py
└── core/
    ├── __init__.py
    ├── test_execution_context.py      # ExecutionContext 测试
    ├── test_execution_engine_core.py  # ToolExecutionEngine 核心测试
    ├── test_execution_phases.py       # 各阶段功能测试
    ├── test_audit_log.py              # 审计日志测试
    └── test_tpst_analysis.py          # TPST 分析测试

test/conftest.py                        # 添加新的 fixtures
```

---

## 🔴 Cycle 1: 基础数据结构

### Red 阶段 - 编写测试

**测试文件**: `test/evolvai/core/test_execution_context.py`

```python
"""Tests for ExecutionContext and ExecutionPhase."""
import time
from enum import Enum

import pytest

from evolvai.core.execution import ExecutionContext, ExecutionPhase


class TestExecutionPhase:
    """Test ExecutionPhase enum."""

    def test_execution_phase_values(self):
        """Test that all expected phases exist."""
        assert ExecutionPhase.PRE_VALIDATION
        assert ExecutionPhase.PRE_EXECUTION
        assert ExecutionPhase.EXECUTION
        assert ExecutionPhase.POST_EXECUTION

    def test_execution_phase_ordering(self):
        """Test that phases have correct ordering."""
        phases = list(ExecutionPhase)
        assert phases[0] == ExecutionPhase.PRE_VALIDATION
        assert phases[1] == ExecutionPhase.PRE_EXECUTION
        assert phases[2] == ExecutionPhase.EXECUTION
        assert phases[3] == ExecutionPhase.POST_EXECUTION


class TestExecutionContext:
    """Test ExecutionContext dataclass."""

    def test_execution_context_creation(self):
        """Test basic ExecutionContext creation."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={"arg1": "value1"},
        )

        assert ctx.tool_name == "test_tool"
        assert ctx.kwargs == {"arg1": "value1"}
        assert ctx.execution_plan is None
        assert ctx.phase == ExecutionPhase.PRE_VALIDATION
        assert ctx.result is None
        assert ctx.error is None

    def test_execution_context_with_plan(self):
        """Test ExecutionContext with execution plan."""
        plan = {"steps": ["step1", "step2"]}
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={},
            execution_plan=plan
        )

        assert ctx.execution_plan == plan

    def test_execution_context_timing(self):
        """Test ExecutionContext time tracking."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={},
        )

        ctx.start_time = time.time()
        time.sleep(0.01)  # Small delay
        ctx.end_time = time.time()

        duration = ctx.end_time - ctx.start_time
        assert duration > 0
        assert duration < 0.1  # Should be quick

    def test_execution_context_token_tracking(self):
        """Test ExecutionContext token metrics."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={},
        )

        ctx.estimated_tokens = 100
        ctx.actual_tokens = 95

        assert ctx.estimated_tokens == 100
        assert ctx.actual_tokens == 95

    def test_execution_context_constraint_tracking(self):
        """Test ExecutionContext constraint violation tracking."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={},
        )

        ctx.constraint_violations = ["violation1", "violation2"]
        ctx.should_batch = True

        assert len(ctx.constraint_violations) == 2
        assert ctx.should_batch is True

    def test_execution_context_to_audit_record(self):
        """Test conversion to audit record."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={"arg": "value"},
        )

        ctx.start_time = time.time()
        ctx.end_time = ctx.start_time + 0.5
        ctx.phase = ExecutionPhase.EXECUTION
        ctx.actual_tokens = 100
        ctx.constraint_violations = []
        ctx.should_batch = False

        record = ctx.to_audit_record()

        assert record["tool"] == "test_tool"
        assert record["phase"] == "execution"
        assert record["duration"] == 0.5
        assert record["tokens"] == 100
        assert record["success"] is True
        assert record["constraints"] == []
        assert record["batched"] is False

    def test_execution_context_to_audit_record_with_error(self):
        """Test audit record with error."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={},
        )

        ctx.start_time = time.time()
        ctx.end_time = time.time()
        ctx.error = ValueError("test error")

        record = ctx.to_audit_record()

        assert record["success"] is False
```

### Green 阶段 - 最小实现

**实现文件**: `src/evolvai/core/execution.py`

```python
"""Core execution engine components."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionPhase(Enum):
    """Execution phases for tool execution."""

    PRE_VALIDATION = "pre_validation"
    PRE_EXECUTION = "pre_execution"
    EXECUTION = "execution"
    POST_EXECUTION = "post_execution"


@dataclass
class ExecutionContext:
    """Complete execution context with audit trail."""

    # Tool information
    tool_name: str
    kwargs: dict[str, Any]
    execution_plan: Any | None = None

    # Timing
    start_time: float = 0.0
    end_time: float = 0.0
    phase: ExecutionPhase = ExecutionPhase.PRE_VALIDATION

    # Constraint tracking (Epic-001)
    constraint_violations: list[str] | None = None
    should_batch: bool = False

    # Execution results
    result: str | None = None
    error: Exception | None = None

    # Token tracking (TPST core)
    estimated_tokens: int = 0
    actual_tokens: int = 0

    def to_audit_record(self) -> dict[str, Any]:
        """Convert to audit record for TPST analysis."""
        return {
            "tool": self.tool_name,
            "phase": self.phase.value,
            "duration": self.end_time - self.start_time,
            "tokens": self.actual_tokens,
            "success": self.error is None,
            "constraints": self.constraint_violations or [],
            "batched": self.should_batch,
        }
```

### Refactor 阶段

- 检查类型注解完整性
- 添加 docstring
- 运行 `uv run poe format`
- 运行 `uv run poe type-check`

---

## 🔴 Cycle 2: ToolExecutionEngine 核心框架

### Red 阶段 - 编写测试

**测试文件**: `test/evolvai/core/test_execution_engine_core.py`

```python
"""Tests for ToolExecutionEngine core functionality."""
from unittest.mock import Mock, MagicMock

import pytest

from evolvai.core.execution import ExecutionContext, ExecutionPhase, ToolExecutionEngine
from serena.tools.tools_base import Tool


class MockTool(Tool):
    """Mock tool for testing."""

    def apply(self, test_arg: str) -> str:
        """Mock apply method.

        :param test_arg: Test argument
        :return: Test result
        """
        return f"result: {test_arg}"


class TestToolExecutionEngine:
    """Test ToolExecutionEngine core functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock SerenaAgent."""
        agent = Mock()
        agent.serena_config = Mock()
        agent.serena_config.tool_timeout = 60
        agent._active_project = Mock()
        agent.is_using_language_server = Mock(return_value=False)
        return agent

    @pytest.fixture
    def mock_tool(self, mock_agent):
        """Create mock tool."""
        return MockTool(mock_agent)

    @pytest.fixture
    def engine(self, mock_agent):
        """Create ToolExecutionEngine instance."""
        return ToolExecutionEngine(agent=mock_agent)

    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert engine._constraints_enabled is False
        assert engine._audit_log == []

    def test_engine_with_constraints_enabled(self, mock_agent):
        """Test engine with constraints enabled."""
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)
        assert engine._constraints_enabled is True

    def test_execute_basic_tool(self, engine, mock_tool):
        """Test basic tool execution."""
        result = engine.execute(mock_tool, test_arg="hello")

        assert result == "result: hello"
        assert len(engine._audit_log) == 1

    def test_execute_creates_context(self, engine, mock_tool):
        """Test that execution creates proper context."""
        result = engine.execute(mock_tool, test_arg="test")

        audit_record = engine._audit_log[0]
        assert audit_record["tool"] == "mock"
        assert audit_record["success"] is True

    def test_execute_tracks_phases(self, engine, mock_tool):
        """Test that execution goes through all phases."""
        # This will be tested via audit log
        result = engine.execute(mock_tool, test_arg="test")

        # Should have gone through all phases successfully
        assert result == "result: test"

    def test_execute_handles_exceptions(self, engine, mock_agent):
        """Test exception handling during execution."""
        class ErrorTool(Tool):
            def apply(self) -> str:
                """Apply method that raises."""
                raise ValueError("Test error")

        error_tool = ErrorTool(mock_agent)
        result = engine.execute(error_tool)

        # Should catch exception and return error message
        assert "Error" in result or "error" in result.lower()

        # Audit log should show failure
        audit_record = engine._audit_log[0]
        assert audit_record["success"] is False

    def test_execute_with_execution_plan(self, engine, mock_tool):
        """Test execution with ExecutionPlan."""
        plan = {"steps": ["analyze", "execute"]}
        result = engine.execute(mock_tool, execution_plan=plan, test_arg="test")

        assert result == "result: test"
        # Plan should be in audit record
        # (Will verify this in integration tests)
```

### Green 阶段 - 最小实现

继续在 `src/evolvai/core/execution.py` 中添加：

```python
import time
from typing import TYPE_CHECKING

from sensai.util import logging

if TYPE_CHECKING:
    from serena.agent import SerenaAgent
    from serena.tools.tools_base import Tool

log = logging.getLogger(__name__)


class ToolExecutionEngine:
    """Unified tool execution engine.

    Provides:
    1. 4-phase execution flow
    2. Complete audit trail
    3. Epic-001 constraint integration point
    4. TPST analysis support
    """

    def __init__(self, agent: "SerenaAgent", enable_constraints: bool = False):
        """Initialize execution engine.

        :param agent: SerenaAgent instance
        :param enable_constraints: Enable Epic-001 constraints
        """
        self._agent = agent
        self._constraints_enabled = enable_constraints
        self._audit_log: list[dict[str, Any]] = []

    def execute(self, tool: "Tool", **kwargs) -> str:
        """Execute tool with full 4-phase flow.

        :param tool: Tool to execute
        :param kwargs: Tool arguments
        :return: Tool execution result
        """
        # Extract execution_plan if present
        execution_plan = kwargs.pop("execution_plan", None)

        # Create execution context
        ctx = ExecutionContext(
            tool_name=tool.get_name(),
            kwargs=kwargs.copy(),
            execution_plan=execution_plan,
            start_time=time.time()
        )

        try:
            # Phase 1: Pre-validation
            ctx.phase = ExecutionPhase.PRE_VALIDATION
            self._pre_validation(tool, ctx)

            # Phase 2: Pre-execution (Epic-001)
            if self._constraints_enabled:
                ctx.phase = ExecutionPhase.PRE_EXECUTION
                self._pre_execution_with_constraints(tool, ctx)

            # Phase 3: Execution
            ctx.phase = ExecutionPhase.EXECUTION
            ctx.result = self._execute_tool(tool, ctx)

            # Phase 4: Post-execution
            ctx.phase = ExecutionPhase.POST_EXECUTION
            self._post_execution(tool, ctx)

            return ctx.result

        except Exception as e:
            ctx.error = e
            log.error(f"Error executing tool {tool.get_name()}: {e}", exc_info=e)
            return f"Error executing tool: {e}"

        finally:
            ctx.end_time = time.time()
            self._audit_log.append(ctx.to_audit_record())

    def _pre_validation(self, tool: "Tool", ctx: ExecutionContext) -> None:
        """Phase 1: Pre-validation checks."""
        # Will implement in Cycle 3
        pass

    def _pre_execution_with_constraints(self, tool: "Tool", ctx: ExecutionContext) -> None:
        """Phase 2: Pre-execution with constraints (Epic-001)."""
        # Placeholder for Epic-001 integration
        pass

    def _execute_tool(self, tool: "Tool", ctx: ExecutionContext) -> str:
        """Phase 3: Actual tool execution."""
        apply_fn = tool.get_apply_fn()
        result = apply_fn(**ctx.kwargs)
        return result

    def _post_execution(self, tool: "Tool", ctx: ExecutionContext) -> None:
        """Phase 4: Post-execution cleanup."""
        # Will implement in Cycle 5
        pass
```

---

## 🔴 Cycle 3-7: 后续循环

后续循环遵循相同的 Red-Green-Refactor 模式：

### Cycle 3: Pre-validation 阶段
- 测试：工具激活检查、项目检查、LSP 检查
- 实现：`_pre_validation()` 完整逻辑

### Cycle 4: Execution 阶段优化
- 测试：线程池集成、超时处理、token 估算
- 实现：异步执行、资源管理

### Cycle 5: Post-execution 阶段
- 测试：日志记录、统计上报、缓存保存
- 实现：`_post_execution()` 完整逻辑

### Cycle 6: 审计日志接口
- 测试：日志查询、过滤、导出
- 实现：`get_audit_log()`, `clear_audit_log()` 等方法

### Cycle 7: TPST 分析接口
- 测试：token 统计、性能分析、优化建议
- 实现：`analyze_tpst()`, `get_slow_tools()` 等方法

---

## 🧰 Mock 和 Fixture 策略

### 共享 Fixtures (在 conftest.py 中)

```python
@pytest.fixture
def mock_serena_agent():
    """Create mock SerenaAgent for testing."""
    agent = Mock()
    agent.serena_config = Mock()
    agent.serena_config.tool_timeout = 60
    agent.serena_config.default_max_tool_answer_chars = 10000
    agent._active_project = Mock()
    agent.is_using_language_server = Mock(return_value=False)
    agent.is_language_server_running = Mock(return_value=False)
    agent.tool_is_active = Mock(return_value=True)
    agent.get_active_tool_names = Mock(return_value=["mock_tool"])
    return agent

@pytest.fixture
def execution_engine(mock_serena_agent):
    """Create ToolExecutionEngine for testing."""
    from evolvai.core.execution import ToolExecutionEngine
    return ToolExecutionEngine(agent=mock_serena_agent)

@pytest.fixture
def execution_engine_with_constraints(mock_serena_agent):
    """Create ToolExecutionEngine with constraints enabled."""
    from evolvai.core.execution import ToolExecutionEngine
    return ToolExecutionEngine(agent=mock_serena_agent, enable_constraints=True)
```

---

## ✅ Definition of Done

### 代码质量

- [ ] 所有测试通过 (`uv run poe test test/evolvai/core`)
- [ ] 测试覆盖率 ≥ 90% (`pytest --cov=evolvai.core`)
- [ ] 类型检查通过 (`uv run poe type-check`)
- [ ] 代码格式化通过 (`uv run poe format`)
- [ ] 无 lint 警告 (`uv run poe lint`)

### 功能完整性

- [ ] ExecutionPhase 枚举定义完整
- [ ] ExecutionContext 数据类功能完整
- [ ] ToolExecutionEngine 4 阶段流程正常工作
- [ ] 审计日志正确记录所有执行
- [ ] TPST 分析接口可用

### 文档

- [ ] 所有类和方法有完整的 docstring
- [ ] 关键设计决策有注释说明
- [ ] README 或设计文档更新

### 集成

- [ ] 与现有 Tool 系统兼容
- [ ] Mock SerenaAgent 依赖清晰
- [ ] 为 Story 0.2 集成做好准备

---

## 📊 每日进度跟踪

### Day 1: Cycle 1-2 (基础框架)
- ✅ Cycle 1: ExecutionPhase + ExecutionContext
- ✅ Cycle 2: ToolExecutionEngine 核心

### Day 2: Cycle 3-4 (核心阶段)
- ⏳ Cycle 3: Pre-validation 实现
- ⏳ Cycle 4: Execution 阶段优化

### Day 3: Cycle 5 (完善阶段)
- ⏳ Cycle 5: Post-execution 实现

### Day 4: Cycle 6-7 (分析接口)
- ⏳ Cycle 6: 审计日志接口
- ⏳ Cycle 7: TPST 分析接口

### Day 5: 完善和测试
- ⏳ 集成测试
- ⏳ 性能测试
- ⏳ 文档完善
- ⏳ DoD 检查

---

## 🔗 相关文档

- [ADR-003: 工具调用链路简化](../../architecture/adrs/003-tool-execution-engine-simplification.md)
- [Phase 0 详细设计](../../architecture/phase-0-tool-execution-engine.md)
- [Epic-001 README](../../../product/epics/epic-001-behavior-constraints/README.md)

---

**最后更新**: 2025-10-27
**更新人**: EvolvAI Team
**下一步**: 开始 Day 1 - Cycle 1 的 Red 阶段
