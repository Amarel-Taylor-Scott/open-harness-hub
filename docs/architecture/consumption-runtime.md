# Consumption Runtime (C-CONSUME-1) — the ingestion→consumption forcing function

The whole pipeline is only "done" when a consumer can ask for context and receive a **served `ContextResponse`**
that contains ONLY verified + promoted + consumable facts, each with source handles and full receipt lineage —
with everything unsafe surfaced separately as warnings. *No artifact is consumable merely because it exists.*

```
INGEST (CFPB) → decompose → [artifacts] → Verification Gate (C40) → Optimization bake-off (C43/C43.1)
   → Consumption-Readiness Gate → ConsumptionService → served ContextResponse.v1 (+ ConsumptionReceipt)
```

## The runtime

`scripts/runtime/consumption.py` (declared runtime owner `ConsumptionService`):

- **`ConsumptionService.serve(...)`** — domain-agnostic. Serves a pack ONLY if its `ConsumptionReadinessReport`
  is consumable; builds a `ContextResponse` (served facts + held-out warnings + receipt lineage + freshness +
  lineage) and a `ConsumptionReceipt`. Truth-only: a `narrative_allegation` is never served; every served fact
  must carry a source handle; a non-consumable pack is **refused** (zero served facts, `answer=""`).
- **`run_cfpb_to_consumption(tenant_id)`** — the end-to-end orchestrator. It (1) ingests + decomposes a real CFPB
  complaint via `decompose_cfpb_complaint`, (2) adds the reference regulatory conflict (Reg E "10 business days"
  authority 3 vs FAQ "30 days" authority 1), (3) verifies the answer fact through the C40 `VerificationGate`,
  (4) runs the C43 optimization bake-off (`CandidateGenerator` → `optimize_many` → promoted best), (5) runs the
  `ConsumptionReadinessGate`, (6) serves a `ContextResponse`. Reuses the existing engines; no second
  bus/store/gateway/optimizer.

## Contracts (registered)

`ContextResponse.v1`, `ConsumptionReceipt.v1`, `ConsumptionRequest.v1` (`schemas/consumption/`), registered in
`architecture/contract_registry.json`. A served fact's schema **requires** `artifact_id` + `source_handle` +
`claim_status`; the response **requires** the three receipt ids + lineage + freshness.

## Proven reference result (offline, deterministic)

`python3 scripts/check_cfpb_to_consumption_end_to_end.py --self-test` produces a served `ContextResponse` where:

- `answer` = **"10 business days"**
- served facts include `fact-rege-10`, each with a source handle + verification + optimization receipt ids
- **FAQ-30 appears only in `held_out_warnings`** (lower-authority conflict loser), never served
- narrative allegations appear only as warnings, never as served facts
- the optimization bake-off ran multiple variants and rejected ≥1
- response carries verification + optimization + consumption receipt ids + lineage (source artifacts, context
  pack, promotion id)
- the response is byte-identical across reruns

## Safety / anti-bypass (proven)

- `check_consumption_service` — serves only consumable packs; handles + lineage on every served fact; held-out
  as warnings; allegations never served; refuses non-consumable packs; schema enforced.
- `check_consumption_blocks_bad_artifacts` — unverified / unpromoted / allegation / unresolved-conflict /
  cross-tenant packs are all refused (no served facts).
- `check_no_consumption_bypass` — no served facts without passing the gate; `ContextResponse` is built only in
  the consumption runtime; web is projection-only; no admin/web/bus bypass.

## Current limitations (honest) + how they're protected

- **Surfaces pending (sequenced next):** the HTTP route `POST /api/context/serve`, the `/consume` UI page, the
  durable `context.consume` worker command, and the minimum Fact-Watchtower freshness slice. The runtime
  forcing function (the served `ContextResponse` with full lineage + safety) is proven now; these are
  projections/entrypoints over it.
- **Vectors/graph lineage** are referenced (artifact ids + source handles + context pack id); wiring the
  `artifact_graph` vector/edge ids into the response lineage is the `check_vector_graph_consumption_path`
  follow-on.
- **Freshness** is graceful (stale_fact_count/fragile_fact_count = 0) until the Fact Watchtower supplies
  `FragilityMetadata`; the C40 gate's fragile-fact check already enforces it once present.

How to invoke (runtime): `python3 -c "from scripts.runtime.consumption import run_cfpb_to_consumption as r; import json; print(json.dumps(r('demo', now='2026-06-05T00:00:00Z')['response'], indent=2))"`.
ADR: `archive/legacy/docs/adr/0006-optimization-harness-governed-improvement.md` (the gate→optimize→consume ladder).
