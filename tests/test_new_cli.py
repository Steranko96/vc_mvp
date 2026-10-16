"""Exercise the complete wizard using prompt answers without a real terminal."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from devforge.cli import app

runner = CliRunner()
ANSWERS = ["My Project", "A learning project", "intermediate", "TypeScript", "minimal"]


def test_new_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    prompt = Mock()
    prompt.unsafe_ask.side_effect = ANSWERS
    with (
        patch("devforge.wizard.questionary.text", return_value=prompt) as text,
        patch(
            "devforge.wizard.questionary.select",
            return_value=prompt,
        ) as select,
    ):
        result = runner.invoke(app, ["new"])
    assert result.exit_code == 0, result.output
    assert text.call_count == 2
    assert select.call_count == 3
    assert [call.kwargs["choices"] for call in select.call_args_list] == [
        ("beginner", "intermediate"),
        ("TypeScript",),
        ("minimal",),
    ]
    path = tmp_path / ".devforge/projects/my-project.json"
    assert str(path) in result.output
    assert json.loads(path.read_text()) == dict(
        schema_version=1,
        name=ANSWERS[0],
        description=ANSWERS[1],
        difficulty=ANSWERS[2],
        language=ANSWERS[3],
        scaffold_level=ANSWERS[4],
    )
    original = path.read_bytes()
    prompt.unsafe_ask.side_effect = ANSWERS
    with (
        patch("devforge.wizard.questionary.text", return_value=prompt),
        patch(
            "devforge.wizard.questionary.select",
            return_value=prompt,
        ),
    ):
        repeated = runner.invoke(app, ["new"])
    assert repeated.exit_code == 1
    assert "already exists" in repeated.output
    assert path.read_bytes() == original


@pytest.mark.parametrize("position", range(5))
@pytest.mark.parametrize("cancellation", [None, KeyboardInterrupt(), EOFError()])
def test_new_cancelled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    position: int,
    cancellation: object,
) -> None:
    monkeypatch.chdir(tmp_path)
    prompt = Mock()
    prompt.unsafe_ask.side_effect = [*ANSWERS[:position], cancellation]
    with (
        patch("devforge.wizard.questionary.text", return_value=prompt),
        patch(
            "devforge.wizard.questionary.select",
            return_value=prompt,
        ),
    ):
        result = runner.invoke(app, ["new"])
    assert result.exit_code == 130
    assert "cancelled" in result.output
    assert not (tmp_path / ".devforge").exists()


def test_new_invalid_input(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    prompt = Mock()
    prompt.unsafe_ask.side_effect = [" ", *ANSWERS[1:]]
    with (
        patch("devforge.wizard.questionary.text", return_value=prompt),
        patch(
            "devforge.wizard.questionary.select",
            return_value=prompt,
        ),
    ):
        result = runner.invoke(app, ["new"])
    assert result.exit_code == 1
    assert "Invalid project configuration" in result.output
    assert not (tmp_path / ".devforge").exists()


def test_new_filesystem_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".devforge").write_text("existing file")
    prompt = Mock()
    prompt.unsafe_ask.side_effect = ANSWERS
    with (
        patch("devforge.wizard.questionary.text", return_value=prompt),
        patch(
            "devforge.wizard.questionary.select",
            return_value=prompt,
        ),
    ):
        result = runner.invoke(app, ["new"])
    assert result.exit_code == 1
    assert "Could not save" in result.output


def test_new_help() -> None:
    result = runner.invoke(app, ["new", "--help"])
    assert result.exit_code == 0
    assert "configuration" in result.output


def test_cleanup_warning_does_not_report_cli_save_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.chdir(tmp_path)
    prompt = Mock()
    prompt.unsafe_ask.side_effect = ANSWERS
    with (
        patch("devforge.wizard.questionary.text", return_value=prompt),
        patch("devforge.wizard.questionary.select", return_value=prompt),
        patch(
            "devforge.storage.os.unlink", side_effect=PermissionError("cleanup denied")
        ),
    ):
        result = runner.invoke(app, ["new"])
    assert result.exit_code == 0, result.output
    assert "Project configuration saved" in result.output
    assert "Could not save" not in result.output
    assert "could not remove temporary file" in caplog.text
    assert (tmp_path / ".devforge/projects/my-project.json").is_file()
