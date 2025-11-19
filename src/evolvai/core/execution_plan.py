"""ExecutionPlan schema and related data structures.

Core data structures for Epic-001 behavior constraints system.
All tool executions will eventually conform to this schema.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RollbackStrategyType(str, Enum):
    """Rollback strategy types."""

    GIT_REVERT = "git_revert"
    FILE_BACKUP = "file_backup"
    MANUAL = "manual"


class ExecutionLimits(BaseModel):
    """Execution limits configuration."""

    max_files: int = Field(default=10, ge=1, le=100, description="Max files")
    max_changes: int = Field(default=50, ge=1, le=1000, description="Max changes")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Timeout (s)")


class ValidationConfig(BaseModel):
    """Validation configuration."""

    pre_conditions: list[str] = Field(default_factory=list, description="Pre-conditions")
    expected_outcomes: list[str] = Field(default_factory=list, description="Expected outcomes")


class RollbackStrategy(BaseModel):
    """Rollback strategy configuration."""

    strategy: RollbackStrategyType = Field(..., description="Strategy type")
    commands: list[str] = Field(default_factory=list, description="Rollback commands")

    @field_validator("commands")
    @classmethod
    def validate_commands(cls, v: list[str], info) -> list[str]:
        """Validate that manual rollback strategy has commands.

        :param v: Commands list
        :param info: Validation context with field values
        :return: Validated commands list
        :raises ValueError: If manual strategy has no commands
        """
        # Get strategy value from validation context
        strategy = info.data.get("strategy")
        if strategy == RollbackStrategyType.MANUAL and not v:
            raise ValueError("Manual rollback strategy requires commands")
        return v


class ExecutionPlan(BaseModel):
    """Execution plan constitution."""

    dry_run: bool = Field(default=True, description="Preview mode")
    validation: ValidationConfig = Field(default_factory=ValidationConfig, description="Validation config")
    rollback: RollbackStrategy = Field(..., description="Rollback strategy")
    limits: ExecutionLimits = Field(default_factory=ExecutionLimits, description="Execution limits")
    batch: bool = Field(default=False, description="Batch mode")
