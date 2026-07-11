# Standards linter (`check_new_code_uses_standards`)

## Purpose

The standards linter is the forcing function that keeps new code shaped like the patterns it
claims to follow. As the repo scales, the danger is not a single bad file — it is *drift*: the
tenth source adapter that forgets `parser_provider`, the proof script with no `--self-test`, the
config template that pastes a raw key, the "projection" route that quietly writes truth. The
linter scans the governed tree and **fails on each of those deviations** so they cannot land.

It is a *standards-coverage* layer that COMPLEMENTS the existing focused guardrails — it does not
duplicate them:

- `scripts/check_no_direct_provider_bypass.py` enforces the wrapper-first rule (processors reach
  storage/bus/LLM only through ports; vendor SDKs live only behind the gateway).
- `scripts/check_file_layout_policy.py` enforces the file-organization policy (no banned vague
  filenames, no unapproved top-level folders).
- `scripts/check_new_code_uses_standards.py` (this one) enforces that new code matches the
  documented **shape** of its pattern, across categories the other two don't cover.

## Proof

```bash
python3 scripts/check_new_code_uses_standards.py --self-test
```

The proof has three layers:

1. **Positive** — the current clean tree passes every rule (the rules are tuned to today's shapes,
   so the linter is green on commit).
2. **Coverage** — each standards category is represented by conforming code, so a rule can't pass
   vacuously (e.g. there really is a conforming source adapter to lint).
3. **Negative** — in a deterministic temp dir it introduces one deviation per rule (a broken source
   adapter, a proof with no `--self-test`, a doc with no heading, a UI page that writes truth, a
   config with a raw secret, a new vague filename, a processor doing a raw storage write) and proves
   the matching rule fires. This is what guarantees the linter actually bites.

## Rules

| Rule | Scope | Requirement |
|---|---|---|
| `source_adapter_shape` | `_repos/baltor/backend/src/baltor/adapters/source/*.py` | declares `source_type` + `parser_provider` + `def ingest(` |
| `proof_self_test` | `scripts/check_*.py` | supports `--self-test` |
| `doc_has_heading` | `docs/standards/*.md` | carries a top-level `# ` heading |
| `projection_safe` | `scripts/runtime/projections.py`, `_repos/baltor/backend/src/baltor/api/projections/*.py` | no truth mutation, no embedded secrets |
| `ui_projection_only` | `_repos/baltor/frontend/*.html` | no durable writes (projection-only) |
| `config_no_raw_secret` | `_repos/dev-rules-context/templates/configs/**.json` | secret references only (`env://…` / `secret://…`) |
| `no_new_vague_filename` | `scripts/`, `_repos/baltor/backend/src/baltor/` | no new `utils.py`/`helpers.py`/`common.py`/… outside the allowlist |
| `processor_no_raw_storage` | processors | no `sqlite3.connect` / raw `import sqlite3` (use ports) |

## Limitations

- The linter is a *shape* check, not a semantic proof — it confirms a source adapter declares the
  required attributes, not that its `ingest` is correct (that is the adapter's own proof).
- Scopes are deliberately narrow (the directories where each pattern's shape is unambiguous) so the
  linter stays green and precise; broadening a scope requires re-tuning the positive layer.
- Honored exceptions are NOT hand-coded into the linter; they live in
  `architecture/pattern_waivers.json` (active, non-expired waivers exempt a path). See
  [waivers](waivers.md). The linter reads waivers for the vague-filename rule today; new rules that
  need exceptions should consult the same waiver list rather than growing per-rule allowlists.
