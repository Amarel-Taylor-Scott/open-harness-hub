# /goal: Build Open Harness Hub — capability-lift components, for hours

You are an autonomous agent (Codex or Claude Code) working in Open Harness Hub.
Run for **hours or days**. **There is no terminal state and no early stop** —
the resilience contract is [`.codex/prompts/direction.md`](direction.md). Never
wait for permission between steps; on any block, error, or completed phase,
switch paths or advance to the next one and keep producing durable, validated
repo changes (not suggestions). The only things that end a run are an explicit
human interrupt or a hard safety violation you must not work around.

## Mission

Build a portable, database-backed registry **and** an easy conversational
builder of reusable AI-pipeline components, reachable by hybrid search. The
headline interaction: a user pastes a task / use-case / LLM challenge and gets
back a working, costed, deployable flow composed from existing components.

**The single canonical goal is [`docs/codex/master-goal.md`](../../docs/codex/master-goal.md).**
Read it first; it reconciles and supersedes the older goal docs and defines the
phases (P0 reconcile → P1 foundation → P2 component MVPs → P3 paste-to-flow
builder → P4 full MVP → P5 scale), the six supervisor gates, and the loop.

## The admission bar (read before generating anything)

A component earns a place **only if it lifts capability beyond a bare LLM** —
lets a model do what it cannot do reliably alone (grounded facts, deterministic
checks, retrieval, domain rules, multi-step verification). Operational test: a
benchmark delta `pipeline_score − bare_model_score` meaningfully **> 0**. If a
frontier model already does it zero-shot, **it does not belong** — do not
generate it, do not catalog it (this includes templated clones and general dev
resources). The highest lift is in esoteric, specialized, verifiable arenas.
Report **useful-promoted/day, not generated/day**. See the non-goals in
`docs/about/project.md`.

## Read first

1. [`docs/codex/master-goal.md`](../../docs/codex/master-goal.md) — canonical goal, phases, gates, loop
2. `AGENTS.md` and `CLAUDE.md` — conventions + hard rules
3. `.research-notes/autonomous-session-ledger.md` — current state; resume here
4. `docs/codex/no-magic-values.md` — single-source-of-truth discipline
5. `taxonomy/SPEC.md` — vocabulary + field definitions
6. `docs/codex/autonomous-session-runbook.md` — the in-session loop engine

## The loop (repeat ~20–45 min/cycle; never stop on a block)

```
ORIENT   read the session ledger; pick the highest-value UNBLOCKED menu item
PLAN     state the one batch this cycle produces (one path)
BUILD    durable change — full row families; real embeddings for promotable rows
VALIDATE fast path on CHANGED paths only (gates 1–2 inline)
RECORD   append a ledger line: counts (generated/staged/committed/vectorized) +
         yield (useful-promoted) + validation result
BRANCH   blocked? switch to another menu path; note roadblock + fallback; do NOT stop
REPEAT
```

## The six supervisor gates (a batch failing any gate is not counted)

1. **Green build** — `python3 scripts/validate.py <changed paths>` exits 0.
2. **Stats fresh** — `python3 scripts/build_readme_stats.py --check` passes.
3. **Novelty/dedupe** — `python3 scripts/factory/capability_lift_gate.py` (SimHash/LSH); reject near-duplicates.
4. **Capability-lift** — same gate: lift floor + filler markers; only count rows that clear the bar.
5. **Provenance** — every promotable row carries `source_url` + `license` + `author`; uncertain → review ticket.
6. **Vectorization** — no promotion without a REAL embedding (see "Embeddings", below); hash vectors are staging-only.

## Work-path menu (priority-ordered; always pick the highest UNBLOCKED item)

Warm start — current state (2026-05-27): validator green; catalog 2,397 YAML
(530 curated + 1,867 candidates); vector store builds over all of them with the
offline **hash placeholder** backend (0 promotable embeddings); the flexible
embedding provider (`scripts/embeddings.py`) and the local showcase server
(`scripts/serve_builder.py`) exist.

- **P1 — make embeddings real (highest value).** The route is wired and
  one switch away. Set a backend and re-embed:
  ```bash
  # local model (needs sentence-transformers):
  OH_EMBED_BACKEND=local-st OH_EMBED_MODEL=all-MiniLM-L6-v2 python3 -m scripts.db.build_vector_store build
  # OR hosted / cloud (OpenAI-compatible, incl. Ollama/vLLM):
  OH_EMBED_BACKEND=http-openai OH_EMBED_BASE_URL=… OH_EMBED_API_KEY=… OH_EMBED_MODEL=text-embedding-3-small python3 -m scripts.db.build_vector_store build
  ```
  Then run `scripts/db/vector_readiness_audit.py` and confirm promotion is
  unblocked only for real vectors. NEVER fake vectors to pass the gate.
- **P2 — capability-lift component MVPs (wedge first).** Build families in the
  regulated/esoteric wedge (ESG/CSDDD, GxP, customs, sanctions, food/water),
  each shipped with a rubric + a benchmark proving a positive bare-vs-pipeline
  delta. Token-efficiency / strict-output families compound across domains.
- **P3 — the paste-to-flow builder.** Improve `scripts/serve_builder.py`
  (hybrid retrieval → assembly honoring wiring rules → cost estimate → optional
  local-model polish). Maintain a builder benchmark (`pasted task → expected
  component flow`) from the Kaggle corpus.
- **Hygiene/throughput fallbacks (always unblocked):** tune the cull
  (`capability_lift_gate.py`), add SimHash/LSH to the factory dedup so a batch
  > ~1–2k stops hanging, finish the `manifest/primitive/artifact → component`
  rename (prose + the `artifacts` table in `dist/catalog.sqlite`), generate
  showcase pipelines/rubrics/benchmarks, add source-surface seeds.

## Operating rules

- Make durable, validated repo changes; small coherent batches; end each cycle green or roll back.
- Route ALL model + embedding work through the provider-neutral resolvers
  (`scripts/embeddings.py`, `scripts/model_routes.py`) so jobs run local now and
  hosted/cloud later by env var only — never hardcode a provider or key.
- No magic values — counts/dims/model-IDs/paths/thresholds/versions have one
  source (`docs/codex/no-magic-values.md`); repo-state counts are computed.
- Preserve provenance, license, trust + privacy boundaries, freshness.
- No real PII/secrets/proprietary dumps — synthetic/public metadata only.
- Do not republish `_reference/`. No new insurance work.
- Promotion boundary: no tenant-visible row with open/high-risk review,
  placeholder embeddings, unresolved provenance, or volatile facts without CDC.
- High-volume rows live in JSONL staging + Postgres/pgvector load plans, not new static files.

## Validation

```bash
# daily fast path (changed paths only):
python3 scripts/validate.py <changed catalog paths>
python3 scripts/build_component_id_index.py --update <changed paths>
python3 scripts/build_catalog_pages.py --paths <changed paths> --update-index
python3 scripts/factory/capability_lift_gate.py            # cull/usefulness report
# release gate (schema/vocab/broad changes only):
python3 scripts/validate.py && python3 scripts/build_readme_stats.py --check
```

## Embeddings & models (local now, cloud later)

- Embeddings: `scripts/embeddings.py` — `OH_EMBED_BACKEND` = auto | local-st |
  http-openai | hash; `OH_EMBED_MODEL` / `OH_EMBED_BASE_URL` / `OH_EMBED_API_KEY`.
  Hash is offline placeholder (non-promotable). Model→dim lives in
  `scripts/_config.py` (no scattered literals).
- LLM/chat (builder polish, labeling): `scripts/model_routes.py` — `OH_LLM_*`;
  defaults to a local Gemma via Ollama, degrades to deterministic output if no
  model is reachable. Optional, never the source of truth.

## Per-cycle report — then immediately continue (never stop)

This is a ledger entry, **not** an ending. After writing it, begin the next
cycle without pausing or asking. Each entry states: what changed; which files
matter; which path (fast vs release gate) was used; the component count;
generated/staged/committed/**vectorized** counts and the **useful-promoted**
yield; validation + gate results; and the next move — which you then start
immediately. "Done" only ever means "pick the next highest-value unblocked item."
