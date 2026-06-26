# YC application draft — 2026-06 (OWNER-GATED: review every line before submission)

DRAFT ONLY. Outward-facing per the change-verification contract: the owner edits founder
facts, picks the company name to apply under, and approves all claims. Every factual claim
below is backed by a repo artifact or the verified 2026-06-11 landscape research — nothing
here is aspirational copy. Numbers marked ⟦computed⟧ must be regenerated at submission time
(no magic values).

## Company / one-liner (50 chars)

> **Baltor: verified context for AI agents.**

Applying entity: **AI Done Right** (holding company). The portfolio applies as one, led by Baltor — not
Baltor *or* Teleon: **Baltor** is the flagship applied product and customer-facing wedge (the 50-char line
above = what a customer buys); **Teleon** is the deterministic capability runtime beneath it; the
**Open\*Hubs** are the open registry + ecosystem. (Owner ratified 2026-06-18: lead with Baltor, keep all
entities — final headline polish is the owner's.)

## What does your company do?

AI agents fail because their context is wrong, stale, or unprovable — not because models are
weak. Baltor is a context-assurance engine: it ingests sources, **establishes which source is
authoritative by provenance** (publisher/domain + verified signature, not assumption — so an SEC
filing outranks a press rumor, provably), signs what passes, issues portable receipts for what
was verified (when, against what), and revokes facts when sources change (CDC). Agents propose;
Baltor disposes.
Under it sits Teleon, a deterministic capability runtime — every capability is promoted or
rejected by eval gates with an evidence ledger, never by vibes — and OpenHarnessHub, an open
registry of ⟦computed: 2,678⟧ governed pipeline components (⟦computed: 1,059⟧ of them action-ready
across the six Action types — adapters, personas, processors, harnesses, rubrics, tools) — each with
provenance and measured-lift admission.

## Why now?

- Agent plumbing is exploding (41.5% of YC W26) but splits into perimeter, identity,
  red-teaming, and observability. The tamper-evident-receipt rail that emerged in 2026
  (Attested Intelligence, Fetch.ai AEVS, Diagrid) signs **EXECUTION — what an agent DID.
  Nobody governs TRUTH — promote / reject / revoke a FACT by earned source authority on a
  regulated beachhead.** Verified across ~95 YC companies (`docs/strategy/yc-context-landscape-2026-06.md`)
  + a 2026-06-13 landscape sweep (`docs/research/agent-governance-landscape-2026-06-13.md`).
- **The EU AI Act reaches full application Aug 2, 2026** — Article 73 serious-incident reporting forces
  organizations to reconstruct *what an agent did and why* on a hard clock: as little as 2 days (a
  widespread infringement or critical-infrastructure disruption), 10 days (a death), 15 days at the
  outside. That is portable receipts + fact lineage, on a deadline. (The flat 72-hour figure is GDPR
  Art. 33 — a separate regime; we don't conflate them.)
- The 2025–26 consolidation wave (Langfuse→ClickHouse at a $15B valuation, Helicone+Trieve→Mintlify,
  Traceloop→ServiceNow, Context.ai→OpenAI, Invariant→Snyk, Lakera→CheckPoint) proves standalone
  observability/evals/security are features — and data platforms (ClickHouse, Atlan) are racing to
  own the AI feedback loop. Assurance has to be a portable rail ABOVE any one platform, which is
  exactly what a provider-neutral receipt is.

## What do you understand that others don't?

1. **Memory is what agents believe; verified context is what you can act on.** Mem0/Zep/
   Supermemory store beliefs. Regulated buyers need proof, freshness contracts, and
   revocation — a different product with a different bar.
2. **Verification cannot be LLMs judging LLMs.** "Self-driving" loops (Respan) and
   multi-model voting (IJFW Trident) let the system grade itself. Our rail is deterministic:
   models propose, gates dispose, receipts record.
3. **The lift bar is the moat's inner wall.** A component enters the registry only if it
   lifts over the bare model AND the lift is structural (won't vanish with the next model
   release). We screen for the negative space models won't close.
4. **Distillation is never replacement.** Raw layers, lineage, held-out items, and rollback
   targets survive every compression — which is why our receipts can be replayed and theirs
   can't.

## Progress / traction (all reproducible from the repo)

- Working end-to-end demo plane: 4 product apps + ⟦computed: 22⟧ hub registries + 25 identity realms
  (separate-realm auth, hash-only keys), a model plane that is offline-deterministic by default
  (reproducible from a clean checkout) with a cloud LLM behind a bring-your-own key — the narrated
  journey videos were filmed against a live cloud model — plus promotable local embeddings; Teleon
  capabilities BUILT by a model and judged by a deterministic gate with receipts per attempt; real
  pipeline runs with citation checks.
- ⟦computed: 2,678⟧-component governed registry; provenance + two-axis admission encoded in
  CI gates; ⟦computed: 29⟧ narrated user-journey videos recorded against the live plane
  (4xx/5xx tripwires — zero HTTP errors on film).
- Deploy layer: one topology file renders Fly.io configs + docker-compose, with a
  self-tested queue-depth Machines controller (KEDA-equivalent) — cloud-ready, provider-
  portable by construction.
- Pre-revenue. Honest gaps we are closing in order: measured-lift evidence on flagship
  components (replacing "unproven" badges), first design-partner deployments, hosted
  public instance.

## Business model

Open protocol + open registry (OpenHarnessHub) as the funnel; revenue = the governed live
layer: Context-Enrichment-as-a-Service (per-verified-fact / per-receipt pricing),
build-on-demand governed pipelines, and Teleon as the runtime SaaS for teams that need
capability gates with evidence. Exports are free; assurance is the product.

## Competition (one line each — full matrix in the landscape doc)

Airbyte moves context, doesn't assure it. Mem0/Zep remember, don't verify. Reducto parses,
doesn't corroborate. Respan watches and self-fixes — no receipts. Kaelio governs SQL shape
for analytics, not facts. Evals/CI gates (Openlayer, Braintrust) gate code versions, not
running context. The receipts rail is empty (verified through W26).

## Asks for the owner before submission

1. Founder story/credentials section (PhD: training-free few-shot segmentation; ghanalexai.com).
2. Choose the applying entity (Baltor product-first vs Teleon platform-first).
3. Approve/adjust every competitive line (outward-facing law).
4. Regenerate ⟦computed⟧ numbers via the family/count checks on submission day.
5. Demo video: the narrated journey set exists; pick the 1-minute cut.
