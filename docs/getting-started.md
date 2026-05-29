# Getting Started

This guide covers what skills are, how to install them, and how to use them in your AI-assisted engineering workflow.

## What Is a Skill?

A **skill** is a folder containing instructions, scripts, and reference material that an AI agent loads on demand.
Skills follow the open [Agent Skills](https://agentskills.io) standard and work with GitHub Copilot, Claude, Cursor, and
other compatible tools.

Skills manage LLM context efficiently — the agent does **not** receive all skill content at startup. Instead, it loads
content progressively:

| Phase          | What Happens                                                                                              |
|----------------|-----------------------------------------------------------------------------------------------------------|
| **Discovery**  | At startup, the agent loads only the `name` and `description` of each installed skill                     |
| **Activation** | When your task matches a skill's description, the agent reads the full `SKILL.md` into context            |
| **Execution**  | The agent follows the skill's instructions, optionally loading reference files or running bundled scripts |

> ⚠️ **The `description` field is the sole activation signal.** If a skill isn't firing, your prompt likely doesn't
> match its description keywords. Rephrase your message to include relevant trigger terms from the skill's description.
> Inside a Copilot CLI session, run `/skills list` to inspect loaded descriptions.
> Outside the CLI, you can run `npx skills list -g` to see all the installed skills.

## Prerequisites: Install Copilot CLI

We use the [GitHub Copilot CLI](https://github.com/github/copilot-cli) as the primary AI-assisted engineering tool.

```bash
# macOS / Linux
curl -fsSL https://gh.io/copilot-install | bash

# macOS (Homebrew)
brew install copilot-cli

# Any platform (npm)
npm install -g @github/copilot
```

Then launch a session from your project directory:

```bash
copilot
```

## Install Skills

### Option A: Vercel Skills CLI (recommended)

The [Vercel Skills CLI](https://github.com/vercel-labs/skills) automates installation via `npx`:

```bash
# List available skills from this repo without installing them
npx skills add https://github.com/AbsaOSS/agentic-toolkit --list

# Install all skills globally (available in every project)
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g

# Install a single skill globally (--skill filters by folder name within the repo)
npx skills add https://github.com/AbsaOSS/agentic-toolkit -g --skill pr-review

# Install project-scoped (into .github/skills/ of the current repo)
npx skills add https://github.com/AbsaOSS/agentic-toolkit
```

> To share project-scoped skills with your team, commit the `.github/skills/` directory.

On first install, `npx skills add` asks two questions interactively:

| Prompt                          | Options                                             | Recommendation                                                                                                                                                                         |
|---------------------------------|-----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Installation method**         | `Symlink` / `Copy`                                  | Use **Symlink** — a single copy lives on disk, and `npx skills update` refreshes it in place. Use **Copy** only if symlinks aren't supported in your environment.                      |
| **Which agents to install to?** | A specific agent directory / **Copy to all agents** | Choose **Copy to all agents** if you want the skills available in Copilot, Claude, Cursor, and any other compatible tool simultaneously. Pick a specific directory to limit the scope. |

These choices are recorded and reused on subsequent updates — you won't be asked again unless you reinstall from
scratch. The global skills directory used is typically `~/.agents/skills/` (recommended for cross-tool compatibility)
or `~/.copilot/skills/`. See [Skills directory location varies](./troubleshooting.md#skills-directory-location-varies)
if you need
to change it later.

#### Update installed skills

```bash
npx skills update         # interactive — prompts for scope
npx skills update -g      # update global skills
npx skills update -y      # auto-detects scope: project-scope if running within a project, else global
```

### Option B: Manual install

Clone this repo and copy skills into your personal space:

```bash
git clone https://github.com/AbsaOSS/agentic-toolkit.git
cp -r agentic-toolkit/skills/*/ ~/.agents/skills/
```

Skills copied into `~/.agents/skills/` (or `~/.copilot/skills/`) are loaded automatically at every session start — no
further action needed.

## Verify Skills Are Loaded

Inside a Copilot CLI session:

```
/skills list    # See all loaded skills and their descriptions
/env            # Full environment: skills, agents, MCP servers, instructions
```

Confirm the skills appear in the list.

## Using Skills in Copilot CLI

GitHub Copilot CLI resolves skills from two locations:

| Scope       | Location                                    | When To Use                                           |
|-------------|---------------------------------------------|-------------------------------------------------------|
| **Global**  | `~/.agents/skills/` or `~/.copilot/skills/` | Available across all projects                         |
| **Project** | `.github/skills/`                           | Specific to one repo — commit to share with your team |

Project skills take precedence over global skills when both exist.

### Managing skills mid-session

```
/skills add <path>        # Add a skill to the current session (temporary)
/skills remove <name>     # Remove a skill from the current session (temporary)
```

> Session-level changes are temporary. Use `npx skills add` or the manual copy for permanent changes.

### Add project-specific skills

For skills that only apply to a specific repository, place them in `.github/skills/` within that repo. These are loaded
automatically when Copilot CLI is launched from that directory, layered on top of your global skills.

```
your-project-repo/
└── .github/
    └── skills/
        └── your-project-skill/
            └── SKILL.md
```

## Troubleshooting

Running into issues? See **[docs/troubleshooting.md](./troubleshooting.md)** guide.
