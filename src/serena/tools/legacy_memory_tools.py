"""
Legacy memory tools - DEPRECATED

This module provides backward compatibility for existing memory functionality.
These tools are deprecated and will be replaced by the new intelligent memory system.

Migration Guide:
- Use docs/ folder for project documentation instead of memory storage
- New intelligent memory system will focus on AI tool optimization
- See docs/serena-intelligent-memory-redesign.md for details

TODO: 未来讨论内部记忆模块时候需要重构
- 当前实现作为向后兼容保留，但不再通过MCP暴露
- Memory应该重构为纯内部API，专注AI助手上下文管理
- 需要评估与SerenaIntelligentMemory的整合方案
- 讨论是否保留文件系统存储或改为更高效的内部存储
"""

import json
import warnings

from serena.tools import Tool


class LegacyMemoryWarning(DeprecationWarning):
    """Warning for deprecated legacy memory functionality"""


def _show_deprecation_warning(alternative: str | None = None) -> None:
    """Show deprecation warning with migration guidance"""
    message = "Legacy memory tools are deprecated. "
    if alternative:
        message += f"Use {alternative} instead. "
    message += "See docs/serena-intelligent-memory-redesign.md for migration guide."
    warnings.warn(message, LegacyMemoryWarning, stacklevel=3)


class WriteMemoryTool(Tool):
    """
    [DEPRECATED] Writes a named memory to Serena's project-specific memory store.

    This tool is deprecated and will be removed in a future version.
    Consider using project docs/ folder for documentation storage.
    """

    def apply(self, memory_name: str, content: str, max_answer_chars: int = -1) -> str:
        """
        [DEPRECATED] Write some information to memory.

        Migration: Use docs/ folder for project documentation instead.
        """
        _show_deprecation_warning("docs/ folder for project documentation")

        # NOTE: utf-8 encoding is configured in the MemoriesManager
        if max_answer_chars == -1:
            max_answer_chars = self.agent.serena_config.default_max_tool_answer_chars
        if len(content) > max_answer_chars:
            raise ValueError(
                f"Content for {memory_name} is too long. Max length is {max_answer_chars} characters. " + "Please make the content shorter."
            )

        return self.memories_manager.save_memory(memory_name, content)


class ReadMemoryTool(Tool):
    """
    [DEPRECATED] Reads the memory with the given name from Serena's project-specific memory store.

    This tool is deprecated and will be removed in a future version.
    Consider using project docs/ folder for documentation storage.
    """

    def apply(self, memory_file_name: str, max_answer_chars: int = -1) -> str:
        """
        [DEPRECATED] Read the content of a memory file.

        Migration: Use docs/ folder for project documentation instead.
        """
        _show_deprecation_warning("docs/ folder for project documentation")
        return self.memories_manager.load_memory(memory_file_name)


class ListMemoriesTool(Tool):
    """
    [DEPRECATED] Lists memories in Serena's project-specific memory store.

    This tool is deprecated and will be removed in a future version.
    Consider using project docs/ folder for documentation storage.
    """

    def apply(self) -> str:
        """
        [DEPRECATED] List available memories.

        Migration: Use docs/ folder for project documentation instead.
        """
        _show_deprecation_warning("docs/ folder for project documentation")
        return json.dumps(self.memories_manager.list_memories())


class DeleteMemoryTool(Tool):
    """
    [DEPRECATED] Deletes a memory from Serena's project-specific memory store.

    This tool is deprecated and will be removed in a future version.
    Consider using project docs/ folder for documentation storage.
    """

    def apply(self, memory_file_name: str) -> str:
        """
        [DEPRECATED] Delete a memory file.

        Migration: Use docs/ folder for project documentation instead.
        """
        _show_deprecation_warning("docs/ folder for project documentation")
        return self.memories_manager.delete_memory(memory_file_name)
