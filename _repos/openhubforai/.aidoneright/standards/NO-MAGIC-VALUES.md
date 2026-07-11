# No Magic Values — single source of truth

> Portable standard for any AI Done Right project. Reference implementation:
> `docs/codex/no-magic-values.md` + the `CLAUDE.md` "No Magic Values" section.

## The rule

Never hand-type a value that must be remembered and updated in more than one place. At scale, a value
typed twice is a value that will drift.

1. **Derive, never transcribe (repo-state numbers).** Any value that *describes the repository* —
   component counts, totals per type, "N emitters", schema/spec version, last-build date — is **computed
   from the source of truth at render or build time**, never typed into committed prose.
2. **One definition, many readers.** A value used in more than one place gets **exactly one definition**
   that everything else imports (embedding dimension, model IDs/routes, schema/spec/catalog version,
   canonical paths, row-family/type names, thresholds, batch/scale targets).
3. **No parallel literals of a constant.** A string that embeds a constant's value is built from the
   constant (`f"vector({DEFAULT_SCHEMA_DIMENSIONS})"`), never a hand-copied `"vector(384)"`.
4. **Name your magic numbers and strings.** Every meaningful literal in logic is a named module-level
   constant with a comment stating unit, rationale, and source. Bare literals are acceptable only for
   trivial identities (`0`, `1`, `""`, `[]`) and genuinely local one-shot values.
5. **Canonical lists live in data, not code.** Component types, industries, capabilities, row families,
   and emitters are read from `vocabularies/` / `schemas/` / a generated index, not re-enumerated in code.
6. **Paths and slugs through one helper**, anchored at the repo root — not `os.getcwd()`, not string
   concatenation sprinkled across modules.
7. **Dates and versions are computed or sourced** — run dates from run metadata, versions from git,
   content identity from canonical hashes. Formatting changes must not mint false versions.
8. **Fail loud on required mirrors.** When a value genuinely must appear in two artifacts, add a
   validate/CI check that recomputes both sides and diffs them, so drift turns red instead of rotting.

## Why

At high volume a hand-typed number makes the registry lie about its own state, breaks dedupe and load
plans, and erodes trust in provenance. The canonical bug: a README that said `172 components` while the
catalog validated hundreds more and generated thousands — typed once, never recomputed, then ~25× wrong.
The same shape recurs as one embedding dimension re-typed across seven modules and model IDs scattered as
bare literals, so a swap means a manual grep-and-replace across the fleet.

## How it is enforced

- Counts in committed text are written by a script inside an auto-generated fenced block
  (`<!-- BEGIN GENERATED:... -->` / `<!-- END GENERATED -->`), and a validate/CI step recomputes and
  diffs them so stale copy **breaks the build** — or the prose links to the live command instead.
- Shared constants live in one config module; shared data lives in `vocabularies/` / `schemas/` and is read.
- A validate assertion fails on any mandatory mirror that drifts.

## DO / DON'T

- DO compute every repo-describing number at build time and diff it in CI.
- DO put a shared value in one place and import it everywhere else.
- DO give every meaningful literal a named constant with unit + rationale + source.
- DON'T transcribe a count, total, or version into prose.
- DON'T re-type the same dimension, model ID, threshold, or path in a second file.
- DON'T embed a constant's value in a string as a parallel literal.
