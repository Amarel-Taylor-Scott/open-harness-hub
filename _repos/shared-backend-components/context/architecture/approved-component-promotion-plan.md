# Approved Component Promotion Plan

The database-backed factory has two separate boundaries:

1. candidate generation and scoring
2. active component publication

The approved component promotion planner handles the second boundary. It reads component candidates, subcomponent candidates, and promotion decisions, then emits a side-effect-free Postgres load bundle.

Outputs:

- `components.csv`
- `component-versions.csv`
- `subcomponents.csv`
- `candidate-state-updates.csv`
- `load-approved-components.sql`
- `approved-component-promotion-plan.json`

## Review Gate

A candidate becomes an active component only when all of these are true:

- the decision is `promote_candidate`
- the decision has no risk flags
- the decision has no review reasons
- the candidate review status is approved

All other decisions still update candidate state:

- `review_before_promotion` becomes `review`
- `hold` becomes `held`
- `reject` becomes `rejected`

This keeps generated rows additive and searchable while preventing low-confidence or dedupe-review rows from becoming reusable components.

## Active Rows

Approved candidates generate:

- one `component` row
- one `component_version` row with `definition_source = generated_factory`
- zero or more `subcomponent` rows
- one candidate state update

The planner maps generated primitive types into the allowed active component types. Generic candidate primitives become `knowledge-pack` rows unless a clearer active type is available.

## Seed Behavior

When the generated candidates belong to dedupe-review clusters, the seed promotion decisions are all `hold`: the planner emits zero active component rows and only candidate-state updates. That is expected — the review boundary is working. The next promotion batch should either resolve dedupe clusters or use explicitly approved synthetic test candidates before publishing active rows.

## Promotion lifecycle (consolidated)

> Folds the durable design of the merged promotion-pipeline plans — daily promotion readiness, dedupe resolution, content approval, promotion decision load, promotion index deltas, and the promotion→CDC bridge. Frozen per-run sample counts live in the archived source docs. The approved-component step above is the *last* stage of this lifecycle; the stages below are what feed and surround it. Every planner here is side-effect free — it writes CSV/SQL/JSONL and review evidence only; database execution is a separate worker or operator step.

Ordered spine (additive at every step — a generated row never publishes itself):

1. candidate generation
2. promotion scoring
3. promotion decision load planning
4. staged database load
5. count audit
6. dedupe resolution + content approval (curator / policy)
7. active component promotion (the plan above)
8. component version history, CDC, and index update

### Daily promotion readiness (governance gate — `scripts/db/daily_promotion_readiness_plan`)

Separates two decisions that must never be collapsed: **candidate-table load readiness** vs **tenant-visible active promotion readiness**. For every staged normalized object it checks: source-record link, dedupe-cluster link, content hash, a minimum count of index records, embedding-work record, review-ticket count, risk tier, and active-promotion blockers. It emits `promotion-readiness.jsonl`, `promotion-review-queue.jsonl`, and a plan summary; it never touches Postgres or staged data. The same planner is reusable across model-ops, source-surface, and worker-fleet runs by passing an explicit `--run-summary`. Staged rows may move toward candidate-table loading while candidates requiring embeddings or review stay blocked from tenant-visible promotion. This gate also surfaced and fixed an upstream hazard — long generated seed IDs were being truncated into duplicate candidate IDs, collapsing rows and index records on merge; batches now add stable hash suffixes to seed IDs, normalized-object IDs, and index-record IDs so daily candidates survive without manual repair.

### Dedupe resolution (`scripts/db/dedupe_resolution_plan`)

Dedupe clearance is NOT content approval — the planner keeps the two decisions separate. Conservative resolution actions: `mark_singleton_resolved` (one public member, no duplicate conflict — still leaves content approval outstanding), `merge_exact_duplicates` (same content hash / exact high-confidence match), `route_to_curator` (ambiguous, non-public, or weak evidence), `hold_for_more_evidence`, `reject_cluster`. It adds a `dedupe_resolution` table and emits load SQL for `dedupe_resolution`, `index_record`, `review_ticket`, and the `review_status` transitions on `normalized_object` / `component_candidate`, giving review queues a durable state transition before the promotion planner runs.

### Content approval (`scripts/db/content_approval_plan`)

The gate between dedupe resolution and active promotion — dedupe clears duplicate risk but does not prove content is ready. Four decisions: `approve_for_promotion`, `review_before_promotion`, `hold`, `reject`. Only `approve_for_promotion` creates a derived `promote_candidate` decision; every other decision creates a review or hold path. A curator or policy-review worker marks selected content approved, then feeds those rows back through the approved-component promotion planner above.

### Promotion decision load (`scripts/db/promotion_decision_load_plan`)

Turns scored candidate JSONL into `promotion-decisions.csv`, `promotion-index-records.csv`, `promotion-review-tickets.csv`, `load-promotion-decisions.sql`, and a plan summary. The SQL loads three operational tables — `promotion_decision` (score, decision, criteria, risk flags, recommended outputs), `index_record` (quality search rows for review queues and ranking), and `review_ticket`. Loading decisions + quality index rows incrementally lets the platform prioritize what to review next by promotion score, capability gap, review risk, source trust, expected deployment frequency, cost savings, and model-swap value — instead of rebuilding search after every scoring run.

### Promotion index deltas (`scripts/db/promotion_index_deltas`)

Updates search/quality indexes incrementally rather than triggering a full rebuild: `quality` (score, decision, review reasons, readiness), `facet` (risk flags, recommended outputs, decision category, source family), and `cost` (cost-savings, economic value, deployment-management value) deltas plus a partition manifest. The output is consumed by the partition registry replay audit to prove candidate scoring produced deterministic index state.

### Promotion → CDC bridge (`scripts/db/promotion_cdc_bridge_plan`)

Connects approved promotion to component change-data-capture. It reads `component-versions.csv` from the approved-promotion planner, converts rows to canonical component-version JSONL, and runs the component CDC planner — emitting `new-component-versions.jsonl`, `component-change-events.jsonl`, change index records, change review tickets, and load SQL. With no previous-version file the bridge treats rows as first-publication events (useful for seed loads); production workers should export previous versions from Postgres whenever a component id already exists. This gives approved batches the same incremental lifecycle spine as public facts and signed knowledge objects: which component changed, which version replaced which, what hashes changed, whether signed-publisher state changed, which search records need refresh, and which changes need review.

> A synthetic **approved-promotion smoke** fixture (one approved candidate walked through promotion → version → subcomponent → CDC bridge → change event → freshness/index → review ticket) is archived alongside the merged sources; it exists so the loader/CDC/index projections can be tested without weakening the review boundary.
