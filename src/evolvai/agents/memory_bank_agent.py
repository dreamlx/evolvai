"""Memory Bank Agent - Lightweight wrapper for Memory Bank MCP operations.

This agent optimizes TPST by providing intelligent, priority-based loading
of project context from Memory Bank, reducing new window startup tokens
from 16-23K to 4.5-7.5K (60-70% reduction).

Phase 1 (Current): Lightweight wrapper with basic intelligence
- Pre-Flight Validation
- Priority-based loading (P0/P1/P2)
- Simple update detection

Phase 2 (Future): Enhanced intelligence
- Code change detection (≥25% trigger)
- Pattern recognition and learning
- Integration with other agents
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Priority(str, Enum):
    """File priority levels for smart loading."""

    P0 = "P0"  # Always load (project brief, current sprint)
    P1 = "P1"  # Load for common tasks (tech context, dev rules)
    P2 = "P2"  # Load for specific needs (patterns, quick notes)


class TaskType(str, Enum):
    """Task types that determine loading strategy."""

    NEW_SESSION = "new_session"  # New window startup
    FEATURE_DEV = "feature_dev"  # Implementing features
    DEBUG = "debug"  # Debugging issues
    REFACTOR = "refactor"  # Code refactoring
    ARCHITECTURE = "architecture"  # Architecture/design work


@dataclass
class ValidationResult:
    """Result of Pre-Flight Validation."""

    project_exists: bool
    missing_files: list[str]  # P0 files that are missing
    status: str  # "ready" | "needs_init" | "incomplete"
    message: str


@dataclass
class LoadResult:
    """Result of Smart Load operation."""

    loaded_files: dict[str, str]  # {fileName: content}
    total_tokens: int  # Estimated token count
    priorities_used: list[str]  # ["P0", "P1"]
    load_strategy: str  # Description of what was loaded


class MemoryBankAgent:
    """Lightweight Memory Bank agent for TPST optimization.

    This agent provides intelligent loading of Memory Bank files based on
    task type and file priorities, reducing token consumption during
    new window startup and task execution.

    Usage:
        agent = MemoryBankAgent(mcp_tools)

        # Check project status
        validation = agent.pre_flight_validation("serena")

        # Smart load for new session
        result = agent.smart_load("serena", TaskType.NEW_SESSION)

        # Access loaded content
        project_brief = result.loaded_files["projectbrief.md"]
    """

    # File priority configuration
    FILE_PRIORITIES = {
        "projectbrief.md": Priority.P0,
        "current-sprint.md": Priority.P0,
        "tech-context.md": Priority.P1,
        "development-rules.md": Priority.P1,
        "system-patterns.md": Priority.P2,
        "quick-notes.md": Priority.P2,
    }

    # Task-specific loading strategies
    LOAD_STRATEGIES = {
        TaskType.NEW_SESSION: [Priority.P0],
        TaskType.FEATURE_DEV: [Priority.P0, Priority.P1],
        TaskType.DEBUG: [Priority.P0, Priority.P1],
        TaskType.REFACTOR: [Priority.P0, Priority.P1],
        TaskType.ARCHITECTURE: [Priority.P0, Priority.P1, Priority.P2],
    }

    # Token estimation (approximate characters / 4)
    ESTIMATED_TOKENS = {
        "projectbrief.md": 1500,
        "current-sprint.md": 1000,
        "tech-context.md": 2000,
        "development-rules.md": 2500,
        "system-patterns.md": 2500,
        "quick-notes.md": 500,
    }

    def __init__(self, mcp_tools: dict[str, Any]):
        """Initialize Memory Bank Agent.

        Args:
            mcp_tools: Dictionary of Memory Bank MCP tools
                - list_projects
                - list_project_files
                - memory_bank_read
                - memory_bank_write
                - memory_bank_update
        """
        self.mcp_tools = mcp_tools
        logger.info("MemoryBankAgent initialized")

    def pre_flight_validation(self, project_name: str) -> ValidationResult:
        """Check project and core files completeness.

        This ensures the Memory Bank is properly initialized before
        attempting to load files.

        Args:
            project_name: Name of the project to validate

        Returns:
            ValidationResult with project status and missing files
        """
        logger.info(f"Running pre-flight validation for project: {project_name}")

        try:
            # Check if project exists
            projects_result = self.mcp_tools["list_projects"]()
            projects = projects_result.get("projects", [])

            if project_name not in projects:
                return ValidationResult(
                    project_exists=False,
                    missing_files=[],
                    status="needs_init",
                    message=f"Project '{project_name}' not found in Memory Bank. "
                    f"Available projects: {projects}",
                )

            # Check P0 files presence
            files_result = self.mcp_tools["list_project_files"](
                projectName=project_name
            )
            existing_files = files_result.get("files", [])

            p0_files = [
                fname
                for fname, priority in self.FILE_PRIORITIES.items()
                if priority == Priority.P0
            ]
            missing_files = [f for f in p0_files if f not in existing_files]

            if missing_files:
                return ValidationResult(
                    project_exists=True,
                    missing_files=missing_files,
                    status="incomplete",
                    message=f"Project exists but missing P0 files: {missing_files}",
                )

            return ValidationResult(
                project_exists=True,
                missing_files=[],
                status="ready",
                message=f"Project '{project_name}' is ready. "
                f"Found {len(existing_files)} files.",
            )

        except Exception as e:
            logger.error(f"Pre-flight validation failed: {e}")
            return ValidationResult(
                project_exists=False,
                missing_files=[],
                status="error",
                message=f"Validation error: {str(e)}",
            )

    def smart_load(
        self, project_name: str, task_type: TaskType = TaskType.NEW_SESSION
    ) -> LoadResult:
        """Smart load Memory Bank files based on task type and priorities.

        This implements the core TPST optimization by loading only the
        files needed for the current task type.

        Loading Strategy:
        - NEW_SESSION: P0 only (~2.5K tokens)
        - FEATURE_DEV/DEBUG/REFACTOR: P0 + P1 (~6.5K tokens)
        - ARCHITECTURE: P0 + P1 + P2 (~9K tokens)

        Args:
            project_name: Name of the project
            task_type: Type of task to optimize loading for

        Returns:
            LoadResult with loaded files and metadata
        """
        logger.info(f"Smart loading for project '{project_name}', task: {task_type}")

        # Determine which priorities to load
        priorities_to_load = self.LOAD_STRATEGIES.get(
            task_type, [Priority.P0, Priority.P1]
        )

        # Filter files by priority
        files_to_load = [
            fname
            for fname, priority in self.FILE_PRIORITIES.items()
            if priority in priorities_to_load
        ]

        # Load files
        loaded_files = {}
        total_tokens = 0

        for fname in files_to_load:
            try:
                result = self.mcp_tools["memory_bank_read"](
                    projectName=project_name, fileName=fname
                )
                content = result.get("content", "")
                loaded_files[fname] = content

                # Estimate tokens
                tokens = self.ESTIMATED_TOKENS.get(fname, len(content) // 4)
                total_tokens += tokens

                logger.debug(f"Loaded {fname} (~{tokens} tokens)")

            except Exception as e:
                logger.warning(f"Failed to load {fname}: {e}")
                # Continue loading other files

        # Generate load strategy description
        priority_names = [p.value for p in priorities_to_load]
        strategy = self._get_strategy_description(task_type, priority_names)

        return LoadResult(
            loaded_files=loaded_files,
            total_tokens=total_tokens,
            priorities_used=priority_names,
            load_strategy=strategy,
        )

    def update_if_needed(
        self, project_name: str, trigger: str = "user_request"
    ) -> bool:
        """Check if Memory Bank update is needed.

        Phase 1 (Current): Simple rule-based triggers
        - user_request: User explicitly requests update

        Phase 2 (Future): Intelligent triggers
        - code_change_detection: ≥25% code change
        - pattern_recognition: New patterns discovered

        Args:
            project_name: Name of the project
            trigger: Update trigger type

        Returns:
            True if update should be performed
        """
        logger.info(f"Checking update for project '{project_name}', trigger: {trigger}")

        if trigger == "user_request":
            return True

        # Future: Add intelligent detection here
        # - Git diff analysis
        # - Pattern change detection
        # - Time-based updates

        return False

    def _get_strategy_description(
        self, task_type: TaskType, priorities: list[str]
    ) -> str:
        """Generate human-readable strategy description."""
        descriptions = {
            TaskType.NEW_SESSION: "Minimal startup (project brief + current sprint)",
            TaskType.FEATURE_DEV: "Feature development (+ tech context + dev rules)",
            TaskType.DEBUG: "Debugging (+ tech context + dev rules)",
            TaskType.REFACTOR: "Refactoring (+ tech context + dev rules)",
            TaskType.ARCHITECTURE: "Architecture work (full context including patterns)",
        }
        return descriptions.get(
            task_type, f"Custom load with priorities: {', '.join(priorities)}"
        )

    def get_file_priority(self, file_name: str) -> Priority | None:
        """Get priority level for a file.

        Args:
            file_name: Name of the file

        Returns:
            Priority level or None if file not in configuration
        """
        return self.FILE_PRIORITIES.get(file_name)

    def estimate_tokens(self, files: list[str]) -> int:
        """Estimate total tokens for a list of files.

        Args:
            files: List of file names

        Returns:
            Estimated token count
        """
        return sum(self.ESTIMATED_TOKENS.get(f, 0) for f in files)
