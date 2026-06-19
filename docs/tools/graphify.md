# [Graphify](https://github.com/safishamsi/graphify)

Graphify is a free, open-source skill that turns a codebase — or any folder of code, SQL schemas, scripts, docs, papers, or media assets (with the right extractors) — into a **queryable knowledge graph**. It does the expensive whole-repo analysis **once, upfront**, so an AI agent can retrieve targeted context from the graph instead of repeatedly grepping and re-reading raw files from scratch. Parsing runs **locally**, and it integrates with Claude Code, Codex, Cursor, Gemini CLI, OpenCode, and others. Built by [safishamsi](https://github.com/safishamsi/graphify); released April 2026 — actively developed but still early-stage.

## Why Graphify

- **Context, pre-computed.** Nodes are functions, files, and concepts; edges are the calls, imports, and semantic relationships between them. The agent gets a map of the project before it touches a single file.
- **Local-first.** Parsing and graph-building run on your machine. The one LLM labelling pass (see below) may send derived cluster summaries to a model provider depending on how you configure it — check Graphify's settings if you need full air-gapping.
- **Broad inputs.** Not just code: SQL schemas, shell/R scripts, docs, and more can land in one graph, so app code + database + infrastructure are queryable together.
- **Drop-in skill.** Registers itself as a skill for the major agents; in Claude Code you invoke it with `/graphify`.

## How it works

Graphify builds the graph in three passes:

1. **Static analysis** with [Tree-sitter](https://tree-sitter.github.io/) — parse files into functions, imports, and call relationships.
2. **Community detection** with Leiden clustering — group related files/modules into clusters of concern (and highlight the most connected ones).
3. **Semantic labelling** — a single LLM pass names the clusters and relationships in human terms.

The output is a **graph JSON**, a **graph report** (`GRAPH_REPORT.md`) summarising the structure, and an optional **HTML visualization**. The agent reads the report to decide *what* to grep or open, rather than exploring blind — so follow-up questions can be scoped from the graph instead of re-scanning the tree from scratch.

## Does it actually save tokens?

Often, yes — but the size of the win depends heavily on **repo size and query type**, so treat the headline multipliers as a best case, not a guarantee.

- **The mechanism is real.** A question like *"where does billing deduct credits?"* can resolve in **~1.7k tokens** of graph lookup versus the **~123k** a naive grep-and-read would burn on a large repo — a ~70× reduction in that scenario. Independent reviews report a wide range (**~7× to ~71×**) depending on the codebase and query.
- **Biggest gains on large, unfamiliar repos** (hundreds of files), where blind exploration is most wasteful. On small or familiar repos the savings are modest and may not repay the build.
- **The build is not free.** The semantic-labelling pass spends tokens, and clustering is CPU-intensive. You pay that cost once; it amortises only if you run enough graph-backed queries afterward.

**Net:** a strong token-saver for navigating and reasoning about large codebases; marginal for small ones. Measure on your own repo (e.g. with [CodeBurn](./codeburn.md)) rather than trusting a single multiplier.

## Trade-offs

- **Staleness.** The graph is a snapshot at build time. After substantial code changes, an agent will read a stale graph and answer confidently from a map that is weeks out of date. Rebuild or `--update` after meaningful changes.
- **Rebuild cost.** Full rebuilds are CPU-heavy; without guards, concurrent rebuilds can pile up and saturate the machine. Incremental `--update` re-extracts only files whose content hash changed — but it carries the Windows caveat below.
- **`--update` is fragile on Windows** (cp1252 encoding, bash-quoting, graph-merge instability). On Windows, prefer a **full rebuild every few sessions** over per-session incremental updates.
- **Best as an audit, not a per-turn habit.** Several reviewers find it most valuable as a one-time architectural-understanding pass rather than something refreshed every session.

---

## Quickstart

Requires **Python 3.10+**. The package is published as `graphifyy` (double-y); the CLI is `graphify`.

```bash
# Recommended (handles PATH automatically)
pipx install graphifyy

# Or with uv
uv tool install graphifyy
```

Register it as a skill for your AI agents:

```bash
graphify install
```

## Usage

Build a graph for the current directory:

```bash
graphify .
```

Common options:

| Option | Effect |
|--------|--------|
| `--update` | Re-extract only files whose content hash changed, then re-cluster (incremental). |
| `--mode deep` | More aggressive relationship extraction (slower, richer graph). |
| `--no-viz` | Skip the HTML visualization; produce report + JSON only. |

Inside **Claude Code**, you can just type:

```
/graphify
```

It reads your files, builds the graph, and writes the report the agent then uses to scope its context.

### Suggested workflow

1. Run `graphify .` once when you start on a large or unfamiliar repo.
2. Let the agent read `GRAPH_REPORT.md` before it greps — ask architecture/navigation questions against the graph.
3. After meaningful code changes, `graphify . --update` — or skip it: if the repo is stable, or you're using Graphify mainly as a one-time architectural audit, a single build is often enough (and a periodic full rebuild beats incremental updates on Windows).
4. Confirm the payoff on your own codebase with a token dashboard like [CodeBurn](./codeburn.md) before adopting it as a habit.

---

## Links

- [GitHub](https://github.com/safishamsi/graphify) — [Website](https://graphify.net/) — [DeepWiki docs](https://deepwiki.com/safishamsi/graphify)
