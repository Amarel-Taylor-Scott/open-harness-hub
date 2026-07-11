# teleon (`aidoneright-teleon`)

Teleon is the purpose-driven, eval-gated, self-adaptive compute **runtime SaaS** of the AI Done Right
portfolio. You declare a capability in **plain text** and Teleon descends it to the cheapest **bounded**
form within your guardrails, promoting only what a proof passes. In the portfolio's moat split, **Teleon
governs what becomes EFFICIENT** (the descent brain: make-it-work → make-it-cheap → deterministic
substitution); Baltor governs what becomes TRUE.

- **Category:** intent-native, eval-gated, self-adaptive compute.
- **One-liner:** *Serverless runs code. Kubernetes runs workloads. Teleon runs purpose.*
- **Standalone value:** the reference implementation of the open **CapabilityTask spec (CTS)** — reusable
  by any tenant, not limited to Baltor (Baltor is only its first internal customer, tenant
  `baltor-internal`).

## What this repo owns

The **PurposeTask / CapabilityTask registry**, runtime selection, implementation candidates, the evidence
ledger, promotion gates, policy gates, boundary approvals, task orientation (operational memory), the
self-adaptation loop, runtime adapters, and the staff/customer assurance dashboard. It does **not** own
customer workflows, domain outcomes, or verticals — those are Baltor's.

The core motion is a ten-stage lifecycle plus a distillation lane: INTENT → SPEC → BUILD → GATE → COMPILE
→ DEPLOY+RUN → OBSERVE → DIAGNOSE → TUNE/ADAPT → RE-GATE, with LLM behaviour distilled to deterministic
rules along the way. Self-adaptation is safe because the **adaptation ladder** lets the system change its
MEANS automatically (L0–L3, each behind its own gate) but never its ENDS (L4/L5 and `forbidden_autonomous`
are human-only), and every output carries `serves_truth = false` — it is evidence, not sellable fact.

## Layout

This is a staged context repo that ALSO **vendors the runtime source**: alongside the operating manual, the
edge contracts, and the consolidated Teleon context, the `src/teleon/**` package lives here under
`backend/src/teleon/` — the PurposeTask controller, adaptation ladder, Parallel-Path Engine,
capability→runtime compiler, OIPS receipts, agent gateway, and the rest — which the context files cite by
path.

- **`CLAUDE.md`** — the agent operating manual: this repo's identity + the Teleon identity locks
  (naming stack, vocabulary, the MEANS-not-ENDS and `serves_truth=false` invariants) + the inherited laws
  (linked, not copied) + fast path, adding-work rules, and scope.
- **`EDGES.md`** — the generated cross-repo edge contract: this repo's role, what it exposes, what it may
  consume (via published interfaces only), who consumes it, and the forbidden edge. This is the ONLY
  cross-repo context a session here needs — neighbors' published edges, not their internals.
- **`context/`** — the consolidated Teleon context, each doc grounded in and linked to a parent-repo
  source:
  - `context/blackbox.md` — the standalone brief: what Teleon **is**, owns, and does (read first).
  - `context/edges.md` — the interface contract: what Teleon consumes/exposes, the same-origin seams, the
    dependency law, migration status, and the invariants to preserve.
  - `context/architecture/` — runtime/compiler internals (capability runtime compiler, execution taxonomy,
    inference lanes, egress graph, self-healing-vs-evolution, universal-computation-compiler, …).
  - `context/strategy/` — the definitive self-improving-runtime vision (per-stage BUILT/DESIGNED/MISSING).
  - `context/codex/` — architecture routes + fallbacks, primitive-assembly thesis, universal workflow /
    multimodal registries, external-feedback briefs.
  - `context/standards/` — the capability-task architecture doctrine.
  - `context/status/`, `context/goals/`, `context/research/` — current-state snapshots, the thin
    control-plane MVP goal, and research grounding.
  - Plus top-level context on the CapabilityTask standard, the PurposeTask dashboard, the shared inference
    gateway / OIPS, free LLM-endpoint intelligence, the demo control tower, and the build constitution.

## How to work in this repo

1. Read `CLAUDE.md`, then `context/blackbox.md` (what Teleon is), then `context/edges.md` + `EDGES.md`
   (how it connects and the boundary law).
2. The load-bearing laws are **inherited, not local** — they live in
   `../dev-rules-context/standards/`; the shared standards statement + glossary live in
   `../dev-rules-context/_shared/`, and the canonical architecture map is `_repos/_shared/ARCHITECTURE-MAP.md`
   (the map `context/edges.md` cites). `CLAUDE.md` links them; do not copy them here.
3. Reuse before you build — most of the runtime already exists (PurposeTask controller, adaptation ladder,
   Parallel-Path Engine, capability→runtime compiler, OIPS receipts, agent gateway). Check `context/`
   before assuming a subsystem is missing.
4. Honor the identity locks: the naming stack and vocabulary are LOCKED; version lives in metadata, never
   in a name or id; ids are minted only through `src.teleon.experiments.ids`.

## Edges (from `EDGES.md`)

- **This repo exposes:** `/api/teleon`, PurposeTask, runtime-selector, evidence-ledger, promotion-gate,
  assurance-portal.
- **May consume (via published interface only):**
  - `dev-rules-context` (`aidoneright-dev-rules-context`) — standards, the surface registry, the check
    tools, `_shared/*`.
  - `shared-backend-components` (`aidoneright-shared-backend-components`) — registry, primitives,
    codegraph, eval-harness, storage-tiers, credential-plane.
  - `openhubforai` (`aidoneright-openhubforai`) — the CapabilityTask spec, eval harnesses, task templates,
    conformance tests, skills.
- **Who consumes this repo (keep interfaces stable):** `aidoneright`, `baltor`.
- **Forbidden (the boundary law):** **`baltor`** — Teleon is reusable infrastructure, never
  Baltor-specific. Teleon MUST NEVER import `src.baltor.*`; the versioned `/api/teleon` contract (plus
  events) is the only coupling. Consume a neighbor ONLY via its exposed interface — never read or import
  its source.
