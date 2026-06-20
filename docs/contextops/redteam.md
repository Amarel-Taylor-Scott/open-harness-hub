# ContextOps — Red-Team (every attack on the invariant fails safely)

> The invariant is sacred: **agents DISCOVER and PROPOSE; Baltor STORES, VERIFIES, RECONCILES, PROVES,
> CONSUMES.** This red-team drives each attack to the REAL guard in a ContextOps module and asserts it
> REFUSES — none can be talked around.

## Purpose

Prove the invariant is structural, not aspirational: there is a concrete, tested guard for every way an agent
or a generated worker could try to serve/promote a fact, drop provenance, invert authority, leak tenant data,
reach the network, or register unproven code.

## Owner

Baltor ContextOps. Each guard lives in the module it protects (triage / extractor / reliability /
cross-source / sandbox gate / research stub / verification recipe).

## Inputs

Purpose-built malicious inputs driven to each guard's failure path. No literal secret value appears in the
proof source — any `api_key` / `sk-` string a negative test needs is BUILT at runtime from fragments.

## Outputs

A BLOCKED/BREACH line per attack; the proof exits non-zero on any breach.

## The nine attacks and the guard that stops each

| # | Attack | Guard (real module) |
|---|---|---|
| 1 | research agent publishes a fact directly | report `serves_truth` pinned False; a candidate agent raises `ResearchAgentUnavailable` (never runs) |
| 2 | generated worker lacks proof | `sandbox_gate.gate_snippet` → `can_register=False` / `rejected` on a failing unit test |
| 3 | source candidate lacks a source handle | `FactAssertionCandidate` raises `MissingSourceHandleError` |
| 4 | FAQ outranks regulation | `reliability.outranks(faq, reg)` is False; `build_verification_recipe` REJECTS a FAQ winner (`ValueError`) |
| 5 | tenant_private source updates global_public | `score_source` `tenant_scope_ok` False; `tenant_private_requires_human_signoff` |
| 6 | recipe uses an unapproved network | sandbox statically BLOCKS network (`SandboxViolation`); the research stub REFUSES a secrets-bearing task |
| 7 | extractor drops source handle | `MissingSourceHandleError` at extract time |
| 8 | LLM output served as truth | minting non-candidate → `CanonicalClaimError`; `llm_claim_requires_source_artifact` refuses an unbacked LLM claim |
| 9 | unverified generated code registered active | proof gate `can_register` False until a unit-test proof passes; high-risk needs human approval |

## Proofs

`scripts/check_contextops_redteam.py` — asserts all nine attacks fail safely against the real guards.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_contextops_redteam.py --self-test
```

## Limitations

- The sandbox's primary defense is a static scan plus an in-process safe-namespace run in a temp dir; it is
  NOT a kernel sandbox. The lean core never executes a generated production worker — that is deferred.
- The red-team covers the spec's nine documented attacks; it is a regression gate, not an exhaustive
  adversarial search.

## Next

- Add fuzzed/mutated variants of each attack as the runtime grows (OPP-contextops-runtime).
- Extend coverage to the worker-execution and watch-scheduler guards once those land.
