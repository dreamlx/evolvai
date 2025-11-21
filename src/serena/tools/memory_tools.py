"""
Memory Tools - DEPRECATED

This module is deprecated and will be removed in a future release.
Use serena.tools.legacy_memory_tools for backward compatibility.
See docs/serena-intelligent-memory-redesign.md for the new intelligent memory system.

DEPRECATION SCHEDULE:
- Version 0.4.0: Deprecated warnings added
- Version 0.5.0: Tools will be removed
- Migration: Use docs/ folder for documentation, new intelligent memory for AI optimization

TODO: 未来讨论内部记忆模块时候需要重构
- Memory应该作为AI助手内部机制，不暴露为MCP工具
- 需要重新设计internal memory API，专注于AI上下文和经验积累
- 考虑与Epic-003 Graph-of-Thought引擎的集成
- 讨论memory的持久化策略和会话管理机制
"""

import json
import warnings
from typing import Literal

from serena.tools import ReplaceContentTool, Tool


class MemoryModuleDeprecationWarning(DeprecationWarning):
    """Warning for deprecated memory module functionality"""


def _show_deprecation_message() -> None:
    """Show deprecation warning with migration guidance"""
    message = (
        "Serena memory module is deprecated. "
        "The new intelligent memory system focuses on AI tool optimization. "
        "For project documentation, use docs/ folder. "
        "See docs/serena-intelligent-memory-redesign.md for details."
    )
    warnings.warn(message, MemoryModuleDeprecationWarning, stacklevel=3)


class WriteMemoryTool(Tool):
    """
    [DEPRECATED] Writes a named memory (for future reference) to Serena's project-specific memory store.

    DEPRECATED: Use docs/ folder for project documentation.
    New intelligent memory system coming in Phase 2.
    """

    def apply(self, memory_file_name: str, content: str, max_answer_chars: int = -1) -> str:
        """
        [DEPRECATED] Write some information to memory.

        DEPRECATED: Use docs/ folder for project documentation.
        """
        _show_deprecation_message()

        # NOTE: utf-8 encoding is configured in the MemoriesManager
        if max_answer_chars == -1:
            max_answer_chars = self.agent.serena_config.default_max_tool_answer_chars
        if len(content) > max_answer_chars:
            raise ValueError(
                f"Content for {memory_file_name} is too long. Max length is {max_answer_chars} characters. "
                + "Please make the content shorter."
            )

        return self.memories_manager.save_memory(memory_file_name, content)


class ReadMemoryTool(Tool):
    """
    [DEPRECATED] Reads the memory with the given name from Serena's project-specific memory store.

    DEPRECATED: Use docs/ folder for project documentation.
    New intelligent memory system coming in Phase 2.
    """

    def apply(self, memory_file_name: str, max_answer_chars: int = -1) -> str:
        """
        [DEPRECATED] Read the content of a memory file.

        DEPRECATED: Use docs/ folder for project documentation.
        """
        _show_deprecation_message()
        return self.memories_manager.load_memory(memory_file_name)


class ListMemoriesTool(Tool):
    """
    [DEPRECATED] Lists memories in Serena's project-specific memory store.

    DEPRECATED: Use docs/ folder for project documentation.
    New intelligent memory system coming in Phase 2.
    """

    def apply(self) -> str:
        """
        [DEPRECATED] List available memories.

        DEPRECATED: Use docs/ folder for project documentation.
        """
        _show_deprecation_message()
        return json.dumps(self.memories_manager.list_memories())


class DeleteMemoryTool(Tool):
    """
    [DEPRECATED] Deletes a memory from Serena's project-specific memory store.

    DEPRECATED: Use docs/ folder for project documentation.
    New intelligent memory system coming in Phase 2.
    """

    def apply(self, memory_file_name: str) -> str:
        """
        [DEPRECATED] Delete a memory file.

        DEPRECATED: Use docs/ folder for project documentation.
        """
        _show_deprecation_message()
        return self.memories_manager.delete_memory(memory_file_name)


class EditMemoryTool(Tool):
    def apply(
        self,
        memory_file_name: str,
        needle: str,
        repl: str,
        mode: Literal["literal", "regex"],
    ) -> str:
        r"""
        Replaces content matching a regular expression in a memory.

        :param memory_file_name: the name of the memory
        :param needle: the string or regex pattern to search for.
            If `mode` is "literal", this string will be matched exactly.
            If `mode` is "regex", this string will be treated as a regular expression (syntax of Python's `re` module,
            with flags DOTALL and MULTILINE enabled).
        :param repl: the replacement string (verbatim).
        :param mode: either "literal" or "regex", specifying how the `needle` parameter is to be interpreted.
        """
        replace_content_tool = self.agent.get_tool(ReplaceContentTool)
        rel_path = self.memories_manager.get_memory_file_path(memory_file_name).relative_to(self.get_project_root())
        return replace_content_tool.replace_content(str(rel_path), needle, repl, mode=mode, require_not_ignored=False)
