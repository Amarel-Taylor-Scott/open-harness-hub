# CFPB ingestion — tested (Chunk 1)

How CFPB data enters Baltor's **Source Systems** stage and becomes governed context objects + a
context pack + a receipt — **no raw corpus dump**. Every figure below is from a real run (commands +
output included); narratives stay labeled as unverified allegations.

## Source (free, no paid cloud)
- **Live:** CFPB Consumer Complaint Database API — `https://www.consumerfinance.gov/data-research/
  consumer-complaints/search/api/v1/` (public, **no auth**), tightly limited (`--limit`, byte-capped).
- **Offline (default, deterministic):** `data/cfpb-demo/complaints-fixture.json` (5 real-shaped records).
- Connector: `scripts/demo_cfpb_context_pack.py`. Source handle prefix: `ctx://cfpb/consumer-complaints`.
- A second CFPB path: `scripts/integrate_cfpb.py` ingests the regulatory side (12 CFR 1005 Reg E) with an
  optional free Federal Register fetch — that's the `/integrate` one-click flow.

## Run it
```bash
# offline (deterministic) — the default
PYTHONPATH=. python3 scripts/demo_cfpb_context_pack.py --out-dir /tmp/cfpb-ingest
# live free sample (no auth), still emits governed artifacts (not raw):
PYTHONPATH=. python3 scripts/demo_cfpb_context_pack.py --live --limit 5 --product "Credit reporting"
```

## What it produces (verified output, offline run)
```
{ "ok": true, "live": false, "record_count": 5,
  "pack_id": "context-pack/cfpb-complaints-demo-8d33754a04eb",
  "trace_id": "trace-cfpb-demo-8d33754a04eb" }
```
Four governed artifacts in `--out-dir` (+ a README) — **no raw narrative dump**:

| artifact | what | governance |
|---|---|---|
| `source-records.json` | 5 normalized CFPB records | source-linked; native_id + source_url |
| `context-objects.json` | 5 context objects (see Chunk 2 shape) | each carries facets + lineage + evidence handle |
| `context-pack.json` | the governed pack: `claims[3]`, `facets[5]`, `object_ids[5]`, `policy[5]`, `risks[3]`, `source_handles[6]` | summary: "Only aggregate claims are candidates for pack-level use; complaint narratives remain unverified allegations." |
| `context-receipt.json` | `claims_included[3]`, `claims_excluded[2]`, `policy_decision[2]`, `sources_used[5]`, `pipeline_id`, `trace_id` | the portable proof of what was served + why claims were excluded |

**Determinism:** the `pack_id`/`trace_id` are content-hash-derived (`…8d33754a04eb`) — re-running the
offline path yields byte-identical ids. The pipeline id is `baltor.demo.cfpb-consumer-complaints.v0`.

## The governance that matters (why this is "governed ingestion", not scraping)
- **Narratives are NOT certified as fact.** Each object's facet:
  `baltor_demo.narrative_policy = "unverified_allegation_do_not_certify_as_fact"` and
  `claim_status = "aggregate_candidate_only"`. The receipt **excludes 2 claims** and **includes 3**
  (aggregate only) — visible, not hidden.
- **Every record keeps a source handle** (`ctx://cfpb/consumer-complaints/complaint/demo-1001`) so any
  claim is expandable back to its origin (the lineage invariant: digestible front, expandable back).
- **Aggregate-only by default** — the pack answers "what can Baltor *safely* say about this public
  sample?", not "repeat the complaints."

## Test status
- Connector run: **`ok: true`, 5 records, 4 artifacts** (offline, deterministic; output above).
- The downstream decomposition contract is a flywheel proof (`decompose_to_context_objects`,
  `document_decompose` — both GREEN; see Chunk 2: `docs/decomposition/decomposition-into-components.md`).
- The regulatory CFPB path (`integrate_cfpb`) is a flywheel proof (`integrate_cfpb --self-test`, GREEN)
  and the `/integrate` page (answer 10, contradiction caught) — see `scripts/integrate_cfpb.py`.

## Next (backlog, not done here)
- Add `demo_cfpb_context_pack --self-test` + register it in the flywheel (currently run-mode only,
  deterministic but not yet a continuous proof). Warrant: proof-per-increment.
