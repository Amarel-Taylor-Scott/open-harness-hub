# Standards — the load-bearing laws every AI Done Right project inherits

Portable, reusable standards generic to any AI Done Right project. Each is one concise doc: the rule,
why it exists, how it is enforced (and which check), and a DO/DON'T. This repository is the cited
reference implementation for each — the "Reference implementation" line in every doc points at the real
code, script, or contract that already enforces it.

Read them in this order. Start with the two headline laws.

## Headline laws (read first)

- **[Change Verification](CHANGE-VERIFICATION.md)** — every change carries a *warrant* (clear user intent,
  or two-plus agreeing sources, or an established principle); design / brand / strategy / product-structure
  is never a unilateral single-agent call. "It's green" is necessary, not sufficient.
- **[Lossless Distillation](LOSSLESS-DISTILLATION.md)** — distillation is never replacement; every
  compression / promotion / LLM-to-rule conversion writes a new *versioned* layer while preserving raw +
  lineage + held-out + rejected + rollback. Omitted ≠ deleted.

## Supporting standards

- **[No Magic Values](NO-MAGIC-VALUES.md)** — never hand-type a value used in more than one place; counts
  are computed from manifests, not prose; one definition imported everywhere; every literal a named
  constant with unit and rationale.
- **[Candidate / Truth Boundary](CANDIDATE-TRUTH-BOUNDARY.md)** — every generated row is born
  `candidate=true, serves_truth=false`; promotion requires source review, an executed passing proof, and
  the gates. Nothing promotes itself.
- **[Verify the Verifier](VERIFY-THE-VERIFIER.md)** — a green suite that can't go red proves nothing: add a
  mutation gate, a byte-identical determinism gate, and a quality ratchet over manifest floors; never seed a
  reproducible harness with `hash()`, and run edit/restore harnesses under `PYTHONDONTWRITEBYTECODE=1`.
- **[Archival — Move, Never Delete](ARCHIVAL-MOVE-NEVER-DELETE.md)** — outdated context is moved (not
  deleted, not untracked) under `archive/legacy/`, kept in git for lineage, status recorded, and excluded
  from model context while staying on disk.
