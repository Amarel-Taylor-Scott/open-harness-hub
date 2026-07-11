# /goal: Repo Line-By-Line Review Sweep

Run a durable, resumable review of the entire owned repository surface, file by file and line by line.

This goal pairs with `scripts/repo_line_review_loop.py`. The command produces deterministic artifacts:

- `.agent/repo-line-review/state.json`
- `.agent/repo-line-review/findings.jsonl`
- `.agent/repo-line-review/summary.md`
- optionally `.agent/repo-line-review/reviewed-lines.jsonl`

## Mission

Iteratively sweep the repo until every owned file has been reviewed and every high-signal finding has been
triaged or fixed. Do not attempt to fit the whole repo into one context. Use checkpointed batches.

## Scope

Review owned source and repo-authored text only. Exclude virtualenvs, `_reference`, archives, generated
dist/site/artifacts, data partitions, caches, and assistant scratch.

The loop reviews:

- Python, JS/JSX/TS/TSX, shell, SQL, CSS, HTML
- JSON/YAML/TOML/config
- Markdown/RST/docs
- catalog/schema/taxonomy files

## Loop

1. Run one bounded batch:

   ```bash
   python3 scripts/repo_line_review_loop.py --max-files 50 --max-lines 12000
   ```

2. Read `.agent/repo-line-review/summary.md` and the newest rows in
   `.agent/repo-line-review/findings.jsonl`.

3. Fix the highest-impact findings first:
   - merge conflict markers
   - secret-like literals
   - syntax errors
   - broken external entrypoints
   - pyprefix drift in already migrated paths
   - dynamic refs that block deterministic migration
   - stale docs / magic values / external contract mismatches

4. Validate the touched area and keep the tree green.

5. Run the next batch. Continue until `done: true`.

## Rules

- Never republish or migrate `_reference`.
- Never mutate virtualenv/dependency code.
- Never leave the proof gate red.
- Record deliberate external entrypoints as compatibility shims.
- Prefer deterministic checks and graph evidence over prose assertions.
- If a finding is not fixable immediately, document why and continue to the next batch.

## Completion

The goal is complete only when:

- `repo_line_review_loop.py` reports `done: true`;
- high/critical findings are fixed or explicitly routed;
- relevant focused checks pass;
- `PYTHONPATH=. python3 scripts/run_proofs.py` is green.
