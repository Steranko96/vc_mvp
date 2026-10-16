# DevForge — V1 Architecture

## 1. Overview

DevForge is a local-first Python CLI application that helps learners practise software engineering through AI-generated projects, structured tickets, and code review.

The architecture follows a modular monolith design.

The product requirements are defined in `docs/MVP_SPEC.md`.

## 2. Technology

- Python 3.12+
- Typer, Rich, Questionary
- OpenAI Codex Python SDK
- GitHub CLI (`gh`)
- Pydantic
- pytest, Ruff, mypy
- uv
- JSON-based local persistence

## 3. Project structure

```text
devforge/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── docs/
│   ├── MVP_SPEC.md
│   └── ARCHITECTURE.md
├── src/
│   └── devforge/
│       ├── __init__.py
│       ├── cli.py
│       ├── commands/
│       ├── wizard/
│       ├── projects/
│       ├── tickets/
│       ├── reviews/
│       ├── agents/
│       ├── github/
│       ├── storage/
│       └── models/
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

This is the target structure, not a requirement to create every module immediately.

## 4. Architectural rules

1. CLI handlers should contain minimal business logic.
2. Business logic must be independently testable.
3. External integrations should use explicit interfaces or adapters.
4. Domain models must not depend on terminal UI libraries.
5. Structured agent output must be validated before use.
6. Filesystem operations must validate paths and handle failures.
7. Avoid unnecessary abstractions, global state, and circular dependencies.

## 5. Core responsibilities

### CLI and wizard

Collect user input, validate selections, and display progress and results.

### Projects

Manage project configurations, scaffold levels, and generation workflows.

### Tickets

Manage implementation tasks, acceptance criteria, dependencies, and completion status.

### Reviews

Coordinate code review, feedback, relevant testing, and ticket completion decisions.

### Agents

Encapsulate Codex SDK integration, agent instructions, execution, and response handling.

### GitHub

Integrate with authenticated GitHub CLI operations for repositories and pull requests.

### Storage

Persist and retrieve local project metadata, configuration, and ticket status.

## 6. Authentication

Reuse existing local Codex authentication where available.

Use GitHub CLI authentication for GitHub functionality.

Never store credentials in project configuration or repository files.

## 7. Agent safety

- Start with restricted workspace permissions.
- Require confirmation before destructive actions.
- Treat generated content as untrusted.
- Validate agent-generated structured data.
- Limit writes to authorised workspace locations.
- Do not execute arbitrary generated project code without explicit safeguards.

## 8. Testing strategy

Unit tests cover domain logic and validation.

Integration tests cover storage, CLI commands, and external integration adapters.

End-to-end tests cover critical user workflows.

Tests must not depend on live Codex or GitHub services unless explicitly designated as live integration tests.

## 9. Architecture decisions

The following decisions are accepted for V1:

- Modular monolith instead of distributed services.
- Local JSON storage instead of a database.
- Existing Codex and GitHub authentication instead of custom OAuth implementations.
- Explicit integration adapters instead of embedding SDK calls throughout the application.

Future changes should be justified by concrete requirements rather than speculative scalability concerns.
