# First Live Capability — OFAC Sanctions Screening (the compliance wedge)

> Status: SCOPE (2026-06-21). Acts on the review board's unanimous verdict (Claude + GLM-5.2 + Kimi-2.7,
> `docs/reviews/panel/`): *"ship ONE real capability, to ONE buyer, with a measured before/after."* This is that one.

## Why this capability (decided, not surveyed)

Of the compliance candidates, **OFAC/sanctions name screening** is the sharpest first ship because it maximizes every
axis that makes a capability provable AND monetizable:

- **Most bounded / deterministic** — the descent story is the cleanest possible demonstration of the Teleon thesis:
  naive = *ask an LLM "is this entity sanctioned?"* (hallucinates names, cites a stale list, no provenance) →
  bounded = *deterministic fuzzy-match against the CURRENT signed OFAC SDN list, with a provenance + freshness receipt.*
- **Authoritative public source already governed** — `architecture/source_authority_registry.json` carries
  **`us-treasury` → "OFAC SDN Search", `tier: official_agency`, `signed: true`**. Public data (no PII to store).
- **A textbook DURABLE gap** (`docs/concepts/capability-valleys.md`) — the SDN list changes constantly; a base model
  can *never* know today's list. This gap does not close when the next model ships → it's structural, not transient.
- **A named buyer with a mandated, paid pain** (below).
- **Extends the existing OFAC beachhead** and reuses `src/baltor/demos/cfpb/` + `src/teleon/evolution/freshness_runtime.py`.

Documented next capability after this proves out: **CFPB/eCFR regulatory-answer with current-law citations** (the CFPB
demo is the head start). Sanctions screening first because it is deterministic end-to-end; regulatory Q&A adds RAG.

## Buyer & pain

- **Buyer:** compliance / AML lead at a fintech, neobank, payments processor, or crypto on-ramp (Series A–C, already
  running screening but bleeding on it). Secondary: legal-ops at a regulated enterprise.
- **Job-to-be-done:** screen a counterparty name (onboarding / payment / periodic re-screen) against the *current*
  US sanctions list and get a defensible match/no-match with provenance an examiner will accept.
- **Why they pay:** screening is legally mandated; a missed true match = regulatory fine + enforcement; a flood of
  false positives = ops cost (analysts clearing junk). They pay for **accuracy + a current list + an audit trail.**

## The capability contract (CapabilityTask)

```
PurposeTask: sanctions.screen.v1
  input:   { name: str, [dob], [country], [entity_type: person|org], [threshold] }
  output:  ScreeningResult {
             verdict: clear | potential_match | match,
             matches: [{ sdn_id, matched_name, score, program, list_published_date }],
             provenance: { source: us-treasury OFAC SDN, list_version, retrieved_at, signed: true },
             freshness:  { list_age, sync_cadence, status: fresh|held_out_stale },
             receipt_id, serves_truth: true (for the match) | review_ticket if borderline
           }
```

## End-to-end flow through the architecture (what makes it "live")

1. **Baltor — ingest → reconcile → harden → serve (the context engine):**
   - Ingest the OFAC SDN list from `us-treasury` (signed source, `source_authority_registry`).
   - Normalize + index names (aliases, transliterations) → a `canonical_entity` / `object_embedding` row family.
   - **Freshness/CDC:** `src/teleon/evolution/freshness_runtime.py` binds the list to a sync cadence (volatility_class
     = high → daily) + a CDC re-heal trigger; a stale list is **held out** (serve nothing stale — the lossless held-out
     status), never a silent stale answer.
2. **Teleon — the descent (the runtime proof):**
   - **Before (unbounded):** an LLM answers "is X sanctioned?" — non-deterministic, no provenance, stale.
   - **After (bounded):** a deterministic matcher (exact + fuzzy: Jaro-Winkler/token over the canonicalized list) under
     objective `maximize_accuracy` / `maximize_determinism` (`src/teleon/objectives` PRESETS), selecting the matcher
     impl from the implementation registry.
   - Record the move as a `DescentAttempt` in the brain (`descent_attempt_store`, history tier of
     `storage_tier_policy.json`): axes `determinism ↑`, `freshness ↑`, `verifiability ↑`, `cost ↓`. The brain learns
     this descent generalizes to other list-screening capabilities (EU/UN/BIS next).
3. **Governance (the crux — why this proves the whole thesis):**
   - The **screening verdict is a governed TRUTH-bearing output** — a deterministic computation over a *signed* source
     with a receipt — NOT an LLM opinion. This is the one place `serves_truth = true`, *because* an LLM never decides it.
   - Any LLM-generated *explanation/narrative* stays `serves_truth=false` (advisory).
   - **Promotion boundary:** a clear-threshold match against a fresh signed list → returned directly; a borderline
     fuzzy near-match → `review_ticket` (human-in-the-loop), never auto-cleared.
   - Every result carries a **receipt** (`src/teleon/inference/receipts.py` pattern): source, list_version, retrieved_at,
     matcher version, score — the audit trail an examiner accepts.

## The margin proof (measured before/after — the thing the board demanded)

Ship with a benchmark harness (the `--self-test` idiom) that reports, on a labeled set (public SDN entries + known
non-matches + synthetic near-misses):

| Metric | LLM-only baseline | Teleon bounded | Why it matters |
|---|---|---|---|
| **Recall** (caught true matches) | measure | target ≥ 0.99 | a miss = a fine |
| **Precision** (false-positive rate) | measure | beat baseline | false positives = analyst cost |
| **Hallucinated/ungrounded citations** | measure (expect >0) | **0** (every match cites an SDN id) | provenance |
| **Freshness lag** (list age at answer) | unbounded (training cutoff) | ≤ sync cadence (e.g. ≤ 24h) | currency |
| **Cost / latency per screen** | LLM call | deterministic match (≪ cost) | the margin story |
| **Reproducibility** | non-deterministic | same input+list_version → same output | auditability |

This single table is the company's first real evidence: *governed, current, provable, cheaper.*

## MVP cut (ship this; everything else is later)

- **In:** single-name screen against the **US OFAC SDN list only**, exact + fuzzy match, freshness receipt, provenance,
  review-ticket on borderline, the benchmark harness, one API endpoint + a thin result view.
- **Out (next):** EU/UN/BIS consolidated lists, batch/bulk screening, ongoing-monitoring re-screen, full KYC, UI polish,
  the CFPB/eCFR regulatory-answer capability.

## Build plan (reuses what exists; ~2 weeks to a design-partner pilot)

1. **Ingest + freshness** — wire the OFAC SDN fetch to `us-treasury` via the source-authority + `freshness_runtime`
   (daily cadence, CDC re-heal, held-out-stale). [Baltor]
2. **Deterministic matcher** — exact + fuzzy over canonicalized names, behind the objective selector; register as a
   capability implementation. [Teleon]
3. **Descent + receipt** — record the before/after `DescentAttempt`; emit the screening receipt. [Teleon]
4. **Governance gates** — `serves_truth=true` only for the deterministic verdict; review-ticket on borderline.
5. **Benchmark harness** — `scripts/check_sanctions_screening.py --self-test` producing the margin table above.
6. **Thin live surface** — one `POST /screen` endpoint + a result view in the Capability Assurance Portal.
7. **Design partner** — one fintech/AML team routes real onboarding names; capture the cost/accuracy delta.

## Non-goals / safety

- No real PII stored — the SDN list is public; query names in tests are synthetic or public figures (`CLAUDE.md` safety).
- Not insurance (out of scope per `CLAUDE.md`). This is AML/sanctions compliance.
- The verdict is decision-support with an audit trail, not legal advice; borderline → human review.

## The one ask of the first design partner

A compliance team willing to (a) send a sample of real onboarding names (or let us screen against their last N), and
(b) tell us their current tool's false-positive rate + cost-per-screen, so the margin table is *their* numbers.
