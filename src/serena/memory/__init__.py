"""
Serena Intelligent Memory System

This package provides intelligent memory capabilities focused on AI tool optimization,
not generic knowledge storage. It learns from user interactions to improve
AI tool selection, command generation, and environment adaptation.

Core Components:
- EnvironmentPreferenceMemory: Shell, Python, Node.js preferences
- CodingStandardsMemory: Naming conventions, code style preferences
- SerenaIntelligentMemory: Unified coordination of all memory components
- ToolPreferenceMemory: Tool usage patterns and effectiveness (future extension)
- ProjectContextMemory: Project feature associations (future extension)

Design Philosophy: KISS principle - simple, effective, focused.
"""

from .coding_standards import CodingStandardsMemory
from .environment_preferences import EnvironmentPreferenceMemory
from .intelligent_memory import SerenaIntelligentMemory

__all__ = ["CodingStandardsMemory", "EnvironmentPreferenceMemory", "SerenaIntelligentMemory"]
