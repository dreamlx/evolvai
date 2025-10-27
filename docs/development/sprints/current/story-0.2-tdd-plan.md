# Story 0.2 TDD 开发计划：集成到 SerenaAgent

**Story ID**: STORY-0.2
**Epic**: Epic-001 (Phase 0: 工具调用链路简化)
**工期**: 3 人天
**风险**: 🔴 高
**依赖**: Story 0.1 (ToolExecutionEngine 实现完成)
**状态**: [PLANNING]

---

## 📋 Story 目标

将 ToolExecutionEngine 集成到 SerenaAgent，简化 Tool.apply_ex()，实现 7 层到 4 层的调用链路简化。

**交付物**：
1. SerenaAgent 创建和管理 ToolExecutionEngine 实例
2. Tool.apply_ex() 委托执行到 ToolExecutionEngine
3. Feature flag 配置（`enable_constraints`）
4. MCP 适配器更新（SerenaMCPFactory）
5. 向后兼容性验证

---

## ⚠️ 风险评估

### 高风险因素

1. **破坏性变更**：修改核心调用链路可能影响所有工具
   - **缓解**：Feature flag + 渐进式迁移

2. **SerenaAgent 生命周期管理**：ToolExecutionEngine 的初始化和清理
   - **缓解**：在 SerenaAgent.__init__() 中统一管理

3. **线程池迁移**：从 SerenaAgent.execute_task() 迁移到 ToolExecutionEngine
   - **缓解**：保留原有线程池配置，平滑迁移

4. **向后兼容性**：现有工具调用不能被破坏
   - **缓解**：充分的集成测试

---

## 🧪 TDD 开发策略

### Red-Green-Refactor 循环计划

采用**逐步集成**策略，每个循环完成一个集成点：

```
Cycle 1: SerenaAgent 初始化 ToolExecutionEngine
  Red → Green → Refactor → Commit

Cycle 2: Tool.apply_ex() 委托到 ToolExecutionEngine
  Red → Green → Refactor → Commit

Cycle 3: Feature flag 配置和控制
  Red → Green → Refactor → Commit

Cycle 4: MCP 适配器集成
  Red → Green → Refactor → Commit

Cycle 5: 向后兼容性验证
  Red → Green → Refactor → Commit
```

---

## 📁 测试文件结构

```
test/evolvai/
└── integration/
    ├── __init__.py
    ├── test_serena_agent_integration.py   # SerenaAgent 集成测试
    ├── test_tool_apply_ex_migration.py    # Tool.apply_ex() 迁移测试
    ├── test_feature_flag.py               # Feature flag 测试
    └── test_mcp_integration.py            # MCP 适配器集成测试

test/serena/
└── test_serena_agent.py                   # 更新现有测试
```

---

## 🔴 Cycle 1: SerenaAgent 初始化 ToolExecutionEngine

### Red 阶段 - 编写测试

**测试文件**: `test/evolvai/integration/test_serena_agent_integration.py`

```python
"""Tests for SerenaAgent integration with ToolExecutionEngine."""
from unittest.mock import Mock, patch

import pytest

from serena.agent import SerenaAgent
from serena.config import SerenaConfig
from evolvai.core.execution import ToolExecutionEngine


class TestSerenaAgentToolExecutionEngineIntegration:
    """Test SerenaAgent creates and manages ToolExecutionEngine."""

    @pytest.fixture
    def minimal_config(self, tmp_path):
        """Create minimal SerenaConfig for testing."""
        config = Mock(spec=SerenaConfig)
        config.serena_home = tmp_path
        config.project_names = []
        config.tool_timeout = 60
        config.enable_execution_engine = True  # NEW: Feature flag
        config.enable_constraints = False      # NEW: Constraints disabled by default
        return config

    def test_agent_creates_execution_engine_on_init(self, minimal_config):
        """Test that SerenaAgent creates ToolExecutionEngine during initialization."""
        agent = SerenaAgent(serena_config=minimal_config)

        assert hasattr(agent, "_execution_engine")
        assert isinstance(agent._execution_engine, ToolExecutionEngine)

    def test_execution_engine_references_agent(self, minimal_config):
        """Test that ToolExecutionEngine has reference to agent."""
        agent = SerenaAgent(serena_config=minimal_config)

        assert agent._execution_engine._agent is agent

    def test_execution_engine_constraints_disabled_by_default(self, minimal_config):
        """Test that constraints are disabled by default."""
        minimal_config.enable_constraints = False

        agent = SerenaAgent(serena_config=minimal_config)

        assert agent._execution_engine._constraints_enabled is False

    def test_execution_engine_constraints_enabled_via_config(self, minimal_config):
        """Test that constraints can be enabled via config."""
        minimal_config.enable_constraints = True

        agent = SerenaAgent(serena_config=minimal_config)

        assert agent._execution_engine._constraints_enabled is True

    def test_execution_engine_disabled_via_feature_flag(self, minimal_config):
        """Test that execution engine can be disabled via feature flag."""
        minimal_config.enable_execution_engine = False

        agent = SerenaAgent(serena_config=minimal_config)

        assert not hasattr(agent, "_execution_engine") or agent._execution_engine is None

    def test_agent_cleanup_stops_execution_engine(self, minimal_config):
        """Test that SerenaAgent cleanup properly handles execution engine."""
        agent = SerenaAgent(serena_config=minimal_config)

        # Execution engine should be created
        assert agent._execution_engine is not None

        # Cleanup should not raise errors
        agent.__del__()  # Or whatever cleanup method exists
```

### Green 阶段 - 最小实现

**实现文件**: `src/serena/agent.py` (修改现有文件)

```python
# 在 SerenaAgent 类中添加

from evolvai.core.execution import ToolExecutionEngine

class SerenaAgent:
    def __init__(
        self,
        serena_config: SerenaConfig,
        # ... 其他参数
    ):
        # ... 现有初始化代码

        # NEW: 创建 ToolExecutionEngine（如果启用）
        self._execution_engine: ToolExecutionEngine | None = None
        if serena_config.enable_execution_engine:
            enable_constraints = getattr(serena_config, "enable_constraints", False)
            self._execution_engine = ToolExecutionEngine(
                agent=self,
                enable_constraints=enable_constraints
            )
```

**配置文件**: `src/serena/config/config.py` (添加新配置)

```python
@dataclass
class SerenaConfig:
    # ... 现有字段

    # NEW: Phase 0 feature flags
    enable_execution_engine: bool = True
    enable_constraints: bool = False
```

---

## 🔴 Cycle 2: Tool.apply_ex() 委托到 ToolExecutionEngine

### Red 阶段 - 编写测试

**测试文件**: `test/evolvai/integration/test_tool_apply_ex_migration.py`

```python
"""Tests for Tool.apply_ex() migration to ToolExecutionEngine."""
from unittest.mock import Mock, patch

import pytest

from serena.agent import SerenaAgent
from serena.tools.tools_base import Tool


class MockSimpleTool(Tool):
    """Simple mock tool for testing."""

    def apply(self, arg1: str) -> str:
        """Mock apply method.

        :param arg1: Test argument
        :return: Test result
        """
        return f"result: {arg1}"


class TestToolApplyExMigration:
    """Test Tool.apply_ex() delegates to ToolExecutionEngine."""

    @pytest.fixture
    def agent_with_engine(self, tmp_path):
        """Create SerenaAgent with execution engine enabled."""
        config = Mock()
        config.serena_home = tmp_path
        config.tool_timeout = 60
        config.enable_execution_engine = True
        config.enable_constraints = False

        agent = SerenaAgent(serena_config=config)
        return agent

    @pytest.fixture
    def agent_without_engine(self, tmp_path):
        """Create SerenaAgent with execution engine disabled."""
        config = Mock()
        config.serena_home = tmp_path
        config.tool_timeout = 60
        config.enable_execution_engine = False

        agent = SerenaAgent(serena_config=config)
        return agent

    def test_apply_ex_uses_execution_engine_when_enabled(self, agent_with_engine):
        """Test that apply_ex() uses ToolExecutionEngine when enabled."""
        tool = MockSimpleTool(agent_with_engine)

        with patch.object(agent_with_engine._execution_engine, "execute") as mock_execute:
            mock_execute.return_value = "mocked result"

            result = tool.apply_ex(arg1="test")

            # Should delegate to execution engine
            mock_execute.assert_called_once()
            assert result == "mocked result"

    def test_apply_ex_uses_legacy_path_when_disabled(self, agent_without_engine):
        """Test that apply_ex() uses legacy path when engine disabled."""
        tool = MockSimpleTool(agent_without_engine)

        result = tool.apply_ex(arg1="test")

        # Should use legacy path (direct execution)
        assert result == "result: test"

    def test_apply_ex_passes_all_kwargs_to_engine(self, agent_with_engine):
        """Test that apply_ex() passes all kwargs to execution engine."""
        tool = MockSimpleTool(agent_with_engine)

        with patch.object(agent_with_engine._execution_engine, "execute") as mock_execute:
            mock_execute.return_value = "result"

            tool.apply_ex(arg1="value1", execution_plan={"steps": []})

            # Check that all kwargs were passed
            call_kwargs = mock_execute.call_args[1]
            assert call_kwargs["arg1"] == "value1"
            assert call_kwargs["execution_plan"] == {"steps": []}

    def test_apply_ex_handles_engine_errors_gracefully(self, agent_with_engine):
        """Test that apply_ex() handles execution engine errors."""
        tool = MockSimpleTool(agent_with_engine)

        with patch.object(agent_with_engine._execution_engine, "execute") as mock_execute:
            mock_execute.side_effect = RuntimeError("Engine error")

            result = tool.apply_ex(arg1="test")

            # Should return error message, not raise
            assert "error" in result.lower() or "Error" in result

    def test_apply_ex_respects_log_call_parameter(self, agent_with_engine):
        """Test that apply_ex() respects log_call parameter."""
        tool = MockSimpleTool(agent_with_engine)

        with patch.object(agent_with_engine._execution_engine, "execute") as mock_execute:
            mock_execute.return_value = "result"

            # With log_call=False, should still work
            result = tool.apply_ex(log_call=False, arg1="test")
            assert result == "result"

    def test_apply_ex_audit_log_populated(self, agent_with_engine):
        """Test that execution creates audit log entries."""
        tool = MockSimpleTool(agent_with_engine)

        result = tool.apply_ex(arg1="test")

        # Check that audit log has entries
        audit_log = agent_with_engine._execution_engine._audit_log
        assert len(audit_log) > 0
        assert audit_log[0]["tool"] == "mock_simple"
```

### Green 阶段 - 实现

**实现文件**: `src/serena/tools/tools_base.py` (修改 Tool.apply_ex())

```python
class Tool(Component):
    # ... 现有代码

    def apply_ex(self, log_call: bool = True, catch_exceptions: bool = True, **kwargs) -> str:
        """
        Applies the tool with logging and exception handling, using the given keyword arguments.

        If SerenaAgent has ToolExecutionEngine enabled, delegates to it.
        Otherwise, uses legacy execution path.
        """

        # NEW: Check if execution engine is enabled
        if hasattr(self.agent, "_execution_engine") and self.agent._execution_engine is not None:
            # Use new execution engine path
            return self._apply_via_execution_engine(log_call, catch_exceptions, **kwargs)
        else:
            # Use legacy execution path (existing implementation)
            return self._apply_legacy(log_call, catch_exceptions, **kwargs)

    def _apply_via_execution_engine(
        self,
        log_call: bool,
        catch_exceptions: bool,
        **kwargs
    ) -> str:
        """Execute tool via ToolExecutionEngine (new path)."""
        try:
            # Delegate to execution engine
            return self.agent._execution_engine.execute(self, **kwargs)
        except Exception as e:
            if not catch_exceptions:
                raise
            log.error(f"Error executing tool via engine: {e}", exc_info=e)
            return f"Error executing tool: {e}"

    def _apply_legacy(
        self,
        log_call: bool,
        catch_exceptions: bool,
        **kwargs
    ) -> str:
        """Execute tool via legacy path (existing implementation)."""
        # This is the EXISTING apply_ex() implementation
        # Copy all the current apply_ex() code here

        def task() -> str:
            apply_fn = self.get_apply_fn()

            # ... (existing implementation)

            return result

        future = self.agent.issue_task(task, name=self.__class__.__name__)
        return future.result(timeout=self.agent.serena_config.tool_timeout)
```

---

## 🔴 Cycle 3: Feature Flag 配置和控制

### Red 阶段 - 编写测试

**测试文件**: `test/evolvai/integration/test_feature_flag.py`

```python
"""Tests for feature flag configuration and control."""
import pytest

from serena.agent import SerenaAgent
from serena.config import SerenaConfig


class TestFeatureFlagControl:
    """Test feature flag configuration and behavior."""

    def test_execution_engine_enabled_by_default(self, tmp_path):
        """Test that execution engine is enabled by default."""
        config = SerenaConfig(serena_home=tmp_path)

        assert config.enable_execution_engine is True

    def test_constraints_disabled_by_default(self, tmp_path):
        """Test that constraints are disabled by default."""
        config = SerenaConfig(serena_home=tmp_path)

        assert config.enable_constraints is False

    def test_can_disable_execution_engine_via_config(self, tmp_path):
        """Test that execution engine can be disabled."""
        config = SerenaConfig(
            serena_home=tmp_path,
            enable_execution_engine=False
        )

        agent = SerenaAgent(serena_config=config)

        assert agent._execution_engine is None

    def test_can_enable_constraints_via_config(self, tmp_path):
        """Test that constraints can be enabled."""
        config = SerenaConfig(
            serena_home=tmp_path,
            enable_constraints=True
        )

        agent = SerenaAgent(serena_config=config)

        assert agent._execution_engine._constraints_enabled is True

    def test_constraints_require_execution_engine(self, tmp_path):
        """Test that enabling constraints without engine logs warning."""
        config = SerenaConfig(
            serena_home=tmp_path,
            enable_execution_engine=False,
            enable_constraints=True  # This should warn
        )

        with pytest.warns(UserWarning, match="Constraints require execution engine"):
            agent = SerenaAgent(serena_config=config)

    def test_feature_flags_loaded_from_yaml(self, tmp_path):
        """Test that feature flags can be loaded from YAML config."""
        config_path = tmp_path / "serena_config.yml"
        config_path.write_text("""
        serena_home: /tmp
        enable_execution_engine: false
        enable_constraints: false
        """)

        config = SerenaConfig.load(config_path)

        assert config.enable_execution_engine is False
```

### Green 阶段 - 实现

```python
# src/serena/config/config.py

@dataclass
class SerenaConfig:
    # ... existing fields

    # Phase 0 feature flags
    enable_execution_engine: bool = True
    enable_constraints: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.enable_constraints and not self.enable_execution_engine:
            import warnings
            warnings.warn(
                "Constraints require execution engine. "
                "Setting enable_execution_engine=False will disable constraints.",
                UserWarning
            )
```

---

## 🔴 Cycle 4: MCP 适配器集成

### Red 阶段 - 编写测试

**测试文件**: `test/evolvai/integration/test_mcp_integration.py`

```python
"""Tests for MCP adapter integration with ToolExecutionEngine."""
from unittest.mock import Mock

import pytest

from serena.agent import SerenaAgent, Tool
from serena.mcp import SerenaMCPFactory


class MockMCPTool(Tool):
    """Mock tool for MCP testing."""

    def apply(self, test_arg: str) -> str:
        """Mock apply.

        :param test_arg: Test argument
        :return: Result
        """
        return f"mcp_result: {test_arg}"


class TestMCPIntegration:
    """Test MCP adapter works with ToolExecutionEngine."""

    @pytest.fixture
    def agent_with_engine(self, tmp_path):
        """Create agent with execution engine."""
        config = Mock()
        config.serena_home = tmp_path
        config.enable_execution_engine = True
        config.enable_constraints = False
        config.tool_timeout = 60

        return SerenaAgent(serena_config=config)

    def test_mcp_tool_uses_execution_engine(self, agent_with_engine):
        """Test that MCP tools use execution engine."""
        tool = MockMCPTool(agent_with_engine)
        mcp_tool = SerenaMCPFactory.make_mcp_tool(tool)

        result = mcp_tool.fn(test_arg="hello")

        # Should go through execution engine and return result
        assert result == "mcp_result: hello"

        # Check audit log was populated
        assert len(agent_with_engine._execution_engine._audit_log) > 0

    def test_mcp_tool_execution_plan_support(self, agent_with_engine):
        """Test that MCP tools support execution_plan parameter."""
        tool = MockMCPTool(agent_with_engine)
        mcp_tool = SerenaMCPFactory.make_mcp_tool(tool)

        plan = {"steps": ["analyze", "execute"]}
        result = mcp_tool.fn(test_arg="hello", execution_plan=plan)

        assert result == "mcp_result: hello"

        # Verify execution plan was captured in audit log
        audit_record = agent_with_engine._execution_engine._audit_log[0]
        # (Plan verification will be in Story 1.1)

    def test_mcp_tool_backwards_compatible(self, tmp_path):
        """Test that MCP tools work without execution engine."""
        config = Mock()
        config.serena_home = tmp_path
        config.enable_execution_engine = False
        config.tool_timeout = 60

        agent = SerenaAgent(serena_config=config)
        tool = MockMCPTool(agent)
        mcp_tool = SerenaMCPFactory.make_mcp_tool(tool)

        result = mcp_tool.fn(test_arg="hello")

        # Should still work via legacy path
        assert result == "mcp_result: hello"
```

### Green 阶段 - 验证

MCP 适配器不需要修改，因为它调用的是 `tool.apply_ex()`，而我们已经在 Cycle 2 中修改了 `apply_ex()` 来委托给 ToolExecutionEngine。

只需要验证集成测试通过即可。

---

## 🔴 Cycle 5: 向后兼容性验证

### Red 阶段 - 编写测试

**测试文件**: `test/evolvai/integration/test_backwards_compatibility.py`

```python
"""Tests for backwards compatibility with legacy code."""
import pytest

from serena.agent import SerenaAgent
from serena.tools.tools_base import Tool


class TestBackwardsCompatibility:
    """Ensure new code doesn't break existing functionality."""

    def test_existing_tools_work_with_engine_enabled(self, tmp_path):
        """Test that all existing tools work with execution engine."""
        # This will run all existing tool tests with engine enabled
        # Will be verified in Story 0.3
        pass

    def test_existing_tools_work_with_engine_disabled(self, tmp_path):
        """Test that all existing tools work with engine disabled."""
        # This ensures legacy path still works
        pass

    def test_agent_initialization_backwards_compatible(self, tmp_path):
        """Test that SerenaAgent can be initialized as before."""
        # Without specifying new feature flags
        config = Mock()
        config.serena_home = tmp_path
        # No enable_execution_engine specified

        agent = SerenaAgent(serena_config=config)

        # Should default to enabled
        assert agent._execution_engine is not None

    def test_tool_usage_patterns_unchanged(self, agent_with_tools):
        """Test that common tool usage patterns still work."""
        # Test various tool invocation patterns
        # This is comprehensive in Story 0.3
        pass
```

---

## ✅ Definition of Done

### 代码质量

- [ ] 所有集成测试通过
- [ ] 测试覆盖率 ≥ 85% (集成测试较复杂)
- [ ] 类型检查通过 (`uv run poe type-check`)
- [ ] 代码格式化通过 (`uv run poe format`)
- [ ] 无 lint 警告

### 功能完整性

- [ ] SerenaAgent 正确创建和管理 ToolExecutionEngine
- [ ] Tool.apply_ex() 正确委托到 ToolExecutionEngine
- [ ] Feature flags 正确控制行为
- [ ] MCP 适配器无缝集成
- [ ] 向后兼容性完整

### 集成验证

- [ ] 现有所有工具测试通过（engine enabled）
- [ ] 现有所有工具测试通过（engine disabled）
- [ ] MCP 服务器正常启动和运行
- [ ] 审计日志正确记录

### 文档

- [ ] SerenaAgent 修改有清晰注释
- [ ] Feature flags 文档完整
- [ ] 迁移指南（如有需要）

---

## 📊 每日进度跟踪

### Day 1: Cycle 1-2 (核心集成)
- ✅ Cycle 1: SerenaAgent 初始化 ToolExecutionEngine
- ✅ Cycle 2: Tool.apply_ex() 迁移

### Day 2: Cycle 3-4 (配置和适配器)
- ⏳ Cycle 3: Feature flag 实现
- ⏳ Cycle 4: MCP 适配器验证

### Day 3: Cycle 5 + 完善
- ⏳ Cycle 5: 向后兼容性验证
- ⏳ 集成测试完善
- ⏳ 文档更新
- ⏳ DoD 检查

---

## 🛡️ 回滚计划

如果集成出现问题：

### Step 1: Feature Flag 禁用
```python
config.enable_execution_engine = False
```

### Step 2: 回退 Tool.apply_ex()
- 保留 `_apply_legacy()` 方法
- 移除 `_apply_via_execution_engine()` 调用
- 直接调用 legacy path

### Step 3: 移除 SerenaAgent 初始化
- 注释掉 ToolExecutionEngine 创建代码

### Step 4: 验证回滚
- 运行所有测试
- 确认功能正常

---

## 🔗 相关文档

- [Story 0.1: 实现 ToolExecutionEngine](./story-0.1-tdd-plan.md) (前置依赖)
- [Story 0.3: 回归测试和性能验证](./story-0.3-tdd-plan.md) (后续 Story)
- [ADR-003: 工具调用链路简化](../../architecture/adrs/003-tool-execution-engine-simplification.md)
- [Phase 0 详细设计](../../architecture/phase-0-tool-execution-engine.md)

---

**最后更新**: 2025-10-27
**更新人**: EvolvAI Team
**前置条件**: Story 0.1 完成
**下一步**: Story 0.3 回归测试
