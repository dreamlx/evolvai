"""
Serena Intelligent Memory System

This package provides intelligent memory capabilities focused on AI tool optimization,
not generic knowledge storage. It learns from user interactions to improve
AI tool selection, command generation, and environment adaptation.

Core Components:
- EnvironmentPreferenceMemory: Shell, Python, Node.js preferences
- CodingStandardsMemory: Naming conventions, code style preferences
- ToolPreferenceMemory: Tool usage patterns and effectiveness
- ProjectContextMemory: Project feature associations

Design Philosophy: KISS principle - simple, effective, focused.
"""

from .environment_preferences import EnvironmentPreferenceMemory

__all__ = ["EnvironmentPreferenceMemory"]
