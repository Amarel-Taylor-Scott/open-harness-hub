# Agent-governance & context-layer landscape — 2026-06-13 (web sweep)

Fresh competitive scan (live web search, 2026-06-13) to update the YC positioning. **Material change
since the 2026-06-11 sweep:** the "verification + receipts" white space is no longer empty — tamper-
evident *execution* receipts are now shipping products. The defensible wedge has moved from "nobody
does receipts" to **"we govern what becomes TRUE, not just sign what happened."** Pair with
`docs/strategy/yc-context-landscape-2026-06.md` (the YC-directory sweep) — this doc is the broader
market + regulatory "why now."

## What changed (the receipt half of the white space is contested)

Tamper-evident **execution receipts** — sign every tool/agent action, hash-link into a continuity
chain — are now real products, not just literature (PROV-AGENT / "Tool Receipts"):

| Player | What they ship | Shape |
|---|---|---|
| **Attested Intelligence** | MCP governance proxy emitting **Ed25519-signed receipts per tool call**, hash-linked tamper-evident chain; USPTO patent (19/433,835, Dec 2025) on "Attested Governance Artifacts" | execution provenance at the MCP boundary |
| **Fetch.ai AEVS** (May 2026) | publicly verifiable, tamper-evident receipts per tool call; on-chain audit trail | execution provenance, on-chain |
| **Diagrid** (Dapr 1.18, Jun 2026) | Workflow History Signing → tamper-evident, independently verifiable execution records + Workflow Attestation | workflow provenance |
| **NexArt** | SHA-256 sealed run records + independent Ed25519 receipts | execution provenance |
| **IAGA-Sentinel** (open, 152★; added 2026-06-18 via DeepRepo intake) | Ed25519+Merkle signed receipts, offline-replayable via a standalone `iaga-verify` binary, explicitly mapped to **EU AI Act Art.12 / Annex IV**; Dictum policy DSL with **egress allowlisting (`url_host`) + PII detection (`secret_ref`)**; honest `is_authoritative:false` for soft (non-kernel) enforcement; AISec 2026 paper | execution provenance + soft policy, EU-sovereign, **open-source** |

**They all sign EXECUTION (what an agent DID).** None do governed **TRUTH promotion** — a deterministic
gate that *promotes or rejects a FACT* (source precedence, revocation/CDC, capability-lift admission),
on a regulated-fact beachhead. That gap is the moat to lead with.

**IAGA-Sentinel (added 2026-06-18 via the DeepRepo intake)** is the first **open-source** entrant and the
most regulatory-specific (explicit EU AI Act Art.12 / Annex IV mapping). Two notes sharpen our read: (1) it
also ships **egress allowlisting + PII detection** in its Dictum policy DSL — overlapping Teleon's egress-
governance plane (`src/teleon/egress/`), so it is a competitor on *both* the receipt rail and egress control;
(2) it still signs EXECUTION, not TRUTH — no source-authority precedence, no fact revocation/CDC, no
capability-lift admission. Its `is_authoritative:false` honesty mirrors our own `serves_truth:false`
discipline — convergent design *validates the category*. Disposition: competitor-on-receipts /
complement-on-truth; its signed execution receipt could be one evidence input behind a port (never our truth
authority). Do not vendor/execute. Re-verify quarterly — this space moves in weeks.

## Consolidation: data platforms are buying the AI feedback loop
- **ClickHouse acquired Langfuse** (Jan 2026) alongside a **$400M Series D at a $15B valuation**
  (Dragoneer). InfoWorld framed it: "data platforms race to own the AI feedback loop." Langfuse =
  2,000+ paying customers, 19 of the Fortune 50.
- **Braintrust** raised **$80M Series B at $800M** (Iconiq, a16z, Greylock, Elad Gil) — "quality
  management system for AI products."
- **Atlan** now markets Baltor's exact line: *"governed enterprise context… whether this agent is
  authorized to query that column at runtime."* Data-catalog incumbents are moving into governed AI
  context — the real medium-term threat (data gravity), consistent with Contextual AI → Google DeepMind.

Implication: standalone observability/evals are being absorbed into data platforms. The durable
position is **above any data platform** — a portable, provider-neutral governance/verification layer
the customer carries between runtimes (the opposite of centralizing telemetry into one vendor).

## Format standardization: a hyperscaler just standardized the context FORMAT (added 2026-06-18)
- **Google Cloud Open Knowledge Format (OKF) v0.1** (announced 2026-06-12; spec at
  `GoogleCloudPlatform/knowledge-catalog/okf/SPEC.md`) formalizes the emergent "LLM-wiki" pattern into a
  vendor-neutral portable standard: a directory of markdown **concept** files + YAML frontmatter (`type`
  required; `title`/`description`/`resource`/`tags`/`timestamp` optional), markdown links forming a concept
  graph, optional `index.md` (progressive disclosure) + `log.md` (chronological history). "If you can `cat` a
  file you can read it; if you can `git clone` you can ship it." Reference impls: a BigQuery enrichment agent,
  a static HTML visualizer, sample bundles; Google's Knowledge Catalog ingests OKF natively.
- **Read for us — this is a tailwind, not a threat, and it sharpens the wedge.** OKF standardizes the
  context *transport/format* (one skeptic: *"a standard, or just a folder?"*). It carries **no verification,
  no earned source authority, no CDC/revocation, no truth-promotion, no capability-lift admission** — exactly
  the assurance layer Baltor/Teleon sit ABOVE. A hyperscaler standardizing portable, file-based, git-shippable
  context **validates the context-layer TAM and the "carry it between runtimes" thesis**, and gives us a clean
  one-liner: *"OKF is how context travels; Baltor governs whether the context in it is true, current, and
  provable."* Disposition: **adopt OKF as a candidate export/ingest format** behind the native-format-preservation
  port (a 9th output mode alongside our governed sidecars — the same "adopt the standard, wrap it with governance"
  play as PROV/OpenLineage/WebAnnotation/JSONPatch), so a governed Baltor context pack ships as an OKF bundle with
  our receipts/lineage as the assurance sidecar. Do not vendor/run the reference BigQuery agent. Re-verify as the
  spec moves past v0.1.

## Why now (hardened)
- **EU AI Act full application Aug 2, 2026** — Article 73 serious-incident reporting requires reconstructing
  *what an agent did and why* on a tiered clock (2 days widespread/critical-infra, 10 days a death, 15 days
  otherwise) → direct demand for receipts + lineage. A hard, dated wedge. (The flat "72-hour" figure is
  GDPR Art. 33, a separate regime — don't conflate.)
- **OWASP Top-10 for Agentic Applications** (Dec 2025) — first formal taxonomy (goal hijacking, tool
  misuse, identity abuse, memory poisoning, cascading failures, rogue agents). A framework to map
  governance coverage against in the pitch.
- **Microsoft Agent Governance Toolkit** (Apr 2026) — open-source, **deterministic sub-millisecond
  policy enforcement** + SLSA build provenance, addresses all 10 OWASP risks. VALIDATES the determinism
  thesis — *and* is incumbent pressure (free, open, Microsoft-backed). Differentiate on governed truth +
  capability-lift, not on "deterministic policy" alone.
- **YC ~60% AI in 2026** (up from 40% in 2024); a whole batch wave is "infrastructure for reliable
  agents" (memory, identity, compliance, monitoring, validation). The category is hot and crowded —
  a sharp one-sentence wedge matters more than ever.

## Adjacent (memory layer — not the wedge, a complement)
- **Mem0** — $24M raised; exclusive memory provider for **AWS Agent SDK**; 186M API calls/Q3 2025.
- **Zep / Graphiti** — temporally-aware knowledge graph (tracks how facts change). Closest *mechanism*
  to fact-revocation, but no governance/promotion gate. Atlan's own framing distinguishes "conversation
  memory" (Mem0/Zep) from "governed enterprise context" (where Baltor plays).

## Recommended positioning deltas (owner decision — not yet applied to the deck)
1. **Stop leading with "receipts."** Receipts are now table-stakes/contested. Lead with **governed
   truth promotion**: "given provenance, Baltor PROVABLY refuses to serve the wrong/stale/unverified
   fact, and emits a portable receipt" — the deterministic gate + CDC/revocation + capability-lift
   admission is what the execution-receipt players don't have.
2. **Use EU-AI-Act-Aug-2 as the "why now"** front and center.
3. **Name the data-gravity threat honestly** (ClickHouse+Langfuse, Atlan) and answer it: portable,
   provider-neutral, sits above any data platform.
4. Re-verify quarterly — this space is moving in weeks, not quarters (Diagrid shipped 2 days before
   this scan).

## Sources
- ClickHouse acquires Langfuse / $400M Series D / $15B: clickhouse.com/blog, siliconangle.com (2026-01-16), infoworld.com
- Braintrust $80M Series B: braintrust.dev, press coverage
- Attested Intelligence / Fetch.ai AEVS / Diagrid (Dapr 1.18) / NexArt: arxiv 2606.04193, cryptobriefing.com, financialcontent.com (2026-06-11), nexart.io
- OWASP Agentic Top-10 (Dec 2025) + Microsoft Agent Governance Toolkit (Apr 2026): opensource.microsoft.com/blog (2026-04-02)
- EU AI Act Aug 2 2026 enforcement: regulatory coverage (kiteworks.com and others)
- Atlan governed context vs Mem0/Zep: atlan.com/know, agentmarketcap.ai
- YC 2026 AI infra wave: ycombinator.com, cbinsights.com, tldl.io
