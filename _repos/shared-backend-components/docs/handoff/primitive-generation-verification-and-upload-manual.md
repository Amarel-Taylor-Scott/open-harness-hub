# Primitive Generation, Verification, and Upload Operating Manual

Paste this file into Claude Code (desktop or web), Codex, or any agentic dev tool to generate more primitives,
verify them with the full tool suite, make them **usable** (searchable by the product), and upload them to GitHub or
another tool. Last reconciled 2026-07-02. Companion to `docs/OPERATIONS-BIBLE.md` (state + operations),
`docs/handoff/claude-code-web-primitive-foundry-operating-manual.md` (foundry consumption), and
`docs/codex/claude-fable-compiled-primitive-routes-handoff.md` (mission + Factory State Snapshot).

**The one rule that was being missed:** generating and verifying a primitive is only *half* the job. A verified row
sitting in `data/dev-intel/primitive_factory/verified_candidates/<label>/` is invisible to the product until the
**registry bridge** loads it into the searchable card set. Every generation run ends with the bridge (§4). All rows
stay `candidate=true` / `serves_truth=false` until a promotion gate says otherwise.

---

## 0. The full pipeline (generation → usable)

```text
raw pre-primitive content (generated_primitive_packs/, catalog, docs, source surfaces)
  -> [A] format/interrogate into a PROMPT QUEUE of shard briefs
  -> [B] generate candidate rows (Fable ultracode lanes | Ollama GLM/Kimi | deterministic table->row)
  -> [C] one-shot VERIFY (deterministic schema/source/proof gate) -> verified_candidates/<label>/
  -> [D] BRIDGE into the searchable registry -> AIDevObserver + product can find them
  -> [E] report counts (multilane report + saturation) ; write negative memory for rejects
  -> [F] (optional) upload the new packs to GitHub / Codex / another tool
```

Where each stage lives:

| stage | command / file |
| --- | --- |
| A. prompt queue from raw content | §2 (`generated_primitive_packs/` → shard briefs) |
| B. generate | §3 (Fable waves) · Ollama `scripts/run_primitive_factory_batch_loop.py` · `scripts/build_primitive_pipeline_catalog_intake.py` |
| C. verify | `scripts/run_primitive_verification_loop.py --source-root <dir> --out-dir <label> --max-ticks 1` |
| D. bridge (make usable) | `scripts/load_verified_candidates_into_registry.py --write` (§4) |
| E. report | `scripts/report_multilane_primitive_generation.py --date-prefix <day> --write` + `scripts/track_primitive_saturation_and_savings.py` |
| F. upload | §7 |

---

## 1. The verifier row schema (what "a primitive" must be)

Machine-enforced by `scripts/verify_primitive_candidates.py`. A candidate row (JSONL, one object/line) needs:

```text
primitive_id, kind (primitive | primitive_group ONLY — family strings go in primitive_kind),
title, input_edge, output_edge (input_edge != output_edge),
contract (dict: summary, input, output, errors[, transformation_logic]),
blackbox (string), effects (>=1 {type,description}), source_refs (>=1 public https url),
mutators (>=1), proof_requirements (>=2, include candidate_boundary_gate),
promotion_blockers (>=1), dedupe_key (lowercase inputedge->outputedge::slug),
candidate=true, serves_truth=false
```

`kind=primitive_group` additionally needs `group_contract` with `visible_input`/`visible_output` exactly equal to
`input_edge`/`output_edge` and `hidden_member_edges` (>=3). Rich-lane quality (not gate-required but strongly
preferred): `edge_contract`, ≥300-char `input_edge_description`/`output_edge_description`, `reuse_profile`.

Output contract for model lanes (single source `scripts/_config.py:PRIMITIVE_CANDIDATE_OUTPUT_CONTRACT` +
`PRIMITIVE_CANDIDATE_PROMPT_EXAMPLE_ROW`): JSONL only, one COMPLETE object per line, no fences/prose, and **stop
after the last complete line if the budget runs low — a truncated object is a reject, fewer complete rows win.**

---

## 2. Turn raw pre-primitive content into a prompt queue

You have thousands of lines of structured raw content in `generated_primitive_packs/`:

```text
generated_primitive_packs/primitive_generated_pack_index.md   <- the index (13 dimension-driven MD table packs)
  *_pack.md files: Markdown tables with columns row_id | ... dimension cols ... | title | input_edge |
    output_edge | known_implementation_families | source_ref_families | effects | proof_requirements | candidate
  *.zip bundles: million_primitive_variation_pack, naics_2digit (300k), atlas_1m+ compact seed, 99pct dev bundle
```

These rows are ALREADY structured (input_edge/output_edge/effects/proof_requirements per row) — they are
**pre-primitive**: dimension-expanded skeletons that need contracts, source refs, and grouping to become full
candidates. Two ways to consume them, both valid (compare with metrics):

**Path 2a — deterministic table→row (zero model tokens, fastest).** Parse each MD table into the verifier row shape:
map `title`→title, `input_edge`/`output_edge` direct, `effects` (split `;`)→`[{type,description}]`,
`proof_requirements` (split `;`)→list (already includes `candidate_boundary_gate`), `source_ref_families`→
`source_refs` (resolve each family to its official https doc URL via a family→url table), synthesize a `contract`
from the dimension columns, mint `dedupe_key` from the edges, set `candidate=true`/`serves_truth=false`. Stage to
`data/dev-intel/primitive_factory/batch_runs/<day>-rawpack/<pack_id>/extracted/extracted_candidates.jsonl`.
Reuse the intake builder pattern in `scripts/build_primitive_pipeline_catalog_intake.py`.

**Path 2b — LLM interrogation → prompt queue → richer members (higher leverage).** Treat each pre-primitive row (or
each pack section) as a BRIEF. Emit a prompt-queue JSONL where each line is one shard brief:

```json
{"brief_id":"rawq:<pack_id>:<slice>","source_pack":"generated_primitive_packs/<file>.md",
 "base_edges":["<input_edge> -> <output_edge>", ...],"topics":["decompose hidden member steps",
 "add source-span + idempotency receipts","format mutators","policy gates"],"target_rows":30,
 "candidate":true,"serves_truth":false}
```

Then run the prompt queue through a generation lane (§3), one brief per lane agent. The queue is the durable
artifact — it lets Claude Code, Codex, Ollama, or a cron drain it incrementally without re-reading the raw packs.

**BUILT 2026-07-03 — both lanes exist and run end-to-end:**

- **Lane 2a — deterministic table→candidate** (`scripts/build_raw_pack_primitive_candidates.py --write`): parses
  the 12 MD table packs, synthesizes the required contract/blackbox/mutators, resolves every `source_ref_family`
  to a real public https doc URL, and stages verifier-shape rows under `batch_runs/<day>-rawpack/`. Measured
  2026-07-03: 7,474 rows → **1,339 distinct-edge primitives verified (0 rejected)**, bridged into the registry.
  The gap (7,474→1,339) is correct edge-first dedup: dimension variants (auth/pagination/error) collapse to the
  same visible edge, preserved as `contract.dimensions`. Zero model tokens.
- **Lane 2b — prompt-queue from million-row seeds** (`scripts/build_prompt_queue_from_seeds.py --write --zip
  generated_primitive_packs/<pack>.zip --max-rows N`): the ZIP bundles are ~1M COMPACT SEEDS (variation
  coordinates); you cannot make a model call per seed. This streams the .tsv members straight out of the .zip and
  CLUSTERS seeds by (domain, family) into one prompt brief per family — each brief summarizes the variation axes,
  samples representative base_edges, and instructs a generation lane to emit the family's MEMBER primitives
  (variations captured as `variation_profile`, not restated rows). Measured 2026-07-03: 200,000 seeds →
  **215 family briefs → 6,880 target primitives**; the row cap is recorded in the manifest (no silent truncation).
  Drain the queue JSONL incrementally through the Fable/Ollama lanes → verify → bridge.

---

## 3. Generate (portfolio — metrics decide the lane)

- **Fable ultracode waves (Claude Code Workflow tool):** one lane agent per brief, each writes ONE
  `extracted_candidates.jsonl` and self-checks. Best schema fidelity (uc02/uc03 verified at 0 rejects). Watch the
  session/usage limit — relaunch dead waves with `Workflow({resumeFromRunId})` so finished shards replay from cache
  free. Effort `medium` for throughput, `high` only for the hardest lanes.
- **Ollama GLM/Kimi (`scripts/run_primitive_factory_batch_loop.py`):** slow-tier recipe (measured 2026-07-02 GLM
  4.3 tok/s, Kimi 6.5): `--prompt-raw-candidate-target 2-3 --max-tokens 6500 --timeout 900 (GLM) / 700 (Kimi)
  --workers 1`. Key swap in `.env` applies per-call (no restarts). Breaker `OLLAMA_PAUSE.json` (session cap 1h /
  concurrency 3 min). Never Gemma 3 — Gemma 4 (`gemma-4-coding`) only, GPU-rate-limited (`GEMMA_RATE_LIMIT.json`).
- **Deterministic (`scripts/build_primitive_pipeline_catalog_intake.py`, table→row Path 2a):** zero model tokens,
  0 rejects when the source is already structured. Highest rows/token.
- **Retry, don't give up:** transient failures go to `scripts/run_primitive_failed_shard_retry_loop.py`
  (`--once` or `--interval-seconds 1800 --max-ticks N` — backoff + fallback routing). A "0 rows" Ollama day is a
  quota/tier event until a tokens/sec probe proves otherwise.

Every generated row lands under `data/dev-intel/primitive_factory/batch_runs/<label>/**/extracted/extracted_candidates.jsonl`.

---

## 4. Verify, then BRIDGE (the step that makes primitives usable)

```bash
# C. deterministic verify (schema + source + proof + dedupe gate) — one shot per label
PYTHONPATH=. python3 scripts/run_primitive_verification_loop.py \
  --source-root data/dev-intel/primitive_factory/batch_runs/<label> \
  --out-dir     data/dev-intel/primitive_factory/verified_candidates/<label> --max-ticks 1

# D. BRIDGE verified -> searchable registry (WITHOUT THIS, the product cannot see the rows)
PYTHONPATH=. python3 scripts/load_verified_candidates_into_registry.py --write
PYTHONPATH=. python3 scripts/check_verified_candidates_registry_load.py --self-test
```

The bridge (`scripts/load_verified_candidates_into_registry.py`) maps EVERY verified candidate across ALL labels
into the edge-foundry card schema (`data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl`),
registered in `src/teleon/observer/registry_search.py::_edge_foundry_paths()`. Proof it worked: the count read by
the product rises. Verify anytime:

```bash
PYTHONPATH=. python3 - <<'PY'
from src.teleon.observer.registry_search import load_edge_foundry_primitive_count, load_edge_foundry_primitives
print("registry cards now:", load_edge_foundry_primitive_count())
print("verified-factory visible:", sum(1 for r in load_edge_foundry_primitives()
      if str(r.get("primitive_id","")).startswith("prim:vf:")))
PY
```

The bridge is deterministic (ids from content hashes, `generated_at` copied from each row's `verified_at`, never
wall-clock), collapses cross-lane duplicates, leaks no local filesystem path, and defaults cards to
`surface_visibility=private_internal_only` (searchable in local/all scope — the real AIDevObserver dev path — never
overclaimed on a public demo). Re-run it after every verification and the whole verified corpus stays consumable.

---

## 5. Verification tool suite (deterministic · skill-based · contract · other)

Match rigor to the primitive's risk. The verifier gate (§4-C) is L3; deeper proof promotes toward truth.

**Deterministic (no model, run first — cheapest, strongest):**
- `scripts/verify_primitive_candidates.py` — schema + source + proof + dedupe gate (the L3 shape gate).
- `scripts/check_verified_candidates_registry_load.py` — bridge/consumability gate.
- `scripts/mine_implemented_code_primitives.py` + `scripts/check_implemented_primitive_compatibility.py` — AST
  source-mined primitives (L4_source_ast_snippet_compiled): module parses, snippet compiles, signature extracted.
- `scripts/compile_verified_candidates_to_codeblocks.py` — lower a verified row to a runnable codeblock + self-test.
- Format/roundtrip proofs (schema_validation, roundtrip_test, idempotency_test, row_count_preservation,
  side_effect_audit) — deterministic fixtures declared in `proof_requirements`; realize them as pytest fixtures.
- `scripts/run_proofs.py` — runs EVERY registered `--self-test` (register new checkers in
  `scripts/flywheel_proof_modules.py`; the module list alone is a no-op false green).

**Skill-based / behavioral (bounded model or executable skill, when determinism can't judge semantics):**
- Fixture-behavior tests: run the primitive on a golden input, assert the output (the "Code Factory" pattern —
  bounded model call wrapped in a compiled, tested harness; parity with hand-tuned prompts + auditability).
- `scripts/check_aidevobserver_session_benchmark.py` + `src/teleon/observer/review.py` — session/skill review over
  `fixtures/benchmarks/aidevobserver_session_review_v0/`.
- Paired-arm benchmark (planned pack): same task/fixtures/gates, different route arm (A0..A8), scorecard decides.
- Skill digestion / rubric checks for capability actions (persona/tool/processor/harness/rubric = an Action).

**Contract-based (the edge is the test):**
- `scripts/check_primitive_hybrid_search.py` — the matcher's fit-class contract (exact/deterministic-edit/
  nondeterministic-edit) — a primitive's `input_edge`/`output_edge` must resolve.
- `openapi_contract_test` / `request_response_fixture` / `auth_scope_review` (API-contract primitives) —
  validate against the declared OpenAPI/AsyncAPI/GraphQL/gRPC spec.
- Group `group_contract` integrity: hidden member edges must chain input→output (visible edges exactly match).
- `architecture/*.json` machine contracts + their `check_*` gates (portfolio dependency law, canonical-id single
  source, pyprefix conformance).

**Other / governance:**
- `license_policy_review`, `privacy/PII/PHI boundary`, `source_span_verification`, `freshness/effective_date`,
  `security/static-analysis`, `human_review` for high-risk domains (healthcare-admin/legal/finance/cloud-mutation).
- Negative memory: every reject writes a suppression record so the same failure is not regenerated (planned pack
  `catalog/knowledge-packs/data/negative-memory-seed/`).

**Adding a new verification tool:** write `scripts/check_<name>.py` with `--self-test` following the
build/check convention (see `docs/OPERATIONS-BIBLE.md` §10), register it in `scripts/flywheel_proof_modules.py`,
and reference the proof name in the primitives' `proof_requirements` so the gate demands it.

---

## 6. Generate with Claude Code / Codex / Ollama / Gemma 4 (agent recipe)

For a bounded, high-yield run in any agentic tool:

```text
1. Read this manual + docs/OPERATIONS-BIBLE.md §3-§6. Do NOT re-read the whole repo.
2. Pick ONE prompt-queue slice (§2) or ONE source surface (OpenAPI dir, MCP registry, PyPI, a raw pack section).
3. Generate ONE JSONL shard of candidate rows (§1 schema; §3 lane). One call = one shard; one row = one primitive.
   Prefer high-leverage primitive_groups (a visible edge hiding >=3 member edges).
4. Self-check the shard inline (every line json.loads; required fields; kind in {primitive, primitive_group};
   unique primitive_id + dedupe_key; candidate/serves_truth flags).
5. Verify (§4-C) and BRIDGE (§4-D). Report counts from manifests, never typed.
6. Write negative memory for rejects. Suggest the next slice. Do not promote to truth.
```

One-primitive prompt contract (for tools that generate a single record or codeblock at a time):

```text
You generate exactly one reusable primitive candidate as one JSON object (no markdown, no prose).
candidate=true, serves_truth=false. Include input_edge, output_edge (different), blackbox, effects,
runtime_targets, contract, proof_requirements (>=2 incl candidate_boundary_gate), promotion_blockers,
source_refs (public https). If code: one fenced block, no network/subprocess/secrets, include a self-test.
Stop cleanly — never emit a truncated object.
```

---

## 7. Upload the new packs to GitHub / Codex / another tool

Generated shards live under `data/dev-intel/` (git-tracked). To publish a batch:

```bash
# branch, stage only the new pack + the bridge artifacts, commit, push
git checkout -b feat/primitives-<day>
git add data/dev-intel/primitive_factory/verified_candidates/<label> \
        data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl \
        data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards_manifest.json
git commit -m "feat(primitives): <label> verified candidates + registry bridge refresh"
git push -u origin feat/primitives-<day>
gh pr create --fill   # or: gh pr create --title ... --body ...
```

Rules: commit ONLY the pack + bridge files (not unrelated working-tree churn from live loops — `git add` explicit
paths, never `git add -A`); branch off `main`, never commit to `main`; large ZIP bundles in
`generated_primitive_packs/` are inputs — keep them out of PRs (they're already large binaries). For Codex or
another tool, hand it this manual + the prompt-queue JSONL + the verifier/bridge commands; the queue is the
portable unit of work. Do not upload real PII/secrets; the bridge already strips local paths from cards.

---

## 8. Definition of done for a generation run

```text
[ ] shard(s) staged under batch_runs/<label>/**/extracted/extracted_candidates.jsonl
[ ] verified: verified_candidates/<label>/manifest.json shows verified > 0 (rejects have reasons)
[ ] bridged: load_verified_candidates_into_registry.py --write ran; check_..._registry_load.py --self-test PASS
[ ] registry count rose (load_edge_foundry_primitive_count() higher than before)
[ ] reported: multilane report + saturation report written for the day
[ ] negative memory written for rejects
[ ] every row candidate=true / serves_truth=false ; no typed counts in any doc
[ ] (optional) new packs pushed to a feature branch + PR
```
