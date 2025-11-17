"""
MCP Tools - Tool Discovery Tests

Dimension 1: 验证 MCP 工具能被 ToolRegistry 正确发现和注册

测试目标:
- evolvai.tools 模块的工具被 ToolRegistry 发现
- 工具名称正确映射（batch_edit, safe_search, etc）
- 工具类可通过名称获取
"""
import pytest


class TestMCPToolDiscovery:
    """MCP 工具发现测试"""

    def test_evolvai_tools_discoverable(self):
        """验证 evolvai.tools 模块的工具被 ToolRegistry 发现

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: ToolRegistry discovers evolvai MCP tools
        DoD: batch_edit, safe_search tools are discoverable

        Given ToolRegistry initialized
        When import serena.tools (triggers auto-import)
        Then batch_edit, safe_search, get_language_hint in tool names
        """
        from serena.tools.tools_base import ToolRegistry
        import serena.tools  # Trigger auto-import of evolvai tools

        tr = ToolRegistry()
        tool_names = tr.get_tool_names()

        # Verify core MCP tools are discovered
        assert "batch_edit" in tool_names, "batch_edit tool not discovered"
        assert "safe_search" in tool_names, "safe_search tool not discovered"
        assert "get_language_hint" in tool_names, "get_language_hint tool not discovered"
        # TODO: Implement in Phase 1.1

    def test_tool_count_baseline(self):
        """验证工具总数符合预期

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Tool count matches baseline
        DoD: Total tools >= 49

        Given ToolRegistry initialized
        When get all tool names
        Then tool count >= 49 (baseline + evolvai tools)
        """
        from serena.tools.tools_base import ToolRegistry
        import serena.tools

        tr = ToolRegistry()
        tool_names = tr.get_tool_names()

        # Baseline: 49 tools (serena + evolvai)
        assert len(tool_names) >= 49, f"Expected >= 49 tools, got {len(tool_names)}"
        # TODO: Implement in Phase 1.1

    def test_tool_class_retrievable(self):
        """验证工具类可以通过名称获取

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Tool classes retrievable by name
        DoD: get_tool_class_by_name returns correct class

        Given tool name "batch_edit"
        When get_tool_class_by_name("batch_edit")
        Then returns BatchEditTool class
        """
        from serena.tools.tools_base import ToolRegistry
        import serena.tools

        tr = ToolRegistry()

        # Test batch_edit
        batch_edit_class = tr.get_tool_class_by_name("batch_edit")
        assert batch_edit_class.__name__ == "BatchEditTool", \
            f"Expected BatchEditTool, got {batch_edit_class.__name__}"

        # Test safe_search
        safe_search_class = tr.get_tool_class_by_name("safe_search")
        assert safe_search_class.__name__ == "SafeSearchTool", \
            f"Expected SafeSearchTool, got {safe_search_class.__name__}"

        # Test get_language_hint
        language_hint_class = tr.get_tool_class_by_name("get_language_hint")
        assert language_hint_class.__name__ == "GetLanguageHintTool", \
            f"Expected GetLanguageHintTool, got {language_hint_class.__name__}"
        # TODO: Implement in Phase 1.1
