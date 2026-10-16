"""Synchronous Codex SDK adapter using existing local authentication."""

from pathlib import Path

from openai_codex import (
    ApprovalMode,
    Codex,
    InvalidParamsError,
    JsonRpcError,
    MethodNotFoundError,
    Sandbox,
    ServerBusyError,
    TransportClosedError,
)
from openai_codex.generated.v2_all import TurnStatus
from pydantic import BaseModel, ValidationError

from devforge.agents.errors import (
    AgentError,
    AgentExecutionError,
    AgentInvalidOutputError,
    AgentMissingResponseError,
)


def _execution_error(stage: str, error: Exception) -> AgentExecutionError:
    """Translate SDK failures without copying untrusted messages or payloads."""
    advice = "Check Codex sign-in, usage limits, and response schema compatibility."
    if isinstance(error, FileNotFoundError):
        advice = "Reinstall openai-codex to restore its bundled Codex runtime."
    elif isinstance(error, TransportClosedError):
        advice = "The Codex connection closed. Check the local runtime and retry."
    elif isinstance(error, ServerBusyError):
        advice = "Codex is temporarily unavailable. Retry later."
    elif isinstance(error, MethodNotFoundError):
        advice = "The runtime does not support this operation. Update openai-codex."
    elif isinstance(error, InvalidParamsError):
        advice = (
            "Check the response schema and options supported by this Codex runtime."
        )

    if isinstance(error, JsonRpcError) and isinstance(error.data, dict):
        # Match only documented codes; never include arbitrary server strings.
        code = error.data.get("codexErrorInfo", error.data.get("codex_error_info"))
        if isinstance(code, str):
            advice = {
                "unauthorized": "Codex authentication failed. Run `codex login` again.",
                "usageLimitExceeded": "Codex usage exhausted. Check your plan limits.",
                "rateLimitExceeded": "Rate limited. Retry after the limit resets.",
                "contextWindowExceeded": "Reduce the prompt or context and retry.",
            }.get(code, advice)
    if stage == "cleanup":
        advice = "Check for a remaining Codex runtime process before retrying."
    return AgentExecutionError(
        f"Codex {stage} failed ({type(error).__name__}). {advice}"
    )


class CodexAgent:
    """One fresh read-only thread per call; no application session state."""

    def run[T: BaseModel](
        self, prompt: str, response_model: type[T], *, working_directory: Path
    ) -> T:
        """Execute and validate a response, closing SDK resources before returning."""
        try:
            directory = working_directory.resolve(strict=True)
            if not directory.is_dir():
                raise ValueError
        except (OSError, ValueError, RuntimeError):
            raise ValueError(
                "Working directory must be an explicitly supplied existing directory."
            ) from None

        schema = response_model.model_json_schema()
        stage = "initialization"
        codex = None
        try:
            # Read existing authentication without logging in or changing it.
            codex = Codex()
            stage = "authentication check"
            account = codex.account().account
            if account is None:
                raise AgentExecutionError(
                    "Codex is not signed in. "
                    "Run `codex login` with your ChatGPT account."
                )
            if account.root.type != "chatgpt":
                raise AgentExecutionError(
                    "DevForge requires ChatGPT authentication to avoid API billing. "
                    "Run `codex login` with your ChatGPT account."
                )
            stage = "thread creation"
            thread = codex.thread_start(
                cwd=str(directory),
                sandbox=Sandbox.read_only,
                approval_mode=ApprovalMode.deny_all,
            )
            stage = "execution"
            result = thread.run(prompt, output_schema=schema)
            if result.status == TurnStatus.interrupted:
                raise AgentExecutionError(
                    "Codex execution was interrupted. Retry when ready."
                )
            if result.status != TurnStatus.completed:
                raise AgentExecutionError(
                    "Codex execution did not complete. "
                    "Check Codex status before retrying."
                )
        except BaseException as error:
            # Explicit close preserves the primary failure if cleanup also fails,
            # including KeyboardInterrupt and SystemExit.
            primary = (
                _execution_error(stage, error)
                if isinstance(error, Exception) and not isinstance(error, AgentError)
                else error
            )
            if codex is not None:
                try:
                    codex.close()
                except Exception as cleanup_error:
                    primary.add_note(
                        f"Codex cleanup also failed ({type(cleanup_error).__name__}). "
                        "Check for a remaining Codex runtime process."
                    )
            if primary is error:
                raise
            raise primary from None
        else:
            try:
                codex.close()
            except Exception as error:
                raise _execution_error("cleanup", error) from None

        response = result.final_response
        if response is None or not response.strip():
            raise AgentMissingResponseError("Codex returned no final response.")
        try:
            return response_model.model_validate_json(response)
        except ValidationError as error:
            reason = (
                "invalid JSON"
                if any(item["type"] == "json_invalid" for item in error.errors())
                else "output does not satisfy the requested response model"
            )
            raise AgentInvalidOutputError(f"Codex returned {reason}.") from None
