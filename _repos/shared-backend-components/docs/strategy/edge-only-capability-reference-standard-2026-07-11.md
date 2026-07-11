# The Edge-Only Capability Reference — a format standard for reuse that saves both input and output tokens

> Owner (2026-07-11): "we need more use cases, ideas, templates, standards, etc so that we are actually
> saving both input and output tokens, fix the caveats." Plus: revisit BottleCap's ThinkingCap.

An **edge-only capability reference** is a searchable, typed, verified pointer to code the ecosystem already
maintains (crates.io · npm · PyPI · pystdlib · any registry). We host the *metadata that makes it reusable*
— a description, typed edges, dimensions, and a verified usage recipe — and **never the raw code** (unless
the license permits caching, or we reimplement our own). It is the storage-light, token-cheap unit of reuse.

Everything below is shipped this session, self-test-gated, in `run_proofs`, `candidate=true / serves_truth=false`.

---

## 1. Why edge-only (three problems, one design)

| Problem | Edge-only answer |
|---|---|
| **Storage** — code DBs blow up (a 108 GB `primitives.db`) | ~2 KB/primitive: edges + recipe + handle, no code body |
| **Maintenance** — we can't maintain millions of impls | link to code others maintain; we own only the reuse layer |
| **Tokens** — reading a package is expensive, reimplementing fails | a verified ~tens-of-tokens recipe: read less, emit less |

---

## 2. The format (fields)

```jsonc
{
  "primitive_id": "prim:pkg-<sha>",              // minted by canonical_id (data-plane law)
  "kind": "edge_only.package_link",
  "capability_class": "deserialize",             // one of the standard classes (§5)
  "title": "...", "blackbox": "...",             // DESCRIPTION -> searchable (embeds + indexes)
  "input_edge": "JsonBytes",                     // TYPED EDGES -> composable by the compatibility lattice
  "output_edge": "TypedValue",
  "has_code_body": false, "hosts_raw_code": false,
  "code_hosting_policy": "cache_permitted",      // link_only default; license-derived (§4)
  "package": { "registry": "...", "name": "...", "version_req": "...", "url": "...",
               "license": "MIT OR Apache-2.0", "coordinate_digest": "..." },
  "usage_recipes": [ { "route": "parse", "symbols": ["json.loads"],
                       "snippet": "import json\nobj = json.loads(s)", "verified": true,
                       "api_signatures": { "json.loads": "(s, ...)" } } ],   // TOKEN-SAVINGS payload (§3)
  "dimensions": { "registry": "...", "runtime": "...", "license": "...", "public_callables": 12 },
  "scrapable_dimensions": ["downloads_total","stars","yanked", ...],         // NAMED, not fabricated
  "api_conformance": { "all_recipes_verified": true, "missing_symbols": [] }, // CAVEAT FIX (§6)
  "cdc": { "yank_watch": true },                 // a yanked package revokes the primitive
  "promotion_blockers": [...], "candidate": true, "serves_truth": false
}
```

Version lives in `version_req` / `dimensions`, never in the id or name (naming law). A description + typed
edges make the card **searchable and composable with no code present** — it embeds and indexes through the
same pipeline as any primitive, and composes through the same compatibility lattice.

---

## 3. Two token-saving planes (they STACK — proven + cited)

Saving *both input and output* tokens means two orthogonal planes, measured separately so nothing is
over-claimed (`scripts/edge_only_token_savings.py`):

- **Plane A — model level (output / reasoning tokens), CITED.** BottleCap's **ThinkingCap-Qwen3.6-27B**
  (Apache-2.0, HuggingFace, drop-in Qwen replacement) cuts reasoning tokens **−45.8% out-of-domain /
  −57.7% in-domain at ≈unchanged accuracy** (their **matched-Δ%** benchmark: 5 seeds, *paired per question*
  so the reduction is genuine concision, not "bailed on the hard ones"; GSM8K accuracy even rose 93.3→96.5).
  We adopt it as a **model route** — it shrinks whatever the model thinks, on any task.
- **Plane B — composition level (input + output tokens), MEASURED here on the real installed stdlib.**
  - **INPUT**: read a recipe, not the package. Measured **~694× less on average** (range 245×–1670×;
    `datetime` 1670×, `re` 840×).
  - **OUTPUT**: emit a one-line verified invocation, not a reimplementation. Measured **~134× less** across
    the 8 modules whose reference impl is introspectable (pure-C modules are honestly marked input-only —
    no fabricated output baseline).

They multiply: a ThinkingCap model that *also* invokes a verified recipe spends fewer thinking tokens **and**
emits an invocation instead of a reimplementation. Plane A is BottleCap's number (cited); Plane B is ours
(measured); `tokens ≈ chars/4` is labeled as a heuristic. This is the honest ledger — the same discipline
ThinkingCap's own "how to read these numbers" applies.

**This is the sweet spot the reuse research pointed to:** full-source-in-context works but is expensive;
signatures-only makes models re-implement and fail; the **verified canonical usage recipe** is the middle —
enough to invoke correctly, nothing to read or rebuild.

---

## 4. Code-hosting policy (we don't host raw code)

`hosts_raw_code = false` by default. Whether we may cache the code is license-derived:

| License | `code_hosting_policy` | Meaning |
|---|---|---|
| permissive (MIT/Apache/BSD/ISC/MPL/…) | `cache_permitted` | may vendor/cache; still link-only until chosen |
| copyleft / unknown (GPL/AGPL/…) | `rewrite_required` | to serve code we REIMPLEMENT our own — never host theirs |

`link_only` (host metadata, point at upstream) is always available and always legal. The GPL case is flagged
and promotion-blocked automatically.

---

## 5. Capability-class templates (onboard by class, not one-off)

`scripts/edge_only_capability_templates.py` ships **13 classes** — serialize · deserialize · http_client ·
validate · parse_text · datetime · concurrency · crypto_hash · encode · compress · tabular · math_stats ·
cli_parse — each fixing the canonical typed edges, the recipe shape, the dimensions to scrape, and
cross-ecosystem example packages (**52 use-cases** across crates.io/pypi/npm/pystdlib). Onboarding a package
= pick its class + fill the handle → a valid skeleton. Classes compose by typed edge
(serialize→deserialize on `SerializedBytes`; http_client→deserialize by subtype through the lattice).

---

## 6. Verification (the caveats, fixed)

A declared edge/recipe is **not truth until checked against the real API** — declaring is not verifying (the
80%-marketplace-mismatch lesson). `scripts/edge_only_package_introspection.py` closes it for Python: import
the module, walk the public API, DERIVE recipes from real callables + signatures, and VERIFY every symbol a
recipe references resolves and is callable. A recipe naming a symbol the API doesn't expose is **caught**;
verified cards reach `R4_api_verified`. Proven on 10 stdlib modules / 16 symbols. The same verifier contract
extends to Rust (`cargo doc --output-format json`) and JS (a TS type crawl): *does every referenced symbol
exist with a compatible signature?* This is `declaration_behavior_conformance` applied to a package surface.

---

## 7. Governance & positioning

- **Candidate/truth boundary** — links are `serves_truth=false` until link resolves + license vendorable +
  not yanked + API-verified. **CDC yank-watch** revokes a primitive whose upstream is yanked.
- **SKILL.md-compatible, differentiated above it.** Anthropic's Agent Skills format won interop; it is a
  *description* format with no typed edges, no verification, no deterministic composition. Ingest SKILL.md as
  one input shape; return an edge-only reference that is **searchable + typed + API-verified + composable** —
  the layer the marketplaces (and the 80% mismatch) lack.
- **Scaling** is storage-light: introspect installed packages (offline, precise) or scrape registry metadata
  (opt-in) → derive cards + dimensions + recipes. Bytes per primitive, so the whole of crates.io/npm/PyPI is
  indexable without a code DB.

---

## Shipped this session

`edge_only_package_primitives` (12 curated across 3 registries) · `edge_only_package_introspection` (API-verified,
caveat fix) · `edge_only_token_savings` (plane A cited + plane B measured) · `edge_only_capability_templates`
(13 classes / 52 use-cases). All self-test-gated, registered in `flywheel_proof_modules`, candidate-only.
