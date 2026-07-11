# Wayland / Wayland Core — competitive intake + what we can learn (2026-06-22)

Governed intake (discovery ≠ trust; serves_truth=false). **Learn-from**, not adopt-blindly. Wayland Core is
Apache-2.0 (FerroxLabs), so techniques are technically vendorable, but we re-implement patterns clean-room behind our
own ports + governance. Sources at the bottom.

## What it is
**Wayland** ("One agent. Every agent.") is a desktop **meta-orchestrator** sitting *above* the model layer —
commands Claude Code, Codex, Gemini, etc. from one "foreman." **Wayland Core** (`@ferroxlabs/wayland-core`, Apache-2.0)
is the lower-level **Rust engine**: a terminal-first agent that plans, runs real tools in an OS-native sandbox, scales
to a swarm, and embeds behind an app over a JSON-stream protocol.

## What it provides (verified from the official site/docs)
- **Structure:** a Rust workspace of focused crates with strict *downward* dependencies — provider-neutral data
  types (`wcore-types`/`wcore-compact`) at the base, then config/providers/tools/MCP, then capability crates (skills,
  memory, sandbox, swarms, browser), with an agent loop on top.
- **Three modes from one binary:** interactive TUI · one-shot `prompt` · headless `--json-stream`.
- **Headless JSON-stream protocol:** typed, *versioned* JSON-Lines — text deltas, tool requests/results, sub-agent
  events, **approval gates**, and a **`retryable` flag on every failure** ("no guessing").
- **Provider plane (~20):** Anthropic/OpenAI/Bedrock/Vertex/Gemini + ~15 OpenAI-compatible + local Ollama; per-request
  retries, **key rotation, cross-provider fallback chains, circuit breakers**; "switching vendors is a one-line change."
- **~75 built-in tools** (files/shell/search/web/media), **availability-gated** credentials, a **"no-stubs contract."**
- **Sandbox + egress:** every shell command in the platform's strongest sandbox (bubblewrap / sandbox-exec /
  AppContainer), **fail-closed when unavailable**; an **egress firewall enforced structurally by a Clippy lint**;
  approval modes + **budget caps that actually block.**
- **Swarms:** Spawn/Delegate parallel sub-agents; **worktree-isolated swarms up to a 100-agent Fleet**, each on its own
  git branch, process-isolated.
- **Memory:** a **5-partition × 3-tier**, SQLite-backed, semantically-searchable store.
- **Skills + self-evolution:** skills **auto-draft after 3 successful runs** via **GEPA**, an *offline* evolutionary
  optimizer that mutates + scores skill prompts across generations, with **full lineage** — explicitly **NOT a live
  self-rewrite**; optimized skills are **reviewed before promotion.**

## What we can LEARN (mapped to our stack)
1. **Typed, versioned headless event protocol with a `retryable` flag + approval-gate events.** Our Agent Capability
   Gateway should expose exactly this shape (JSON-Lines: deltas, tool req/result, sub-agent, approval, `retryable`) so
   agents/CI embed Teleon cleanly. **High value, low risk — file it.**
2. **Resilience in the provider plane:** circuit breakers + explicit cross-provider fallback *chains* + key rotation.
   Our `llm_port`/inference gateway has lanes + degradation; adding circuit-breaker + fallback-chain semantics is a
   concrete hardening. **File it.**
3. **GEPA-style *offline* evolutionary skill optimization (mutate+score across generations, lineage, promotion review,
   never live self-rewrite).** This strongly **validates** our descent brain + lossless-distillation law + the
   self-healing/evolution boundary + promotion gates — and suggests adding an *evolutionary* descent strategy
   (mutate+score capability/skill prompts offline) alongside the current axis descents. **File as a descent-strategy candidate.**
4. **Structural guardrail enforcement (egress firewall as a Clippy lint):** enforce a guardrail at the *build/lint*
   layer, not runtime config — analogous to our proof-gated checks (dependency law / plane separation). Reinforces
   "enforce in code, not convention."
5. **"No-stubs contract" + availability-gated tools + fail-closed sandbox** = exactly our *honest-unavailable, never
   fabricate* stance (`UnavailableOCR`, serves_truth=false). Independent **validation** of our approach.
6. **5-partition × 3-tier memory** — a concrete reference for our tiered storage / memory provider.

## Where WE differ (the wedge — they don't do this)
Wayland is a **horizontal execution orchestrator** ("OS for AI agents"). It coordinates agents + runs tools; it does
**not** govern *truth* or optimize *cost-appropriateness*. Our two moats sit exactly where it's silent:
- **Baltor governs what's TRUE** — verify gate, provenance, CDC, *discovery ≠ trust*. Wayland orchestrates execution,
  not verified context.
- **Teleon governs what's EFFICIENT** — the unbounded→bounded **descent** (cheapest tier/model/tool that meets the
  bar), with a measured cost receipt. Wayland switches providers, but doesn't *descend* a capability to the cheapest
  appropriate path.
- We could even sit **under** a Wayland-style orchestrator as the governed, efficient capability layer it calls (the
  "right model for every task" + "verified truth" backend) — a partnership/positioning angle, not just a competitor.

## Governance
Candidate-only (serves_truth=false). Apache-2.0 → permissive (techniques vendorable, but learn clean-room). The user's
"1900+ skills / Flux / Qwen / OpenClaw" notes are from marketing/older material and aren't on the current core
site/docs (which state **~75 tools, ~20 providers, GEPA skills**) — treat the higher figures as unverified.

## Sources
- [Wayland Core](https://getwayland.com/core) · [Wayland](https://getwayland.com/) · [Wayland Docs](https://docs.getwayland.com/) · [GitHub: FerroxLabs/wayland](https://github.com/ferroxlabs/wayland)
