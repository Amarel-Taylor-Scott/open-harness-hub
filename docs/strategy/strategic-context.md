# Strategic context + codebase reconciliation (2026-05-29)

The owner's canonical strategic framing, **reconciled with what's actually built**. This doc records the
strategy *and* maps it to the code, flags divergences (per the "surface tension, don't silently
re-architect" rule), and lists only the smallest remaining steps. Detail lives in [[positioning-v2.md]]
(canonical positioning), [[north-star.md]] (M1–M5 execution), [[beat-contextual-positioning.md]],
[[oracle-corpus-and-tooling-map.md]], [[open-core-line-and-learn-from-contextual.md]].

## The canonical positioning (unchanged — already committed)
- **One line:** *"Verified, current, provable context — for the agent you already run."*
- **The wedge sentence:** *"Most platforms check your docs are current. We check your docs are correct —
  against the source of truth."*
- **The verified bundle (the moat — nobody sells all three):** **provenance** (signed origin, C2PA +
  attestation registry) + **verification** (adversarial check vs the authority + HITL ← the differentiator)
  + **freshness** (track the source, flag stale/contradicted).
- **Two products, one platform:** OHH = the **open funnel + consumption surface** (NOT a feature-competitor);
  the Verified Context Service (CEaaS) = the **headline business + moat**. The join: a corpus/tool governed
  **once**, consumed two ways (wired into an OHH harness, or served into any agent/RAG platform).
- **Priorities:** CEaaS verified-corpus capability → agent-neutral serving + upstream push-exporters
  (Contextual/Snowflake/Databricks) → one wedge beachhead (sanctions) end-to-end → OHH as the free funnel.

## Reconciliation — Part 2 concepts vs what EXISTS (reuse, don't rebuild)
| Concept the flow needs | Status in the codebase |
|---|---|
| Authoritative/oracle source registry | **EXISTS** — `data/source-registry.jsonl` (51 + 13 oracle sources: ILO/DOL/FATF/EUR-Lex/SEC/EU-FLR/CSDDD/EUDR) |
| Corpora + tiers (raw→compressed→hyper) + fingerprint | **EXISTS** — `scripts/enrichment/tier_pipeline.py` (real; per-tier fidelity) |
| Provenance (signed origin) | **DEF** — `catalog/processors/assurance/oracle-c2pa-attest.yaml` (impl = next) |
| Verification (vs authority + adversarial) | **REAL** — `corpus_integrity_check` (anti-poisoning), `multi_source_corroborate` (independence-aware); **DEFS** — claim-refute, web-search-verify, authority-fetch-diff |
| Freshness signals | **REAL** — `scripts/sanctions/sanctions_freshness.py` (stale/contradicted + would-be-violation); **DEF** — corpus-freshness-diff |
| Cross-source conflicts | **DEF** — `cross-source-reconcile.yaml` |
| Human-in-the-loop | **PARTIAL** — verdicts emit quarantine/review (the HITL hook); the review-queue object exists in schemas |
| Compliance artifacts (EU-AI-Act/AIBOM) | **EXISTS** — export emitters (SPDX/C2PA/JSON-LD/EU-AI-Act skeleton) |
| **End-to-end flow** (ingest→verify→serve→report) | **BUILDING NOW** — `scripts/pipeline/verified_context_flow.py` (wave `wqm8sua15`) |

**Most of Part 2/3 is already implemented this session (M1–M4).** Extend these; don't re-introduce parallel entities.

## Divergence to DECIDE (flagged, not silently changed)
- **Naming-as-config / `web/products.js`.** Part 3 suggests product names live in one source of truth like
  `web/products.js`. **We removed `products.js`** when we split the front-end into self-contained per-product
  folders (`web/harness-hub/`, `web/context-enrichment/`) — the owner's explicit earlier instruction ("separate
  folders for all front-end work, only backend shared"). So naming is currently **per-folder, not centralized.**
  These two goals conflict. **Options (owner's call):**
  1. *(recommended, smallest)* a shared **brand data file** (e.g. `web/brand.json` — pure data, not front-end
     logic) that each per-folder front-end + the server read at serve time → names/taglines centralized
     **without** cross-importing front-end code (satisfies both the folder-split and naming-as-config).
  2. keep per-folder hardcoded (status quo) + a one-line note documenting where each brand string lives.
  3. re-introduce `products.js` (reverses the folder-split decision — not recommended).
  I'll implement (1) only on your go — it touches both front-end folders + the server (a design/naming call).

## Smallest remaining steps (most is built; weigh order against the running wave)
1. **Finish the e2e verified-context flow** — building now (`wqm8sua15`); commit when verified.
2. **Provenance impl** — make `oracle-c2pa-attest` real (signed manifest + hash registry) — the one assurance
   component still a definition.
3. **Push-exporters** — `deliver/` exporters that push a verified corpus *into* Contextual (Documents API),
   Snowflake/Databricks (the upstream-supplier play) — extends the existing `deliver/` bucket.
4. **`/why` page** — head-to-head (us vs Contextual vs raw RAG vs DIY) led by "current vs correct"; uses the
   Part-4 copy below; honest (don't pitch against their builder/actions/governance).
5. **OHH consumption surface** — let the Knowledge Corpus primitive bind a verified corpus + show its
   assurance status (provenance/verification/freshness) — keep the free tier intact, resist builder feature-creep.

## Part 4 copy (recorded for the /why page + landings — adapt, not final)
- Hero: *"Verified, current, provable context — for the agent you already run." / "We don't just retrieve
  your knowledge. We prove it's right."*
- OHH: *"Power your agents with governed harnesses." / "Open, portable, governed — works with the tools you
  already use, no lock-in."*
- CEaaS: *"Provenance + verification + freshness. Nobody sells all three together."*
- /why columns: vs Contextual — *"They ground the answer in your corpus — even if it's wrong. We verify the
  corpus."*; vs raw RAG — *"Retrieval without verification is confident wrongness."*; vs DIY — *"Stop
  hand-maintaining regulatory corpora; subscribe to verified, always-current truth."*
- Sanctions beachhead — *"Sanctions lists change as often as daily. A stale index is a federal violation.
  We keep your context current — and prove it."*

---
*warrant: user-intent — the owner's "Strategic Context for Claude Code" (treat as context to reconcile,
reuse-first, flag divergence); corroboration — the committed positioning-v2 + the M1–M4 implementations.*
