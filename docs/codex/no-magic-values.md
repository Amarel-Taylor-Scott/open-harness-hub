# No Magic Values — Single Source of Truth

> Context and rules for every agent and contributor (Codex, Claude Code,
> Cursor, human PRs) working in OpenHubForAI. The goal: **no number,
> string, count, path, model ID, dimension, threshold, or version that has
> to be remembered and updated by hand in more than one place.**

At billion-component scale (`docs/codex/billion-component-goal.md`) a value
that is hand-typed in two places is a value that *will* drift. Drift here is
not cosmetic — it makes the registry lie about its own state, breaks dedupe
and load plans, and erodes trust in provenance. This page exists because we
already shipped real instances of the bug.

## Real drift already in the tree (use as the canonical examples)

1. **Hand-typed catalog count.** `README.md` says
   `**172 components** ... v0.3.0`. The catalog actually validates **509
   tracked** definitions (and thousands more machine-generated under
   `scale*/`). The number was typed once and never recomputed — it is now
   ~25× wrong. A count that already exists programmatically
   (`scripts/oh_hub.py stats`, `scripts/build_catalog_index.py`) must never
   be transcribed into prose by hand.
2. **A constant and a parallel literal of the same value.**
   `scripts/db/pgvector_embedding_load_plan.py` defines
   `DEFAULT_SCHEMA_DIMENSIONS = 384` (line 13) **and** hardcodes the string
   `"... the canonical vector(384) schema ..."` in a safety note (line 218).
   Change the constant and the message silently lies.
3. **One dimension copied across many files.** The embedding dimension `384`
   is independently re-typed in at least seven modules under `scripts/db/`
   (`daily_embedding_execution_batch_plan.py`, `embedding_execution_plan.py`,
   `theory_batch_governance_bridge.py`, `pgvector_embedding_load_plan.py`,
   `local_hash_embedding_worker.py`, `build_vector_index.py`, …). There is no
   single definition to change.
4. **Scattered model IDs.** Strings like `"all-MiniLM-L6-v2"`,
   `"gemma2:2b"`, `"text-embedding-3-small"`, `"claude-sonnet-4-6"` appear as
   bare literals in individual scripts with no shared registry, so a model
   swap means a manual grep-and-replace across the fleet.

## The rules

### 1. Derive, never transcribe (repo-state numbers)
Any value that *describes the repository* — component counts, totals per
type, "N emitters", "N verticals", schema/spec version, last-build date —
must be **computed from the source of truth at render or build time**, not
typed into committed prose.

- If a count must appear in committed text, a script writes that text and the
  block is marked auto-generated (e.g. fenced by
  `<!-- BEGIN GENERATED:catalog-stats -->` / `<!-- END GENERATED -->`), and a
  CI/validate step recomputes and diffs it so stale copy **breaks the build**.
- Otherwise, link to the live source (`python scripts/oh_hub.py stats`)
  instead of pasting a frozen number.

### 2. One definition, many readers
A value used in more than one place gets **exactly one definition** that
everything else imports. This applies to:

- embedding dimension(s) and the canonical `vector(D)` SQL type;
- model IDs / route names (embedding, rerank, judge, generation);
- schema version, spec version, catalog version;
- canonical repo paths (`catalog/`, `dist/`, `schemas/`, `vocabularies/`);
- row-family names, component-type names, dedupe/promotion thresholds;
- daily/scale targets and batch sizes.

Put shared Python constants in a single config module (e.g.
`scripts/_config.py`); put shared *data* (types, industries, capabilities,
row families) in `vocabularies/` or `schemas/` and **read it** rather than
re-listing it in code.

### 3. No parallel literals of a constant
If a string or message embeds a value that a constant already owns, build the
string from the constant — `f"vector({DEFAULT_SCHEMA_DIMENSIONS})"` — never a
hand-copied `"vector(384)"`. The same rule covers log lines, error messages,
SQL fragments, doc strings, and emitted JSON.

### 4. Name your magic numbers and strings
A bare literal that carries meaning in logic must be a **named
module-level constant with a comment stating unit, rationale, and source**:

```python
# Jaccard shingle overlap above which two normalized bodies are treated as
# the same cluster. Tuned on the 2026-05 dedupe eval; see docs/...
JACCARD_DUPLICATE_THRESHOLD = 0.60
```

Bare literals are only acceptable for trivial identities (`0`, `1`, `""`,
`[]`) and genuinely local one-shot values that appear exactly once and mean
nothing elsewhere.

### 5. Canonical lists live in data, not code
The set of component types, industries, capabilities, modalities, trust
boundaries, row families, and emitters is **data**. Read it from
`vocabularies/*.yaml`, `schemas/`, or a generated index. Do not hardcode the
enumeration in multiple scripts — that is rule 2 applied to lists, and it is
how "14 component types" goes stale.

### 6. Paths and slugs through one helper
Repo-relative paths resolve through a single path/config helper anchored at
the repo root (not `os.getcwd()` and not string concatenation sprinkled
across modules). Slug and component-ID construction (`{type}/{slug}`,
hash suffixes) goes through the existing shared builders so format changes
happen once.

### 7. Dates and versions are computed or sourced
Never hand-type "today" or a version into generated output. Derive run dates
from run metadata, versions from git/commit/tag, and content identity from
canonical hashes (per the ID & hash discipline in `CLAUDE.md`). Formatting
changes must not mint false versions; source changes must stay detectable.

### 8. Fail loud on required mirrors
When a value genuinely must appear in two artifacts (a doc badge, a README
table, an emitted card), add a check that recomputes both sides and diffs
them in `scripts/validate.py` or CI. Drift should turn red, not rot quietly.

## Author checklist (before commit)

- [ ] No count, total, or version describing the repo is hand-typed in prose.
- [ ] Every value I used in >1 place has a single definition I imported.
- [ ] No string hardcodes a value that a constant already owns.
- [ ] Every meaningful literal in logic is a named constant with a comment.
- [ ] Type/industry/row-family lists are read from `vocabularies/`/`schemas/`,
      not re-enumerated.
- [ ] Paths resolve from the repo-root helper; no `cwd`-relative surprises.
- [ ] Any mandatory mirror has a validate/CI check that fails on drift.

## How to remediate the existing instances

1. Add `scripts/_config.py` (or extend the existing shared lib) with
   `DEFAULT_EMBEDDING_DIMENSIONS`, an embedding/judge/rerank **model
   registry**, canonical paths, and schema/spec versions.
2. Replace the seven-plus `384` literals and the scattered model-ID strings
   with imports; build every `vector(...)` message via f-string from the
   constant.
3. Replace the README "172 components / v0.3.0" block with a generated,
   diff-checked stats block (driven by `oh_hub stats` /
   `build_catalog_index.py`), or with a pointer to the live command.
4. Add a `validate.py` assertion that the README/docs stats block matches a
   fresh recomputation.

These are tracked as recommended follow-ups from the 2026-05-26 repo review;
do them opportunistically when touching the affected files.
