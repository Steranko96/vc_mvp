"""Adapter tests never start Codex or require authentication or network access."""

import traceback
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from openai_codex import (
    ApprovalMode,
    Codex,
    InvalidParamsError,
    JsonRpcError,
    MethodNotFoundError,
    Sandbox,
    ServerBusyError,
    TransportClosedError,
    TurnResult,
)
from openai_codex.api import Thread
from openai_codex.generated.v2_all import GetAccountResponse, TurnStatus
from pydantic import BaseModel, ConfigDict

from devforge.agents import (
    AgentExecutionError,
    AgentInvalidOutputError,
    AgentMissingResponseError,
    StructuredAgent,
)
from devforge.agents.codex import CodexAgent


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    count: int


@pytest.fixture
def sdk() -> Iterator[MagicMock]:
    with patch("devforge.agents.codex.Codex", autospec=Codex) as factory:
        client = factory.return_value
        client.account.return_value = GetAccountResponse.model_validate(
            {
                "account": {"type": "chatgpt", "email": None, "planType": "plus"},
                "requiresOpenaiAuth": True,
            }
        )
        thread = MagicMock(spec=Thread)
        client.thread_start.return_value = thread
        thread.run.return_value = TurnResult(
            id="test-turn",
            status=TurnStatus.completed,
            error=None,
            started_at=None,
            completed_at=None,
            duration_ms=None,
            final_response='{"summary": "Ready", "count": 2}',
            items=[],
            usage=None,
        )
        yield factory


def test_structured_response_and_configuration(sdk: MagicMock, tmp_path: Path) -> None:
    agent: StructuredAgent = CodexAgent()
    result = agent.run("Summarize", Answer, working_directory=tmp_path)

    assert isinstance(result, Answer)
    assert result == Answer(summary="Ready", count=2)
    sdk.assert_called_once_with()
    client = sdk.return_value
    client.account.assert_called_once_with()
    client.thread_start.assert_called_once_with(
        cwd=str(tmp_path.resolve()),
        sandbox=Sandbox.read_only,
        approval_mode=ApprovalMode.deny_all,
    )
    client.thread_start.return_value.run.assert_called_once_with(
        "Summarize", output_schema=Answer.model_json_schema()
    )
    client.close.assert_called_once_with()


@pytest.mark.parametrize("response", [None, "", " \n\t"])
def test_missing_response(sdk: MagicMock, tmp_path: Path, response: str | None) -> None:
    client = sdk.return_value
    client.thread_start.return_value.run.return_value.final_response = response
    with pytest.raises(AgentMissingResponseError, match="no final response"):
        CodexAgent().run("Summarize", Answer, working_directory=tmp_path)
    client.close.assert_called_once_with()


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        ("not JSON: secret-output", "invalid JSON"),
        ('{"summary": "secret-output",', "invalid JSON"),
        ('{"summary": "secret-output"}', "requested response model"),
        (
            '{"summary": "Ready", "count": "secret-output"}',
            "requested response model",
        ),
        (
            '{"summary": "Ready", "count": 2, "extra": "secret-output"}',
            "requested response model",
        ),
        ("null", "requested response model"),
        ("[]", "requested response model"),
    ],
)
def test_invalid_output_is_sanitized_and_resources_are_closed(
    sdk: MagicMock, tmp_path: Path, response: str, reason: str
) -> None:
    client = sdk.return_value
    client.thread_start.return_value.run.return_value.final_response = response
    prompt = "secret-prompt"
    with pytest.raises(AgentInvalidOutputError, match=reason) as caught:
        CodexAgent().run(prompt, Answer, working_directory=tmp_path)
    rendered = "".join(traceback.format_exception(caught.value))
    assert "secret-output" not in rendered
    assert "secret-prompt" not in rendered
    client.close.assert_called_once_with()


@pytest.mark.parametrize(
    "stage", ["initialization", "authentication check", "thread creation", "execution"]
)
def test_sdk_failure_is_sanitized_and_resources_are_closed(
    sdk: MagicMock, tmp_path: Path, stage: str
) -> None:
    client = sdk.return_value
    error = RuntimeError("secret-credential secret-prompt secret-output")
    if stage == "initialization":
        sdk.side_effect = error
    elif stage == "authentication check":
        client.account.side_effect = error
    elif stage == "thread creation":
        client.thread_start.side_effect = error
    else:
        client.thread_start.return_value.run.side_effect = error

    prompt = "secret-prompt"
    with pytest.raises(
        AgentExecutionError, match=f"{stage} failed.*RuntimeError"
    ) as caught:
        CodexAgent().run(prompt, Answer, working_directory=tmp_path)
    rendered = "".join(traceback.format_exception(caught.value))
    assert "secret-credential" not in rendered
    assert "secret-prompt" not in rendered
    assert "secret-output" not in rendered
    if stage == "initialization":
        # No client was acquired. The SDK cleans up partial initialization.
        client.close.assert_not_called()
    else:
        client.close.assert_called_once_with()


def test_cleanup_failure_is_an_execution_error(sdk: MagicMock, tmp_path: Path) -> None:
    sdk.return_value.close.side_effect = OSError("secret-credential")
    with pytest.raises(AgentExecutionError, match=r"cleanup failed \(OSError\)"):
        CodexAgent().run("Summarize", Answer, working_directory=tmp_path)


@pytest.mark.parametrize(
    "account", [None, {"type": "apiKey"}, {"type": "amazonBedrock"}]
)
def test_authentication_rejected_before_execution(
    sdk: MagicMock, tmp_path: Path, account: dict[str, str] | None
) -> None:
    client = sdk.return_value
    client.account.return_value = GetAccountResponse.model_validate(
        {"account": account, "requiresOpenaiAuth": True}
    )
    with pytest.raises(AgentExecutionError, match="codex login"):
        CodexAgent().run("Summarize", Answer, working_directory=tmp_path)
    client.thread_start.assert_not_called()
    client.close.assert_called_once_with()
    client.login_api_key.assert_not_called()
    client.login_chatgpt.assert_not_called()
    client.logout.assert_not_called()


@pytest.mark.parametrize("status", [TurnStatus.interrupted, TurnStatus.failed])
@pytest.mark.parametrize("response", [None, '{"summary": "Partial", "count": 1}'])
def test_incomplete_turn_never_returns_a_model(
    sdk: MagicMock, tmp_path: Path, status: TurnStatus, response: str | None
) -> None:
    result = sdk.return_value.thread_start.return_value.run.return_value
    result.status = status
    result.final_response = response
    with pytest.raises(AgentExecutionError):
        CodexAgent().run("Summarize", Answer, working_directory=tmp_path)
    sdk.return_value.close.assert_called_once_with()


@pytest.mark.parametrize(
    "error", [RuntimeError("secret-output"), KeyboardInterrupt(), SystemExit(2)]
)
@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_cleanup_failure_preserves_primary_exception(
    sdk: MagicMock, tmp_path: Path, error: BaseException, cleanup_fails: bool
) -> None:
    client = sdk.return_value
    client.thread_start.return_value.run.side_effect = error
    if cleanup_fails:
        client.close.side_effect = OSError("secret-credential")
    expected = AgentExecutionError if isinstance(error, Exception) else type(error)
    with pytest.raises(expected) as caught:
        CodexAgent().run("Summarize", Answer, working_directory=tmp_path)
    if isinstance(error, Exception):
        assert "execution failed (RuntimeError)" in str(caught.value)
    else:
        assert caught.value is error
    if cleanup_fails:
        assert "cleanup also failed (OSError)" in caught.value.__notes__[0]
    rendered = "".join(traceback.format_exception(caught.value))
    assert "secret-credential" not in rendered
    assert "secret-output" not in rendered
    client.close.assert_called_once_with()


@pytest.mark.parametrize(
    ("error", "advice"),
    [
        (FileNotFoundError("secret"), "Reinstall openai-codex"),
        (TransportClosedError("secret"), "connection closed"),
        (ServerBusyError(-32000, "secret"), "Retry later"),
        (MethodNotFoundError(-32601, "secret"), "Update openai-codex"),
        (InvalidParamsError(-32602, "secret"), "response schema"),
        (
            JsonRpcError(-32000, "secret", {"codexErrorInfo": "unauthorized"}),
            "codex login",
        ),
        (
            JsonRpcError(-32000, "secret", {"codexErrorInfo": "usageLimitExceeded"}),
            "plan limits",
        ),
        (
            JsonRpcError(-32000, "secret", {"codexErrorInfo": "rateLimitExceeded"}),
            "limit resets",
        ),
        (
            JsonRpcError(
                -32000, "secret", {"codex_error_info": "contextWindowExceeded"}
            ),
            "Reduce the prompt",
        ),
        (
            JsonRpcError(-32000, "secret", {"codexErrorInfo": "secret"}),
            "schema compatibility",
        ),
        (
            JsonRpcError(-32000, "secret", {"codexErrorInfo": {"secret": "secret"}}),
            "schema compatibility",
        ),
        (RuntimeError("secret"), "usage limits"),
    ],
)
def test_sdk_failure_diagnostics_are_actionable_and_sanitized(
    sdk: MagicMock, tmp_path: Path, error: Exception, advice: str
) -> None:
    sdk.return_value.thread_start.return_value.run.side_effect = error
    prompt = "secret-prompt"
    with pytest.raises(AgentExecutionError, match=advice) as caught:
        CodexAgent().run(prompt, Answer, working_directory=tmp_path)
    assert "secret" not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_invalid_directory_fails_before_sdk_initialization(
    sdk: MagicMock, tmp_path: Path, kind: str
) -> None:
    directory = tmp_path / kind
    if kind == "file":
        directory.write_text("not a directory")
    with pytest.raises(ValueError, match="existing directory"):
        CodexAgent().run("Summarize", Answer, working_directory=directory)
    sdk.assert_not_called()


def test_working_directory_is_required(sdk: MagicMock) -> None:
    with pytest.raises(TypeError, match="working_directory"):
        CodexAgent().run("Summarize", Answer)  # type: ignore[call-arg]
    sdk.assert_not_called()


def test_relative_directory_is_resolved(
    sdk: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "project").mkdir()
    monkeypatch.chdir(tmp_path)
    CodexAgent().run("Summarize", Answer, working_directory=Path("project"))
    assert sdk.return_value.thread_start.call_args.kwargs["cwd"] == str(
        (tmp_path / "project").resolve()
    )


def test_each_call_owns_a_new_client_and_thread(sdk: MagicMock, tmp_path: Path) -> None:
    agent = CodexAgent()
    for _ in range(2):
        agent.run("Summarize", Answer, working_directory=tmp_path)
    assert sdk.call_count == 2
    assert sdk.return_value.thread_start.call_count == 2
    assert sdk.return_value.close.call_count == 2


def test_consumer_can_receive_a_fake_agent(tmp_path: Path) -> None:
    class FakeAgent:
        def run[T: BaseModel](
            self, prompt: str, response_model: type[T], *, working_directory: Path
        ) -> T:
            return response_model.model_validate({"summary": "Fake", "count": 1})

    def consumer(agent: StructuredAgent) -> Answer:
        return agent.run("Summarize", Answer, working_directory=tmp_path)

    assert consumer(FakeAgent()) == Answer(summary="Fake", count=1)
