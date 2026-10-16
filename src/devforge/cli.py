"""The DevForge command-line entry point."""

from importlib.metadata import version
from typing import Annotated

import typer

app = typer.Typer(help="DevForge — learn software engineering through practice.")


def show_version(value: bool) -> None:
    """Print the installed package version and exit."""
    if value:
        typer.echo(f"DevForge {version('devforge')}")
        raise typer.Exit()


@app.callback(invoke_without_command=True, no_args_is_help=True)
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=show_version,
            is_eager=True,
            help="Show the installed version and exit.",
        ),
    ] = False,
) -> None:
    """Run the DevForge CLI."""
