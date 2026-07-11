# North Star Gap Closure Loop Command

Run a deterministic status pass over the remaining north-star gaps:

```bash
python3 scripts/north_star_gap_closure_loop.py
```

Refresh inventory first when files changed:

```bash
python3 scripts/repo_code_inventory.py . --out .agent/repo-code-inventory
python3 scripts/north_star_gap_closure_loop.py
```

Artifacts:

- `.agent/north-star-gap-closure/state.json`
- `.agent/north-star-gap-closure/summary.md`

Pair this command with `.codex/prompts/north-star-gap-closure-goal.md` for a long-running Codex goal.

## What The Loop Tracks

- `repo_wide_unique_naming`
- `blast_radius_graph`
- `disagreement_management`
- `primitive_derivation`
- `registry_vectorization_search`
- `promotion_gate`

The command is intentionally conservative. It is not a proof of completion; it is a repeatable routing
artifact that tells the next agent which gap to close next and what evidence currently supports that
classification.

## Standard Cycle

```bash
python3 scripts/repo_code_inventory.py . --out .agent/repo-code-inventory
python3 scripts/north_star_gap_closure_loop.py
sed -n '1,220p' .agent/north-star-gap-closure/summary.md
# implement one bounded next action
PYTHONPATH=. python3 scripts/run_proofs.py
python3 scripts/north_star_gap_closure_loop.py
```

## Stop Conditions

Stop and report if:

- the full proof gate goes red and cannot be fixed in the same cycle;
- a proposed primitive source has unclear license/provenance;
- a registry-generation path would create placeholder/synthetic trusted records;
- a migration requires unsafe broad rename/revert behavior;
- a customer-control/compliance path is being hidden instead of modeled.
