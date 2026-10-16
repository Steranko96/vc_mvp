"""Smoke tests for the public CLI."""

from importlib.metadata import version

from typer.testing import CliRunner

from devforge.cli import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "DevForge" in result.output
    assert "--version" in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == f"DevForge {version('devforge')}"
