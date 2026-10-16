# DevForge

A local-first Python CLI for learning software engineering through practice.
This repository currently provides the application skeleton only: CLI help,
version reporting, packaging, and development tooling.

## Setup

Install Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/),
then run the following from this repository's root (`vc_mvp/`):

```sh
uv sync
```

This installs DevForge and its development dependencies in a local `.venv`.
The `uv.lock` file records dependency versions for reproducible installs.

## Run

```sh
uv run devforge --help
uv run devforge --version
```

The CLI uses Typer with Rich help output. Questionary is installed for future
interactive prompts. Product workflows are not implemented yet.

## Development checks

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
```

Application code lives in `src/devforge/`, and CLI smoke tests live in `tests/`.
The package uses the `uv_build` build backend and exposes the `devforge` command.

See [agent guidelines](docs/AGENTS.md), the [MVP specification](docs/MVP_SPEC.md),
and the [Python architecture](docs/ARCHIRECTURE.md) for project context.
The older MVP specification uses the DevQuest name and a TypeScript application
stack; this foundation follows the DevForge Python architecture.
