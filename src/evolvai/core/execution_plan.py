"""ExecutionPlan schema and related data structures.

Core data structures for Epic-001 behavior constraints system.
All tool executions will eventually conform to this schema.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RollbackStrategyType(str, Enum):
    """Rollback strategy types.

    Defines available rollback strategies for tool execution failures.
    """

    GIT_REVERT = "git_revert"
    FILE_BACKUP = "file_backup"
    MANUAL = "manual"


class ExecutionLimits(BaseModel):
    """Execution limits configuration.

    Defines resource limits for tool execution to prevent runaway operations.
    """

    max_files: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of files to process",
    )
    max_changes: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of changes to perform",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Execution timeout in seconds",
    )


class ValidationConfig(BaseModel):
    """Validation configuration.

    Defines pre-conditions and expected outcomes for tool execution validation.
    """

    pre_conditions: list[str] = Field(
        default_factory=list,
        description="Pre-conditions that must be satisfied before execution",
    )
    expected_outcomes: list[str] = Field(
        default_factory=list,
        description="Expected outcomes after execution",
    )


class RollbackStrategy(BaseModel):
    """Rollback strategy configuration.

    Defines how to rollback tool execution in case of failure.
    """

    strategy: RollbackStrategyType = Field(
        ...,
        description="Rollback strategy type",
    )
    commands: list[str] = Field(
        default_factory=list,
        description="Rollback commands to execute",
    )

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
    """Execution plan constitution.

    All tool executions must conform to this constraint specification.
    This is the core schema for Epic-001 behavior constraints system.
    """

    dry_run: bool = Field(
        default=True,
        description="Whether to preview execution without actually performing it",
    )
    validation: ValidationConfig = Field(
        default_factory=ValidationConfig,
        description="Validation configuration",
    )
    rollback: RollbackStrategy = Field(
        ...,
        description="Rollback strategy (required)",
    )
    limits: ExecutionLimits = Field(
        default_factory=ExecutionLimits,
        description="Execution limits",
    )
    batch: bool = Field(
        default=False,
        description="Whether to batch multiple operations",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "dry_run": True,
                    "rollback": {
                        "strategy": "git_revert",
                        "commands": [],
                    },
                    "limits": {
                        "max_files": 10,
                        "max_changes": 50,
                        "timeout_seconds": 30,
                    },
                }
            ]
        }
    }
