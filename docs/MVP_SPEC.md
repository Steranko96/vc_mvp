# DevQuest — MVP Product & Technical Specification

**Version:** 0.1.0  
**Status:** Ready for initial Codex planning  
**Product type:** Local-first CLI application  
**Primary user:** Individual learning software engineering through practical projects

## 1. Product overview

DevQuest is an AI-assisted software engineering learning tool.

The user describes a software project they would like to build. An interactive CLI wizard collects their goals, experience level, and preferences.

DevQuest uses Codex to generate a structured learning project consisting of:

- A runnable, intentionally incomplete codebase.
- A project README and setup instructions.
- A sequenced backlog of engineering tickets.
- Learning objectives and acceptance criteria for each ticket.
- A basic automated testing setup.

The user implements the tickets themselves, using DevQuest to request mentoring, run validations, and receive code reviews.

Optional GitHub integration allows learners to create pull requests and request AI-generated reviews.

### Core product principle

**AI assists the learning process without replacing the learner.**

Code generation is permitted during initial project scaffolding. During the learning phase, the agent must not silently implement the learner's outstanding tickets.

## 2. V1 scope

### Included

1. Interactive project creation wizard.
2. Beginner and intermediate difficulty levels.
3. Single supported generated project stack.
4. Minimal starter-code scaffold.
5. AI-generated, structured learning tickets.
6. Local ticket management and progress tracking.
7. AI mentorship with graduated hints.
8. Automated validation and AI code assessment.
9. Local Git repository initialization.
10. Optional GitHub repository and PR integration.
11. PR reviews initiated manually through the CLI.
12. Codex integration using existing supported ChatGPT authentication.

### Explicitly excluded

- Web application or graphical interface.
- Cloud backend, hosted services, or user accounts.
- Custom GitHub OAuth implementation.
- Multiple generated technology stacks.
- Advanced pre-existing codebase generation.
- Empty-project scaffold mode.
- Automated cloud PR review bots or webhooks.
- Multi-agent orchestration.
- Gamification, achievements, or leaderboards.
- Automatic implementation of learner tickets.
- Automatic merging of PRs.
- Custom model training or fine-tuning.

These are potential future features, not requirements for v1.

## 3. Target user experience

### 3.1 First-time setup

The user installs DevQuest and runs:

`devquest doctor`

DevQuest checks for:

- Supported Node.js runtime.
- Git installation.
- Codex CLI installation.
- Working Codex authentication.
- Optional GitHub CLI installation and authentication.

DevQuest must explain missing dependencies and how to resolve them.

It should reuse supported Codex and GitHub CLI authentication flows, not collect or store credentials itself.

### 3.2 Project creation

The user runs:

`devquest init`

An interactive wizard asks:

1. **Project name:** A human-readable name.
2. **Project description:** Free-text description of what they want to build.
3. **Difficulty:** Beginner or intermediate.
4. **Starter scaffold:** Minimal starter project (the only v1 mode).
5. **Technology stack:** TypeScript + Node.js (the only supported generated stack).
6. **GitHub integration:** Local only, or create a GitHub repository.

The tool should validate inputs and present a summary for confirmation before generation.

The user selects an empty destination directory, or DevQuest creates a new directory at the requested path.

### 3.3 Project generation

DevQuest sends the project requirements to Codex.

Codex produces a project plan containing:

- Product overview.
- Learning objectives.
- Proposed architecture.
- Initial scaffold components.
- A sequenced backlog of 4–6 tickets.
- Acceptance criteria for each ticket.
- Test expectations.

The user reviews the plan before generation.

Once approved, DevQuest generates the starter codebase.

Generation must not implement the functionality reserved for future learning tickets.

The project must be runnable and pass its baseline checks immediately after generation.

### 3.4 Learning workflow

The user enters the generated project directory.

They can then:

- Inspect the backlog.
- Read a ticket.
- Ask the mentor for guidance.
- Implement features manually.
- Run tests.
- Request an assessment of their work.
- Mark a ticket as complete following a successful assessment.
- Create a GitHub PR.
- Request a PR review.

Progress must persist between CLI executions.

## 4. Functional requirements

### FR-01: CLI framework

Provide an executable CLI command named `devquest`.

The CLI must support interactive prompts, noninteractive status commands, meaningful errors, and readable terminal output.

Every command must provide `--help`.

The CLI must fail gracefully when invoked outside a DevQuest project.

### FR-02: Codex integration

Build a dedicated Codex adapter.

The adapter is responsible for:

- Detecting Codex availability.
- Checking authentication readiness.
- Invoking supported Codex operations.
- Supplying project-specific context.
- Validating structured responses.
- Handling failures and interruptions.
- Returning results to the rest of the application.

Prefer a documented local Codex integration that works with the user's existing ChatGPT sign-in.

The adapter must not require an OpenAI API key or silently fall back to separately billed API requests.

Before building the full application, validate this integration with a small working proof of concept.

If the required integration is unsupported in the user's environment, display an actionable error rather than attempting an undocumented workaround.

### FR-03: Project wizard

Implement a guided project-creation process.

Requirements:

- Input validation.
- Confirmed project configuration before generation.
- Helpful defaults.
- Cancel support.
- Clear failure handling.
- Protection against overwriting files.

The wizard should not expose unsupported stack or scaffold options as selectable choices.

### FR-04: Generated project structure

Suggested structure:

```text
my-learning-project/
├── .devquest/
│   ├── project.json
│   └── tickets/
│       ├── 001.json
│       ├── 002.json
│       └── ...
├── src/
├── tests/
├── docs/
│   └── PROJECT.md
├── README.md
├── package.json
├── tsconfig.json
└── .gitignore
```

Generated projects should use standard Node.js and TypeScript conventions.

The `.devquest` directory stores project-specific metadata and ticket progress. It must contain no secrets.

The generated project README must explain how to install dependencies, run the application, run tests, and begin the learning journey.

### FR-05: Ticket generation

Generate 4–6 tickets per project.

Each ticket must include:

- Unique identifier.
- Title.
- Description.
- Learning objectives.
- Prerequisites or dependencies.
- Acceptance criteria.
- Expected validation or tests.
- Estimated relative complexity.
- Status.

Valid statuses:

- `todo`
- `in_progress`
- `completed`

Tickets should follow a logical progression.

Each ticket should be small enough to review independently and should provide meaningful hands-on engineering work.

The agent must avoid including a complete implementation solution in the ticket description.

Tickets are stored locally as structured JSON and must be readable through the CLI.

### FR-06: Mentor functionality

Command:

`devquest mentor "How should I approach this?"`

The mentor must understand:

- The project description.
- The selected difficulty.
- Relevant tickets.
- The current ticket, if selected.
- Relevant project files.

Default behaviour:

1. Explain relevant concepts.
2. Provide guidance and hints.
3. Suggest an approach.
4. Escalate to pseudocode or a small illustrative example only when the learner requests more help.

The mentor should adapt its explanations to the learner's difficulty level.

It must not directly modify learner implementation files.

The user must be able to ask follow-up questions within a mentor session.

### FR-07: Ticket assessment

Command:

`devquest review 001`

The review process must:

1. Load the ticket and its acceptance criteria.
2. Inspect the relevant implementation.
3. Run available deterministic checks, including tests and type checks.
4. Ask Codex to assess the implementation against the requirements.
5. Report failures, strengths, and suggestions.
6. Recommend whether the ticket is ready for completion.

Assessment outputs:

- `pass`
- `needs_changes`
- `unable_to_assess`

A `pass` requires relevant acceptance criteria to be supported by evidence and required checks to pass.

The agent must not claim that checks passed unless they were actually executed successfully.

The review must distinguish objective test results from subjective AI feedback.

The user remains able to override the agent's recommendation manually, but overrides must be visibly recorded.

### FR-08: Test strategy

All generated projects must contain a working testing framework.

Initial scaffolding must provide baseline tests for functionality that already exists.

Tickets should describe appropriate additional tests the learner needs to implement.

The reviewer may suggest missing test cases but must not silently add tests or change implementation code.

Testing expectations must be proportional to ticket complexity.

For v1, support unit and lightweight integration tests. Browser E2E testing and external-service testing are not required.

### FR-09: Local Git workflow

Generated projects must be initialized as Git repositories, unless the user explicitly opts out of Git initialization.

The project must have a sensible `.gitignore`.

DevQuest should teach conventional branching and commit practices through documentation and guidance.

Do not automatically commit learner changes.

### FR-10: GitHub integration

Use the existing GitHub CLI (`gh`) for authentication and repository operations.

Requirements:

- Detect whether `gh` is installed.
- Check authentication status.
- Offer the supported GitHub CLI login flow.
- Create a GitHub repository only with explicit confirmation.
- Support creation of a pull request from the current feature branch.
- Display the resulting PR URL.

No custom OAuth server or storage of GitHub tokens is required.

GitHub should remain optional for purely local learning.

### FR-11: Pull request review

Command:

`devquest pr review <number>`

The tool must:

1. Retrieve the specified PR and its diff.
2. Identify any associated learning ticket.
3. Compare the changes against ticket acceptance criteria.
4. Provide feedback on correctness, maintainability, testing, and clarity.
5. Identify significant actionable concerns.
6. Produce a structured review summary.

Reviews must be displayed locally by default.

A separate explicit confirmation is required before publishing review feedback to GitHub.

The tool must never automatically approve, merge, or close a pull request.

In v1, PR review is manually triggered from the learner's machine, not via a hosted GitHub automation.

### FR-12: Persistent state

DevQuest must store and restore:

- Project configuration.
- Ticket definitions.
- Ticket statuses.
- Ticket completion overrides.
- GitHub repository association.
- Relevant review metadata.

State must survive process restarts.

Use local files rather than introducing a database.

Writes should be atomic where practical, and invalid state files should result in actionable errors rather than silent data loss.

## 5. CLI command contract

| Command | Purpose |
|---|---|
| `devquest doctor` | Check dependencies and authentication readiness |
| `devquest init` | Launch the project wizard |
| `devquest status` | Display project and ticket progress |
| `devquest tickets` | List project tickets |
| `devquest ticket 001` | Display ticket details |
| `devquest ticket start 001` | Mark a ticket in progress |
| `devquest mentor "question"` | Request AI mentoring |
| `devquest check` | Run configured project checks |
| `devquest review 001` | Evaluate ticket implementation |
| `devquest ticket complete 001` | Record completion, with review evidence or explicit override |
| `devquest pr create 001` | Create a PR for ticket 001 |
| `devquest pr review 123` | Review an existing GitHub PR |

Commands must follow consistent naming, output, and error conventions.

## 6. Technical architecture

### Recommended application stack

- **Language:** TypeScript.
- **Runtime:** Node.js LTS.
- **CLI framework:** Commander or equivalent.
- **Interactive prompts:** `@inquirer/prompts` or equivalent.
- **Runtime validation:** Zod or equivalent.
- **Testing:** Vitest or equivalent.
- **Git:** Native Git CLI.
- **GitHub:** Official `gh` CLI.
- **AI engine:** Supported local Codex interface.

Dependencies should be selected deliberately, kept minimal, and documented.

### Suggested modules

```text
src/
├── cli/
│   ├── commands/
│   └── prompts/
├── core/
│   ├── projects/
│   ├── tickets/
│   ├── reviews/
│   └── mentoring/
├── integrations/
│   ├── codex/
│   ├── git/
│   └── github/
├── infrastructure/
│   ├── filesystem/
│   ├── process/
│   └── config/
└── index.ts
```

This is a suggested starting structure, not a requirement to create unnecessary abstractions.

### Architecture principles

- Separate CLI presentation from business logic.
- Isolate external tools behind small, testable adapters.
- Validate all AI-generated structured data.
- Avoid implementing a generic agent framework.
- Prefer simple synchronous workflows unless concurrency is justified.
- Make external process invocation explicit and testable.
- Avoid unnecessary background services.

## 7. AI workflow contracts

Use distinct AI tasks rather than one unrestricted, general-purpose agent.

### Project planner

Input: validated wizard configuration.

Output: schema-validated project plan and ticket backlog.

Must not write project files during planning.

### Scaffold generator

Input: approved project plan.

Output: runnable starter repository.

Must preserve intentionally unimplemented ticket functionality.

### Mentor

Input: question, difficulty, selected ticket, bounded project context.

Output: educational guidance.

Must not modify project files.

### Reviewer

Input: ticket criteria, code context, changes, and available check results.

Output: structured assessment with supporting evidence.

Must not modify project files or ticket completion state.

All AI responses must be treated as untrusted data and validated or constrained as appropriate.

## 8. Safety and reliability

### Filesystem

- Restrict generated file operations to the selected project directory.
- Resolve and validate paths before writing.
- Reject path traversal outside the project root.
- Protect existing files against accidental overwrites.
- Avoid executing instructions embedded in untrusted repository content as if they were developer instructions.

### Command execution

- Prefer argument-based process spawning rather than shell string interpolation.
- Use timeouts and cancellation for external processes.
- Capture exit codes and useful diagnostic output.
- Require explicit approval for potentially destructive operations.
- Never bypass the user's Codex sandbox or approval settings.

### Data and credentials

- Never log authentication tokens.
- Never commit secrets.
- Use existing CLI credential stores.
- Explain when project files or code are sent to an AI service.
- Keep learner data local except for explicitly requested Codex and GitHub operations.

### Failure recovery

- Do not leave partially generated projects masquerading as complete.
- Preserve useful diagnostic information.
- Avoid destructive retries.
- Provide clear recovery instructions when generation fails.

## 9. Definition of done

The MVP is complete when a learner can successfully perform this end-to-end scenario:

1. Install DevQuest and run `devquest doctor`.
2. Authenticate with an existing supported Codex account.
3. Create a TypeScript learning project using the wizard.
4. Review and approve the proposed project plan.
5. Receive a runnable, tested minimal scaffold.
6. View 4–6 logically sequenced learning tickets.
7. Start a ticket and manually implement the required feature.
8. Request hints from the mentor without having their solution overwritten.
9. Run project tests and type checks.
10. Request a ticket review containing clear, evidence-based feedback.
11. Address review findings and receive a passing reassessment.
12. Record ticket completion and see updated progress.
13. Optionally publish their work to GitHub through a feature branch and PR.
14. Request a PR review and explicitly choose whether to publish feedback.

### Quality gates

The DevQuest application itself must:

- Pass type checking, linting, and automated tests.
- Test critical state transitions.
- Test malformed AI responses.
- Test missing or failed external dependencies.
- Test cancellation and nonzero process exits.
- Test filesystem safety and overwrite protection.
- Test GitHub operations using mocks or controlled fixtures.
- Include clear setup and contributor documentation.
- Run the core local workflow without GitHub configured.

The project must not depend on real Codex or GitHub calls for its ordinary automated unit tests.

## 10. Implementation phases

### Phase 0: Integration feasibility

Before implementing product features:

- Validate a supported Codex invocation method.
- Validate existing ChatGPT authentication.
- Confirm structured output can be obtained reliably.
- Confirm a local project can be supplied as context.
- Verify expected failure and usage-limit behaviour.
- Document the chosen integration and limitations.

**Exit criterion:** A small, repeatable proof of concept demonstrates the intended authentication and AI execution path.

If subscription-backed orchestration cannot be validated, stop and report the blocker rather than introducing separately billed APIs.

### Phase 1: CLI foundation

Implement CLI structure, dependency checking, project configuration, state management, and tests.

### Phase 2: Project generator

Implement the wizard, project planner, plan approval, scaffold generation, and ticket creation.

### Phase 3: Learning workflow

Implement ticket navigation, mentor interactions, test execution, code review, and completion tracking.

### Phase 4: GitHub workflow

Implement optional repository creation, PR creation, and manually triggered PR review.

### Phase 5: Hardening

Add failure handling, edge-case testing, documentation, end-to-end fixtures, and packaging.

Each phase must leave the repository in a working, tested state.

## 11. Instructions for Codex

You are implementing DevQuest v0.1.0 according to this specification.

Do not immediately generate the entire application.

First:

1. Read and analyse this specification.
2. Identify material ambiguities, assumptions, and technical risks.
3. Verify the Codex integration approach against current supported interfaces.
4. Propose a minimal architecture and dependency list.
5. Produce a phased implementation plan with small, independently testable engineering tasks.
6. Highlight decisions requiring product-owner input.
7. Present the plan for approval before modifying project files.

During implementation:

- Work incrementally, one approved task at a time.
- Prefer straightforward, maintainable solutions.
- Explain architectural decisions and important trade-offs.
- Add proportional automated tests.
- Run relevant checks after changes.
- Report what changed, what was tested, and any remaining risks.
- Do not add out-of-scope features without permission.
- Do not silently change product requirements.
- Do not store credentials or introduce separately billed AI APIs.
- Do not claim features are working without verifying them.

**The objective is a small, reliable, understandable MVP — not a feature-complete platform.**
