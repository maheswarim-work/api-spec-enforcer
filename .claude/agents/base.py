"""Base agent class for the multi-agent system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from mcp.context_provider import Context


class AgentStatus(str, Enum):
    """Status of an agent execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class AgentResult:
    """Result of an agent execution."""

    agent_name: str
    status: AgentStatus
    output: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        """Calculate execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


class Agent(ABC):
    """Base class for all agents in the system.

    Each agent has a specific responsibility and receives only the context
    it needs (following MCP principles). Agents can be composed into
    workflows where the output of one agent feeds into another.
    """

    def __init__(self, name: str) -> None:
        """Initialize the agent.

        Args:
            name: Human-readable name for the agent.
        """
        self.name = name
        self._context: Context | None = None
        self._result: AgentResult | None = None

    @property
    def context(self) -> Context | None:
        """Get the current context."""
        return self._context

    @property
    def result(self) -> AgentResult | None:
        """Get the last execution result."""
        return self._result

    def set_context(self, context: Context) -> None:
        """Set the context for this agent.

        Args:
            context: Context object with relevant information.
        """
        self._context = context

    def execute(self, **kwargs: Any) -> AgentResult:
        """Execute the agent's task.

        Args:
            **kwargs: Additional arguments for the agent.

        Returns:
            AgentResult with the execution outcome.
        """
        started_at = datetime.now()

        try:
            output = self.run(**kwargs)
            self._result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.SUCCESS,
                output=output,
                started_at=started_at,
                completed_at=datetime.now(),
            )
        except Exception as e:
            self._result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now(),
            )

        return self._result

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Run the agent's main logic.

        Args:
            **kwargs: Additional arguments for the agent.

        Returns:
            Output of the agent's execution.

        Raises:
            Exception: If the agent fails to execute.
        """
        pass

    @abstractmethod
    def get_required_context_types(self) -> list[str]:
        """Get the context types required by this agent.

        Returns:
            List of ContextType values needed.
        """
        pass

    def format_output(self) -> str:
        """Format the agent's output for display.

        Returns:
            Human-readable string representation of the output.
        """
        if self._result is None:
            return f"{self.name}: No result available"

        if self._result.status == AgentStatus.FAILED:
            return f"{self.name}: FAILED - {self._result.error}"

        return f"{self.name}: SUCCESS"
