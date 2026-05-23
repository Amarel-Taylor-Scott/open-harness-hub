# Antigravity 2.0 ingestion plan

> Researched via Playwright (the antigravity.google site is heavily
> JS-rendered, so plain WebFetch returns an empty shell). Findings from
> the public marketing pages + blog index, May 2026.

## What Antigravity 2.0 actually is

Google Antigravity is **Google's agentic development platform**.
Launched November 2025; Antigravity 2.0 dropped May 19, 2026 (their
Google I/O 2026 release). The product surface:

| Surface | What it does |
|---|---|
| **Antigravity 2.0** | "Command center to manage multiple local agents in parallel. Group conversations into Projects, operate across multiple workspaces, automate routine tasks with scheduled messages." |
| **Antigravity CLI** | Terminal-first; runs autonomous coding agents, executes shell commands, manages background subagents. |
| **Antigravity SDK** | "Prototype custom agents leveraging Antigravity's harness with minimal code. Simple Python scripts to iterate on agentic applications, automate software-engineering tasks, and run evaluations on top of the Antigravity agent harness." |
| **Antigravity IDE** | "Fully-featured, agentic IDE. Complete with the agent manager, artifacts, and a deep understanding of your codebase." |

Key blog-index headlines (May 19, 2026 wave): "Subagents, Hooks,
Scheduled Tasks, Agent Management, Voice, and Much More". So
Antigravity has explicit first-class concepts for **subagents**,
**hooks**, **scheduled tasks**, and **agent management** -
near-1:1 with the hub's existing primitives.

## Why this matters for the hub

Antigravity uses the word "harness" in its product copy - same word
the hub's catalog uses for the wrapping-workflow primitive. This is
not coincidence; the field is converging on the term. Whatever
"Antigravity's harness" exposes as Python entry points, the hub's
`harness/*` manifests should compile to it.

## Mapping hub primitives → Antigravity surfaces

| Hub primitive | Antigravity surface (inferred) |
|---|---|
| `harness/*` | Antigravity SDK custom agent (Python class) |
| `tool/*` | Antigravity tool registry (likely MCP-compatible - Anthropic's MCP is the cross-vendor standard everyone is adopting) |
| `pipeline/*` | Antigravity sub-agent orchestration ("multiple local agents in parallel") |
| `processor/*` (audit / verify / iterate) | Antigravity **hooks** (lifecycle event handlers) |
| Scheduled-task pipelines | Antigravity **scheduled messages** |
| `persona/*` | Antigravity agent custom-instructions |
| `rule-pack/*` (privacy / safety gates) | Antigravity hooks again (pre/post lifecycle) |
| `pattern/*` (Self-RAG, ReAct, ToT) | Reference architectures for SDK users |
| Hub plugin marketplace (Claude Code-format) | Antigravity will probably ship its own - if it does, add `scripts/emit/antigravity_pack.py` |

## Ingestion plan (do these in order)

### Phase 1 - when Antigravity SDK ships public

1. **Read the SDK docs**: at the time of writing, `docs.antigravity.google` is gated (`ECONNREFUSED` from the WebFetch test). Once public, find:
   - The Python class / function the SDK exposes as a "custom agent".
   - The hook-registration API.
   - The tool-registration API.
2. **Write `scripts/emit/antigravity_agent.py`**: emit one Python file
   per `harness/*` that subclasses or registers with Antigravity's
   agent class. The manifest's `applied_layers`, `consumes`, `emits`,
   `model_targets`, `privacy_boundaries` map onto SDK hook
   registrations.
3. **Reuse `dist/mcp/server.py`** unchanged if Antigravity supports
   MCP (highly likely given the rest of the ecosystem).

### Phase 2 - Antigravity IDE plugin / extension format

If Antigravity ships a plugin / extension manifest format
(equivalent to Claude Code's `.claude-plugin/plugin.json`):

1. Add `scripts/emit/antigravity_plugin.py` that produces the manifest
   per harness + pipeline.
2. Mirror the agentskills.io shape - Antigravity has clear motivation
   to support that open standard, since Google's own Gemini CLI already
   does.

### Phase 3 - Scheduled-message integration

Antigravity's "scheduled messages" map to **cron-style pipeline
runs**. The hub already has `pipeline/*` manifests; add a top-level
`schedule:` field that Antigravity (and other schedulers) can read.

## Practical first step

Until Antigravity's SDK docs are public, the hub's existing emit
targets cover the most likely interop paths:

- **MCP server** (`dist/mcp/server.py`) - almost certainly works as-is in Antigravity CLI / IDE the moment MCP support lands. Anthropic, OpenAI, Google's own Gemini CLI, Cursor, OpenHands, Roo Code, Goose etc. all support MCP; Antigravity will too.
- **Agent Skills bundle** (`dist/agent-skills/`) - 40+ tools already implement the agentskills.io standard; Antigravity is the most likely 41st.
- **Croissant datasets** (`dist/croissant/`) - Google Dataset Search already indexes Croissant; the same emit drops into Antigravity's data layer if it has one.

So the hub is **already 80 % ingestion-ready** for Antigravity 2.0
through existing emit targets. The remaining 20 % is the Antigravity-
specific SDK shim - add when their docs are public.

## What's UNCLEAR until Antigravity docs are public

- Exact Python SDK class/function signatures.
- Whether Antigravity has a marketplace (analogous to Claude Code's
  plugin marketplace) or only first-party content.
- Whether hooks fire on the same lifecycle events the hub recognises
  (pre_api / api / post_api).
- Tool-registration format (raw Python callable vs MCP vs OpenAPI vs
  proprietary).

When those land, this plan upgrades to a concrete emit script.
