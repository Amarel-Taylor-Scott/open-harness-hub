# Standards Review Pack — Pattern System Sign-Off

This is the **review pack** for the Baltor pattern/standards system: one place a reviewer
can sign off that the standards layer is real, grounded, and self-enforcing. It summarizes
the pattern miner scan, the standards catalog, the template catalog, the routine library,
the waivers, the top anti-patterns, a sample generated component, and the proof results.

It is a META layer over existing code — no new runtime, bus, worker, gateway, optimizer, or
parser. Every catalog it references is a single source on disk; the live numbers come from
those catalogs and the proofs, not from hand-typed counts in this prose (No-Magic-Values).

Re-verify this pack with `python3 scripts/check_standards_review_pack.py --self-test`
(asserts this doc exists and references the real catalogs + the master proofs).

---

## 1. Pattern miner report

- **Source:** `.agent/pattern_miner_report.json` (rendered: `docs/status/pattern-miner-report.md`)
- **Detector:** `scripts/pattern_miner.py` — an AST/grep scan over the governed tree that grades
  each canonical shape and flags one-offs, anti-patterns, and unstandardized repetitions.
- **What the scan found:** the canonical 25 detected patterns, candidate templates, recommended
  standards, unstandardized repetitions, and the anti-patterns below. The report's
  `detected_patterns` / `candidate_templates` are the inputs to the registry + template catalog.
- **Proofs:** `scripts/check_pattern_miner.py --self-test`, `scripts/check_pattern_registry.py --self-test`.

## 2. Standards catalog

- **Source:** `architecture/standard_catalog.json` — one construction standard per shape (the
  contract a template generates against and a check enforces). `status_enum`: draft, active,
  enforced, deprecated.
- Each standard names: `pattern_id`, `must_have` / `must_not_have`, naming / file-location /
  contract / proof / doc / registry / security / observability rules, REAL `examples` paths,
  `template_ids`, and `enforcement_proofs`.
- **Proof:** `scripts/check_standard_catalog.py --self-test` (every example path is real; every
  referenced template exists; the required standard_ids are all defined).
- **Field guide:** `docs/examples/standardized-patterns.md` names the ONE canonical example per
  shape; `scripts/check_standardized_examples.py --self-test` keeps it honest.

## 3. Template catalog

- **Source:** `architecture/template_catalog.json` — the scaffold a standard generates from.
  `status_enum`: candidate, active, deprecated. The active templates are fully built (real
  `template_path` + a `files/` tree of `{{variable}}` placeholders); the rest are planned candidates.
- **Generator:** `scripts/generate_from_template.py` renders a new, standards-conformant component
  and writes a content-addressed generation receipt (no wall-clock in the id).
- **Proofs:** `scripts/check_template_catalog.py --self-test`, `scripts/check_template_generation.py --self-test`.

## 4. Routine library

- **Source:** `architecture/routine_library.json` — the named, blessed way to do each operation,
  grouped by stage (ingestion, decomposition, durable-worker, reconciliation, optimization,
  api/ui, docs/proof). Each routine names its `pattern_id`, `template_id` (if any), inputs/outputs,
  commands, proofs, anti-patterns, and REAL example paths (empty examples are explicitly
  declared-but-not-yet-implemented).
- **Doc:** `docs/standards/routine-library.md`.
- **Proof:** `scripts/check_routine_library.py --self-test`.

## 5. Waivers

- **Source:** `architecture/pattern_waivers.json` — the explicit, time-boxed exceptions to the
  standards linter. Every waiver names an owner, a `replacement_plan`, a `proof_that_safe`, and an
  `expires_by_pass` (a deterministic pass counter, NOT a wall-clock date, so the proof stays
  offline). A waiver with `status=="expired"` FAILS the proof — that is the forcing function that
  makes debt get paid.
- **Doc:** `docs/standards/waivers.md`.
- **Proof:** `scripts/check_pattern_waivers.py --self-test`.

## 6. Top anti-patterns (REAL, from the scan)

The miner records anti-patterns as `{kind, path, detail}` against real paths. The current top
anti-pattern:

- `vague_filename` — `scripts/new.py` — *"vague filename 'new.py' hides intent"*. (Real file on
  disk; flagged because the file name does not state its purpose. Resolution: rename to a
  purpose-named module or record a waiver.)

The standards linter (`scripts/check_new_code_uses_standards.py`) is the live enforcement of the
no-anti-pattern rule on new code; the file-layout policy (`scripts/check_file_layout_policy.py`)
catches banned/vague filenames at the tree level.

## 7. Sample generated component

To show the generator produces a standards-conformant component, generate a proof scaffold:

```bash
python3 scripts/generate_from_template.py --template proof.self_test.v1 \
    --proof_name sample_demo --title "Sample demo proof" \
    --owner scripts/sample.py --subject_module scripts.sample
```

This renders `scripts/check_sample_demo.py` from `templates/proof/self_test.v1/`, conforming to
`standard.proof_script.v1` (it carries `--self-test`, prints PASS/FAIL, exits 0/1), and writes a
**content-addressed** generation receipt (`gen-<sha256[:16]>` — deterministic, the SAME inputs
always yield the SAME receipt id, never a wall-clock id). The generator REFUSES on a missing
required variable and REFUSES to overwrite an existing file without `--force`. (This pack does not
commit the generated file; the command above reproduces it on demand.)

## 8. Proof results (the gates that back this pack)

| Gate | Proof | What it asserts |
|---|---|---|
| Pattern registry | `scripts/check_pattern_registry.py --self-test` | 25 canonical ids; every detected example exists; maturity honest; matrix in sync. |
| Miner report | `scripts/check_pattern_miner.py --self-test` | the scan is real and well-formed. |
| Standards catalog | `scripts/check_standard_catalog.py --self-test` | every example real; templates exist; required standards defined. |
| Template catalog | `scripts/check_template_catalog.py --self-test` | active templates have real `template_path` + `files/`. |
| Template generation | `scripts/check_template_generation.py --self-test` | a template renders a conforming, deterministic component. |
| Routine library | `scripts/check_routine_library.py --self-test` | routines map to canonical patterns; example paths real. |
| Waivers | `scripts/check_pattern_waivers.py --self-test` | every waiver is keyed, owned, and not expired. |
| Standardized examples | `scripts/check_standardized_examples.py --self-test` | the field guide cites only real examples + proofs. |
| **Full-stack honesty** | `scripts/check_pattern_standards_full_stack.py --self-test` | every active standard is backed by a real proof + docs + examples/opportunity + owner; no matrix drift; the proof BITES on an over-claim. |
| This pack | `scripts/check_standards_review_pack.py --self-test` | this doc exists and references the real catalogs + master proofs. |

## 9. Known gap (reported, not hidden)

Several governance / cross-cutting patterns are graded `standard` by the registry's own rule
(a real implemented example + a passing proof) but do **not** yet have a dedicated card in
`architecture/standard_catalog.json`: `source_artifact_pattern`, `capability_catalog_entry_pattern`,
`held_out_warning_pattern`, `structured_logging_pattern`, `section_maturity_entry_pattern`,
`dependency_emulator_pattern`, `multi_source_fixture_pattern`. The full-stack proof surfaces these
explicitly (STATUS column shows `standard (no catalog card)`) and they remain backed by a real
proof + docs + examples — so the proof passes — but adding their standard cards is an open
follow-up for the registry owner (reported to MAIN). This pack records the gap rather than hiding it.

---

**Sign-off:** when every proof in section 8 is green and the known gap in section 9 is acknowledged,
the standards layer is verifiably real and self-enforcing.
