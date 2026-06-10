# Authoring a component template

A template lets the factory generate a new component that already conforms to a standard. This page is the
recipe for adding one (e.g. promoting a `candidate` template in `architecture/template_catalog.json` to
`active`).

## Anatomy

```
templates/<category>/<template_id>/
  template.json            # the manifest
  files/                   # the source tree; mirrors the OUTPUT layout, with {{variable}} placeholders
    scripts/...            # implementation source(s)  -> become STUBS with a failing TODO
    docs/...               # doc source(s)              -> carry all required headings
```

`templates/configs/` is owned by another lane; do not author config templates here.

## The manifest (`template.json`)

```json
{
  "template_id": "<category>.<thing>.v1",
  "standard_id": "standard.<thing>.v1",
  "variables": [
    {"name": "thing_name", "required": true, "description": "what it controls + where it lands"}
  ],
  "files": [
    {"path_template": "scripts/<area>/{{thing_name}}.py", "source": "files/scripts/<area>/thing_name.py"}
  ],
  "required_commands_after_generation": ["python3 scripts/check_{{thing_name}}.py --self-test"],
  "required_registry_updates": ["architecture/contract_registry.json#... += {{thing_name}}"],
  "required_proofs": ["scripts/check_{{thing_name}}.py"],
  "required_docs": ["docs/<area>/{{thing_name}}.md"]
}
```

- **`path_template`** is the OUTPUT path with `{{variable}}` substitution; **`source`** is the file under
  `files/` that supplies the body (also `{{variable}}`-substituted).
- **`variables`**: mark every one the component cannot be generated without as `"required": true`. The
  generator refuses (nonzero exit) if a required variable is missing.
- **`required_*`**: these are echoed back by the generator as the next steps and recorded on the receipt.
  Keep registry updates pointed at the SHARED manifests the main agent owns (the generator never edits them).

## Variable substitution rules

- Placeholders are exactly `{{variable_name}}` (optional surrounding spaces are allowed). Names are
  `[a-zA-Z0-9_]+`.
- An unknown placeholder is left untouched (so a typo is visible in the output, not silently blanked) — but
  the proofs assert a fully built `active` template leaves no `{{` in generated files for its declared
  variables.
- Do not embed a constant's value as a literal in two places (No-Magic-Values). If a value must appear in
  both the impl and the proof, drive it from a single `{{variable}}` or a named constant.

## Required doc headings (for `docs.section_page.v1` and any docs source)

A generated doc page MUST contain, as `##` headings, in this order:

`Purpose` · `Owner` · `Inputs` · `Outputs` · `Contracts` · `Ports` · `Adapters` · `Registry entries` ·
`Proofs` · `Commands` · `Limitations` · `Opportunities` · `Next steps`.

`scripts/check_template_generation.py` asserts all of them are present in the rendered docs page.

## Proof scaffold rules (for `proof.self_test.v1` and any generated proof)

A generated proof MUST:

- expose `--self-test`;
- use a deterministic temp dir (`tempfile.mkdtemp`) for any filesystem work and clean it up;
- be content-addressed (no `datetime.now` / `time.time` / RNG in ids or assertions);
- make NO network call;
- print `[ok]`/`[FAIL]` lines + a `PASS`/`FAIL` summary;
- exit `0` on pass, `1` on fail.

Model new proofs on the existing repo proofs (`scripts/check_event_envelope.py`,
`scripts/check_file_layout_policy.py`).

## Stubs vs passing scaffolds

- Implementation sources (`.py`, `.html`) should ship as **stubs that fail loudly** — `raise
  NotImplementedError(...)` with a `TODO(stub)` and a proof that FAILS until the component is implemented. A
  generated-but-unbuilt component must never read as green.
- The proof scaffold itself (`proof.self_test.v1`) ships **passing** (its harness mechanics are real) with a
  clearly-marked placeholder for the subject assertions.

## Checklist to promote a `candidate` template to `active`

1. Create `templates/<category>/<template_id>/template.json` + the `files/` tree.
2. Set the catalog entry `status` to `active` and point `template_path` at the real manifest.
3. Run the three lane proofs:
   ```
   python3 scripts/check_standard_catalog.py --self-test
   python3 scripts/check_template_catalog.py --self-test
   python3 scripts/check_template_generation.py --self-test
   ```
4. Generate a sample component and run its emitted `--self-test` command.
5. Hand the `required_registry_updates` to the main agent (the generator never touches shared manifests).
