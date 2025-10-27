"""Core execution engine components."""
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ExecutionPhase(Enum):
    """Execution phases for tool execution."""

    PRE_VALIDATION = "pre_validation"
    PRE_EXECUTION = "pre_execution"
    EXECUTION = "execution"
    POST_EXECUTION = "post_execution"


@dataclass
class ExecutionContext:
    """Complete execution context with audit trail."""

    # Tool information
    tool_name: str
    kwargs: dict[str, Any]
    execution_plan: Any | None = None

    # Timing
    start_time: float = 0.0
    end_time: float = 0.0
    phase: ExecutionPhase = ExecutionPhase.PRE_VALIDATION

    # Constraint tracking (Epic-001)
    constraint_violations: list[str] | None = None
    should_batch: bool = False

    # Execution results
    result: str | None = None
    error: Exception | None = None

    # Token tracking (TPST core)
    estimated_tokens: int = 0
    actual_tokens: int = 0

    def to_audit_record(self) -> dict[str, Any]:
        """Convert to audit record for TPST analysis."""
        return {
            "tool": self.tool_name,
            "phase": self.phase.value,
            "duration": self.end_time - self.start_time,
            "tokens": self.actual_tokens,
            "success": self.error is None,
            "constraints": self.constraint_violations or [],
            "batched": self.should_batch,
        }
