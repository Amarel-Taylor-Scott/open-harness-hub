# Generic source → consumption

`_repos/shared-backend-components/scripts/runtime/source_consumption.py` is the **domain-agnostic** orchestrator that takes any source
*type* and walks it through the existing Baltor engines to a single served `ContextResponse` — or an
honest `non_consumable_reason`. It generalizes `run_cfpb_to_consumption` (which proved one hand-built
domain) to **any** source the `SourceAdapterPort` can normalize.

It introduces **no second** consumption service, optimizer, verifier, parser, or bus. It is pure wiring
over seams that already exist.

## Entry point

```python
from scripts.runtime.source_consumption import run_source_to_consumption

result = run_source_to_consumption(
    source_type, payload, *,
    tenant_id, source_id, scope="global_public", authority="unknown",
    require_optimized=True, now="1970-01-01T00:00:00Z",
)
```

Deterministic + offline: `now` is **injected** (no wall-clock); all ids are content-addressed by the
underlying engines (no RNG).

## The motion (reused engines)

```
payload
  └─ source_adapters.normalize(source_type, ...)         # the SourceAdapterPort
        ├─ consumable:false  (pdf / html / unknown)  ──▶  non_consumable_reason + raw source artifacts
        └─ consumable:true
              └─ assemble atomic_fact / narrative_allegation into a pack
                    └─ VerificationGate.evaluate(...)            # C40, per fact → allow / hold_out
                    └─ OptimizationHarness.optimize_many(...)    # C43 bake-off → promote best non-regressing
                    └─ ConsumptionReadinessGate.assess(...)      # C43.1 verified + promoted + leak-free
                    └─ ConsumptionService.serve(...)             # ── the ONE consumption service ──
                          └─ ContextResponse (served)  OR  refused → non_consumable_reason
```

- `source_record` / `source_field` artifacts stay as **lineage only** — they are never assembled as
  servable facts. Only `atomic_fact` and `narrative_allegation` enter the pack.
- Structured fields → **promotion-eligible** `atomic_fact`. Free-text → held-out `narrative_allegation`,
  surfaced **separately** as a warning and never served as truth.
- `require_optimized=True` means a served pack must have been **promoted** by the harness, not passed
  through raw.

## The honest non-consumable boundary

A source whose parser is a **cataloged candidate** (`pdf` → Docling, `html`) or whose type is unknown
returns:

```python
{"consumable": False, "non_consumable_reason": "parser_unavailable: ...",
 "source_artifacts": [...raw stored...], "response": None, "summary": {...}}
```

There is **no faked `ContextResponse`** and **no fabricated served fact**. The raw payload is stored as a
source artifact so lineage is preserved and the source can be re-processed once a real parser lands.

## RUN SUMMARY

Every run returns a deterministic `summary` dict:

| field | meaning |
|---|---|
| `run_id` | content-addressed run id |
| `tenant_id` / `source_type` / `source_scope` / `parser_provider` | source identity |
| `source_artifact_count` | raw source artifacts stored |
| `atomic_fact_count` / `allegation_count` | facts vs. held-out allegations assembled |
| `conflict_count` | cross-source conflicts (0 for a single source) |
| `verification_status` | `allow` / `hold_out` / `no_facts` |
| `optimization_status` | `promote` / `reject` |
| `consumption_status` | `served` / `refused` / `non_consumable` |
| `served_fact_count` / `held_out_warning_count` | what the response served vs. held out |
| `non_consumable_reason` | the reason when not served (empty when served) |

## Source matrix

`_repos/shared-backend-components/architecture/multi_source_run_matrix.json` is the per-source-TYPE run matrix: each row declares a
`source_type`, a `payload`, a `scope`, and the `expected_consumption_status`. See
[`_repos/shared-backend-components/docs/status/multi-source-regression.md`](../status/multi-source-regression.md) for the live table.

## Proofs

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_source_to_consumption_generic.py --self-test
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_multi_source_regression.py --self-test
```

- `check_source_to_consumption_generic` — a generic JSON source and a tenant-private CSV each reach a
  schema-valid served `ContextResponse` (handles present, allegations held out, no global leak); a PDF
  source returns `consumable:false` with a `parser_unavailable` reason; deterministic.
- `check_multi_source_regression` — runs **every** matrix row and asserts each matches its expected
  `consumption_status`; candidate rows are never served as fact; no tenant-private→global leak.
