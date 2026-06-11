# Standards & best-practices adoption — assessment (2026-06-11)

Owner asked: what protocol/class/data-object/framework standards, JSON logging, classification/
prioritization frameworks, thin global base classes, K8s/cloud-function patterns, I/O, abstraction,
or cleanup should we adopt/improve? Honest answer: **most are already in place** — the work is
spreading them consistently and formalizing the one missing base, not adding heavy frameworks.

## Already adopted (a genuine strength — don't redo)

| Standard | Where | Status |
|---|---|---|
| **CloudEvents 1.0** (event envelope) | `src/teleon/io/event_io.py` (`project_event_envelope`) | adopted for the event/bus plane |
| **OpenTelemetry** semantic conventions (service.name, trace_id, span_id) | `src/teleon/compiler/compile.py` (`_otel_attrs` on every compiled unit) | adopted for compiled runtimes |
| **JSON Schema 2020-12** | `schemas/**` (extensive) + `scripts/validate.py` (CI-gated) | repo-wide |
| **EU AI Act** risk classes, **NIST AI RMF** controls, **ISO/IEC 42001** controls, **W3C DPV** data-protection | `schemas/_common.schema.json $defs/envelope` (component envelope) | adopted for catalog components |
| Single-source taxonomies (durability/lift classification) | `scripts/eval/reason_codes.py` (imported, never redefined) | the classification framework |
| Ports / dependency-inversion (abstraction) | `src/teleon/ports/*` (Execution/Sandbox/Reward/Environment/Blackboard providers) | the flexibility/abstractability layer |
| Provider graph + governed routing | `architecture/model_provider_graph.json` + OIPS | + measured-efficiency reorder (this session) |
| Single-source config, no-magic-values | `docs/codex/no-magic-values.md` + drift gates | enforced |

## The one real gap — now closed

The ~70 RUNTIME records (ModelInvocationReceipt, CompiledRuntimeUnit, TeleonRunReceipt, HealOutcome,
the lift result, worker claims) all carried `schema_version` + `is_truth:false` + provenance **by
hand** — a shared convention with no single producer. **`src/teleon/io/governed_record.py`** (NEW,
12/12) is the thin base they extend: one `mint_record` / `validate_record` for the envelope
(`schema_version` + `is_truth` + `provenance` + OTel `trace` + `created_at`), OTel-correlatable,
stdlib-only — records stay plain dicts (the portability strength), they just get one base to adopt.
This is the "thin global class that gets extended" the owner asked for.

## Remaining work — CONSISTENCY, not new frameworks (incremental, owner-paced)

1. **Migrate the runtime records onto `governed_record`** — receipts, compiled units, run receipts,
   heal outcomes, lift results adopt `mint_record` (incremental; each keeps its payload). Low risk.
2. **Spread OTel** beyond the compiler — carry `trace_id`/`span_id` through receipts + the event
   planes so one trace correlates capability → model call → launch → event (the compiler already
   shows the convention).
3. **CloudEvents for the new CDC + controller events** — the self-healing source-change events and
   the worker-controller receipts should project through `event_io` too (the projector exists).
4. **OpenLineage / W3C PROV for lineage** — the governance moat; align the provenance field to a
   recognized lineage format so it's interoperable (memory `baltor-wedge-wraps-providers`). Medium.
5. **Structured service logging** — replace ad-hoc `print`/JSONL with a single governed-record log
   line per service (use `governed_record`), so logs are queryable like everything else.

## Deliberately NOT adopting (the discipline is the strength)

- **Pydantic / heavy data-object frameworks** — stdlib dicts + JSON Schema is faster (cold start on
  Fly), dependency-free, and already validated. A framework buys marginal typing for a real cost.
- **Knative / K8s operators** — Fly Machines is the chosen runtime substrate; the compiler emits
  `k8s_job` as a *portability hedge*, not a Knative dependency. Don't build an operator.
- **A new classification/prioritization framework** — `reason_codes` is the single-source taxonomy;
  `queuePriority` exists in `_common.schema.json`. Adding a framework would fragment the source.
- **A second event/receipt format** — CloudEvents + the governed-record envelope are enough; do not
  invent a third.

## Open-source to wrap as governed CANDIDATES (discovery ≠ trust)

OpenLineage (lineage), the OTel data model (we emit OTel-shaped JSON without the SDK to stay
dep-free), CloudEvents (already), JSON-Patch (for `ctxv://` versioned diffs) — all as candidate
formats/inputs behind the governance rail, never blindly trusted, consistent with how we wrap
ktx/LiteLLM/etc.

**Bottom line:** the standards posture is already strong and explicitly compliance-aligned (EU AI
Act / NIST / ISO 42001 / DPV / CloudEvents / OTel / JSON Schema). The high-value moves are the
governed-record base (done) + spreading OTel/CloudEvents/lineage consistently — incremental cleanup,
not a re-architecture.
