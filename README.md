# Implementation Plugin

Run an approved implementation plan in small, reviewable increments without
treating one approval as permission for every action that follows.

## Why staged implementation?

Large plans are easier to control when the work is divided into increments that
can be prepared, implemented, reviewed, and accepted independently. This makes
assumptions visible earlier, keeps diffs small enough to review properly, and
gives you a safe place to pause when the repository no longer matches the plan.

Staging is also useful when work spans more than one conversation. The current
state, approvals, workspace, evidence, and next legal action live in the
repository instead of depending on a handoff from memory.

The tradeoff is deliberate: progress may stop at an approval or evidence gate.
That pause is part of the workflow, not a failure.

## What this plugin does

The plugin provides one skill, `implementing-staged-plans`. It reads a
repository-backed implementation program, checks which source, plan, workspace,
and approvals are current, then advances only the next action that is actually
authorized.

Depending on the program state, that action might be read-only orientation,
repository preparation, exact-file planning, test-first implementation, review,
remediation, diff acceptance, handoff preparation, or program closure. If a
required binding is missing or stale, the skill explains what is blocking the
work and stops before the prohibited action.

It does not turn plan approval into blanket authority. Commits, pull requests,
merges, releases, deployments, destructive operations, publications, permission
changes, and other external effects still need authority for that exact action.

## When to use it

Use this plugin when:

- a repository contains an approved multi-step implementation program;
- work needs clear plan, implementation, review, and acceptance boundaries;
- several increments may span multiple sessions or contributors;
- preserving pre-existing work and exact repository state matters; or
- you want the next legal action identified before anything changes.

## When not to use it

You probably do not need this plugin for a small, self-contained edit with no
persisted implementation program. It also does not create product requirements
from a vague idea or replace the technical and human reviewers required by your
project.

## Five-minute start

From a local checkout of this repository, register its marketplace and install
the plugin:

```bash
codex plugin marketplace add /absolute/path/to/implementation-plugin
codex plugin add implementation-plugin@implementation-workflows
```

Open the target repository in Codex and start with a concrete program and
manifest path:

```text
$implementing-staged-plans

Orient to program LIBRARY-001 using
implementation-programs/LIBRARY-001/manifest.json. The approved plan is
docs/library-search-plan.md. Use approval:standard and advance only the next
legal action.
```

The first response may be a read-only orientation or a request for the smallest
missing approval. Code changes are not guaranteed merely because the skill was
invoked.

For remote marketplaces, standalone skills, Claude Code Desktop, VS Code, and
development-mode options, see [Installation](docs/installation.md).

## Choose what you want to do

- Start or resume a program: use the prompts in
  [Common workflows](docs/workflows.md).
- Compare approval modes or invocation names: open the
  [Reference](docs/reference.md).
- Fix a blocked or stale run: work from the symptom in
  [Troubleshooting](docs/troubleshooting.md).
- Package, validate, or update the plugin: use the
  [Maintainer guide](docs/maintainers.md).

## Installation

The plugin can be installed from a Codex or Claude marketplace, loaded directly
from a local checkout, or installed as a standalone skill. Marketplace routes
keep the plugin identity and platform metadata; standalone installation is
useful when you want only the skill.

The repository includes marketplace metadata, but it is not automatically
listed in a public directory. Remote commands work only after the relevant
repository revision is accessible from the host. The
[installation guide](docs/installation.md) labels each route and its
prerequisites.

## Safety boundary

The skill treats repository artifacts and current Git observations as the source
of truth. A prompt, chat handoff, approval mode, or successful static check does
not replace missing authority or prove that an external action happened.

When a gate fails, expect a bounded result: what was verified, what action was
requested, why it is or is not permitted, and the next legal action.

## Documentation

- [Installation](docs/installation.md)
- [Common workflows](docs/workflows.md)
- [Reference](docs/reference.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Maintainer guide](docs/maintainers.md)
- [Canonical skill instructions](skills/implementing-staged-plans/SKILL.md)
