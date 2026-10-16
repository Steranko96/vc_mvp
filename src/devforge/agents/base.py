"""Small SDK-independent interface for dependency injection."""

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class StructuredAgent(Protocol):
    """Consumers accept this protocol so tests can supply a fake agent."""

    def run[T: BaseModel](
        self, prompt: str, response_model: type[T], *, working_directory: Path
    ) -> T:
        """Return validated output using an explicitly supplied existing directory.

        Raise ValueError for an invalid directory, or AgentError for execution,
        missing responses, and invalid output. Never return unvalidated JSON.
        """
        ...
