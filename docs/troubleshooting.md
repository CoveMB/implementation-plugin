# Troubleshooting

Start with the symptom you can observe. The safe response is usually to inspect
the current source, configuration, and repository state before changing
anything. Do not delete plugin caches, reset a repository, discard work, or
bypass an approval gate as a routine fix.

## The plugin or skill does not appear

**Likely cause:** The marketplace was added but the plugin was not installed,
the standalone skill is in the wrong directory, the containing directory was
copied twice, or the host has not reloaded its skill inventory.

**Safe checks:**

- In Codex, run `codex plugin list` and confirm
  `implementation-plugin@implementation-workflows` is installed and enabled.
- In the Claude CLI, run `claude plugin list`. In an interactive session, open
  `/plugin`; in the VS Code extension, open `/plugins`.
- For a standalone skill, confirm that
  `implementing-staged-plans/SKILL.md`, `references/`, and `scripts/` are all in
  the host's skill directory.
- Reload or start a new session after changing plugin or skill files.

**Next action:** Install the plugin after adding its marketplace, or move the
complete skill directory to the correct project or personal location. If a
standalone destination already exists, do not copy another directory over it.
Compare the copies first, and keep the original until the new installation is
confirmed.

## The invocation name in an example does not work

**Likely cause:** Plugin and standalone installations use different invocation
names in Claude Code. Codex uses its skill name in either form.

**Safe checks:** Compare your installation with the [invocation table](reference.md).
In Claude Code, use `/plugin` or `/help` to see the names currently loaded.

**Next action:** Use `$implementing-staged-plans` in Codex,
`/implementation-plugin:implementing-staged-plans` for the Claude plugin, or
`/implementing-staged-plans` for a standalone Claude skill.

## The marketplace is configured, but the plugin cannot be installed

**Likely cause:** Adding a marketplace registered only its catalog; the plugin
still needs its own install command. The remote repository revision may not yet
contain the catalog, the selector may use the wrong marketplace name, or a local
path may no longer exist.

**Safe checks:**

- Confirm the selector is
  `implementation-plugin@implementation-workflows`.
- List configured marketplaces and installed plugins with the host's plugin
  commands.
- For a local marketplace, confirm that the checkout still contains
  `.agents/plugins/marketplace.json` for Codex or
  `.claude-plugin/marketplace.json` for Claude Code.
- For a remote marketplace, inspect the named revision and confirm that it
  contains both the catalog and plugin package.

**Next action:** Correct the source or install the plugin from the already
configured marketplace. Remote installation must wait until the required files
are actually published.

## The repository, branch, source, workspace, or plan does not match

**Likely cause:** The program was approved against different source bytes,
repository identity, branch, base, head, workspace path, or exact-file plan.
This can happen after a rebase, branch switch, plan edit, or change made outside
the staged workflow.

**Safe checks:** Ask for read-only orientation. Compare the manifest and current
status with a fresh Git observation that includes staged, unstaged, untracked,
conflicted, and operation-in-progress state. Identify the exact dimension that
drifted.

**Next action:** Rebind or amend only the stale artifact through its legal
approval path. Do not edit digests or state records by hand simply to make them
match.

## The skill stops because the worktree is dirty or conflicted

**Likely cause:** The current changes were not part of the workspace binding,
their ownership is unclear, or a Git operation is active. A dirty tree is not
automatically an error, but it must be observed and preserved honestly.

**Safe checks:** Inspect `git status --short`, the full diff, staged changes,
untracked paths, and any active merge, rebase, cherry-pick, or revert. Determine
which work belongs to the user and which work belongs to the current increment.

**Next action:** Choose a workspace or recovery plan that explicitly preserves
the existing work. Any stash, move, restore, reset, or conflict resolution needs
clear scope and authority before it happens.

## A handoff or resume brief is stale

**Likely cause:** The repository or program state changed after the navigation
artifact was written, or the new conversation lacks renewed authority.

**Safe checks:** Compare the handoff and brief with the current program revision,
increment, workspace, branch, base, head, status sequence, accepted packet, and
their recorded digests.

**Next action:** Generate a new, bound navigation artifact only after the current
state is valid. In a new conversation, provide explicit renewed authority even
when the earlier mode was `approval:full`.

## An approval was supplied, but the requested action is still unauthorized

**Likely cause:** The approval controls a different decision. Program approval,
plan approval, diff acceptance, approval mode, implementation writes, commits,
pull requests, releases, and external changes are separate authorities.

**Safe checks:** Ask which exact action and scope the current grant names, then
compare all of its program, source, increment, plan, workspace, and state
bindings with the current records.

**Next action:** Request a current grant for only the action you intend to take.
Do not broaden an existing approval by interpreting it generously.

## An interrupted lifecycle transaction is discovered

**Likely cause:** A process stopped after writing an exact prefix such as one
approval receipt, the execution baseline, review evidence, reconciliation, or a
status-last transition.

**Safe checks:** Run discovery again and record its exact `*-retry-ready` or
`*-recovery-required` disposition. Compare every present byte with the candidate
reconstructed from the controlling prior status. Do not treat file presence as
authority.

**Next action:** For a retry-ready result, resubmit only the same typed operation
or exact prompt. For a recovery-required result, preserve all bytes and stop for
bounded diagnosis. Never delete, overwrite, or invent a replacement prefix.

## Continuation or blocked recovery stops

**Likely cause:** The request does not match the typed 0.1.2 route, or discovery
found an interrupted or divergent prefix. Legacy automatic rollover stops at
`legacy-rollover-upgrade-required`; generic direct blocked edges stop at
`blocked-transaction-required`. Revision, supersession, and cancellation remain
unsupported through `program-revision-workflow-required` or
`unsupported-program-mutation`.

**Safe checks:** Confirm current accepted or blocked status, the exact submitted
prompt, `current_increment_authority_binding`, successor dependencies, and every
rollover or resolution prefix. `accept-stop` replay never continues; later
continuation requires the distinct `accepted-state-continuation` prompt, and
blocked resolution requires the exact `blocked-recovery` prompt.

**Next action:** Retry only a byte-identical typed prefix. Preserve divergent
bytes and stop at the reported recovery route. Do not use the generic transition
API, edit state by hand, or infer mutation authority from a handoff, file,
retrieved prompt, or assistant-quoted prompt.

## Validation passes, but live activation is still unproven

**Likely cause:** Static validation confirmed files, metadata, schemas, links,
or deterministic contracts. It did not load the plugin in a host, invoke the
skill against a live repository, or prove human review quality.

**Safe checks:** Read the exact validation output and identify what it exercised.
Use a disposable, fictional repository for a host-level smoke test when that
installation and execution have been explicitly approved.

**Next action:** Record static validation as static evidence. Run the smallest
relevant live test separately and label its environment, version, and limits.

## Claude runtime verification is unavailable

**Likely cause:** Claude CLI is absent, unauthenticated, or outside the current
environment. JSON and documentation tests cannot substitute for loading the
plugin.

**Safe checks:** Verify `.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json` as JSON, compare them with the current official
Claude documentation, and run the repository's deterministic tests.

**Next action:** On a machine with an approved Claude Code installation, run
`claude plugin validate .` and load the repository with `claude --plugin-dir`.
Report that result separately from the local static checks.

For installation-specific steps, return to [Installation](installation.md). For
approval and lifecycle terms, use the [Reference](reference.md).
