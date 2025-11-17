"""
MCP Tools Testing - Shared Fixtures

Provides common fixtures for MCP tool testing to ensure test isolation
and reduce code duplication.
"""
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_agent(tmp_path):
    """创建 mock SerenaAgent 用于 MCP 工具测试

    自动使用 tmp_path 作为项目根目录，确保测试隔离。

    Returns:
        Mock: Mock SerenaAgent with get_project_root() configured

    Example:
        def test_something(mock_agent):
            tool = BatchEditTool(mock_agent)
            # mock_agent.get_project_root() returns isolated tmp directory

    """
    agent = Mock()
    agent.get_project_root.return_value = str(tmp_path)
    return agent


@pytest.fixture
def simple_project(tmp_path):
    """创建简单的测试项目结构

    结构:
        tmp_path/
        ├── file1.py
        ├── file2.py
        └── file3.py

    每个文件包含 "old_value" 用于批量编辑测试。

    Returns:
        Path: 项目根目录路径

    Example:
        def test_batch_edit(simple_project, mock_agent):
            # simple_project already has 3 .py files
            tool = BatchEditTool(mock_agent)
            result = tool.apply(pattern="old_value", replacement="new_value")

    """
    (tmp_path / "file1.py").write_text("old_value = 1")
    (tmp_path / "file2.py").write_text("old_value = 2")
    (tmp_path / "file3.py").write_text("old_value = 3")
    return tmp_path


@pytest.fixture
def go_project(tmp_path):
    """创建 Go 项目结构（用于 safe_search 测试）

    注意: safe_search 当前使用 mock 数据，此 fixture 仅用于
    验证 MCP 层功能（JSON 格式、参数传递等），不验证实际搜索结果。

    结构:
        tmp_path/
        ├── main.go
        └── handler.go

    Returns:
        Path: 项目根目录路径

    Example:
        @pytest.mark.skip(reason="safe_search uses mock data")
        def test_safe_search(go_project, mock_agent):
            # go_project has Go files for area detection
            tool = SafeSearchTool(mock_agent)
            result = tool.apply(query="func main")

    """
    (tmp_path / "main.go").write_text("package main\n\nfunc main() {\n\tprintln(\"Hello\")\n}\n")
    (tmp_path / "handler.go").write_text("package main\n\nfunc handleRequest() {\n\t// handler\n}\n")
    return tmp_path
