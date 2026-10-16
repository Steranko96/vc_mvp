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

## Structured agent adapter

`devforge.agents.StructuredAgent` is the application interface. Consumers should
accept it as a dependency so unit tests can supply a fake. The SDK implementation
is `devforge.agents.codex.CodexAgent`:

```python
from pathlib import Path

from pydantic import BaseModel

from devforge.agents import StructuredAgent
from devforge.agents.codex import CodexAgent


class Summary(BaseModel):
    summary: str


agent: StructuredAgent = CodexAgent()
result = agent.run(
    "Summarize this project.",
    Summary,
    working_directory=Path("/absolute/path/to/existing/project"),
)
print(result.summary)
```

Each call creates a fresh synchronous SDK client and checks that an existing
ChatGPT account is signed in. It creates a read-only thread with permission
escalation denied, supplies the model's JSON Schema as `output_schema`, and returns
a Pydantic-validated model. The SDK client is closed on success and
failure. Interrupted or incomplete turns never return a model. If execution and
cleanup both fail, the primary exception is preserved and a sanitized cleanup
note is attached. Keyboard interrupts and process exits propagate after cleanup.
Relative directories are resolved explicitly; missing directories and
files raise `ValueError` before Codex starts. The directory is a context location,
not a restriction on which files Codex can read.

The official `openai-codex` dependency includes its pinned Codex CLI runtime.
Configure your existing local Codex sign-in separately before using the adapter;
DevForge does not log in, collect API keys, or change authentication state. It uses
the SDK's local authentication and default model configuration. Missing sign-in,
API-key accounts, and other authentication modes are rejected before thread
creation; use `codex login` with your ChatGPT account separately. Prompts and project
context are sent through Codex when you invoke `run`; existing CLI commands do not
invoke it.

Catch `AgentExecutionError`, `AgentMissingResponseError`, or
`AgentInvalidOutputError` from `devforge.agents` (all derive from `AgentError`).
Execution errors identify the failing stage and exception type, with fixed
remediation guidance for recognized SDK error types and structured error codes.
When the SDK exposes only an opaque runtime error, guidance lists sign-in, usage
limits, and schema compatibility checks. Raw SDK error messages, validation
inputs, prompts, and responses are omitted from application
diagnostics. The adapter adds no retries, streaming, or application session
persistence. The service may reject JSON Schema features it does not support.
Unit tests mock the SDK and do not require authentication or network access.

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
