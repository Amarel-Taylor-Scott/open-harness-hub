# Repo Line Review Loop Command

Run one bounded deterministic review batch:

```bash
python3 scripts/repo_line_review_loop.py --max-files 50 --max-lines 12000
```

Run continuously until the owned-source sweep completes:

```bash
python3 scripts/repo_line_review_loop.py --loop --max-files 50 --max-lines 12000 --sleep 2
```

Record a hash row for every reviewed line:

```bash
python3 scripts/repo_line_review_loop.py --emit-line-records --max-files 25 --max-lines 8000
```

Artifacts are written under `.agent/repo-line-review/`:

- `state.json` — cursor, manifest hash, completed files, reviewed lines, finding count
- `findings.jsonl` — deterministic finding rows
- `reviewed-lines.jsonl` — optional per-line hash ledger
- `summary.md` — current human/agent handoff

Pair this command with `.codex/prompts/repo-line-review-goal.md` for a long-running Codex/Claude goal.

The command excludes virtualenvs, `_reference`, archives, generated dist/site/artifacts, data partitions,
caches, and assistant scratch by default. It is designed to sweep the repo in small green batches, not to
dump the whole repository into a single context window.
