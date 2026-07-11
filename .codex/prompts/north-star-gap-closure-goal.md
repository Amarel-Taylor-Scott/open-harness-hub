# /goal: North Star Gap Closure Loop

Run the remaining Teleon/code-intelligence north-star gaps as a durable, proof-gated loop.

This goal pairs with `scripts/north_star_gap_closure_loop.py`. The command writes:

- `.agent/north-star-gap-closure/state.json`
- `.agent/north-star-gap-closure/summary.md`

## Mission

Close the honest north-star gaps without losing the green proof baseline:

1. Repo-wide unique AI-first naming.
2. Best-possible edit/blast-radius graph: data-flow, operation graph, UI/JSX seams, dynamic-ref handling.
3. Disagreement adjudication: multi-model candidates, deterministic evidence, owner decisions, promotion records.
4. Primitive derivation beyond wrappers: source-level mutation plans and verified variants.
5. Primitive registry builder: real-code records, vector/search export, no placeholders promoted.
6. Promotion gate for public/private primitive records.

## Loop

1. Refresh current evidence:

   ```bash
   python3 scripts/repo_code_inventory.py . --out .agent/repo-code-inventory
   python3 scripts/north_star_gap_closure_loop.py
   ```

2. Read `.agent/north-star-gap-closure/summary.md`.

3. Work only the `next_gap` unless there is a proof-blocking regression.

4. Implement one bounded improvement:
   - code or schema;
   - contract JSON;
   - checker/proof;
   - docs/handoff;
   - generated artifact refresh.

5. Run focused checks for the changed layer.

6. Run:

   ```bash
   PYTHONPATH=. python3 scripts/run_proofs.py
   ```

7. Re-run:

   ```bash
   python3 scripts/north_star_gap_closure_loop.py
   ```

8. Repeat until all tracked gaps are `ready_or_green`.

## Rules

- Do not run unsafe repo-wide rename sweeps. Migrate package-sized, proof-gated slices.
- Do not promote LLM output as truth.
- Do not allow placeholder/synthetic primitive records into trusted registries.
- Do not hide unresolved dynamic refs; mark them unresolved and route them.
- Preserve customer control paths: source export, package/private-service/API modes, BYOK, SBOM/provenance, rollback.
- Keep `_reference`, generated dist/site/artifacts, data partitions, caches, and assistant scratch outside owned-source migration unless explicitly targeted.

## Completion

The goal is complete only when:

- `north_star_gap_closure_loop.py` reports every tracked gap `ready_or_green`;
- primitive registry builder and promotion gate exist and pass;
- line/code inventory artifacts are refreshed;
- hybrid review packets are refreshed;
- `PYTHONPATH=. python3 scripts/run_proofs.py` is green.
