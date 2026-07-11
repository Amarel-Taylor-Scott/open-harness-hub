# Component Standards — the load-bearing laws every component follows

This is the shared contract that keeps independently-managed components (pre-LLM, LLM/model, post-LLM,
runtime) compatible. It is a **concise index**, not a second copy: the canonical, portable law set lives in
**[`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md)** (one concise doc per law:
the rule, why, how it is enforced + which check, and a DO/DON'T). Read the linked canonical doc before acting
on a law; on any conflict, the canonical doc wins. Repo-specific operating detail is in root `CLAUDE.md` and
`docs/codex/`.

---

## The portable laws (canonical set — `../dev-rules-context/standards/`)

1. **[Change Verification](../dev-rules-context/standards/CHANGE-VERIFICATION.md)** — every change carries a
   **warrant** before commit (clear user intent, ≥2 independent agreeing sources, or an established principle),
   matched to blast radius; design / brand / strategy / vocabulary / pricing / product-structure is **never** a
   unilateral single-agent call. "It's green" is necessary, not sufficient.
2. **[Lossless Distillation](../dev-rules-context/standards/LOSSLESS-DISTILLATION.md)** — distillation is
   **never replacement**; every compression / promotion / optimization / LLM→deterministic-rule conversion
   writes a new **versioned** derived layer while preserving the raw layer, intermediates, lineage, held-out,
   rejected candidates, and a rollback target. Omitted / held-out / rejected / superseded ≠ deleted.
3. **[No Magic Values](../dev-rules-context/standards/NO-MAGIC-VALUES.md)** — never hand-type a value used in
   more than one place; repo-state numbers are **computed**, not typed (the `172` README-count drift is the
   canonical bug); a shared value gets one definition and is imported; every literal is a named constant with a
   unit/rationale.
4. **[Candidate / Truth Boundary](../dev-rules-context/standards/CANDIDATE-TRUTH-BOUNDARY.md)** — every
   generated row is born `candidate=true, serves_truth=false`; promotion requires source review, an executed
   passing proof, and the gates. Nothing promotes itself; only a governed Baltor truth output is
   `serves_truth=true`.
5. **[Verify the Verifier](../dev-rules-context/standards/VERIFY-THE-VERIFIER.md)** — a green suite that can't
   go red proves nothing: add a mutation gate, a byte-identical determinism gate, and a quality ratchet over
   manifest floors; never seed a reproducible harness with `hash()`.
6. **[Archival — Move, Never Delete](../dev-rules-context/standards/ARCHIVAL-MOVE-NEVER-DELETE.md)** —
   outdated / superseded context is **moved** (not deleted, not untracked) under `archive/legacy/<original-path>`
   with its status recorded, kept in git for lineage + rollback, and excluded from model context while staying
   on disk. Never mislabel LIVE/GENERATED data as "legacy."
7. **[Globally-Unique Naming](../dev-rules-context/standards/GLOBALLY-UNIQUE-NAMING.md)** — every defined thing
   (code object **or** generated data record) gets a **globally-unique, location-derived, meaning-bearing name**
   that resolves it with zero ambiguity: `py_<kind>__<file>__<scope>__<name>` for Python (engine
   `scripts/pyprefix.py`), `canonical_id(prefix, *parts)` for data (single source `src.teleon.experiments.ids`).
   Version lives in `schema_version` **metadata**, never in a name or id (no `.vN`, no `@N`).
8. **[Multi-Path Development](../dev-rules-context/standards/MULTI-PATH-DEVELOPMENT.md)** — don't decide *how*
   to do something up front; **build out all reasonable paths, benchmark, then choose + keep a fallback** (which
   canonicalizer / retriever / embedder / compose strategy is an experiment with a receipt, not an opinion).

## Repo-specific operating standards (load-bearing here; not in the portable set)

These two are enforced in this repository but are not part of the portable law set above; their canonical
detail is in `CLAUDE.md` + `docs/codex/`:

- **Codegraph change audit** — before AND after editing a `.py` file/function/class/method, audit its strong
  connections on the weighted code graph and update the load-bearing neighbors in the SAME change
  (`PYTHONPATH=. python3 scripts/codegraph.py --audit <path|module|symbol>`). A green suite says the code runs;
  the graph says what else the change can break. Source: `docs/codex/codegraph-change-audit-protocol.md`;
  `CLAUDE.md` §"Code-Graph Change Audit".
- **Promotion boundary** — a candidate can be structurally load-ready (source, dedupe, content hash, embedding
  work, index records) yet MUST NOT become tenant-visible while it has open review tickets, high-risk review
  requirements, placeholder embeddings, unresolved source/signature questions, or volatile public facts without
  CDC/revocation. Report the stages separately; never report raw generated lines as active components. Source:
  `CLAUDE.md` §§"Promotion Boundary", "Required Row Families", "Daily Factory Target".

---

## Per-pattern standards (the component-shape layer)

The laws above are cross-cutting. The *shape* of a specific component pattern (source adapter, durable command
handler, projection route/page, provider adapter, proof script, docs page) is governed separately by the
normative standards + runnable templates in `docs/standards/README.md` → `architecture/standard_catalog.json` /
`template_catalog.json`, generated by `scripts/generate_from_template.py` and proven by
`check_standard_catalog.py` / `check_template_catalog.py` / `check_template_generation.py`. `enforced` standards
(e.g. `standard.proof_script`, `standard.tenant_isolation`) are non-negotiable for any new component. Use those
to build a conforming component; use the laws here to keep it compatible once components are managed
independently.
