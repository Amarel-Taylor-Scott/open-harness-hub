# Portfolio PMF solidification — 2026-07-01

> **Status:** candidate strategy synthesis (owner-directed review, 2026-07-01). Warrants: owner briefs pasted
> 2026-07-01 (AIDevObserver-leads positioning critique; primitive-database brief; runtime-shape taxonomy), the
> owner moat reframe (memory `moat-reframe-data-not-capability-gap`), BIBLE §2 (AIDevObserver = the WEDGE), and
> the 2026-07-01 full-repo review (10 parallel audits). This doc RECONCILES the strategy docs' contradictions;
> where it supersedes a claim, the superseded doc is named. It does not change the architectural laws.

## 1. The center of gravity (owner-stated, 2026-07-01)

**The primitive substrate is the core product.** Teleon, AIDevObserver, and Baltor are all CONSUMERS of the
primitives. The bar the substrate must clear: organized · appropriately set up · easily searchable · SMALL ·
SHORT · REMIXABLE — such that coding agents complete large real-world tasks and benchmarks by reading only the
**edges** of primitives (`input_edge`/`output_edge` contracts, blackbox one-liners), never full code, and
ordering them into a graph runtime (`src/teleon/dag/pipeline_dag.py:DAG.run`, verified by
`src/teleon/synthesis/dag_contract.py`).

Substrate state (verified 2026-07-01): 72,804 edge cards + 5,005 search cards + 41 primitive-kind families +
200 runtime shapes + 193 source-backed groups with proof bundles and promotion gates; edge-aware lexical search
is live (`src/teleon/observer/registry_search.py:search_route_level_primitives`); the DAG executor is real.
**The open gap is EVIDENCE, not infrastructure:** no benchmark yet isolates primitive lift (bare agent vs
primitive-first agent), and every record remains `candidate`/`serves_truth=false` — the promotion gate has never
been crossed. See §6.

## 2. Commercial lead: AIDevObserver (the wedge goes first)

Per the owner brief (2026-07-01) and BIBLE §2, the public story leads with developer speed through reuse:

> **Stop AI coding agents from rebuilding what your team already has.**
> AIDevObserver reviews AI coding sessions, finds missed helpers and templates, estimates wasted context, and
> turns accepted findings into reusable team memory.

- Safety/compliance is a **secondary lens** (present for managers; never the lead).
- **Mode A — Observer Review** (lightweight, candidate advice only) launches first; **Mode B — Teleon Route**
  (proof-gated compiled routes) is the drill-down. Teleon internals (CandidateBundle/PlanLock/promotion) stay
  behind "advanced architecture" in public copy.
- Public naming simplification: **AIDevObserver** = product · **AIDevObserver Benchmark Lab** = internal demo/replay/eval mode inside it, not a branded surface ·
  Teleon = engine (mostly hidden) · OpenHubForAI = registry source (shown only in matches) · Baltor = verified
  context layer (deferred) · AI Done Right = company. The dependency law is internal language, not demo copy.
- First buyer: AI platform lead / DevEx / engineering-productivity lead; developer adoption stays self-serve.
- Manager metric: **"Measure reuse, not just model usage"** (reuse caught, duplicate helpers, tokens avoided
  with the estimate-basis labeled: exact | tokenizer-estimated | deterministic proxy).

## 3. Moat reconciliation (resolves contradictions C1 + C4 from the 2026-07-01 audit)

The strategy docs carried three competing moat framings. Reconciled hierarchy (per the owner reframe, memory
`moat-reframe-data-not-capability-gap`, + `first-live-capability-sanctions-screening.md`):

1. **External moat (what we sell): governed data** — Verified · Current · Provable context with provenance,
   freshness/CDC, receipts. Orthogonal to model progress.
2. **Internal bar (what we admit): the two-axis lift gate** — lift over bare model AND structural durability
   (`scripts/eval/reason_codes.py`). This is a selection criterion, not the pitch.
3. **Supporting engine (how it compounds): the Determinism Factory + reuse flywheel** — expensive resolution
   distilled (losslessly) into deterministic rules from VERIFIED cases; accepted/dismissed findings become team
   memory. This makes the data moat cheaper to maintain, it is not itself the lead claim.

Where `baltor-gtm-fundraising-plan.md` leads with procedure-mining and `product-market-monetization-brief.md`
leads with the lift gate, both now read as layers 3 and 2 under the governed-data lead.

## 4. Product verdicts (from the 2026-07-01 audits, condensed)

| Product | PMF state | Sharpest strength | Binding gap |
|---|---|---|---|
| **AIDevObserver** | Wedge, pre-distribution | 16/16 screens live; 14 real intervention modules; consent gate #0 built | **No install path**: extension uncompiled, no PyPI, no marketplace/MCP-directory presence |
| **Baltor** | Pre-revenue wedge proven | OFAC live catch (2026-06-14, 19,065-row list); CFPB invariant; provider-directory vertical code | No signed design partner; moat story now reconciled (§3) |
| **Teleon** | Engine, not a standalone product (resolves C2) | Registry federation + synthesis + receipts + promotion gates live locally | No independent ICP today — revisit only via the agent-gateway ("agents as customers") once the wedge distributes |
| **OpenHubForAI** | Commons/funnel | Contribution workflow real + gated; hub engine + component store governed | 1,059 seeded components unverified by the lift gate; free→paid boundary designed, not coded |
| **AI Done Right (parent)** | Holding narrative | Portfolio shell + GTM checklist exist | Founder story has 16 `[OWNER TO FILL]` placeholders — owner-only work |

**Portfolio-level revenue blockers (all products share them):** (1) billing seam is a deliberate
`NotConfigured` stub (`scripts/billing_plane.py` StripeAdapter — owner-gated, never faked); (2) no production
domains/DNS/TLS wired; (3) AIDevObserver not packaged. These three are the whole distance between "built" and
"sellable".

## 5. Depth-before-breadth: from stated to enforced (resolves C3)

The recent registry sprawl (queueing/business-models/influencer-monetization/code-porting catalogs) advanced
breadth while the declared beachhead (provider-directory) has no paying customer — the Foundational Law's
binding constraint, stated but unenforced. **Proposal (owner gate):** extend `scripts/proposal_backlog.py` with
a vertical-gating check — new registry/generalization proposals queue (not merge) until the beachhead vertical
has (a) a signed design partner or (b) recurring revenue. Until the owner rules, reviewers treat new-breadth
diffs as needing an explicit depth warrant in the ledger.

## 6. The evidence program (first benchmarks, per the owner briefs)

1. **AIDevObserver Session-Review Benchmark v0** — 8 domains × 10 session fixtures, each with expected findings,
   expected `source_ref`, false-positive traps, and a clean-session negative control. Primary metric:
   high-confidence source_ref precision; plus recall by category, tokens-avoided (basis-labeled), replay
   determinism, redaction correctness.
2. **Primitive-lift A/B** — same task twice: Run A bare coding agent · Run B primitive-first (edge search →
   route → assemble → prove). Score correctness, proof completeness, tokens, time, pitfalls avoided. This is the
   missing instrumentation the Gemma-4 LeetCode artifacts (100% pass, no baseline isolation) do not provide.
3. **Runtime-shape reuse** — same `core_group_edge` delivered as py.fn / api.endpoint / queue.consumer /
   cron.job / microservice…: measure whether ONLY the wrapper changes (hidden member edges reused). Substrate
   already has the axes (41 kind families, 200 runtime shapes). Intake rule: external brief ids like
   `grp:...@1` are adapted — the `@N` moves to `schema_version` metadata (naming law).

The program is now PUBLIC-FACING: `docs/whitepapers/read-the-edges-not-the-code.md` (the edge-first
composition thesis + first measured numbers, honest trade-offs included) and
`docs/benchmarks/edge-first-composition-benchmark-plan.md` (arms, resource envelope incl. context bytes +
machine memory, corpora, phases P1–P7: search → ordering/hybrid graphing → deterministic mutations → genetic
tournaments → troubleshooting drills → tier-ladder ablations → longitudinal reuse). M0 shipped 2026-07-01:
486x context reduction at output equivalence on the deterministic floor, +8 MB/+0.6 s runtime tax reported
alongside it.

## 7. Development-tool fleet (recorded)

The dev plane runs multi-harness, multi-model: **Codex** (per-package migrations), **Claude Code** (primary
agent harness + /loop), **Kimi K2.7-code** and **GLM 5.2** (Ollama-cloud lanes: stall-breaker forks, rerank,
IDE model lanes), **Gemma 4** (local/CPU batch lane + coding benchmarks). AIDevObserver supervises sessions
across these harnesses (its IDE exposes deterministic/Kimi/GLM lanes) — the fleet is both tooling AND the
first user of the wedge.

## 8. Superseded / to-update ledger

- `_repos/fundraising/context/baltor-gtm-fundraising-plan.md` — moat framing subordinated to governed-data lead (§3).
- `docs/strategy/founder-market-fit.md` — blocked on owner placeholders (irreducibly owner work).
- BIBLE §2/§3/§8 — reconciled 2026-07-01 (showcase canonical; AIDevObserver surface = `web/aidevobserver`;
  naming Law 10 added).
