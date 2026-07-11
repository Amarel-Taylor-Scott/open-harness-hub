# Parent brand: ContextIsEverything Group → AI Done Right (founding-thesis preservation)

**Status:** locked 2026-06-08 (owner: *"I went with AIDoneRight.dev"*). Repo-canonical;
**pending owner** formal trademark search + domain registration. Canonical source of the brand
values is `_repos/shared-backend-components/architecture/brand.json` — this doc is the *narrative
and rollback record*, not a second source of truth.

This is a **rename of the PARENT / holding company only**. It is **lossless**: the prior brand and
the founding thesis are preserved, not erased ([[lossless-distillation-law]]).

## What changed

| Field | Before (superseded) | After (canonical) |
|---|---|---|
| Company name | ContextIsEverything Group | **AI Done Right** |
| Wordmark | — | **AI Done Right** (spaced) |
| Domain | — | **aidoneright.dev** (compact) |
| Primary tagline | Context is Everything | **AI systems that can do the work, show the work, and prove the work.** |
| Short tagline | — | **Efficient. Appropriate. Easy.** |
| Developer tagline | — | **Write the capability; we make it efficient.** |

An interim candidate **"AI is Everything"** was considered and rejected in the same dialogue; it is
preserved in `brand.json` as `superseded.earlier_tagline_candidate` so the decision trail is intact.

The **short** and **developer** taglines were revised after the 2026-06-08 rename to track the current
`brand.json` single source (`tagline_short` = "Efficient. Appropriate. Easy."; `tagline_developer` =
"Write the capability; we make it efficient."). The earlier interim wordings — short **"Context.
Capability. Proof."** and developer **"The platform for governed agentic work."** — are superseded but
retained here as the decision trail (lossless). The primary tagline is unchanged and still mirrors
`brand.json` `tagline`.

## What did NOT change (scope)

- **Products keep their names: Baltor and Teleon.** The distinctive, ownable marks are the PRODUCTS
  (Baltor, Teleon, the OpenHubForAI registries). The parent name is the **promise, not the legal moat**.
- The **OpenHubForAI.io network** is marketing / lead-gen, not the parent identity.
- The `holding_company` **slug** in `company_portfolio_map.json` stays `contextiseverything` — it is a
  code identifier, not a display string. This rename is display-strings-only; we do not churn
  identifiers (and `check_brand_canonical` asserts the slug is preserved).

## Why "Context is Everything" is preserved, not deleted

"Context is Everything" was the **founding thesis**: most AI systems fail because they treat *output*
as truth, *discovery* as trust, and *tool access* as capability — and the missing layer is governed
**context**. That thesis is *still true* and is exactly what **Baltor** does ("Baltor governs what
agents know"). The rename widened the parent promise to the whole agentic-work stack — context
**and** capability **and** proof — which "Context is Everything" alone no longer covered once Teleon
(capability/runtime) and the receipts/proof layer became first-class.

So the line is **retained as Baltor's origin line / founding thesis**, and may continue to appear in
Baltor product narrative. It is *demoted from parent tagline*, not retired from the company's story.
(Owner action still open: confirm whether it stays as Baltor's origin line or fully retires —
`brand.json owner_actions_outstanding`.)

## Name risk (recorded, owner-gated)

"AI Done Right" is a **common phrase** (eLearning courses, IP-law webinars, USPTO/AI commentary, an
`aidoneright.com.au` consulting site). Use **AIDoneRight.dev** as the operating brand + domain +
parent site, **not** as the sole legal/trademark moat. Keep the distinctive product marks (Baltor,
Teleon, OpenHubForAI registries) ownable. **Run a formal trademark search before heavy spend** (owner legal
action — out of repo scope).

## Rollback

`architecture/brand.json` is the single source. To roll back: revert `company_name` / `tagline` to
`superseded.*` and re-propagate (a one-file edit + propagation to `company_portfolio_map.json`,
`portfolio_lib.py`, the design bundle `products.js`, and the brand proofs). History in
`.research-notes/`, `.agent/` ledgers, and memory is **not** rewritten.

## Single source + drift guard

`architecture/brand.json` is canonical (no-magic-values). `check_brand_canonical` asserts the locked
identity loads, the superseded brand + interim candidate are preserved as the rollback target, Baltor
+ Teleon are recorded unchanged, the name is full words (no abbreviation —
[[no-abbreviations-in-naming]]), and the portfolio map's parent `display_name` **mirrors** the brand
file with **no drift**.
