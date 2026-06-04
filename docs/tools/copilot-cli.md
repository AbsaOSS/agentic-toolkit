# [GitHub Copilot CLI](https://github.com/features/copilot/cli)

GitHub Copilot CLI is a fully agentic, terminal-native coding agent from GitHub. Not to be confused with the older `gh copilot suggest` shell helper -- this is a complete autonomous agent that edits files, runs commands, creates PRs, and iterates toward goals. It supports multiple LLM providers (Claude, GPT, Gemini) within the same tool and integrates natively with the GitHub ecosystem.

## Why Copilot CLI

- **Multi-model** -- switch between Claude Sonnet/Opus, GPT-5.x, and Gemini models mid-session via `/model`.
- **Plan + Autopilot modes** -- Plan mode builds a structured approach for your review; Autopilot executes autonomously.
- **Built-in GitHub integration** -- repos, issues, PRs, and code search through natural language.
- **MCP server support** -- GitHub's own MCP server built-in, plus custom MCP servers.
- **LSP support** -- go-to-definition, hover, and diagnostics for richer code understanding.
- **Custom agents** -- define reusable `.agent.md` files with specialized instructions and tools.
- **Subscription-based** -- uses your existing GitHub Copilot subscription (Free through Enterprise).

## Trade-offs

- Requires a GitHub Copilot subscription (usage-based AI Credits since June 2026).
- Opus models restricted to Pro+ and above.
- MCP tool schemas add token overhead -- 40 tools can cost 10-15KB per turn.
- Younger than Claude Code as an agentic tool; ecosystem still maturing.
- Some Windows-specific rendering issues (flickering, keyboard input).

---

## Quickstart

```bash
# npm
npm install -g @github/copilot

# Homebrew
brew install github/copilot/copilot

# WinGet (Windows)
winget install GitHub.CopilotCLI

# Shell script
curl -fsSL https://cli.github.com/copilot/install.sh | bash
```

Authenticate:

```bash
copilot auth
```

Requires an active GitHub Copilot subscription (Free, Pro, Pro+, Max, Business, or Enterprise).

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `/model` | Switch AI model mid-session |
| `/compact` | Manually compress session context |
| `/clear` | Reset conversation context |
| `/session` | Show session metrics |
| `/usage` | Show token usage metrics |
| `/add-dir` | Grant access to specific directories |
| `/remote` | Control session from github.com or mobile |
| `/chronicle` | Review session history with personalized tips |
| `/every` | Schedule recurring prompt at interval |
| `/after` | Schedule one-shot prompt after delay |
| `/rubber-duck` | Adversarial feedback mode |
| `/experimental` | Toggle experimental features |

Full reference: [CLI Command Reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference)

---

## Custom Instructions

Copilot CLI uses `copilot-instructions.md` files (not `CLAUDE.md` or `AGENTS.md`):

| Scope | Location |
|-------|----------|
| Global | `~/.copilot/copilot-instructions.md` |
| Repository | `.github/copilot-instructions.md` |
| Path-specific | `.github/instructions/NAME.instructions.md` (with path globs) |

Custom agents use `.agent.md` files:

| Scope | Location |
|-------|----------|
| Global | `~/.copilot/agents/NAME.agent.md` |
| Project | `.github/agents/NAME.agent.md` |

Invoke with: `copilot --agent=refactor-agent --prompt "..."`. See [Creating Custom Agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli).

---

## Configuration

Config lives in `~/.copilot/` (override with `COPILOT_HOME` env var).

| File | Purpose |
|------|---------|
| `settings.json` | User preferences (JSONC) |
| `config.json` | Internal application state |
| `copilot-instructions.md` | Global custom instructions |

Settings cascade: User -> Repository -> Local. CLI flags and env vars take highest precedence.

**Key environment variables:**

| Variable | Purpose |
|----------|---------|
| `COPILOT_HOME` | Redirect config/state storage |
| `COPILOT_GITHUB_TOKEN` | Auth token (also checks `GH_TOKEN`, `GITHUB_TOKEN`) |
| `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` | Comma-separated list of instruction directories |

---

## Token-Saving Extensions

Each MCP tool registration costs 100-500 tokens per step. With many servers, overhead adds up fast. These extensions help keep token usage under control.

### [caveman](https://github.com/JuliusBrussee/caveman)

Ultra-compressed communication mode that cuts ~75% of output tokens while keeping full technical accuracy. Caveman ships rule files that auto-detect Copilot CLI during install. The agent speaks in terse, fragment-style responses -- all technical substance preserved, all filler removed.

Install on Windows:

```powershell
irm https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.ps1 | iex
```

Install on macOS/Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash
```

Caveman installs as always-on rule files for Copilot CLI (not a plugin/extension). Rules are placed in your `copilot-instructions.md`.

### [context-mode](https://github.com/mksglu/context-mode)

Context window optimization via MCP server. Sandboxes tool output so raw bytes never enter the context window -- up to 98% reduction. Tracks edits, git operations, tasks, and errors in SQLite with FTS5 search. On compaction, retrieves only BM25-ranked relevant content.

Copilot CLI support since v1.0.0. Connects as a custom MCP server:

```bash
npm install -g context-mode
```

Then add to your Copilot CLI MCP configuration. See [platform support docs](https://github.com/mksglu/context-mode/blob/main/docs/platform-support.md) for Copilot-specific setup.

### [RTK (Rust Token Killer)](https://github.com/rtk-ai/rtk)

CLI proxy that rewrites verbose shell commands into token-optimized equivalents (60-90% savings on dev operations). Two approaches for Copilot CLI:

**Official RTK init:**

```bash
rtk init -g --copilot
```

**Community approach** -- [rtk-for-copilot](https://github.com/Martin-Sciarrillo/rtk-for-copilot) uses `copilot-instructions.md` to teach the agent to route commands through RTK. No hooks needed; place instructions at `~/.copilot/copilot-instructions.md` (global) or `.github/copilot-instructions.md` (per-repo).

---

## Troubleshooting

### Authentication fails

Run `copilot auth` to re-authenticate. Check that `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, or `GITHUB_TOKEN` is set correctly if using env vars. Older clients may fail to communicate with servers -- keep the tool updated.

### Rate limiting / credits exhausted

Copilot CLI enforces session and weekly (7-day) limits based on token consumption with model multipliers. Opus models consume credits faster. Check remaining credits with `/usage`. Downgrade model with `/model` to stretch budget.

### High token overhead from MCP tools

Each registered MCP tool schema is included in every API call. 15 servers x 15 steps = ~265K tokens of overhead from unused tools. Audit with GitHub's `copilot-token-audit` extension. Remove MCP servers you don't actively use.

### Windows rendering issues

Known platform-specific bugs with terminal flickering, scrolling, and keyboard input. Keep the tool updated; many are fixed in recent releases.

---

## Links

- [Product Page](https://github.com/features/copilot/cli) -- [Documentation](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/overview) -- [GitHub](https://github.com/github/copilot-cli) -- [npm](https://www.npmjs.com/package/@github/copilot) -- [Plans & Pricing](https://github.com/features/copilot/plans)
