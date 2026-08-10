# Implementation Plugin Documentation Design

**Status:** Approved in conversation on 2026-08-09

## Purpose

Create reader-facing documentation and cross-platform packaging for the Implementation Plugin. A reader may know Codex but may be new to staged implementation workflows. The documentation must explain the method before asking the reader to use the plugin, then help them install, invoke, and apply the plugin without reading its internal implementation.

The shared workflow remains `skills/implementing-staged-plans/`. Codex and Claude packaging expose that same skill; they must not fork or restate its normative workflow.

## Current Context

- The repository contains a valid Codex manifest at `.codex-plugin/plugin.json`.
- The plugin contains one skill: `implementing-staged-plans`.
- The root design plan and bootstrap runbook are implementation and historical references, not beginner documentation.
- The repository has no reader-facing `README.md` or task-oriented documentation set.
- The lifecycle implementation and program evidence are committed on `agent/complete-staged-plan-lifecycle`.
- `skills/implementing-staged-plans/agents/openai.yaml`, `skills/implementing-staged-plans/scripts/validate_package.py`, and `tests/test_package_validation.py` contain pre-existing user-owned local changes that disable implicit invocation. This work must preserve those changes.
- This documentation effort must not edit accepted `implementation-programs/ISP-001/` evidence.
- The work adds local files only. It does not install, publish, share, submit, commit, push, or create a pull request.

## Audience

The primary reader:

- already knows how to open and use Codex;
- may also use Claude Code or Claude Desktop;
- has an implementation plan or expects to create one;
- has not used a staged implementation workflow before;
- needs practical examples more than lifecycle internals.

Maintainers are a secondary audience. Their validation and packaging information belongs in a separate guide so it does not interrupt the beginner path.

## Goals

1. Explain staged implementation in plain language, including its benefits and limits.
2. Explain what the plugin does, when to use it, and when another workflow is more suitable.
3. Document every supported Codex and Claude installation route that the package can truthfully support.
4. Provide copyable examples for every user-visible lifecycle action and approval mode.
5. Make authority boundaries, hard stops, and later-action permissions easy to recognize.
6. Keep platform-specific installation and invocation details separate from the shared workflow.
7. Verify documentation structure, internal links, packaging JSON, commands, and examples deterministically where possible.
8. Use natural, direct prose without weakening technical precision.

## Non-goals

- Explain how to use Codex generally.
- Reproduce the full internal design plan, program schema, or script implementation.
- Teach users to hand-edit lifecycle state or evidence files.
- Claim that a marketplace or universal directory listing exists before publication.
- Perform or authorize installation, publication, sharing, submission, release, deployment, migration, or another external action.
- Add a license, author email, privacy policy, terms, logo, or other metadata whose factual or legal basis has not been supplied.
- Modify the accepted ISP-001 program record or its closure evidence.

## Documentation Architecture

### `README.md`

The README is the front door. It will contain:

1. A one-sentence description of the outcome.
2. The problem with executing a large plan as one uncontrolled change.
3. A short staged-workflow explanation: plan, increment, evidence and review, decision, then continuation.
4. General advantages: smaller review surfaces, explicit decisions, recoverable boundaries, protected existing work, and traceable evidence.
5. A concise suitability section covering when to use and when not to use the plugin.
6. A five-minute quick start using a fictional repository and program.
7. An “I want to…” navigation list linking to task-specific workflows.
8. Links to installation, workflows, reference, troubleshooting, and maintainer guides.
9. A clear statement that commits, pull requests, releases, and other later actions require separate authorization.

The README will not expose the internal ISP-001 history as the learning path.

### `docs/installation.md`

The installation guide will use a support matrix before detailed steps. Each route will be labelled as one of:

- available from the current repository;
- available after the repository is reachable from a configured marketplace;
- available only after a separate public-directory publication step;
- conditional on a trusted packaged archive existing.

Codex routes:

1. ChatGPT/Codex desktop Plugins Directory through a configured marketplace.
2. Codex CLI marketplace registration with `codex plugin marketplace add`.
3. Codex CLI installation with `codex plugin add implementation-plugin@implementation-workflows`.
4. Local repository marketplace installation.
5. Repository-scoped standalone skill under `.agents/skills/implementing-staged-plans/`.
6. Personal standalone skill under `$HOME/.agents/skills/implementing-staged-plans/`.
7. Installation from the repository through `$skill-installer`.

Claude routes:

1. Claude Desktop’s plugin browser after adding the marketplace.
2. Interactive `/plugin marketplace add` and `/plugin install` commands.
3. Claude CLI marketplace registration with `claude plugin marketplace add`.
4. Claude CLI installation with `claude plugin install implementation-plugin@implementation-workflows`.
5. Session-only loading with `claude --plugin-dir /absolute/path/to/implementation-plugin`.
6. Personal standalone skill under `$HOME/.claude/skills/implementing-staged-plans/`.
7. Project-scoped standalone skill under `.claude/skills/implementing-staged-plans/`.
8. Session-only loading from a trusted archive with `claude --plugin-url` when an archive exists.

The guide will include trust warnings for plugins, marketplaces, repository content, and remote archives. It will not include destructive uninstall or cache-cleaning commands as routine setup.

### `docs/workflows.md`

The workflow guide will organize examples by user intent. Every example will include:

- when to use it;
- required inputs;
- a copyable prompt or command;
- expected plugin behavior;
- the mandatory stopping point;
- the user’s next decision.

It will cover:

1. Start from an approved implementation plan.
2. Capture or approve a program and select a workspace.
3. Choose an approval mode.
4. Prepare and execute one increment.
5. Accept an increment and stop.
6. Accept an increment and authorize the next increment.
7. Hold the current diff while asking a question.
8. Request a bounded repair.
9. Request a program-level amendment.
10. Reject work or request rollback planning.
11. Continue within a suitable current conversation.
12. Resume in a new conversation with a validated brief.
13. Reconcile and close a completed program.
14. Separately decide and authorize a commit, pull request, release, or other later action.
15. Understand incomplete, contradictory, stale, or unauthorized requests.

Examples will use fictional identifiers such as `LIBRARY-001`, `INC-002`, and `/work/library-catalog`. They will not present repository-specific ISP-001 records as reusable templates.

### `docs/reference.md`

The reference guide will define:

- program, increment, exact-file plan, evidence, review packet, handoff, reconciliation, and closure packet;
- the lifecycle at a high level;
- the five approval modes and their actual interruption and acceptance behavior;
- the difference between approval mode, action authorization, and later external authorization;
- common hard stops and the smallest legal next action;
- what the plugin can verify mechanically and what still needs human judgment;
- invocation syntax for each supported installation form.

The five modes are:

- `approval:standard`;
- `approval:pre-approve`;
- `approval:full-increment`;
- `approval:full-diff`;
- `approval:full`.

The guide will link to the skill for canonical rules instead of duplicating long normative passages.

### `docs/troubleshooting.md`

Troubleshooting will be symptom-led. It will cover:

- the plugin or skill does not appear;
- the invocation name differs between plugin and standalone-skill installation;
- a marketplace is configured but the plugin cannot be installed;
- repository identity, branch, source, workspace, or plan bindings do not match;
- the plugin stops on dirty or conflicting work;
- a handoff or resume brief is stale;
- an approval was supplied but the requested action remains unauthorized;
- validation passes but live activation is still unproven;
- Claude runtime verification is unavailable in the maintainer’s environment.

Each entry will explain the likely cause, safe checks, and a bounded next action. It will not advise users to delete caches, reset repositories, discard work, or bypass approval controls as a default remedy.

### `docs/maintainers.md`

The maintainer guide will contain:

- the documentation and packaging file map;
- the shared-skill/no-fork rule;
- version synchronization between Codex and Claude manifests;
- how to update install commands from primary platform documentation;
- how to run focused and full validation;
- what the local checks do and do not prove;
- a release-readiness checklist that stops before publication or external mutation.

## Platform Packaging

### Codex

Preserve the exact existing `.codex-plugin/plugin.json` contract:

- `name`: `implementation-plugin`;
- `version`: `0.1.0`;
- `description`: `Run approved implementation programs one reviewable increment at a time.`;
- `skills`: `./skills/`.

The existing package validator treats those four fields as the exact approved manifest. Put marketplace display metadata in the catalog instead of widening the manifest.

Add `.agents/plugins/marketplace.json`:

- marketplace identifier: `implementation-workflows`;
- display name: `Implementation Workflows`;
- plugin identifier: `implementation-plugin`;
- plugin source: the repository root as the relative source `./`;
- installation policy: `AVAILABLE`;
- authentication policy: `ON_INSTALL`, the marketplace compatibility value required by the published example; the plugin itself declares no credential or MCP-server dependency;
- category: `Productivity`, a value used by the published marketplace schema example.

### Claude

Add `.claude-plugin/plugin.json`:

- name: `implementation-plugin`;
- display name: `Implementation Plugin` when supported;
- version synchronized with the Codex manifest;
- description aligned with the shared skill;
- skills path: `./skills/`;
- repository metadata without personal email or unsupported legal claims.

Add `.claude-plugin/marketplace.json`:

- marketplace identifier: `implementation-workflows`;
- owner name: `CoveMB`;
- plugin identifier: `implementation-plugin`;
- source: the repository root using a valid relative source;
- description aligned with the manifest.

The Claude package will reuse the default `skills/<name>/SKILL.md` layout. Codex-specific `agents/openai.yaml` remains optional platform metadata and is not treated as a Claude contract.

## Invocation Contract

- Codex plugin or standalone skill: `$implementing-staged-plans`
- Claude marketplace plugin: `/implementation-plugin:implementing-staged-plans`
- Claude standalone skill: `/implementing-staged-plans`

Natural-language invocation remains possible when the host allows implicit skill selection, but examples will lead with explicit invocation because it is easier to verify.

## Writing and Editorial Rules

The documentation will:

- use plain words before defined lifecycle terms;
- define each term on first use;
- prefer short paragraphs and task-based headings;
- vary sentence rhythm naturally without manufactured informality;
- use lists when they improve scanning, not as the default shape for every section;
- keep commands, file paths, identifiers, conditions, and warnings exact;
- remove promotional claims that the repository evidence does not establish;
- distinguish static validation from live integration, activation, publication, and human-review evidence;
- avoid chatbot framing, generic conclusions, inflated benefits, repeated contrast formulas, and unnecessary jargon;
- preserve the user’s approval and authorization distinctions.

After drafting, run the Editorial Humanizer pipeline as a factual-integrity and natural-voice pass. The pass may improve structure and wording but may not change commands, supported routes, approval behavior, or evidence boundaries.

## Safety, Privacy, and Authority

- Installation instructions must tell readers to trust the plugin and marketplace source before enabling them.
- Examples must not contain credentials, private paths, personal data, or repository-specific program evidence.
- Documentation must not imply that installing the plugin grants permission to change a repository or an external system.
- No example may combine plan approval with commit, push, pull-request, publication, release, deployment, migration, destructive-operation, or provider-state authority.
- Marketplace metadata will not include an email address or legal assertion not already established by the repository.
- The implementation must preserve all pre-existing staged, unstaged, and untracked user work.

## Verification Design

Add `tests/test_distribution_documentation.py` as a focused, standard-library test module. It will verify:

1. Required reader-facing files exist.
2. Codex and Claude manifests and marketplace catalogs parse as JSON.
3. Manifest names, versions, skill paths, and marketplace selectors agree.
4. All repository-relative Markdown links resolve to regular files.
5. Markdown code fences are balanced.
6. Reader-facing files contain no `TODO`, `TBD`, or unfinished placeholder markers.
7. Reader-facing examples do not use `ISP-001` as a reusable example.
8. Required invocation and installation commands appear in the appropriate guides.

Update the existing package validator and its tests narrowly so that only `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json` are allowed marketplace filenames. Other `marketplace.json` locations remain forbidden. Preserve the pre-existing implicit-invocation changes in both dirty files.

Verification sequence:

1. Run the focused documentation test and observe the expected failure before creating reader-facing files or packaging metadata.
2. Add the minimal documentation and packaging needed to pass.
3. Run the focused test until it passes.
4. Run the repository package validator.
5. Run the complete unit-test suite once against the coherent final tree.
6. Run `git diff --check`.
7. Compare Codex commands with the installed `codex-cli 0.146.0` help output.
8. Compare Codex and Claude routes with current official documentation.

The environment does not currently provide a Claude CLI. Claude manifest and marketplace verification is therefore structural and source-backed, not a live Claude install or activation result. The final report must state this limitation.

## Acceptance Criteria

The work is complete when:

1. A beginner can explain the plugin’s purpose after reading the README introduction.
2. A reader can distinguish staged implementation from a one-shot implementation request.
3. Every supported installation route has prerequisites, exact commands, activation guidance, and a truthful availability label.
4. Every user-visible workflow and approval mode has a copyable fictional example.
5. Commit, pull-request, publication, release, and other later-action boundaries are explicit.
6. Shared workflow rules have one canonical owner and platform guides do not fork them.
7. Natural-language editorial review finds no material formulaic, inflated, or unclear prose.
8. Focused documentation tests, package validation, the complete unit-test suite, and `git diff --check` pass on the final tree.
9. The final report distinguishes deterministic checks from unperformed Claude runtime, marketplace publication, plugin installation, and live workflow testing.
10. Existing user-owned local changes and accepted ISP-001 evidence remain intact.

## Risks and Mitigations

### Platform instructions drift

Codex and Claude plugin commands may change. Keep platform-specific commands in the installation guide, link to primary documentation, and require a maintainer freshness check before release.

### Duplicate policy drifts from the skill

Long copies of normative rules will become stale. Explain behavior in user terms, link to the canonical skill, and test only stable user-facing contracts.

### “All installation methods” becomes an unsupported promise

Label each route by actual availability and prerequisites. Describe universal-directory or archive installation only as conditional until that distribution exists.

### Beginner clarity weakens safety language

Use plain language without removing exact authorization distinctions, hard stops, or residual limitations.

### New documentation overlaps program evidence or local work

Create a separate reader-facing documentation set and packaging files. Do not edit `implementation-programs/ISP-001/` or rewrite the accepted lifecycle record. Patch the package validator and its test at non-overlapping lines while preserving the existing implicit-invocation edits.

## Primary External References

- OpenAI, “Package your plugin”: <https://developers.openai.com/plugins/build/plugins>
- OpenAI, “Build skills”: <https://learn.chatgpt.com/docs/build-skills>
- Anthropic, “Create plugins”: <https://code.claude.com/docs/en/plugins>
- Anthropic, “Create and distribute a plugin marketplace”: <https://code.claude.com/docs/en/plugin-marketplaces>
- Anthropic, “Plugins reference”: <https://code.claude.com/docs/en/plugins-reference>
