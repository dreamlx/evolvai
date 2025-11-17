# MCP Tools Testing Plan

**状态**: [DRAFT]
**创建日期**: 2025-01-15
**Story**: 2.2 Day 6 - MCP Tool Testing
**目标**: 验证 batch_edit 和 safe_search MCP 工具的完整性和正确性

---

## 测试目标

验证 MCP 工具层能够：
1. 被 ToolRegistry 正确发现和注册
2. 提供完整的参数 schema 供 MCP 客户端使用
3. 生成 LLM 友好的工具描述（docstring）
4. 返回格式正确的 JSON 结果
5. 正确处理错误并返回可操作的错误信息
6. 与 ExecutionPlan 约束系统集成

---

## 测试范围

### 覆盖的 MCP 工具

- ✅ `batch_edit` (BatchEditTool)
- ✅ `safe_search` (SafeSearchTool)
- ✅ `get_language_hint` (GetLanguageHintTool)
- ⚠️ `safe_exec` (SafeExecTool) - 可选，已有独立测试

### 不在本次范围

- ❌ MCP 协议层测试（MCP server/client 通信）
- ❌ 工具内部业务逻辑（已有单元测试覆盖）
- ❌ 性能压力测试

---

## 测试维度分解

### Dimension 1: 工具发现 (Tool Discovery)

**目标**: 验证 ToolRegistry 能正确发现和加载 evolvai MCP 工具

**测试用例**:

```python
# test/serena/tools/test_mcp_tool_discovery.py

class TestMCPToolDiscovery:
    def test_evolvai_tools_discoverable(self):
        """验证 evolvai.tools 模块的工具被 ToolRegistry 发现"""
        from serena.tools.tools_base import ToolRegistry
        import serena.tools  # 触发自动导入

        tr = ToolRegistry()
        tool_names = tr.get_tool_names()

        # 验证核心 MCP 工具存在
        assert "batch_edit" in tool_names
        assert "safe_search" in tool_names
        assert "get_language_hint" in tool_names

    def test_tool_count_baseline(self):
        """验证工具总数符合预期"""
        tr = ToolRegistry()
        tool_names = tr.get_tool_names()

        # 基准：49 个工具 + batch_edit + safe_search + get_language_hint
        assert len(tool_names) >= 49

    def test_tool_class_retrievable(self):
        """验证工具类可以通过名称获取"""
        tr = ToolRegistry()

        batch_edit_class = tr.get_tool_class_by_name("batch_edit")
        assert batch_edit_class.__name__ == "BatchEditTool"

        safe_search_class = tr.get_tool_class_by_name("safe_search")
        assert safe_search_class.__name__ == "SafeSearchTool"
```

**成功标准**:
- ✅ 所有断言通过
- ✅ 无 ImportError
- ✅ 工具计数准确

---

### Dimension 2: 参数 Schema 验证 (Parameter Schema)

**目标**: 验证 MCP 工具的参数定义完整且类型正确

**测试用例**:

```python
# test/evolvai/tools/test_mcp_parameter_schema.py

class TestBatchEditParameterSchema:
    def test_required_parameters(self):
        """验证必需参数定义"""
        from serena.tools.tools_base import ToolRegistry

        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("batch_edit")
        metadata = tool_class.get_apply_fn_metadata_from_cls()

        # 验证必需参数存在
        assert "pattern" in metadata.parameters
        assert "replacement" in metadata.parameters

        # 验证类型注解
        assert metadata.parameters["pattern"].annotation == str
        assert metadata.parameters["replacement"].annotation == str

    def test_optional_parameters_with_defaults(self):
        """验证可选参数有合理默认值"""
        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("batch_edit")
        metadata = tool_class.get_apply_fn_metadata_from_cls()

        # 验证默认值
        assert metadata.parameters["scope"].default == "**/*"
        assert metadata.parameters["preview"].default == False

    def test_execution_plan_parameter_type(self):
        """验证 ExecutionPlan 参数类型正确"""
        from evolvai.core.execution_plan import ExecutionPlan

        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("batch_edit")
        metadata = tool_class.get_apply_fn_metadata_from_cls()

        # ExecutionPlan 应该是 Optional[ExecutionPlan]
        execution_plan_param = metadata.parameters["execution_plan"]
        # 验证类型注解包含 ExecutionPlan
        assert "ExecutionPlan" in str(execution_plan_param.annotation)


class TestSafeSearchParameterSchema:
    def test_query_parameter_required(self):
        """验证 query 参数必需且类型正确"""
        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("safe_search")
        metadata = tool_class.get_apply_fn_metadata_from_cls()

        assert "query" in metadata.parameters
        assert metadata.parameters["query"].annotation == str

    def test_area_selector_enum_values(self):
        """验证 area_selector 默认值"""
        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("safe_search")
        metadata = tool_class.get_apply_fn_metadata_from_cls()

        # 默认值应该是 "auto"
        assert metadata.parameters["area_selector"].default == "auto"

    def test_mode_parameter_defaults(self):
        """验证 mode 参数默认值"""
        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("safe_search")
        metadata = tool_class.get_apply_fn_metadata_from_cls()

        assert metadata.parameters["mode"].default == "balanced"
```

**成功标准**:
- ✅ 所有参数类型注解正确
- ✅ 默认值合理
- ✅ 复杂类型（ExecutionPlan, Optional, list[dict]）正确处理

---

### Dimension 3: Docstring 提取测试 (LLM Tool Description)

**目标**: 验证工具 docstring 完整且对 LLM 友好

**测试用例**:

```python
# test/evolvai/tools/test_mcp_docstring.py

class TestBatchEditDocstring:
    def test_docstring_exists_and_not_empty(self):
        """验证 batch_edit 有非空 docstring"""
        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("batch_edit")

        docstring = tool_class.get_apply_docstring_from_cls()

        assert docstring is not None
        assert len(docstring) > 100  # 至少 100 字符

    def test_docstring_contains_required_sections(self):
        """验证 docstring 包含关键部分"""
        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("batch_edit")
        docstring = tool_class.get_apply_docstring_from_cls()

        # 必需部分
        assert "Args:" in docstring
        assert "Returns:" in docstring
        assert "Examples:" in docstring or "Example:" in docstring

    def test_docstring_parameter_descriptions(self):
        """验证所有参数都有说明"""
        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("batch_edit")
        docstring = tool_class.get_apply_docstring_from_cls()

        # 核心参数应该有说明
        assert "pattern:" in docstring or "pattern :" in docstring
        assert "replacement:" in docstring or "replacement :" in docstring
        assert "preview:" in docstring or "preview :" in docstring

    def test_docstring_includes_safety_warnings(self):
        """验证 docstring 包含安全提示（ADR-004）"""
        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("batch_edit")
        docstring = tool_class.get_apply_docstring_from_cls()

        # 应该提到文件级回滚
        assert "rollback" in docstring.lower()
        assert "file-level" in docstring.lower() or "file level" in docstring.lower()


class TestSafeSearchDocstring:
    def test_docstring_describes_area_detection(self):
        """验证 safe_search docstring 说明区域检测功能"""
        tr = ToolRegistry()
        tool_class = tr.get_tool_class_by_name("safe_search")
        docstring = tool_class.get_apply_docstring_from_cls()

        # 应该提到区域检测
        assert "area" in docstring.lower()
        assert "detect" in docstring.lower() or "auto" in docstring.lower()
```

**成功标准**:
- ✅ Docstring 长度充分（≥100 字符）
- ✅ 包含 Args/Returns/Examples
- ✅ 参数说明完整
- ✅ 包含安全/使用建议

---

### Dimension 4: JSON 结果格式测试 (Result Serialization)

**目标**: 验证 MCP 工具返回有效且结构正确的 JSON

**测试用例**:

```python
# test/evolvai/tools/test_mcp_json_results.py

class TestBatchEditJSONResult:
    def test_preview_mode_returns_valid_json(self, tmp_path):
        """验证 preview 模式返回有效 JSON"""
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool
        from unittest.mock import Mock

        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("old_value = 1")

        # 创建 mock agent
        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        # 创建工具并调用
        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="old_value",
            replacement="new_value",
            scope="*.py",
            preview=True
        )

        # 验证 JSON 有效性
        result = json.loads(result_json)

        # 验证必需字段
        assert "success" in result
        assert "affected_files" in result
        assert "changes_count" in result
        assert "unified_diff" in result

    def test_apply_mode_includes_rollback_id(self, tmp_path):
        """验证 apply 模式包含 rollback_id"""
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool
        from unittest.mock import Mock

        test_file = tmp_path / "test.py"
        test_file.write_text("old = 1")

        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="old",
            replacement="new",
            preview=False  # Apply mode
        )

        result = json.loads(result_json)

        # 应该包含 rollback_id
        assert "rollback_id" in result
        if result["success"]:
            assert result["rollback_id"] is not None

    def test_error_response_format(self, tmp_path):
        """验证错误响应格式正确"""
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool
        from unittest.mock import Mock

        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="[invalid(regex",  # 无效正则
            replacement="new"
        )

        result = json.loads(result_json)

        # 验证错误格式
        assert result["success"] == False
        assert "error_message" in result
        assert len(result["error_message"]) > 0


class TestSafeSearchJSONResult:
    def test_successful_search_json_structure(self, tmp_path):
        """验证成功搜索的 JSON 结构"""
        import json
        from serena.tools.safe_search_tool import SafeSearchTool
        from unittest.mock import Mock

        # 创建简单项目结构
        (tmp_path / "main.go").write_text("func main() {}")

        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        tool = SafeSearchTool(mock_agent)
        result_json = tool.apply(
            query="main",
            area_selector="auto"
        )

        result = json.loads(result_json)

        # 验证关键字段
        assert "success" in result
        assert "query" in result
        assert "total_results" in result
        assert "execution_report" in result

        # 验证嵌套结构
        report = result["execution_report"]
        assert "detected_areas" in report
        assert "execution_time_ms" in report
```

**成功标准**:
- ✅ 返回字符串可被 json.loads() 解析
- ✅ 必需字段存在
- ✅ 嵌套结构正确
- ✅ 类型正确（数字不是字符串等）

---

### Dimension 5: 错误处理测试 (Error Handling)

**目标**: 验证错误被正确捕获并返回 LLM 友好的错误信息

**测试用例**:

```python
# test/evolvai/tools/test_mcp_error_handling.py

class TestBatchEditErrorHandling:
    def test_invalid_regex_error(self, tmp_path):
        """验证无效正则表达式返回清晰错误"""
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool
        from unittest.mock import Mock

        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="[unclosed(",
            replacement="new"
        )

        result = json.loads(result_json)

        # 验证错误信息
        assert result["success"] == False
        assert "error_message" in result
        assert "regex" in result["error_message"].lower() or "pattern" in result["error_message"].lower()

    def test_execution_plan_constraint_violation(self, tmp_path):
        """验证 ExecutionPlan 约束违规返回清晰错误"""
        import json
        from evolvai.tools.batch_edit_tool import BatchEditTool
        from evolvai.core.execution_plan import ExecutionPlan, ExecutionLimits, RollbackStrategy, RollbackStrategyType
        from unittest.mock import Mock

        # 创建 5 个测试文件
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text("old")

        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        # 创建严格约束（max_files=2）
        plan = ExecutionPlan(
            rollback=RollbackStrategy(strategy=RollbackStrategyType.FILE_BACKUP),
            limits=ExecutionLimits(max_files=2, max_changes=100)
        )

        tool = BatchEditTool(mock_agent)
        result_json = tool.apply(
            pattern="old",
            replacement="new",
            scope="*.txt",
            execution_plan=plan
        )

        result = json.loads(result_json)

        # 验证约束错误
        assert result["success"] == False
        assert "error_message" in result
        assert "max_files" in result["error_message"].lower()


class TestSafeSearchErrorHandling:
    def test_dangerous_query_rejected(self, tmp_path):
        """验证危险查询被拒绝"""
        import json
        from serena.tools.safe_search_tool import SafeSearchTool
        from unittest.mock import Mock

        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        tool = SafeSearchTool(mock_agent)
        result_json = tool.apply(
            query=".*"  # 危险查询
        )

        result = json.loads(result_json)

        # 验证拒绝
        assert result["success"] == False
        assert "error" in result
        assert "broad" in result["error"]["message"].lower()
```

**成功标准**:
- ✅ 错误不导致异常抛出
- ✅ 返回 success=False + error_message
- ✅ 错误信息描述问题
- ✅ 包含修复建议（如果可能）

---

### Dimension 6: ExecutionPlan 集成测试

**目标**: 验证 ExecutionPlan 约束在 MCP 层正确传递和执行

**测试用例**:

```python
# test/evolvai/tools/test_mcp_execution_plan.py

class TestBatchEditExecutionPlan:
    def test_execution_plan_passed_to_core(self, tmp_path):
        """验证 ExecutionPlan 被传递到 BatchEditor"""
        from evolvai.tools.batch_edit_tool import BatchEditTool
        from evolvai.core.execution_plan import ExecutionPlan, ExecutionLimits
        from unittest.mock import Mock, patch

        mock_agent = Mock()
        mock_agent.get_project_root.return_value = str(tmp_path)

        plan = ExecutionPlan(limits=ExecutionLimits(max_files=10))

        tool = BatchEditTool(mock_agent)

        # Mock BatchEditor.batch_edit 以验证调用
        with patch("evolvai.tools.batch_edit_tool.BatchEditor.batch_edit") as mock_batch_edit:
            mock_batch_edit.return_value = Mock(
                success=True,
                affected_files=[],
                changes_count=0,
                unified_diff="",
                rollback_id=None,
                error_message=None,
                duration_ms=0.0
            )

            tool.apply(
                pattern="test",
                replacement="new",
                execution_plan=plan
            )

            # 验证 BatchEditor.batch_edit 被调用时包含 execution_plan
            assert mock_batch_edit.called
            call_kwargs = mock_batch_edit.call_args[1]
            assert "execution_plan" in call_kwargs
            assert call_kwargs["execution_plan"] == plan
```

**成功标准**:
- ✅ ExecutionPlan 参数正确传递到核心层
- ✅ 约束验证在核心层执行
- ✅ 违规时返回明确错误

---

## 测试实施计划

### Phase 1: 基础测试 (Day 6.1-6.2)

**优先级**: P0 - 必须通过

**任务**:
1. ✅ 创建测试文件结构
2. ✅ 实现 Dimension 1: 工具发现测试
3. ✅ 实现 Dimension 2: 参数 Schema 测试
4. ✅ 实现 Dimension 3: Docstring 测试

**交付物**:
- `test/serena/tools/test_mcp_tool_discovery.py`
- `test/evolvai/tools/test_mcp_parameter_schema.py`
- `test/evolvai/tools/test_mcp_docstring.py`

**验收标准**: 所有测试通过，覆盖率 ≥ 80%

---

### Phase 2: 集成测试 (Day 6.3-6.4)

**优先级**: P0 - 必须通过

**任务**:
1. ✅ 实现 Dimension 4: JSON 结果格式测试
2. ✅ 实现 Dimension 5: 错误处理测试
3. ✅ 实现 Dimension 6: ExecutionPlan 集成测试

**交付物**:
- `test/evolvai/tools/test_mcp_json_results.py`
- `test/evolvai/tools/test_mcp_error_handling.py`
- `test/evolvai/tools/test_mcp_execution_plan.py`

**验收标准**: 所有测试通过，无遗漏场景

---

### Phase 3: 文档和总结 (Day 6.5)

**优先级**: P1 - 建议完成

**任务**:
1. ✅ 更新测试覆盖率报告
2. ✅ 生成测试总结文档
3. ✅ 记录发现的问题和改进建议
4. ✅ 更新 Story 2.2 进度

**交付物**:
- 测试覆盖率报告
- `docs/testing/reports/mcp-tools-test-report.md`
- Story 2.2 Phase 2 完成标记

---

## 风险和缓解

### 风险 1: safe_search 核心是模拟实现

**描述**: `_search_in_area()` 返回 mock 数据，无法测试真实搜索功能

**影响**:
- ⚠️ JSON 结果测试基于假数据
- ⚠️ 无法验证实际搜索准确性

**缓解措施**:
1. 在测试中明确标注 "基于模拟数据"
2. 测试重点放在 MCP 层（参数传递、JSON 格式）
3. 将实际搜索功能测试推迟到 safe_search 核心实现完成后

### 风险 2: ExecutionPlan 序列化复杂

**描述**: ExecutionPlan 是嵌套 Pydantic 模型，MCP 参数传递可能有问题

**影响**:
- ⚠️ MCP 客户端可能无法正确构造 ExecutionPlan 参数

**缓解措施**:
1. 详细测试 ExecutionPlan 参数序列化
2. 提供清晰的 JSON schema 示例
3. 如果必要，考虑简化 ExecutionPlan 为字典参数

---

## 成功标准

### 定量标准

- ✅ 测试通过率 = 100%
- ✅ 代码覆盖率 ≥ 80% (MCP 工具层)
- ✅ 所有 6 个测试维度完整覆盖
- ✅ 0 个 critical 级别问题遗留

### 定性标准

- ✅ MCP 工具可被 ToolRegistry 发现
- ✅ LLM 能理解工具用途（基于 docstring）
- ✅ 错误信息对 LLM 友好
- ✅ JSON 结果格式稳定

---

## 后续行动

完成此测试计划后：

1. **Story 2.2 Phase 2 完成验证**
   - 所有测试通过
   - MCP 工具可用性确认

2. **Story 2.2 Phase 3 准备**（可选）
   - safe_search 实际搜索工具集成
   - 性能基准测试

3. **文档更新**
   - 更新 Story 2.2 进度
   - 记录 ADR（如果有架构变更）
   - 创建 Lesson（如果有经验教训）

---

**最后更新**: 2025-01-15
**下次审查**: Phase 1 完成后
