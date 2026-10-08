# Tools for Agentic Development

A curated catalog of tools that support AI-powered agentic programming workflows. Each tool has its own guide covering what it does, how to get started, recommended extensions, and common issues.

## What Are Agentic Development Tools?

Agentic development tools are CLI-based AI coding agents that operate directly in your terminal. They read, write, and edit code, run shell commands, and iterate autonomously toward a goal you describe in natural language. Unlike traditional IDE copilots that autocomplete single lines, agentic tools take ownership of multi-step tasks: implementing features, debugging across files, running tests, and fixing what breaks.

## Tool Guides

| Tool | Description |
|------|-------------|
| [Pi](./pi.md) | Minimal, open-source, BYOK terminal coding agent with a rich extension ecosystem |
| [GitHub Copilot CLI](./copilot-cli.md) | Multi-model agentic terminal agent with native GitHub integration |
| [CodeBurn](./codeburn.md) | CLI/TUI dashboard tracking AI coding token usage, cost, and performance across 25+ tools |
| [Graphify](./graphify.md) | Builds a local, queryable knowledge graph of a codebase so agents retrieve targeted context instead of re-reading files |

> **Adding a new tool?** Create `docs/tools/<tool-name>.md` and add a row to the table above.
