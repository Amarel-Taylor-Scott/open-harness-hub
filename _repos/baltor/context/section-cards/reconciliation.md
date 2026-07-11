# Reconciliation — section card

Section: `reconciliation` (category: reconciliation) · critical-path.

## Purpose

A detected conflict is not the end — reconciliation DECIDES which side wins, by deterministic precedence, and
writes a receipt so the decision is auditable. Precedence (highest first): exact regulation / source-of-law >
FAQ / summary; newer `source_version` > older at equal authority; structured-field fact > narrative
allegation; human-signed > LLM suggestion. If nothing wins, the fact is HELD OUT of the promoted context pack
rather than guessed. This is why the reference answer is "10 business days" (Reg E, authority 3) and FAQ-30
appears only as a held-out warning.

## Owner module

`_repos/shared-backend-components/scripts/artifact_graph/reconciliation.py` — `Reconciler.reconcile(...)`. Every `reconciliation_id` is a
deterministic hash; each reconciliation emits a receipt (decision, winner, losers, rule).

## Contracts

Input: `conflict`. Output: `reconciliation`. Registered runtime owner `Reconciler`
(`_repos/shared-backend-components/architecture/runtime_ownership.json#Reconciler`).

## Proof scripts

`_repos/shared-backend-components/scripts/check_cfpb_reconciliation.py` (registered in the flywheel) — asserts the Reg E winner, the FAQ-30
hold-out, and a stable reconciliation receipt across reruns.

## Commands

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_cfpb_reconciliation.py --self-test
```

## Limitations

Precedence is a fixed, rule-based ranking; conflicts not separable by these rules are held out (refused), not
auto-resolved — safe but conservative. "Human-signed > LLM suggestion" depends on those provenance fields
being present upstream.

## Opportunities

Extend the precedence ladder for new source classes; surface held-out reasons in the consume UI; tie unresolved
holds to review tickets.
