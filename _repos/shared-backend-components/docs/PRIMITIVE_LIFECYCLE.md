# Primitive Lifecycle, Provenance & Truth-Serving Policy

> A primitive does **not** serve truth because tests pass. It needs schema, verifier, security, benchmark,
> deterministic-replay, and provenance **evidence** — each a receipt. Engine:
> `scripts/primitive_lifecycle.py`. This is the governance plane of the deterministic primitive supply chain.

## The five stages

```
candidate --[schema + verifier + self-test]--------------> validated
validated --[security pass + benchmark + det. replay]-----> certified
certified --[provenance + run_proof + reviewer/policy]----> production   (serves_truth eligible)
production --[superseded / drift / security / regression]-> deprecated
any        --[malicious / failed security / unverifiable]-> quarantined
```

Every generated primitive is born **candidate** (`serves_truth=false`). `promote(card, to_stage, receipts)`
refuses any transition whose required receipts are absent, and a **security-gate `quarantine` verdict forces
`quarantined`** regardless of the requested target (fail-safe).

| Transition | Required receipts |
|---|---|
| candidate → validated | `schema_valid=true`, `self_test_pass=true`, card has `verifier_id` |
| validated → certified | `security_status=="pass"`, `deterministic_replay=true`, `benchmark_result` present |
| certified → production | `provenance` + `run_proof` present, plus `reviewer` or `policy_approval` |
| → deprecated | `deprecation_reason` |
| → quarantined | `quarantine_reason` (or an automatic security quarantine) |

## Truth-serving policy (`validate_truth_serving`)

`serves_truth=true` is allowed **only** when ALL hold: `lifecycle_stage=="production"`; `determinism_level`
in {D0_pure, D1_seeded, D2_bounded_external} (D3_hybrid / D4_stochastic may **not** serve truth); a
`security_status=="pass"` receipt; a `benchmark_result` receipt; a `verifier_id`; a `provenance`; not
quarantined; not deprecated. `audit_pool()` asserts no live card claims `serves_truth=true` without passing
this policy — today the pool is **clean** (all 141 cards are `candidate`, 0 violations).

## Provenance (SLSA-shaped, `build_provenance`)

Deterministic record: `primitive_id`, `artifact_hash` (content-addressed via `canonical_id`), `source_pack`,
`source_files`, `verifier_id`, and the build/verifier/security/benchmark commands, plus `commit_sha`. This is
"what built the artifact + how it is verified", the SLSA integrity model applied to primitives.

## Run it

```bash
python3 scripts/primitive_lifecycle.py --self-test    # the state machine's own proof
python3 scripts/primitive_lifecycle.py --audit-pool   # assert nothing is casually serving truth
```

Consolidates `promote_primitive` / `generate_primitive_provenance` / `validate_truth_serving_policy` into one
cohesive, self-tested module (repo convention: one module → one `--self-test` → `run_proofs`).
