# Candidate / Truth Boundary — nothing promotes itself

> Portable standard for any AI Done Right project. Reference implementations:
> the `{"candidate": True, "serves_truth": False}` boundary stamped on every record in
> `scripts/check_quality_ratchet.py`; the "never serves truth" markers throughout
> `scripts/flywheel_proof_modules.py`; the `CLAUDE.md` "Promotion Boundary" section;
> `docs/codex/surface-and-development-contract.md`.

## The rule

Every generated row is **born a candidate**: `candidate = true`, `serves_truth = false`. A candidate
becomes tenant-visible truth (`serves_truth = true`) **only** after source review, an **executed passing
proof**, and the promotion gates. Nothing promotes itself.

- **Generation is not promotion.** Raw generated lines, unique staged rows, candidate-table load
  readiness, active promotion readiness, committed rows, and vector-search product readiness are
  **separate counts** — never report generated lines as active components.
- **Candidate-load-ready is not publication-ready.** A candidate can be structurally load-ready (it has
  source, dedupe, content hash, embedding work, index records) yet must **not** become tenant-visible
  while it has open review tickets, a high-risk review requirement, placeholder embeddings, unresolved
  source or signature questions, or volatile public facts without change/revocation handling.
- **`serves_truth = true` is set only on an executed, passing proof** — never by assertion, never by a
  model's own claim, never because a demo printed a number.

## Why

An LLM output is a candidate, not a fact. If generated rows could mark themselves true, the moat (governed,
provenanced data) collapses into an ungoverned pile the moment volume ramps. The boundary keeps the
expensive, trust-bearing step — human/proof review — as the only path from candidate to served truth, and
keeps the metrics honest by refusing to count candidates as product.

## How it is enforced

- **Records carry the boundary as data.** Emitters stamp `candidate: true, serves_truth: false` on every
  row (see the `BOUNDARY` constant reused across the reference scripts), so a downstream reader can filter
  truth from candidates without trusting prose.
- **A proof gate flips the bit.** Only an executed check that passes (for example, a leaf primitive proven
  via an executed proof, counted in a computed manifest) may raise a row to `serves_truth = true`.
- **A verified-to-registry bridge, run every generation run, is what makes proven rows visible** — verified
  rows stay siloed until an explicit mapping step promotes them; the registry-visible count, not the raw
  generated count, is the real metric.
- **Promotion readiness is a separate planned step** (a daily promotion-readiness plan), never a side
  effect of generation.

## DO / DON'T

- DO stamp `candidate: true, serves_truth: false` on every generated row at birth.
- DO keep generated / staged / load-ready / promotion-ready / committed / search-ready as distinct counts.
- DO require an executed passing proof plus source review before `serves_truth = true`.
- DON'T report raw generated lines as active components.
- DON'T let a row, a demo, or a model promote itself to truth.
- DON'T publish a candidate with open review tickets, placeholder embeddings, or unresolved source
  questions, even when it is structurally load-ready.
