# [Pi Coding Agent](https://pi.dev/)

Pi is a minimal, open-source, BYOK (bring your own key) terminal-based AI coding agent created by Mario Zechner. It ships with only four built-in tools (read, write, edit, bash) and a ~300-word system prompt, making it one of the leanest coding agents available. Everything else is added through extensions.

## Why Pi

- **Multi-provider** -- supports 20+ LLM providers (Anthropic, OpenAI, Google, xAI, DeepSeek, Mistral, Groq, and more).
- **Subscription login** -- `/login` works with Claude Pro/Max, ChatGPT Plus/Pro, and GitHub Copilot subscriptions (no API key needed).
- **Extensible** -- skills, prompt templates, themes, and hooks are bundled as Pi packages and shared via npm or git.
- **Session tree** -- every message has an id and parentId; `/tree` navigates, `/fork` branches a new session from the current point.
- **Multiple modes** -- interactive, print/JSON, RPC, and SDK (for embedding Pi in other tools).
- **Auto-compaction** -- context is automatically compacted when approaching limits.
- **Project instructions** -- uses `AGENTS.md` files (in `~/.pi/agent/`, parent dirs, or CWD).

## Trade-offs

- Minimal core means you **need extensions** for features like sub-agents, permissions, or plan mode.
- Younger ecosystem -- fewer extensions and less community content than Claude Code or Cursor.
- Some rough edges remain: agent can hang on provider switches mid-session, `grep`/`diff` exit-code 1 is misreported as an error.

---

## Quickstart

```bash
brew install pi-coding-agent
```

Or via npm:

```bash
npm install -g @earendil-works/pi-coding-agent
```

Verify the install:

```bash
pi --version
pi --help
```

---

## Suggested Extensions

### [context-mode](https://github.com/mksglu/context-mode)

Context window optimization for AI coding agents. Sandboxes tool output so raw bytes never enter the context window -- reducing consumption by up to 98%. Tracks edits, git operations, tasks, errors, and decisions in SQLite with FTS5 full-text search. On compaction, only BM25-ranked relevant content is retrieved.

```bash
pi install npm:context-mode
```

### [pi-caveman](https://github.com/v2nic/pi-caveman)

Ultra-compressed communication mode that cuts ~75% of output tokens while preserving full technical accuracy. Based on [caveman by Julius Brussee](https://github.com/JuliusBrussee/caveman). Provides `/caveman`, `/caveman-commit`, `/caveman-review`, `/caveman-help`, and `/caveman:compress` commands. Supports multiple intensity levels and persists settings across sessions.

```bash
pi install npm:pi-caveman
```

### [pi-subagents](https://github.com/tintinweb/pi-subagents)

Claude Code-style autonomous sub-agents for Pi. Spawn specialized agents in isolated sessions, each with its own tools, system prompt, model, and thinking level. Run foreground or background, steer mid-run, resume completed sessions, and define custom agent types. Includes a live widget UI with spinners, tool activity, and token counts.

```bash
pi install npm:@tintinweb/pi-subagents
```

### [pi-rtk-optimizer](https://github.com/MasuRii/pi-rtk-optimizer)

Automatically rewrites bash tool commands to their [RTK](https://github.com/example/rtk) equivalents and compacts noisy tool output to reduce context window usage. Delegates rewrite decisions to the installed `rtk rewrite` command, keeping RTK as single source of truth. Includes a runtime guard when the `rtk` binary is unavailable. Slash commands: `/rtk show`, `/rtk verify`, `/rtk stats`, `/rtk reset`.

```bash
pi install npm:pi-rtk-optimizer
```

### [pi-permission-system](https://github.com/MasuRii/pi-permission-system)

Centralized, deterministic permission gates for tool, bash, MCP, skill, and special operations. Features tool filtering (hides disallowed tools before the agent starts), system prompt sanitization, runtime enforcement (block/ask/allow with UI confirmation), and bash command control. Supports project-local permission files.

```bash
pi install npm:pi-permission-system
```

---

## Troubleshooting

### Pi won't start after install

**PATH not set.** The `pi` binary may not be on your PATH after `npm install -g`. Verify with `which pi` (macOS/Linux) or `where pi` (Windows). If missing, check `npm config get prefix` and add its `bin/` subdirectory to your PATH.

### `pi install` fails with "not a valid git URL"

**Relative path bug.** Running `pi install local-path` (without `./` prefix) makes Pi treat it as a git URL. Always use the explicit prefix:

```bash
# Wrong
pi install my-extension

# Correct
pi install ./my-extension
```

See [Issue #1426](https://github.com/badlogic/pi-mono/issues/1426).

### Agent hangs or freezes

Several known causes:

- **Provider switch mid-session** -- switching LLM providers while a session is active can cause a hang. Restart the session.
- **Streaming never resolves** -- if the agent is stuck in a "working" state with no progress, interrupt with `Ctrl+C` and restart.
- **Offline/proxy issues** -- use `--offline` or `PI_OFFLINE=1` to disable startup network calls if behind a proxy.

### Extension install issues

- **Temp directory permissions** -- older versions used the OS temp directory for extension installs. Update Pi to a recent version which uses `~/.pi/agent/tmp/extensions` with `0700` permissions.
- **npm registry errors** -- make sure your npm registry is reachable. If behind a corporate proxy, configure npm with `npm config set proxy` / `npm config set https-proxy`.

### grep/diff shows false errors

Pi's bash tool treats `grep`/`diff` exit code 1 (meaning "no matches") as an error. This is a known issue ([#3051](https://github.com/earendil-works/pi/issues/3051)). The agent usually recovers, but may retry unnecessarily.
