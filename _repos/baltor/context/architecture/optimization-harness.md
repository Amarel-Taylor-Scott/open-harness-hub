# Optimization Harness (C43) — governed improvement, a wrappable/chainable optimizer suite

Optimization runs **after** the Verification Gate (C40). It may make context smaller / cheaper / faster /
better-ranked — but it must **never silently change truth**, promote an allegation, leak tenant data, drop an
answer-critical fact, hide a conflict, or fabricate. So Optimization is a *governed* loop, not a vague stage:

```
verified pack → [candidate optimizer chain] → measure vs BASELINE → RegressionGate → promote ONLY on lift + zero regressions → receipt
```

## A suite of optimizers, one wrapper contract

`_repos/shared-backend-components/scripts/runtime/optimization.py`. Every optimizer is a swappable wrapper behind ONE stable contract so they
**compose into a chain**:

```python
class Optimizer(Protocol):
    name: str
    def optimize(self, pack: dict, *, signals: dict) -> dict: ...   # pure, deterministic, returns a NEW pack
```

Shipped suite (multiple variations of optimization):

| Optimizer | What it does |
|---|---|
| `DedupeOptimizer` | collapse artifacts that repeat the same fact (content hash / subject·predicate·object) |
| `ExcludeHeldOutOptimizer` | drop held-out / conflicted / stale artifacts from the promoted pack (kept as warnings) |
| `AuthorityRankOptimizer` | order by authority + freshness; optional top-k |
| `CompressionOptimizer` | compress verbose text via a `CompressionProvider` while preserving source handles + structure |

`chain(*optimizers)` returns a `CompositeOptimizer` (itself an `Optimizer`) — "easily wrapped, chained." The
compression seam is governed by the capability catalog (slot `compression`: `compression.stub@v1` wired,
**LLMLingua** the candidate primary) so the first real compression dependency can't land without a card.

## The harness: baseline → candidate → regression → promotion

`OptimizationHarness.run(baseline_pack, optimizer, *, answer_fact_ids, signals, now)` returns a decision +
`OptimizationReceipt` (content-addressed, injected time, schema `OptimizationReceipt`). It **promotes only
when** there is measured lift (fewer tokens or fewer artifacts) **and zero regressions**:

| Regression check | Fails when the candidate… |
|---|---|
| `answer_facts_preserved` | drops an answer-critical fact |
| `source_handles_preserved` | strips a source handle off a kept artifact |
| `no_held_out_or_allegation_promoted` | leaves a held-out conflict or a `narrative_allegation` in the pack |
| `no_tenant_leak` | injects another tenant's `tenant_private` artifact |
| `nothing_fabricated` | invents an artifact id not in the baseline |

A faster/smaller candidate that loses an answer fact is **rejected** — proven. A no-lift (identity)
optimization is **not promoted** — optimization must actually improve to win.

## Definition of done before any optimization "wins"

baseline captured · candidate isolated · same snapshot+corpus · source handles preserved · no new unresolved
conflicts · no allegation promoted · no tenant leak · no schema/contract/architecture drift · measured lift
improves · latency/cost acceptable · regression suite green · promotion receipt written.

Proof: `_repos/shared-backend-components/scripts/check_optimization_harness.py` (CFPB pack: dedupe a duplicate Reg E fact, exclude the held-out
FAQ-30 + a stale fact + an allegation, compress, keep the answer fact + its handle, promote with receipt; and
reject a candidate that drops the answer fact or leaves a held-out conflict). ADR:
`archive/legacy/docs/adr/0006-optimization-harness-governed-improvement.md`.

## Generalized: a multi-variant bake-off + consumption-readiness (C43.1)

Optimization is a **suite of variations**, not one optimizer:

- `BaselineSnapshot.of(pack)` freezes the comparison target (content-hash fingerprint + answer facts + handle coverage).
- `CandidateGenerator.generate(snapshot)` emits MANY candidate variants by varying knobs — `context_pack_dedupe`,
  `exclude_held_out`, `authority_topk_3`, `compression_budget_80/40`, `strict_conflict_exclusion` — each a concrete
  chained `Optimizer` + signals.
- `OptimizationHarness.optimize_many(baseline, candidates)` runs the **bake-off**: every variant against the same
  baseline, then promotes the best non-regressing one by measured lift. (A dedupe-only candidate that leaves the
  held-out FAQ-30 in is *rejected*; the compression+exclude variants win.)
- `ConsumptionReadinessGate.assess(pack, verification_receipt, optimization_receipt)` is the bridge to Consumption:
  a pack is consumable **only** if it was gate-verified (`allow`) AND harness-promoted AND carries both receipts AND
  leaks no held-out/conflict/allegation/cross-tenant artifact — emitting a `ConsumptionReadinessReport`. *No artifact
  is consumable merely because it exists.*

### External optimizer/eval/tracker tools (cataloged, wrapped, candidate-only)

Wrapped behind ports + cataloged in `external_capability_catalog.json` (stub wired, real tool = candidate primary):
`prompt_optimization` (**DSPy**), `hyperparameter_optimization` (**Optuna**), `eval_runner` (**promptfoo**),
`rag_evaluation` (**Ragas**, advisory only — deterministic grounding stays the authority), `experiment_tracking`
(**MLflow**, SQLite ledger first), and `compression` (**LLMLingua**). None imported yet; the first real dependency
can't land without its card.

Proof: `_repos/shared-backend-components/scripts/check_optimization_suite.py` (snapshot determinism · ≥6 variants · bake-off promotes some & rejects
others · best preserves the Reg E answer + handle & excludes held-out · end-to-end verify→optimize→consumable ·
consumption gate blocks unpromoted/unverified/leaky packs · external tools cataloged).

Next stage: **Consumption Runtime** — serve the optimized + verified + receipted pack to the agent with lineage +
freshness (only consumable packs; held-out surfaced separately as warnings).
