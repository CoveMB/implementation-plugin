# Maintainer guide

The repository packages one canonical skill for two hosts. Maintenance should
keep that shared implementation intact, update platform metadata together, and
separate local validation from installation or publication claims.

## File map

| Path | Purpose |
| --- | --- |
| `.codex-plugin/plugin.json` | Exact Codex plugin identity and shared skill path |
| `.agents/plugins/marketplace.json` | Codex marketplace catalog and display policy |
| `.claude-plugin/plugin.json` | Claude plugin identity and shared skill path |
| `.claude-plugin/marketplace.json` | Claude marketplace catalog |
| `skills/implementing-staged-plans/SKILL.md` | Canonical routing behavior |
| `skills/implementing-staged-plans/references/` | Focused lifecycle procedures |
| `skills/implementing-staged-plans/scripts/` | Deterministic validation and state helpers |
| `skills/implementing-staged-plans/agents/openai.yaml` | Codex presentation and invocation policy |
| `README.md` | Reader entry point |
| `docs/installation.md` | Platform and installation routes |
| `docs/workflows.md` | Copyable, task-based examples |
| `docs/reference.md` | Terms, modes, permissions, and invocation names |
| `docs/troubleshooting.md` | Symptom-led recovery guidance |
| `tests/test_distribution_documentation.py` | Distribution metadata and reader-document contract |
| `tests/test_package_validation.py` | Package invariants and narrow catalog exceptions |

## Keep one shared skill

Do not create a second copy of the skill under `.claude-plugin/` or
`.codex-plugin/`. Both platform manifests point to `./skills/`, and both hosts
load `skills/implementing-staged-plans/`. A fork would allow behavior and safety
rules to drift between platforms.

Platform-specific metadata may differ where the schemas require it. It must not
change the meaning of the shared skill.

## Keep identity and versions synchronized

Before a versioned release, compare:

- `name`, `version`, `description`, and `skills` in the Codex and Claude
  manifests;
- plugin names and marketplace names in both catalogs;
- the Claude marketplace version with both manifests; and
- every installation selector and invocation example in the reader guides.

The existing Codex manifest has an exact four-field repository contract. Put
display metadata and marketplace policy in `.agents/plugins/marketplace.json`
instead of adding fields to `.codex-plugin/plugin.json`.

Claude marketplace versions are pinned strings. When behavior changes are meant
to reach installed users, update the synchronized package version deliberately
and document the release. Do not bump versions merely to make local validation
pass.

## Refresh platform instructions

Installation commands and schemas can change. Before publication, compare this
repository with the current primary documentation:

- [Build Codex plugins](https://developers.openai.com/plugins/build/plugins)
- [Build and use Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code plugins](https://code.claude.com/docs/en/plugins)
- [Claude plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude Code Desktop](https://code.claude.com/docs/en/desktop)
- [Claude Code in VS Code](https://code.claude.com/docs/en/ide-integrations)

Check the locally installed CLI help as well. Documentation pages describe the
current platform, while the local help describes the client a maintainer can
actually test.

## Validate a change

Run the focused documentation contract first:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_distribution_documentation -v
```

Validate the plugin's own package contract:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py .
```

To compare a caller-selected installed copy without discovering, installing, or
repairing anything, supply its exact root explicitly:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 skills/implementing-staged-plans/scripts/validate_package.py . --compare-installed /absolute/path/to/installed/implementation-plugin
```

The parity inventory is deliberately limited to `.codex-plugin/plugin.json`
and regular files under `skills/implementing-staged-plans/`. Repository docs,
tests, plans, Git metadata, caches, runtime state, and `.claude-plugin/` are not
installed-copy parity owners.

Then run the complete unit-test suite once on the coherent tree:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest
```

Finish with whitespace and local Codex command-shape checks:

```bash
git diff --check
codex plugin add --help
codex plugin marketplace add --help
```

If Claude Code is available and local plugin testing has been approved, add:

```bash
claude plugin validate .
claude --plugin-dir /absolute/path/to/implementation-plugin
```

Loading a plugin starts a host session and is separate from static package
validation. Do not perform it silently in a maintenance-only task.

## What these checks prove

The local tests can establish that required files exist, metadata stays
consistent, reader-document links resolve, examples retain the expected command
and invocation forms, forbidden package surfaces remain blocked, and the
deterministic workflow contracts pass their unit tests.

They do not prove:

- Claude runtime loading;
- marketplace registration or plugin installation;
- listing in a public plugin directory;
- live skill behavior in a real implementation program;
- semantic correctness or human review quality; or
- any commit, push, pull request, publication, release, deployment, or external
  action.

Record each stronger claim only after running the relevant approved test or
action and preserving its direct evidence.

## Release-readiness checklist

- Re-read the canonical skill and all platform manifests.
- Confirm the version and identity fields agree.
- Confirm all examples use fictional project identifiers and contain no secrets
  or private paths.
- Recheck install commands against primary platform documentation and local CLI
  help.
- Confirm standalone copy examples cover macOS or Linux and Windows PowerShell,
  and stop rather than merging into an existing skill directory.
- Run focused tests, package validation, the full suite, and `git diff --check`.
- Review the complete diff and preserve unrelated user work.
- Test local loading in each claimed host when the host is available and that
  action is approved.
- If advertising local `.zip` loading or `--plugin-url`, build and test a trusted
  archive with the minimum documented Claude Code version first.
- Treat marketplace registration, public-directory submission, commits, pushes,
  releases, and publication as separate external actions requiring explicit
  approval.

Passing this checklist makes the tree ready for a release decision. It does not
perform that decision or publish anything.
