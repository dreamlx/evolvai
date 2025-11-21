"""
MCP Tools - Parameter Schema & Docstring Tests

Dimension 2: 验证 MCP 工具的参数定义完整且类型正确
Dimension 3: 验证工具 docstring 完整且对 LLM 友好

测试目标:
- 参数类型注解正确
- 必需参数和可选参数标记正确
- 默认值合理
- Docstring 包含 Args/Returns/Examples
- 参数说明完整
"""


class TestBatchEditParameterSchema:
    """BatchEdit 参数 Schema 测试"""

    def test_required_parameters(self):
        """验证必需参数定义

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Required parameters correctly defined
        DoD: pattern, replacement are required and typed as str

        Given BatchEditTool class
        When get apply function metadata
        Then pattern and replacement are required str parameters
        """
        import inspect

        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Get apply method signature
        sig = inspect.signature(BatchEditTool.apply)
        params = sig.parameters

        # Verify pattern is required and typed as str
        assert "pattern" in params, "pattern parameter not found"
        pattern_param = params["pattern"]
        assert pattern_param.default == inspect.Parameter.empty, \
            "pattern should be required (no default)"
        assert pattern_param.annotation is str, \
            f"pattern should be typed as str, got {pattern_param.annotation}"

        # Verify replacement is required and typed as str
        assert "replacement" in params, "replacement parameter not found"
        replacement_param = params["replacement"]
        assert replacement_param.default == inspect.Parameter.empty, \
            "replacement should be required (no default)"
        assert replacement_param.annotation is str, \
            f"replacement should be typed as str, got {replacement_param.annotation}"
        # TODO: Implement in Phase 1.2

    def test_optional_parameters_with_defaults(self):
        """验证可选参数有合理默认值

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Optional parameters have sensible defaults
        DoD: scope="**/*", preview=False

        Given BatchEditTool class
        When get apply function metadata
        Then scope defaults to "**/*" and preview defaults to False
        """
        import inspect

        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Get apply method signature
        sig = inspect.signature(BatchEditTool.apply)
        params = sig.parameters

        # Verify scope has correct default
        assert "scope" in params, "scope parameter not found"
        scope_param = params["scope"]
        assert scope_param.default == "**/*", \
            f"scope should default to '**/*', got {scope_param.default}"
        assert scope_param.annotation is str, \
            f"scope should be typed as str, got {scope_param.annotation}"

        # Verify preview has correct default
        assert "preview" in params, "preview parameter not found"
        preview_param = params["preview"]
        assert preview_param.default is False, \
            f"preview should default to False, got {preview_param.default}"
        assert preview_param.annotation is bool, \
            f"preview should be typed as bool, got {preview_param.annotation}"
        # TODO: Implement in Phase 1.2

    def test_execution_plan_parameter_type(self):
        """验证 ExecutionPlan 参数类型正确

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: ExecutionPlan parameter is Optional[ExecutionPlan]
        DoD: Type annotation includes ExecutionPlan

        Given BatchEditTool class
        When get execution_plan parameter annotation
        Then annotation contains ExecutionPlan type
        """
        import inspect
        from typing import get_args, get_origin

        from evolvai.core.execution_plan import ExecutionPlan
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Get apply method signature
        sig = inspect.signature(BatchEditTool.apply)
        params = sig.parameters

        # Verify execution_plan parameter exists
        assert "execution_plan" in params, "execution_plan parameter not found"
        exec_plan_param = params["execution_plan"]

        # Verify default is None (Optional)
        assert exec_plan_param.default is None, \
            f"execution_plan should default to None, got {exec_plan_param.default}"

        # Verify type annotation is Optional[ExecutionPlan]
        annotation = exec_plan_param.annotation
        origin = get_origin(annotation)
        
        # Check if it's Optional (Union with None)
        if origin is not None:
            args = get_args(annotation)
            assert ExecutionPlan in args, \
                f"ExecutionPlan not found in type annotation {annotation}"
            assert type(None) in args, \
                "None not found in type annotation (should be Optional)"
        else:
            # If no origin, might be just ExecutionPlan (which is also valid)
            assert annotation == ExecutionPlan, \
                f"Expected ExecutionPlan, got {annotation}"
        # TODO: Implement in Phase 1.2


class TestSafeSearchParameterSchema:
    """SafeSearch 参数 Schema 测试"""

    def test_query_parameter_required(self):
        """验证 query 参数必需且类型正确

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: query parameter is required str
        DoD: query is required and typed as str

        Given SafeSearchTool class
        When get apply function metadata
        Then query is required str parameter
        """
        import inspect

        from serena.tools.safe_search_tool import SafeSearchTool

        # Get apply method signature
        sig = inspect.signature(SafeSearchTool.apply)
        params = sig.parameters

        # Verify query is required and typed as str
        assert "query" in params, "query parameter not found"
        query_param = params["query"]
        assert query_param.default == inspect.Parameter.empty, \
            "query should be required (no default)"
        assert query_param.annotation is str, \
            f"query should be typed as str, got {query_param.annotation}"
        # TODO: Implement in Phase 1.2

    def test_area_selector_enum_values(self):
        """验证 area_selector 默认值

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: area_selector defaults to "auto"
        DoD: Default value is "auto"

        Given SafeSearchTool class
        When get area_selector parameter
        Then default value is "auto"
        """
        import inspect

        from serena.tools.safe_search_tool import SafeSearchTool

        # Get apply method signature
        sig = inspect.signature(SafeSearchTool.apply)
        params = sig.parameters

        # Verify area_selector has correct default
        assert "area_selector" in params, "area_selector parameter not found"
        area_selector_param = params["area_selector"]
        assert area_selector_param.default == "auto", \
            f"area_selector should default to 'auto', got {area_selector_param.default}"
        assert area_selector_param.annotation is str, \
            f"area_selector should be typed as str, got {area_selector_param.annotation}"
        # TODO: Implement in Phase 1.2

    def test_mode_parameter_defaults(self):
        """验证 mode 参数默认值

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: mode defaults to "balanced"
        DoD: Default value is "balanced"

        Given SafeSearchTool class
        When get mode parameter
        Then default value is "balanced"
        """
        import inspect

        from serena.tools.safe_search_tool import SafeSearchTool

        # Get apply method signature
        sig = inspect.signature(SafeSearchTool.apply)
        params = sig.parameters

        # Verify mode has correct default
        assert "mode" in params, "mode parameter not found"
        mode_param = params["mode"]
        assert mode_param.default == "balanced", \
            f"mode should default to 'balanced', got {mode_param.default}"
        assert mode_param.annotation is str, \
            f"mode should be typed as str, got {mode_param.annotation}"
        # TODO: Implement in Phase 1.2


class TestBatchEditDocstring:
    """BatchEdit Docstring 测试"""

    def test_docstring_exists_and_not_empty(self):
        """验证 batch_edit 有非空 docstring

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Docstring exists and is substantial
        DoD: Docstring length >= 100 characters

        Given BatchEditTool class
        When get apply docstring
        Then docstring length >= 100
        """
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Get apply method docstring
        docstring = BatchEditTool.apply.__doc__

        # Verify docstring exists
        assert docstring is not None, "apply method has no docstring"

        # Verify docstring is substantial
        assert len(docstring) >= 100, \
            f"Docstring too short: {len(docstring)} chars (expected >= 100)"
        # TODO: Implement in Phase 1.3

    def test_docstring_contains_required_sections(self):
        """验证 docstring 包含关键部分

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Docstring has Args/Returns/Examples
        DoD: All required sections present

        Given BatchEditTool apply docstring
        When check for sections
        Then "Args:", "Returns:", "Examples:" all present
        """
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Get apply method docstring
        docstring = BatchEditTool.apply.__doc__
        assert docstring is not None, "apply method has no docstring"

        # Verify required sections
        assert "Args:" in docstring, "Docstring missing 'Args:' section"
        assert "Returns:" in docstring, "Docstring missing 'Returns:' section"
        assert "Examples:" in docstring, "Docstring missing 'Examples:' section"
        # TODO: Implement in Phase 1.3

    def test_docstring_parameter_descriptions(self):
        """验证所有参数都有说明

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: All parameters documented in docstring
        DoD: pattern, replacement, preview described

        Given BatchEditTool apply docstring
        When check parameter descriptions
        Then pattern, replacement, preview all documented
        """
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Get apply method docstring
        docstring = BatchEditTool.apply.__doc__
        assert docstring is not None, "apply method has no docstring"

        # Verify core parameters are documented
        assert "pattern:" in docstring.lower(), \
            "Docstring missing 'pattern' parameter description"
        assert "replacement:" in docstring.lower(), \
            "Docstring missing 'replacement' parameter description"
        assert "preview:" in docstring.lower(), \
            "Docstring missing 'preview' parameter description"
        # TODO: Implement in Phase 1.3

    def test_docstring_includes_safety_warnings(self):
        """验证 docstring 包含安全提示（ADR-004）

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Docstring mentions rollback safety
        DoD: "rollback", "file-level" mentioned

        Given BatchEditTool apply docstring
        When check for safety keywords
        Then "rollback" and "file-level" present
        """
        from evolvai.tools.batch_edit_tool import BatchEditTool

        # Get apply method docstring
        docstring = BatchEditTool.apply.__doc__
        assert docstring is not None, "apply method has no docstring"

        # Verify safety-related keywords (case-insensitive)
        docstring_lower = docstring.lower()
        assert "rollback" in docstring_lower, \
            "Docstring missing 'rollback' safety keyword"
        assert "file-level" in docstring_lower or "file level" in docstring_lower, \
            "Docstring missing 'file-level' safety keyword"
        # TODO: Implement in Phase 1.3


class TestSafeSearchDocstring:
    """SafeSearch Docstring 测试"""

    def test_docstring_describes_area_detection(self):
        """验证 safe_search docstring 说明区域检测功能

        Story: 2.2 Day 6 - MCP Tool Testing
        Scenario: Docstring explains area detection
        DoD: "area", "detect" or "auto" mentioned

        Given SafeSearchTool apply docstring
        When check for area detection keywords
        Then "area" and ("detect" or "auto") present
        """
        from serena.tools.safe_search_tool import SafeSearchTool

        # Get apply method docstring
        docstring = SafeSearchTool.apply.__doc__
        assert docstring is not None, "apply method has no docstring"

        # Verify area detection keywords (case-insensitive)
        docstring_lower = docstring.lower()
        assert "area" in docstring_lower, \
            "Docstring missing 'area' keyword"
        assert "detect" in docstring_lower or "auto" in docstring_lower, \
            "Docstring missing 'detect' or 'auto' keyword for area detection"
        # TODO: Implement in Phase 1.3
