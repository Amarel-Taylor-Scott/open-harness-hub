# Backlog status — "all items working, fully wired, no orphaned paths" (2026-06-12)

Status of every item in the platform 5W1H backlog (`platform-5w1h-analysis-2026-06-12.md`
Part E) plus the three de-orphan wirings. Gates at close: flywheel **GREEN 447/447**,
validate clean, recording-readiness **GO**.

## Done + wired

| # | Item | What shipped | Wired into |
|---|---|---|---|
| 1 | Silent auth fallback | preview banner across all kits — a down identity service can't look like a saved sign-up | `oh-site.jsx` (harness-hub/baltor/teleon + dist); 4 auth/design proofs green |
| 2 | Bridge 56 catalog processors | `catalog_processor_bridge` (dispatch by id/kind) + `catalog_runtime_adapter` (97 as runtime Processors) | **`default_registry()` now registers all 97** (102 refs); built-JSON dispatch index keeps the runtime stdlib-only (C35) |
| 3 | Live model scorers in `measure` | `eval_scorers` — reference-free faithfulness proxy scores lift WITHOUT gold; LLM N-judge bounded | **`MeasurementStage` defaults to `LadderJudge`**; `make test` |
| 4 | Mistral/OpenRouter/Ollama lanes | first-class `from_env()` lanes + Mistral graph node + per-lane wiring proof | `check_model_provider_lanes` (flywheel); live smoke when keyed |
| 7 | Docling + staging→gate job | docling seam already complete; **`promote_staged`** measure→gate promoter | `make ingest-promote`; flywheel; offline holds the boundary, a route promotes |
| 8 | OIPS external-signal + quality | `quality_from_receipts` + `load_external_leaderboard` + shape-bridge | **wired into `oips.py` ranking**; committed leaderboard fixture; cheapest-CAPABLE not cheapest |
| 9 | Cohort policy selector | usage shape → cohort → compression curve | **`compress_with_cohort_policy()`** the wired entry point; `usage_gated_compress` honors the weights; the showcase uses it |
| 10a | Semantic novelty dedup | bounded heavy-paraphrase embedding lane (disjoint-vocab duplicates) | `foundry/novelty` `is_duplicate` includes `embed_near`; inert offline |
| 10c | Receipt (9426) + state (9427) services | both implemented (append-only receipts; replayed state) | **activated in the registry** (start_command + ready_url); live HTTP 200; flywheel |

De-orphan note: before this pass, the runtime bridge / scorer ladder / cohort selector were
self-tested but referenced only by their own modules — built, not used. They are now wired
into `default_registry`, `MeasurementStage`, and `compress_with_cohort_policy` respectively.

## Owner-gated / remaining

| # | Item | State |
|---|---|---|
| 5 | Record the CFPB proof video | **OWNER-GATED** — recording-readiness gate is GO (every surface up, every seam answers); needs a person to record. Not a code task. |
| 6 | Marketing-nav polish | **mostly non-issues** — the app mapper showed Settings exists (sidebar + palette), the logo navigates home, and the email field is present in `/signin` `/signup`; the one real bug (the silent fallback, #1) is fixed. Residual: raise the de-emphasized footer Settings link + an optional inline nav email CTA — cosmetic. |
| 10b | Gate verdicts/receipts in the app UI | **remaining frontend enhancement** — the backend is ready (the receipt service at :9426 serves the receipts; the gate emits verdicts). The UI affordance to surface "proposed → verified → promoted" with the receipt is a scoped frontend build (its own session) and is the one substantive item not yet built. |

## No-orphans confirmation

Every artifact built in this pass is reachable from a real path: the catalog processors from
`default_registry` (the runner), the scorer ladder from `MeasurementStage` (the gate), the
cohort policy from `compress_with_cohort_policy`, the OIPS producers from `oips.py`, the
promote job from `make ingest-promote`, the two services from the service registry, and all of
the above from the flywheel proof suite (447 modules). Nothing built here is referenced only by
its own self-test.
