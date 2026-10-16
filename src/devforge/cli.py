"""The DevForge command-line entry point."""

from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from rich.text import Text

from devforge.storage import save_project
from devforge.wizard import WizardCancelled, collect_project_config

app = typer.Typer(help="DevForge — learn software engineering through practice.")


@app.command()
def new() -> None:
    """Describe a project and save its configuration in the current directory."""
    console = Console()
    try:
        config = collect_project_config()
        path = save_project(config, Path.cwd())
    except WizardCancelled:
        console.print("Project creation cancelled. No configuration saved.")
        raise typer.Exit(code=130) from None
    except ValidationError as error:
        console.print("Invalid project configuration:", style="red")
        for detail in error.errors():
            console.print(f"{detail['loc'][0]}: {detail['msg']}", markup=False)
        raise typer.Exit(code=1) from None
    except FileExistsError:
        console.print(
            "A configuration with this project ID already exists. Choose another name."
        )
        raise typer.Exit(code=1) from None
    except OSError as error:
        console.print(f"Could not save project configuration: {error}", markup=False)
        raise typer.Exit(code=1) from None

    table = Table(title="Project configuration saved")
    table.add_column("Setting")
    table.add_column("Value")
    for label, value in (
        ("Name", config.name),
        ("Description", config.description),
        ("Difficulty", config.difficulty),
        ("Language", config.language),
        ("Scaffold level", config.scaffold_level),
    ):
        table.add_row(label, Text(value))
    console.print(table)
    console.print(f"Saved to: {path}", markup=False, soft_wrap=True)


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
