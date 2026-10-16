"""Safe application errors that do not expose prompts or returned values."""


class AgentError(Exception):
    """Base class for agent failures."""


class AgentExecutionError(AgentError):
    """SDK initialization, execution, or resource cleanup failed."""


class AgentMissingResponseError(AgentError):
    """The agent returned no final response."""


class AgentInvalidOutputError(AgentError):
    """The final response was invalid JSON or failed model validation."""
