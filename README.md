# DevForge

A local-first Python CLI for learning software engineering through practice.
The CLI provides help, version reporting, and an interactive project configuration
wizard. Project generation is not implemented yet.

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
uv run devforge new
```

`devforge new` uses Questionary to collect a project name, description, difficulty
(beginner or intermediate), language (TypeScript on Node.js), and
scaffold level (minimal). These are saved preferences only; the
command does not generate source code or invoke Codex.

The wizard displays the saved path under `.devforge/projects/<project-id>.json`
relative to your current directory. Existing IDs are rejected, including names
that normalize to the same ID. Ctrl-C or Ctrl-D cancels with exit code 130 before
writing a configuration. Validation and filesystem failures exit with code 1.

See the [configuration format](docs/PROJECT_CONFIG.md) and its
[version 1 JSON Schema](docs/project-config-v1.schema.json). Do not enter secrets
in the name or description: those fields are stored as plain text. No credentials
or environment settings are collected.

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
