# Routine library (the blessed way to do X, and where it's already done)

## Purpose

The routine library (`architecture/routine_library.json`) is the canonical inventory of **reusable
routines** — named, repeatable units of work — grouped by the stage they serve. At scale, the
expensive question is not "can this be done?" but "what is the *blessed* way to do this, and where is
it already done so I can copy it instead of reinventing it?" The routine library answers exactly
that. It is a META index over existing code: it introduces no new runtime, worker, or framework.

Each routine names:

- `routine_id` and `category` (one of the seven stage categories);
- `pattern_id` — the canonical pattern it instantiates (single source: the canonical 25-pattern list);
- `template_id` — the config type / template it starts from (or `null`);
- `inputs` / `outputs` — the contract;
- `commands` — how to run or prove it;
- `proofs` — the `check_*.py` scripts that hold it honest;
- `anti_patterns` — the ways it is commonly done wrong;
- `examples` — **real repo paths** where the routine already exists (verified to exist; empty only
  when the routine is declared-but-not-yet-built, in which case it carries a `note`).

## Categories

| Category | Covers |
|---|---|
| `ingestion_routines` | full_sync, incremental_sync, backfill, webhook_ingest, folder_scan, health_check, retry_failed, reconcile_sync_state |
| `decomposition_routines` | structured_record_to_atomic_facts, narrative_to_allegations, parsed_document_to_tree, table_to_cells, paragraph_to_sentences |
| `durable_worker_routines` | enqueue, claim_with_lease, ack, nack_retry, dead_letter, idempotency_check, outbox_publish |
| `reconciliation_routines` | generate_conflict_candidates, detect_deadline_conflict, apply_authority_policy, apply_freshness_policy, generate_held_out_warning, write_reconciliation_receipt |
| `optimization_routines` | freeze_baseline, generate_candidates, evaluate_candidate, regression_gate, promote_candidate, consumption_readiness_check |
| `api_ui_routines` | projection_route, detail_route, status_route, review_page, dashboard_panel |
| `docs_proof_routines` | self_test_script, section_doc, current_state_report, review_pack_section |

## Proof

```bash
python3 scripts/check_routine_library.py --self-test
```

The proof enforces: the file parses; every routine carries all required keys; no duplicate
`routine_id`; every `pattern_id` is one of the canonical 25; every `category` is declared; **every
non-empty `example`/`proof` path points at a file that actually exists** (a routine that names a file
that no longer exists is a stale claim and fails); and routines with empty examples carry a `note`.

## Limitations

- The library indexes routines that EXIST plus a small number declared-but-not-yet-built (clearly
  marked with `examples: []` + a `note`, e.g. `webhook_ingest`, `paragraph_to_sentences`). It is not
  a roadmap of everything that should exist.
- `examples` are pointers, not the only place a routine appears — they are one verified anchor to
  copy from, not an exhaustive call-graph.
- The library is descriptive of shape, not a registry the runtime loads; it does not execute
  anything. Keeping it honest is the proof's job (paths must resolve), and keeping it current is a
  documentation-discipline job when routines move.
