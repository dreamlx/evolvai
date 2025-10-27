"""
Tests for Legacy Memory Tools.

Tests backward compatibility and deprecation warnings for legacy memory functionality.
"""

import json
import tempfile
import warnings
from pathlib import Path
from unittest.mock import Mock

import pytest

from serena.agent import SerenaAgent
from serena.config.serena_config import ProjectConfig
from serena.project import Project
from serena.tools.legacy_memory_tools import DeleteMemoryTool, LegacyMemoryWarning, ListMemoriesTool, ReadMemoryTool, WriteMemoryTool


@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_project(temp_project_root):
    """Create a mock project for testing tools."""
    project_config = ProjectConfig(
        project_name="test_project",
        language="python",
        ignored_paths=[],
        excluded_tools=set(),
        read_only=False,
        ignore_all_files_in_gitignore=True,
        initial_prompt="",
        encoding="utf-8",
    )
    return Project(project_root=str(temp_project_root), project_config=project_config)


@pytest.fixture
def mock_agent(mock_project):
    """Create a mock Serena agent."""
    agent = Mock(spec=SerenaAgent)
    agent.project = mock_project
    agent.serena_config = Mock()
    agent.serena_config.default_max_tool_answer_chars = 10000

    # Mock memories_manager
    agent.memories_manager = Mock()

    return agent


class TestLegacyMemoryTools:
    """Test cases for legacy memory tools backward compatibility."""

    @pytest.fixture
    def write_tool(self, mock_agent):
        """Create WriteMemoryTool instance."""
        return WriteMemoryTool(mock_agent)

    @pytest.fixture
    def read_tool(self, mock_agent):
        """Create ReadMemoryTool instance."""
        return ReadMemoryTool(mock_agent)

    @pytest.fixture
    def list_tool(self, mock_agent):
        """Create ListMemoriesTool instance."""
        return ListMemoriesTool(mock_agent)

    @pytest.fixture
    def delete_tool(self, mock_agent):
        """Create DeleteMemoryTool instance."""
        return DeleteMemoryTool(mock_agent)

    def test_write_memory_deprecation_warning(self, write_tool, mock_agent):
        """Test that WriteMemoryTool shows deprecation warning."""
        mock_agent.memories_manager.save_memory.return_value = "Memory saved successfully"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = write_tool.apply("test_memory", "test content")

            # Check that deprecation warning was raised
            assert len(w) == 1
            assert issubclass(w[0].category, LegacyMemoryWarning)
            assert "deprecated" in str(w[0].message).lower()
            assert "docs/ folder" in str(w[0].message)

        # Should still work functionally
        mock_agent.memories_manager.save_memory.assert_called_once_with("test_memory", "test content")
        assert result == "Memory saved successfully"

    def test_read_memory_deprecation_warning(self, read_tool, mock_agent):
        """Test that ReadMemoryTool shows deprecation warning."""
        mock_agent.memories_manager.load_memory.return_value = "Memory content"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = read_tool.apply("test_memory")

            # Check that deprecation warning was raised
            assert len(w) == 1
            assert issubclass(w[0].category, LegacyMemoryWarning)
            assert "deprecated" in str(w[0].message).lower()

        # Should still work functionally
        mock_agent.memories_manager.load_memory.assert_called_once_with("test_memory")
        assert result == "Memory content"

    def test_list_memories_deprecation_warning(self, list_tool, mock_agent):
        """Test that ListMemoriesTool shows deprecation warning."""
        mock_agent.memories_manager.list_memories.return_value = ["memory1", "memory2"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = list_tool.apply()

            # Check that deprecation warning was raised
            assert len(w) == 1
            assert issubclass(w[0].category, LegacyMemoryWarning)

        # Should still work functionally
        mock_agent.memories_manager.list_memories.assert_called_once()
        assert json.loads(result) == ["memory1", "memory2"]

    def test_delete_memory_deprecation_warning(self, delete_tool, mock_agent):
        """Test that DeleteMemoryTool shows deprecation warning."""
        mock_agent.memories_manager.delete_memory.return_value = "Memory deleted successfully"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = delete_tool.apply("test_memory")

            # Check that deprecation warning was raised
            assert len(w) == 1
            assert issubclass(w[0].category, LegacyMemoryWarning)

        # Should still work functionally
        mock_agent.memories_manager.delete_memory.assert_called_once_with("test_memory")
        assert result == "Memory deleted successfully"

    def test_write_memory_content_length_validation(self, write_tool, mock_agent):
        """Test WriteMemoryTool content length validation."""
        # Mock agent with small max answer chars
        mock_agent.serena_config.default_max_tool_answer_chars = 10

        # Test with content that's too long
        long_content = "This content is way too long for the limit"

        with pytest.raises(ValueError, match="Content for test_memory is too long"):
            write_tool.apply("test_memory", long_content)

    def test_write_memory_uses_default_max_chars(self, write_tool, mock_agent):
        """Test WriteMemoryTool uses default max chars when not specified."""
        mock_agent.memories_manager.save_memory.return_value = "Saved"

        # Should not raise an error for content within default limit
        result = write_tool.apply("test_memory", "short content")

        mock_agent.memories_manager.save_memory.assert_called_once_with("test_memory", "short content")
        assert result == "Saved"

    def test_read_memory_with_custom_max_chars(self, read_tool, mock_agent):
        """Test ReadMemoryTool with custom max chars parameter."""
        mock_agent.memories_manager.load_memory.return_value = "Memory content"

        result = read_tool.apply("test_memory", max_answer_chars=100)

        mock_agent.memories_manager.load_memory.assert_called_once_with("test_memory")
        assert result == "Memory content"

    def test_legacy_memory_warning_class(self):
        """Test LegacyMemoryWarning class properties."""
        warning = LegacyMemoryWarning("Test message")

        assert issubclass(LegacyMemoryWarning, DeprecationWarning)
        assert str(warning) == "Test message"

    def test_deprecation_warning_includes_migration_guidance(self, write_tool, mock_agent):
        """Test that deprecation warnings include migration guidance."""
        mock_agent.memories_manager.save_memory.return_value = "Saved"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            write_tool.apply("test_memory", "content")

            warning_message = str(w[0].message)
            assert "serena-intelligent-memory-redesign.md" in warning_message
            assert "migration guide" in warning_message.lower()

    def test_all_legacy_tools_use_same_warning_function(self, write_tool, read_tool, list_tool, delete_tool, mock_agent):
        """Test that all legacy tools use the same warning function."""
        mock_agent.memories_manager.save_memory.return_value = "Saved"
        mock_agent.memories_manager.load_memory.return_value = "Content"
        mock_agent.memories_manager.list_memories.return_value = []
        mock_agent.memories_manager.delete_memory.return_value = "Deleted"

        # Apply all tools and collect warnings
        warnings_list = []

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            write_tool.apply("test", "content")
            read_tool.apply("test")
            list_tool.apply()
            delete_tool.apply("test")

            warnings_list = [str(warning.message) for warning in w]

        # All warnings should mention deprecation and migration
        for warning_msg in warnings_list:
            assert "deprecated" in warning_msg.lower()
            assert "docs/ folder" in warning_msg

    def test_backward_compatibility_maintained(self, write_tool, read_tool, list_tool, delete_tool, mock_agent):
        """Test that legacy tools maintain backward compatibility."""
        # Setup mock responses
        mock_agent.memories_manager.save_memory.return_value = "Memory saved"
        mock_agent.memories_manager.load_memory.return_value = "Memory content"
        mock_agent.memories_manager.list_memories.return_value = ["memory1", "memory2"]
        mock_agent.memories_manager.delete_memory.return_value = "Memory deleted"

        # Test all operations work as expected
        write_result = write_tool.apply("test_memory", "test content")
        assert write_result == "Memory saved"
        mock_agent.memories_manager.save_memory.assert_called_with("test_memory", "test content")

        read_result = read_tool.apply("test_memory")
        assert read_result == "Memory content"
        mock_agent.memories_manager.load_memory.assert_called_with("test_memory")

        list_result = list_tool.apply()
        assert json.loads(list_result) == ["memory1", "memory2"]
        mock_agent.memories_manager.list_memories.assert_called_once()

        delete_result = delete_tool.apply("test_memory")
        assert delete_result == "Memory deleted"
        mock_agent.memories_manager.delete_memory.assert_called_with("test_memory")

    def test_legacy_tools_docstrings_contain_deprecation_notice(self, write_tool, read_tool, list_tool, delete_tool):
        """Test that legacy tools have deprecation notices in docstrings."""
        # Check WriteMemoryTool
        assert "DEPRECATED" in WriteMemoryTool.__doc__
        assert "deprecated" in WriteMemoryTool.apply.__doc__

        # Check ReadMemoryTool
        assert "DEPRECATED" in ReadMemoryTool.__doc__
        assert "deprecated" in ReadMemoryTool.apply.__doc__

        # Check ListMemoriesTool
        assert "DEPRECATED" in ListMemoriesTool.__doc__
        assert "deprecated" in ListMemoriesTool.apply.__doc__

        # Check DeleteMemoryTool
        assert "DEPRECATED" in DeleteMemoryTool.__doc__
        assert "deprecated" in DeleteMemoryTool.apply.__doc__

    def test_legacy_tools_inherit_from_tool_base(self, write_tool, read_tool, list_tool, delete_tool):
        """Test that legacy tools properly inherit from Tool base class."""
        from serena.tools.tools_base import Tool

        assert isinstance(write_tool, Tool)
        assert isinstance(read_tool, Tool)
        assert isinstance(list_tool, Tool)
        assert isinstance(delete_tool, Tool)

        # Check they have the required apply method
        assert hasattr(write_tool, "apply")
        assert hasattr(read_tool, "apply")
        assert hasattr(list_tool, "apply")
        assert hasattr(delete_tool, "apply")
