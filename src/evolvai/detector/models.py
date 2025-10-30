"""Data models for project area detection."""

from dataclasses import dataclass


@dataclass
class ProjectArea:
    """Represents a detected project area with associated metadata.

    A ProjectArea defines a logical section of a codebase that uses
    a specific programming language and has its own build configuration
    and file organization patterns.
    """

    name: str  # Area identifier (e.g., "backend-go")
    language: str  # Language name (e.g., "go", "typescript")
    root_path: str  # Absolute path to area root
    confidence: str  # "High", "Medium", or "Low"
    evidence: list[str]  # Supporting evidence list
    file_patterns: list[str]  # Include glob patterns
    exclude_patterns: list[str]  # Exclude glob patterns
