# Observability + Lineage Provider Seam & Interchange Standards (C-OBS-1)

Baltor **wraps** observability/lineage tools — it never becomes another tracing or lineage API. This
pass adds the code seam behind the two catalog slots and the four interchange standards that make a
Baltor receipt **portable** without handing any external tool authority over truth.

> Invariant: **providers DESCRIBE; Baltor proofs / receipts / the flywheel stay the authority.** A
> provider can render what happened into any standard format, but it can neither mutate canonical state
> nor change a claim's status. An *allegation* stays an *allegation* in every rendering.

## The two seams

| Slot (catalog) | Port | Wired stub (active) | Candidates (catalog-only) | I/O |
|---|---|---|---|---|
| `observability_provider` | `ObservabilityProvider` | `observability.baltor_local_trace@v1` | Langfuse · Phoenix · LangSmith | `ContextOperationSpan[] → SpanTree` |
| `lineage_provider` | `LineageProvider` | `lineage.baltor_local@v1` | OpenLineage | `LineageEvent → LineageFacet` |

- `_repos/baltor/backend/src/baltor/observability/tracing/provider.py` — spans → `SpanTree` (nesting, deterministic order by `(occurred_at, span_id)`, held-out propagation). Spans are **frozen** dataclasses, so a provider physically cannot mutate canonical state through them.
- `_repos/baltor/backend/src/baltor/observability/projections/lineage.py` — `LineageEvent → LineageFacet` (normalized record **plus** standards renderings + a content hash for CDC).
- `_repos/baltor/backend/src/baltor/observability/projections/standards.py` — the four deterministic mappers.

External candidates stay `status: candidate` behind the port; the **wired** adapter is always the
local stub (enforced by `check_context_provider_catalog` + `check_observability_governance_redteam`).
Adopting Langfuse/OpenLineage for real requires a card + contract test + fallback (no `pip install`
on this host today — the candidates are pre-registered so the first real dep can't land unchecked).

## The four adopted standards

1. **W3C PROV-JSON** — `to_prov_json(event)` → `prefix` + `entity`/`activity`/`agent` + `used` /
   `wasGeneratedBy` / `wasAttributedTo` / `wasDerivedFrom`. Outputs are entities generated-by the
   activity and attributed-to the accountable agent; each output `wasDerivedFrom` each input. Baltor
   governance facets (`authority`, `claim_status`, `receipt_id`, `held_out`, `verified_current`) ride
   on the output entities under the `baltor:` prefix.
2. **OpenLineage RunEvent** (spec 2-0-2) — `to_openlineage_run_event(event, event_type=…)` →
   `eventType`/`eventTime`/`producer`/`schemaURL`/`run`/`job`/`inputs`/`outputs`. The run and every
   output dataset carry a `baltor_governance` custom facet (`_producer` + `_schemaURL` + the facet
   keys). `runId` is a **deterministic** UUID derived by hashing `event_id` (no `uuid4`, so the demo
   reproduces). There is already a *template* emitter at `_repos/shared-backend-components/scripts/emit/openlineage.py` for pipeline
   catalog cards; this is the **runtime** lineage seam.
3. **W3C Web Annotation** — `to_web_annotation(...)` anchors a claim to a source span: `@context` =
   `anno.jsonld`, `body` = the claim (with `baltor:governance`), `target.selector` = a
   `FragmentSelector` carrying the `ctx://…#page=…&block=…` handle, plus an optional
   `TextQuoteSelector` for the exact quote. This is the standard, portable way to say *"this claim is
   anchored to this span of this source."*
4. **RFC 6902 JSON Patch** — `to_json_patch(before, after, governance, …)` emits a deterministic
   `add`/`remove`/`replace` op list (keys sorted, RFC 6901 pointer escaping `~0`/`~1`) for a fact /
   version delta (supersession, reconciliation change) — CDC-friendly and content-hashable. The bare
   `patch` array is standards-conformant; the wrapper records `from_version`/`to_version` + governance.

## The governance / anti-laundering guard

`governance_facet()` filters any attributes dict down to **only** `GOVERNANCE_FACET_KEYS` (the single
source of the portable-receipt fields). This is the laundering guard proven by
`check_observability_governance_redteam`:

- an allegation stays an allegation across PROV / OpenLineage / Web Annotation;
- a held-out record is flagged in every rendering (consumers drop it; never served as truth);
- forged/extra governance keys (`is_truth`, `override_authority`, …) are stripped;
- records are frozen; providers expose no `save`/`commit`/`write`/`publish` method;
- the named external providers stay candidate-only; the wired adapter is the local stub;
- every rendering is deterministic (same input → identical bytes).

## Proofs

`check_observability_provider_seam` · `check_lineage_standards_adapters` ·
`check_observability_governance_redteam` — all offline, deterministic, in `baltor_flywheel.py`
`PROOF_MODULES`.

## Deferred (`OPP-observability-surface`)

Real Langfuse/OpenLineage adapters behind the ports (needs the dep), a live `/observability` trace
view (projection-only over `SpanTree`/`LineageFacet`), an OpenTelemetry collector seam, and emitting
these renderings from the live pipeline run. The seam + standards land now; the heavy surfaces are
honestly deferred.
