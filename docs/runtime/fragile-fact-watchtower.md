# Fragile Fact Watchtower (minimum slice — FACT-1..7)

## Purpose

A fact that perishes must be **caught before it is served as truth**. The watchtower attaches a freshness
contract (**FragilityMetadata**) to every fragile fact, watches it under a cadence (**WatchPolicy**), and when
a fact passes its refresh horizon it emits a durable **VerificationTask** whose refresh stores an **evidence**
record — never a fabricated answer. The C40 verification gate already reads a fragility dict gracefully; this
slice supplies the real metadata, classifier, and refresh planner that the gate's fragile-fact check was
designed against.

This is the **minimum**: deterministic, offline, stdlib-only. There is no second runtime/bus/worker; the
watchtower reuses the existing C40 gate seam and the governed artifact-type registry.

## Owner

- `src/baltor/facts/` — the watchtower home (section `fragile_fact_watchtower`).
- Logic owner: `src/baltor/facts/refresh_planner.py` (planner) + `src/baltor/facts/classifier.py` (classifier).
- Contracts owner: `src/baltor/contracts/artifacts/` (the six frozen dataclasses).

## Contracts (six artifact types, all v1, content-addressed ids)

| Artifact | Module | Schema | Key fields |
|---|---|---|---|
| FactAssertion | `src/baltor/contracts/artifacts/fact_assertion.py` | `schemas/artifacts/FactAssertion.schema.json` | `claim_type` ∈ CLAIM_SHAPED, `scope`, `asserted_at` |
| CanonicalFact | `src/baltor/contracts/artifacts/canonical_fact.py` | `schemas/artifacts/CanonicalFact.schema.json` | `status` (9-value lifecycle), `scope`, `fragility_id` |
| FragilityMetadata | `src/baltor/contracts/artifacts/fragility_metadata.py` | `schemas/artifacts/FragilityMetadata.schema.json` | `volatility_class`, `last_verified_at` + (`next_verify_at` OR `ttl_seconds`) + `watch_policy_id` |
| WatchPolicy | `src/baltor/contracts/artifacts/watch_policy.py` | `schemas/artifacts/WatchPolicy.schema.json` | `refresh_interval_seconds`, `no_refresh`, `escalate_on_conflict` |
| VerificationTask | `src/baltor/contracts/artifacts/verification_task.py` | `schemas/artifacts/VerificationTask.schema.json` | `due_at` (missed horizon), `scope`, `watch_policy_id`, `status` |
| VerificationResult | `src/baltor/contracts/artifacts/verification_result.py` | `schemas/artifacts/VerificationResult.schema.json` | `new_status`, `applied`, `evidence`, `next_verify_at` |

Reused single sources of truth (NOT duplicated): `FactAssertion.claim_type` references
`scripts.pipeline_runtime.artifact_types.CLAIM_SHAPED`; `CanonicalFact.status` /
`FragilityMetadata.volatility_class` / `scope` enums live once in the contract modules and the schemas mirror
them.

### Enums

- `scope` ∈ `{global_public, tenant_private, tenant_override, system_reference}`
- `CanonicalFact.status` ∈ `{candidate, verified_current, stale, contested, superseded, held_out, tenant_override, needs_human, deprecated}` (servable: `verified_current`, `tenant_override`)
- `FragilityMetadata.volatility_class` ∈ `{stable, low, medium, high, realtime}`
- `FactAssertion.claim_type` ∈ CLAIM_SHAPED `{atomic_fact, narrative_allegation, conclusion, emotion_signal}`

## Input

A fact's `claim_type`, `source_authority`, `claim_text`, and an **injected** `last_verified_at` (epoch
seconds). The classifier (`src/baltor/facts/classifier.py`) maps text cues (`current`, `deadline`, `rate`,
`fee`, …) + authority → `volatility_class` → `WatchPolicy` → `FragilityMetadata`.

## Output

- `FragilityMetadata` + recommended `WatchPolicy` (classifier).
- A durable `VerificationTask` for any stale fact (planner `plan_task`).
- A `VerificationResult` carrying a stored **evidence** artifact dict (planner `refresh`); a tenant-scoped
  refresh against a `global_public` fact is **refused** (`applied=False`, status `held_out`).
- Gate compatibility: a stale fragile fact handed to `scripts.runtime.verification_gate.VerificationGate` is
  `hold_out`; a fresh one (or a stale one with a queued task) is `allow`.

## Port

`FragileFactProviderPort` (declared in the matrix) — a live external-source provider would implement it. In
this minimum, the external check is **stubbed** in `FactRefreshPlanner._stub_external_evidence`: it stores a
deterministic evidence record (no network, no customer fetch).

## Proof

`scripts/check_watchtower_minimum_freshness.py` (`--self-test`, 31 checks). It asserts: Reg E "10 business
days" gets `last_verified_at` + `next_verify_at` + `watch_policy_id`; FAQ-30 is conflict-prone, medium-or-
higher volatility; demo source is `no_refresh` and never stale; a stale fact yields a durable VerificationTask
(stable id across reruns); the refresh stores **evidence** (not an answer); a tenant_private refresh cannot
update a global_public fact; determinism across reruns; each of the six schemas validates via
`scripts.runtime.schema_validator.validate_ref`; and gate-compatibility (stale → held_out, fresh/queued →
allow, no_refresh → never stale).

## Commands

```bash
PYTHONPATH=. python3 scripts/check_watchtower_minimum_freshness.py --self-test
```

(Run from the repo root. Exit 0 = PASS.)

## Limitations

- The external-source refresh is **stubbed** to a stored evidence record — no live fetch / `FragileFactProviderPort` adapter yet.
- The planner emits one task per stale fact and a one-shot result; there is no persistent task queue (reuse the
  existing runtime store/seam when this graduates beyond the minimum).
- Reconciliation of a refreshed value against a contested canonical fact is signaled (`needs_human` on
  `escalate_on_conflict`) but the reconciler stays the authority — the watchtower only drives freshness state.
- No CDC/event emission in this slice (no second bus); a fact's status transition is returned, not published.
