# ContextOps — The CFPB Reference Example (end-to-end thesis proof)

> FAQ "30 days" vs Regulation E "10 business days": the canonical case where a base model would confidently
> repeat the wrong restatement. The foundry composes the REAL modules to land on the source-of-law value —
> WITHOUT any agent or LLM ever serving the fact.

## Purpose

Be the single deepest proof that the whole invariant holds on a realistic conflict: detection → bounded
discovery → ranked recipe → deterministic extraction → reliability → cross-source → reconciliation → cost.

## Owner

Baltor ContextOps. The reconciliation decision is owned by the EXISTING authority,
`_repos/shared-backend-components/scripts/artifact_graph/reconciliation.py`; this example REPRODUCES it (assert-equivalence), never replaces it.

## Inputs

- `fact_key = reg_e.error_resolution.deadline`, tenant `acme`, scope `global_public`.
- Two offline fixtures: an eCFR regulation snippet ("...within 10 business days...") and a CFPB FAQ snippet
  ("...the bank generally has 30 days..."), with handles `ctx://public/source/ecfr/12-CFR-1005.11#...` and
  `ctx://public/source/cfpb-faq/error-resolution#q12`.
- A fixture-backed `ResearchTask` (offline, no secrets).

## The composition (each stage uses the real module)

1. **TRIAGE** — the FAQ-"30 days" claim fires `needs_reconciliation` + `is_low_authority` +
   `is_conflict_candidate`; `serves_truth` False.
2. **RESEARCH** — `research.local_stub@v1` returns a `SourceDiscoveryReport` (`serves_truth=False`) that
   DISCOVERS the official regulation candidate; every candidate carries a `source_handle`.
3. **DISCOVERY/RANK** — `SourceDiscoveryDriver` ranks the eCFR regulation ABOVE the FAQ and PROPOSES a
   `SourceRecipe` for the regulation (M1→M2).
4. **RECIPES** — an M3 `VerificationRecipe` is built (a FAQ `winning_source_type` is REJECTED at build time).
5. **EXTRACT** — the deterministic `duration_parser` extracts `10 business_days` (regulation) and `30 days`
   (FAQ) as CANDIDATE `FactAssertionCandidate`s (`claim_status=candidate`, `promotion_eligible=False`), each
   tied to its source handle. A deterministic RE-verify reproduces the candidate with NO fresh agent run.
6. **RELIABILITY** — the regulation source OUTRANKS the FAQ source (`outranks(reg, faq)` is True).
7. **CROSS_SRC** — the recipe's policy (`current_value_requires_fresh_source`) is satisfied by a fresh official
   read.
8. **RECONCILE** — the EXISTING deterministic authority makes Reg-E "10 business days" the WINNER and HOLDS OUT
   the FAQ "30 days"; the decision is `resolved_by_authority`, resolver `deterministic`. Re-running is
   byte-identical.

## Outputs

A reconciliation receipt naming the authority precedence, the won value `10 business_days` traced to the
deterministic extractor candidate, and the assertion that no agent/LLM ever served the fact.

## Proofs

`_repos/shared-backend-components/scripts/check_contextops_cfpb_reference.py` — asserts every stage above plus the invariant: NO agent/LLM served
the fact (every agent output `serves_truth=False`), the extractor output is `claim_status=candidate` with a
source handle, a deterministic re-verify reproduces it without a fresh agent run, and the reconciliation
outcome is byte-equivalent to the existing artifact-graph reconciliation authority.

## Commands

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_contextops_cfpb_reference.py --self-test
# the existing reconciliation reference this example reproduces:
python3 _repos/shared-backend-components/scripts/check_cfpb_reconciliation.py --self-test
```

## Limitations

- Fixtures stand in for the live eCFR / CFPB sources (lean core is offline). Live fetch is deferred to
  `OPP-contextops-runtime`.
- The reliability factor profiles are deterministic defaults, not a learned model.

## Next

- Replace fixtures with a recipe-driven offline-cached fetch once the runtime worker lands.
- Add a second conflicting fact_key (e.g. a fee/rate) to exercise the `current_value` freshness path live.
