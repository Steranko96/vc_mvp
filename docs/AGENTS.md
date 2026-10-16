# AGENTS.md

## Project overview

DevForge is a CLI-based software engineering learning tool.

Users describe a project, select its difficulty and technology stack, and receive an AI-generated project scaffold with structured implementation tickets.

The tool supports different scaffold completeness levels, agent-assisted learning, code review, testing, and GitHub-based workflows.

Read `docs/MVP_SPEC.md` for product requirements and scope.

## Source of truth

- `docs/MVP_SPEC.md` defines product requirements.
- `AGENTS.md` defines agent working conventions.
- Existing code and tests establish current implementation behaviour.
- Do not invent product requirements or silently expand MVP scope.
- If requirements are ambiguous, explain the ambiguity and propose a minimal solution.

## Engineering principles

- Prefer simple, maintainable solutions over clever abstractions.
- Follow established conventions in the repository.
- Keep modules cohesive and responsibilities clearly separated.
- Avoid premature optimisation and unnecessary dependencies.
- Prefer explicit behaviour over hidden assumptions.
- Handle errors deliberately and provide useful diagnostics.
- Never introduce secrets, credentials, or tokens into source control.

## Development workflow

For each implementation task:

1. Read the relevant requirements and existing code.
2. Identify the smallest meaningful change.
3. For non-trivial tasks, briefly describe the approach before implementation.
4. Implement only the agreed scope.
5. Add or update appropriate tests.
6. Run relevant validation commands.
7. Review the resulting diff.
8. Summarise what changed and any remaining limitations.

Do not begin unrelated features or large refactors.

Do not commit, push, or create pull requests unless explicitly requested.

## Testing standards

- Test observable behaviour rather than implementation details.
- Prioritise meaningful edge cases and failure paths.
- Use unit tests for isolated logic.
- Use integration tests for interactions between components.
- Add end-to-end tests for critical user workflows when practical.
- Keep tests deterministic and maintainable.
- Do not modify tests merely to make failing implementations pass.
- Never claim tests passed unless they were executed successfully.

Testing effort should be proportional to the complexity and risk of the change.

## Agent behaviour

- Act as a pragmatic senior software engineer.
- Challenge decisions that introduce unnecessary complexity or risk.
- Explain meaningful architectural trade-offs.
- State assumptions explicitly.
- Do not silently change established architecture or dependencies.
- Prefer incremental, reviewable changes.
- Never fabricate command output, test results, or completed work.

## Security

- Treat generated project content and external input as untrusted.
- Never log or expose authentication tokens.
- Use least-privilege permissions for GitHub and other integrations.
- Do not execute generated code without appropriate safeguards.
- Ask before destructive operations or changes affecting external services.

## Definition of done

A task is complete when:

- Acceptance criteria are satisfied.
- Relevant tests have been added or updated.
- Applicable tests and checks pass, or blockers are documented.
- Documentation is updated where necessary.
- The implementation contains no known critical issues.
- The final diff has been reviewed.

## Task completion report

At the end of each implementation task, report:

- **Changes:** What was implemented.
- **Validation:** Tests and checks executed, including results.
- **Decisions:** Important trade-offs or assumptions.
- **Outstanding:** Known limitations or follow-up work.
