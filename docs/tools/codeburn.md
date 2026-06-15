# [CodeBurn](https://codeburn.app/)

CodeBurn is an open-source CLI and TUI dashboard that tracks AI coding token usage, cost, and performance across 25+ AI coding tools. It breaks down spending by task type, model, tool, project, and provider. Everything runs locally -- no wrapper, no proxy, no API keys. Built by [AgentSeal](https://github.com/getagentseal).

## Why CodeBurn

- **25+ providers** -- Claude Code, Cursor, Codex, Gemini CLI, Pi, Copilot, Cline, Roo Code, and many more. Auto-detected from session data on disk.
- **Zero overhead** -- reads existing session files directly, prices calls via LiteLLM. No proxy or API key needed.
- **Task classification** -- deterministic categorization (coding, debugging, feature dev, refactoring, testing, exploration, planning, delegation, git ops, build/deploy, brainstorming, conversation) from tool usage patterns, no LLM calls.
- **One-shot rate** -- tracks how often the AI gets edits right on the first try, per model and task category.
- **macOS menubar app** -- live spend widget that refreshes every 30 seconds.

## Trade-offs

- Menubar mode is macOS-only (Swift/SwiftUI).
- Cursor support degraded -- Cursor stopped writing per-call token counts to its local DB in early 2026, so parsing may report $0.
- Some providers (Kiro, Copilot) estimate tokens from content length since session data lacks explicit counts.

---

## Quickstart

```bash
brew tap getagentseal/codeburn
brew install codeburn
```

Or via npm:

```bash
npm install -g codeburn
```

Or run without installing:

```bash
npx codeburn
```

Launch the interactive TUI dashboard:

```bash
codeburn
```

---

## Menubar Mode (macOS)

Install and launch with a single command:

```bash
codeburn menubar
```

Reinstall with `codeburn menubar --force`. The menubar icon shows spend for the selected period. Click to open a popover with agent tabs, trend/forecast/pulse/stats views, activity breakdowns, optimize findings, and CSV/JSON export.

**Configure period from terminal:**

```bash
defaults write org.agentseal.codeburn-menubar CodeBurnMenubarPeriod -string month
```

Allowed values: `today`, `week`, `month`, `sixMonths`.

**Compact mode** (drops decimals):

```bash
defaults write org.agentseal.codeburn-menubar CodeBurnMenubarCompact -bool true
```

---

## Commands

### Dashboard & Reports

| Command | Description |
|---------|-------------|
| `codeburn` | Interactive TUI dashboard (default: 7 days) |
| `codeburn today` | Today-only view |
| `codeburn month` | Current month view |
| `codeburn status` | Compact one-liner with today + month totals |
| `codeburn report` | Full report with custom period/format |

Report supports filters:

```bash
codeburn report -p 30days
codeburn report -p all
codeburn report --from 2026-04-01 --to 2026-04-10
codeburn report --provider claude
codeburn report --project myapp
codeburn report --format json
codeburn report --refresh 60          # auto-refresh interval in seconds
```

### Analysis

| Command | Description |
|---------|-------------|
| `codeburn optimize` | Find waste patterns, get copy-paste fixes (graded A-F) |
| `codeburn compare` | Side-by-side model comparison (1-shot rate, cost/edit, cache hit) |
| `codeburn yield` | Productive vs reverted vs abandoned spend (requires git repo) |
| `codeburn models` | Per-model token and cost table |

```bash
codeburn optimize -p today
codeburn compare -p week --provider claude
codeburn yield -p 30days
codeburn models --by-task --top 10
```

### Export

```bash
codeburn export                       # CSV (today, 7d, 30d)
codeburn export -f json
codeburn export --project inventory
```

### Configuration

| Command | Description |
|---------|-------------|
| `codeburn plan set claude-max` | Track against $200/month plan |
| `codeburn plan set claude-pro` | Track against $20/month plan |
| `codeburn plan set custom --monthly-usd 200 --provider codex` | Custom plan |
| `codeburn plan reset` | Remove plan config |
| `codeburn currency GBP` | Set display currency (162 ISO 4217 codes) |
| `codeburn currency --reset` | Back to USD |
| `codeburn model-alias "my-proxy" "claude-opus-4-6"` | Map proxy model names |

### TUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `1`-`5` | Switch period (Today, 7D, 30D, Month, 6M) |
| `c` | Model comparison |
| `o` | Optimize view |
| `b` | Go back |
| `p` | Toggle providers |

---

## Suggested Workflow

1. Run `codeburn optimize` to find waste. Wait 48 hours, run again to see improvement.
2. After a week, use `codeburn compare` to decide if your default model fits your task mix.
3. In git repos, run `codeburn yield` monthly to see how much AI spend translates into landed commits.
4. Watch one-shot rate per category weekly -- this tracks your prompting skill, not just the model.

### Reading the Dashboard

| Signal | Likely meaning |
|--------|---------------|
| Cache hit < 80% | System prompt or context not stable |
| Lots of `Read` calls | Agent re-reading same files, missing context |
| Low 1-shot rate (~30%) | Agent stuck in retry loops |
| Opus dominating small turns | Overpowered model for simple tasks |
| Bash dominated by `git status`, `ls` | Agent exploring instead of executing |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CLAUDE_CONFIG_DIR` | Override Claude Code data directory |
| `CLAUDE_CONFIG_DIRS` | OS-delimited list of Claude directories to scan together |
| `CODEX_HOME` | Override Codex data directory |

Multiple Claude configs can be merged:

```bash
CLAUDE_CONFIG_DIRS=~/.claude-work:~/.claude-personal codeburn
```

---

## Troubleshooting

### No data showing

CodeBurn reads session files from disk. If a provider shows no data, verify the tool has been used and check that its data directory exists. Use environment variables to point to non-default locations.

### Cursor shows $0

Cursor stopped writing per-call token counts to `state.vscdb` in early 2026. This is a Cursor-side change, not a CodeBurn bug.

### First run is slow

On large Cursor databases, the first scan can take up to a minute. Results are cached after.

### JSON integration

```bash
codeburn report --format json | jq '.projects'
codeburn today --format json | jq '.overview.cost'
```

---

## Links

- [Website](https://codeburn.app/) -- [Documentation](https://codeburn.app/docs) -- [GitHub](https://github.com/getagentseal/codeburn) -- [npm](https://www.npmjs.com/package/codeburn) -- [Discord](https://discord.gg/w2sw8mCqep)
