# External repos brief — verified, positioned for Baltor (2026-06-04)

Owner handed a list of repos to research. Per the repo's **verify-first / never-trust-a-list**
principle, every entry below was web-confirmed (owner/name + what it actually is) by parallel
research agents before being recorded. Star counts are **approximate, as of 2026-06-04** (volatile
external numbers — not treated as canonical values; do not mirror them into code/prose).

Verdicts: **ADOPT-PATTERN** (lift a concrete technique) · **REFERENCE** (read, don't lift) ·
**OUT-OF-SCOPE** (off-thesis for a governed Context Engine — do not expand into).

## ADOPT-PATTERN (on-thesis, verified)

### `anthropics/financial-services` — github.com/anthropics/financial-services (~30k★, Apache-2.0) ✓
Anthropic's official Claude-for-Financial-Services solution: Claude + Agent Skills + MCP data
connectors (FactSet, S&P/Kensho, Moody's, PitchBook, Morningstar, LSEG, Snowflake/Databricks) plus
an open reference repo of named agent templates (KYC Screener, GL Reconciler, Earnings Reviewer…).
Announce: anthropic.com/news/claude-for-financial-services (+ /advancing-claude-for-financial-services).
- **Why it matters most:** this lands squarely in Baltor's **sanctions/regulated-financial
  beachhead** — it is simultaneously a frontier *complement* and a *competitor*. Its governance
  posture is the industry-credible framing to mirror, then differentiate on.
- **Lift (governance pattern):** the **"AI drafts, humans sign off"** doctrine — every output staged
  for qualified-human review, no autonomous binding/ledger-posting/onboarding approval. Baltor
  already encodes this (demo-local review queue, no canonical mutation, "applying = separate grant").
- **Adjacent template:** the **KYC Screener** agent (`plugins/vertical-plugins/operations/`):
  parse onboarding docs → rules-engine eval → flag gaps → stage for compliance sign-off. Mirrors our
  verified_context_flow sanctions path.
- **Differentiate on what they leave to the firm:** continuous verification, freshness/CDC,
  portable receipts, measured fidelity. Their **`scripts/check.py`** (cross-file ref resolution +
  skill-drift detection) is a concrete model for governed, drift-checked agent assets.

### `anthropics/claude-cookbooks` — github.com/anthropics/claude-cookbooks (~44.9k★) ✓
Companion article "Building Effective Agents" (anthropic.com/engineering/building-effective-agents) —
THE most-cited agent best-practices source, first-party to Baltor's Claude-Code-style build loop.
`patterns/agents/` holds reference impls of the five workflows.
- **Lift:** the **evaluator-optimizer** pattern (generate → independent evaluate → refine) as the
  template for Baltor's continuous-verification + adversarial-validation loop; **orchestrator-workers**
  for the autonomous build loop.

### `NirDiamant/agents-towards-production` — github.com/NirDiamant/agents-towards-production (~20.6k★) ✓
28+ code-first tutorials taking GenAI agents prototype → enterprise deployment (observability, eval,
security, RAG/memory; even a Contextual-AI RAG tutorial — our competitor space).
- **Lift:** its production-hardening structure — LangSmith tracing + LlamaFirewall/Apex
  eval-and-security testing — to model Baltor's verification rail + ops dashboard.

### `nidhinjs/prompt-master` — github.com/nidhinjs/prompt-master (~8.7k★, MIT) ✓
A Claude skill (SKILL.md) that auto-generates tool-specific prompts and keeps a **"Memory Block"**
that re-injects prior decisions so the model doesn't contradict earlier work.
- **Lift:** the **Memory Block** pattern — deterministically distill prior decisions into a pinned,
  prepended block (a mini reconciled context pack) so long sessions can't drift. Directly mirrors
  Baltor's reconcile/anti-fragile motion; fold into our skill files + autonomous loop.

### `obra/superpowers` — github.com/obra/superpowers (very large/popular, MIT; v5.1.0 May 2026) ✓
An agentic **skills framework + dev methodology**: composable `skills/<name>/SKILL.md` files that
auto-route by task type (brainstorm → write-plan → TDD → systematic-debug → subagent-driven-dev).
Skills invoked via Claude Code's native **`Skill` tool**; YAML frontmatter where `description`
encodes the *trigger condition*.
- **Lift:** the **trigger-in-`description`-frontmatter convention** + a meta "router" skill that gates
  each turn into the right sub-skill before responding. Maps onto Baltor's existing markdown skills
  (we already invoke skills via the `Skill` tool) — borrow the format/methodology, not a drop-in.

### `VoltAgent/awesome-design-md` — github.com/VoltAgent/awesome-design-md (~87.5k★) ✓
Curated `DESIGN.md` files (plain-text design-system docs) droppable into a project so coding agents
generate a matching UI. 72 design systems; companion `VoltAgent/awesome-claude-design`.
- **Lift (DONE this pass):** the **9-section DESIGN.md schema** → authored `docs/standards/DESIGN.md`
  documenting Baltor's shipped dark/ops aesthetic (grounded in the real `web/baltor` CSS).

## REFERENCE (read, don't lift)

### `HKUDS/DeepTutor` — github.com/HKUDS/DeepTutor (~24.6k★; v1.4.2 May 2026) ✓
Agent-native tutoring platform; end-product domain is off-thesis, but its **versioned RAG-ready
document library + three-layer memory** are adjacent to Baltor's context-pack/lineage concerns.
Worth reading as a comparison point for source-linked, CDC-tracked context packs.

## OUT-OF-SCOPE (off-thesis — do NOT expand into)

- **`charlie947/social-media-skills`** (~1.4k★) ✓ — 17 Claude skills turning an agent into a social-
  media operator. Social/growth-content automation; explicitly off-thesis.
- **`opentunz`** ⚠ — no canonical match; real candidates (`opentune/opentune` music downloader,
  `lilinwang/opentune` toy fine-tuner, `Arturo254/OpenTune` YT-Music client) are all music/audio/
  fine-tune tooling. None touch governed/verified context; the fine-tune one is training-based,
  contrary to our frozen-model + governed-data thesis.
- **`cporter202/automate-faceless-content`** (~2.7k★) ✓ — (the garbled
  `copportercporter202/automate-0faceless-content` resolves here) a faceless-video content-farm course
  with an affiliate funnel. Directly the off-thesis category.

## Flagged for separate verification
- **`ai-boost/awesome-harness-engineering`** ⚠ — surfaced as an "AI agent harness engineering"
  awesome-list (evals/memory/MCP/observability/orchestration) with direct topical overlap, but NOT
  confirmed (owner/name/stars unverified). Verify before citing.

## What changed this pass (proven increments)
- `docs/standards/DESIGN.md` — authored from the VoltAgent schema, grounded in real `web/baltor` CSS.
- `research/future-ideas.md` — prioritized adopt-backlog from these findings.
