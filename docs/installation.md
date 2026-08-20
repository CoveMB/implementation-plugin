# Installation

Choose the route that matches where you use the skill and how you want updates
to be managed. A marketplace installation keeps the plugin package intact. A
standalone installation copies only the skill and is often simpler for one
repository or one user.

The commands below were checked against Codex CLI 0.146.0 and the official
Codex and Claude plugin documentation on August 10, 2026. Claude CLI was not
available in the local verification environment, so the Claude commands are
source-checked rather than runtime-checked. PowerShell was also unavailable, so
the Windows copy examples were reviewed but not run locally.

CLI examples in `bash` blocks use macOS and Linux paths. On Windows, the same
Codex and Claude CLI commands can be entered in PowerShell after replacing each
path with its Windows equivalent. The standalone copy sections provide complete
PowerShell examples because file-copy syntax differs between platforms.

## Trust the source first

A plugin can add instructions and executable helpers to an agent session. Before
installing, inspect the marketplace, plugin manifest, skill instructions, and
scripts at the exact revision you intend to use. Prefer a source you control or
trust, pin a revision when reproducibility matters, and never put credentials in
an installation command or marketplace file.

## Route overview

| Host | Route | Availability | Persistence | Invocation |
| --- | --- | --- | --- | --- |
| Codex app | Public plugin marketplace | Conditional on directory publication | Installed plugin | `$implementing-staged-plans` |
| Codex app and CLI | Repository marketplace | Ready locally; remote after the catalog is published | Installed plugin | `$implementing-staged-plans` |
| Codex app and CLI | Local marketplace path | Available from a checkout | Installed plugin | `$implementing-staged-plans` |
| Codex | Project standalone skill | Available by copying the skill directory | Current repository | `$implementing-staged-plans` |
| Codex | Personal standalone skill | Available by copying the skill directory | Current user | `$implementing-staged-plans` |
| Codex | `$skill-installer` | Available when the source repository is accessible | Current user | `$implementing-staged-plans` |
| Claude Code Desktop | Plugin browser in the Code tab | Remote after the catalog is published; local marketplaces can be configured separately | Installed plugin | `/implementation-plugin:implementing-staged-plans` |
| Claude Code in VS Code | Graphical `/plugins` manager | Remote after the catalog is published; local marketplace path available now | Installed plugin | `/implementation-plugin:implementing-staged-plans` |
| Claude Code | Interactive marketplace commands | Remote after the catalog is published; local path available now | Installed plugin | `/implementation-plugin:implementing-staged-plans` |
| Claude Code | CLI marketplace commands | Remote after the catalog is published; local path available now | Installed plugin | `/implementation-plugin:implementing-staged-plans` |
| Claude Code | `--plugin-dir` development load | Available from a checkout or local `.zip` archive | Current session | `/implementation-plugin:implementing-staged-plans` |
| Claude Code | `--plugin-url` archive load | Conditional on a trusted packaged archive | Current session | `/implementation-plugin:implementing-staged-plans` |
| Claude Code | Project standalone skill | Available by copying the skill directory | Current repository | `/implementing-staged-plans` |
| Claude Code | Personal standalone skill | Available by copying the skill directory | Current user | `/implementing-staged-plans` |

## Install as a Codex plugin

### From the repository marketplace

Once the marketplace catalog is available on the repository's default branch,
register it and install the plugin:

```bash
codex plugin marketplace add CoveMB/implementation-plugin --ref main
codex plugin add implementation-plugin@implementation-workflows
codex plugin list
```

Adding a marketplace only registers the catalog. The second command installs
the plugin from that catalog. `codex plugin list` lets you confirm the installed
plugin and its enabled state.

These remote commands are publication-dependent. They will not work until the
catalog and plugin files exist on the named accessible revision.

Codex also accepts HTTPS and SSH Git marketplace sources. These forms register
the same repository through a different transport:

```bash
codex plugin marketplace add https://github.com/CoveMB/implementation-plugin.git --ref main
codex plugin marketplace add git@github.com:CoveMB/implementation-plugin.git --ref main
```

Use SSH only when your existing Git credentials authorize that repository.

### From a local checkout

Use an absolute path so the catalog remains unambiguous:

```bash
codex plugin marketplace add /absolute/path/to/implementation-plugin
codex plugin add implementation-plugin@implementation-workflows
codex plugin list
```

This is the quickest way to test repository changes before publication. Keep the
checkout available until installation is confirmed, and register it again if
you move it.

### From the Codex app marketplace

If the plugin appears in the Codex plugin marketplace, open its page and choose
Install. Public-directory discovery is a separate publication step; including a
marketplace catalog in this repository does not list it automatically.

For a custom repository marketplace, register the catalog with the CLI first.
The app and CLI use the same plugin package identity, so the installed skill is
invoked as `$implementing-staged-plans`.

## Install as a standalone Codex skill

Use this route when you want the skill without marketplace metadata. Copy the
entire `implementing-staged-plans` directory because it contains referenced
procedures and validation scripts. The examples below are for a first install:
they stop if the destination already exists so an earlier copy is not merged or
overwritten. Compare an existing copy with the new source before updating it.

### For one repository

From the target repository:

On macOS or Linux:

```bash
mkdir -p .agents/skills
test ! -e .agents/skills/implementing-staged-plans && cp -R /absolute/path/to/implementation-plugin/skills/implementing-staged-plans .agents/skills/implementing-staged-plans
```

On Windows PowerShell:

```powershell
$skillSource = "C:\absolute\path\to\implementation-plugin\skills\implementing-staged-plans"
$skillDestination = Join-Path (Get-Location) ".agents\skills\implementing-staged-plans"
New-Item -ItemType Directory -Force (Split-Path $skillDestination) | Out-Null
if (Test-Path $skillDestination) {
    throw "Destination already exists: $skillDestination"
}
Copy-Item -Recurse $skillSource $skillDestination
```

Restart or reload Codex after adding the skill. Repository skills are useful
when a team wants the same version checked into the project.

### For the current user

On macOS or Linux:

```bash
mkdir -p ~/.agents/skills
test ! -e ~/.agents/skills/implementing-staged-plans && cp -R /absolute/path/to/implementation-plugin/skills/implementing-staged-plans ~/.agents/skills/implementing-staged-plans
```

On Windows PowerShell:

```powershell
$userRoot = [Environment]::GetFolderPath("UserProfile")
$skillSource = "C:\absolute\path\to\implementation-plugin\skills\implementing-staged-plans"
$skillDestination = Join-Path $userRoot ".agents\skills\implementing-staged-plans"
New-Item -ItemType Directory -Force (Split-Path $skillDestination) | Out-Null
if (Test-Path $skillDestination) {
    throw "Destination already exists: $skillDestination"
}
Copy-Item -Recurse $skillSource $skillDestination
```

Personal skills are available across repositories for that user. A copied skill
does not update automatically when this repository changes.

### With the skill installer

Ask Codex to install the skill from its repository subdirectory:

```text
Use $skill-installer to install
https://github.com/CoveMB/implementation-plugin/tree/main/skills/implementing-staged-plans
```

This route also depends on the named source being accessible. Review the source
and revision before installing it.

## Install as a Claude Code plugin

Plugin installation preserves the package namespace. The skill is invoked as
`/implementation-plugin:implementing-staged-plans`.

### From Claude Code Desktop

In the Claude Desktop app, open the Code tab and start a local or SSH session.
Choose **Plugins** from the **+** menu beside the prompt, then choose **Add
plugin** to browse the configured marketplaces. Select this plugin and install
it for the scope you want.

The desktop plugin browser displays plugins from marketplaces that are already
configured for Claude Code. Plugins are not available in remote desktop
sessions.

### From Claude Code in VS Code

Open the Claude Code panel in VS Code and enter `/plugins` to open the graphical
plugin manager. Use the **Marketplaces** tab to add the GitHub repository, a
catalog URL, or an absolute local marketplace path. Then use the **Plugins** tab
to install the plugin and choose user, project, or local scope. Follow any
restart banner before trying the invocation.

The VS Code extension and CLI share their installed plugins and marketplace
configuration, so a plugin installed through either surface is available to
the other.

### From an interactive Claude Code session

For the repository marketplace:

```text
/plugin marketplace add CoveMB/implementation-plugin
/plugin install implementation-plugin@implementation-workflows
/reload-plugins
```

For a local checkout, replace the repository name in the first command with the
absolute path to the checkout.

### From the Claude CLI

```bash
claude plugin marketplace add CoveMB/implementation-plugin
claude plugin install implementation-plugin@implementation-workflows
```

For local verification:

```bash
claude plugin marketplace add /absolute/path/to/implementation-plugin
claude plugin install implementation-plugin@implementation-workflows
```

The repository commands become usable only after the marketplace files are
available at the remote source. The local path route does not require
publication.

Claude marketplace registration also accepts a full Git URL or a direct URL to
a hosted `marketplace.json` file. A direct catalog URL is useful only when every
plugin source in that catalog remains fetchable from the published location.

By default, Claude records marketplaces and plugins for the current user. Use an
explicit scope when a team should share the configuration or when it should stay
local to one checkout:

```bash
claude plugin marketplace add CoveMB/implementation-plugin --scope project
claude plugin install implementation-plugin@implementation-workflows --scope project
claude plugin marketplace add /absolute/path/to/implementation-plugin --scope local
claude plugin install implementation-plugin@implementation-workflows --scope local
```

Project scope writes shared project configuration; local scope uses local,
normally uncommitted configuration. Review the resulting settings change before
sharing it.

### Load a checkout or local archive for one session

During plugin development, load the package directory directly:

```bash
claude --plugin-dir /absolute/path/to/implementation-plugin
```

Claude Code 2.1.128 or later also accepts a local `.zip` archive through the
same option:

```bash
claude --plugin-dir /absolute/path/to/implementation-plugin-0.1.2.zip
```

Neither command installs the plugin permanently. The archive must contain a
valid plugin at its root. Claude Code 2.1.129 or later can also load a packaged
`.zip` archive from a trusted URL for one session:

```bash
claude --plugin-url https://example.com/implementation-plugin-0.1.2.zip
```

This repository does not currently publish a `.zip` archive. Do not point
`--plugin-url` at the Git repository itself; the URL must return the archive
bytes. Check `claude --help` when using a different client version.

## Install as a standalone Claude Code skill

Standalone Claude skills are not plugin-namespaced, so invoke this copy as
`/implementing-staged-plans`.

### For one repository

On macOS or Linux:

```bash
mkdir -p .claude/skills
test ! -e .claude/skills/implementing-staged-plans && cp -R /absolute/path/to/implementation-plugin/skills/implementing-staged-plans .claude/skills/implementing-staged-plans
```

On Windows PowerShell:

```powershell
$skillSource = "C:\absolute\path\to\implementation-plugin\skills\implementing-staged-plans"
$skillDestination = Join-Path (Get-Location) ".claude\skills\implementing-staged-plans"
New-Item -ItemType Directory -Force (Split-Path $skillDestination) | Out-Null
if (Test-Path $skillDestination) {
    throw "Destination already exists: $skillDestination"
}
Copy-Item -Recurse $skillSource $skillDestination
```

### For the current user

On macOS or Linux:

```bash
mkdir -p ~/.claude/skills
test ! -e ~/.claude/skills/implementing-staged-plans && cp -R /absolute/path/to/implementation-plugin/skills/implementing-staged-plans ~/.claude/skills/implementing-staged-plans
```

On Windows PowerShell:

```powershell
$userRoot = [Environment]::GetFolderPath("UserProfile")
$skillSource = "C:\absolute\path\to\implementation-plugin\skills\implementing-staged-plans"
$skillDestination = Join-Path $userRoot ".claude\skills\implementing-staged-plans"
New-Item -ItemType Directory -Force (Split-Path $skillDestination) | Out-Null
if (Test-Path $skillDestination) {
    throw "Destination already exists: $skillDestination"
}
Copy-Item -Recurse $skillSource $skillDestination
```

Reload Claude Code after adding a standalone skill. For an update, compare the
existing destination with the new source and replace it deliberately; do not
merge a new directory into it.

## Refresh an installed plugin

For Codex, refresh the Git marketplace snapshot and inspect the available and
installed versions:

```bash
codex plugin marketplace upgrade implementation-workflows
codex plugin list
```

The current Codex CLI does not expose a separate `plugin update` command. Follow
the installed client's UI or release guidance before replacing an installed
copy.

For Claude Code, update the marketplace and then the installed plugin:

```bash
claude plugin marketplace update implementation-workflows
claude plugin update implementation-plugin@implementation-workflows
```

Updating is a configuration and network action. Run it intentionally and review
the new source revision before enabling changed plugin code.

## Which route should you choose?

- Use a marketplace when you want a normal plugin installation and a stable
  plugin identity.
- Use a local marketplace or `--plugin-dir` while developing or reviewing this
  repository.
- Use a project skill when the repository should pin and share the workflow.
- Use a personal skill when you want the workflow available across your own
  repositories.

After installation, continue with [Common workflows](workflows.md) or check the
[invocation reference](reference.md).

## Official platform references

- [Build Codex plugins](https://developers.openai.com/plugins/build/plugins)
- [Build and use Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code plugins](https://code.claude.com/docs/en/plugins)
- [Claude Code Desktop](https://code.claude.com/docs/en/desktop)
- [Claude Code in VS Code](https://code.claude.com/docs/en/ide-integrations)
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference)
