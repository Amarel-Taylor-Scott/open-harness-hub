# Implementation Guidance — what's HARD vs FLEXIBLE

For the developer recreating these prototypes in a real codebase. Read after
`START-HERE-CLAUDE-CODE.md` **and `DESIGN-CONTRACT.md` — the contract overrides anything
more permissive here.** This splits the spec into **hard constraints** (must hold or it
stops being the same design), **flexible** (adapt to your stack), and **judgment calls**.

> **Post-mortem note:** a previous implementation drifted by treating the prototypes as
> inspiration — swapping fonts, icon libraries, UI-kit components, and rewording copy.
> The FLEXIBLE list below is now much narrower as a result. Default to **porting verbatim**.

---

## 🔒 HARD constraints — do not break

These are what make it a *branded house*. Violating any one breaks visual/brand consistency.

1. **Tokens are the only source of color & scale.** Every color resolves from `oh-tokens.css`;
   type/spacing size against `--fs-*` / `--pad-*`. **Never** hardcode a hex or a px for
   color/scale in a site stylesheet. (Layout px — grid gaps, fixed widths — is fine.)
2. **One card primitive.** Every card/panel surface is the shared `.oh-card` (border + radius +
   background + shadow). Don't re-declare per component. (Baltor `.ce-*` and OpenHubForAI `.pt-panel`
   *compose* it — keep that.)
3. **One type system.** `--font-display` = **Hanken Grotesk** everywhere; monospace for code/IDs.
   The `--fs-*` scale is shared — don't introduce new sizes.
4. **Single-source brand.** A brand's name, wordmark, tagline, accent and glyph live **only** in
   `shared/products.js`. No accent hex or wordmark duplicated inline. **One `--accent` per brand**
   is the *only* thing that differs between sites.
5. **Dark mode parity.** Every surface is legible in light **and** dark; the accent resolves
   per-theme (`--accent-weak` is translucent so hue survives both). No inline accent that defeats
   the dark token.
6. **Zero horizontal overflow**, every route, every breakpoint. Mobile reflows to one column.
7. **Accessibility floors:** body contrast ≥ 4.5:1, secondary text ≥ 3.6:1; a visible
   `:focus-visible` ring on every interactive (incl. text inputs); mobile hit targets ≥ 44px.
8. **The registry pattern.** All 21 OpenHubForAI registries are **one engine** (`makeHub`) driven by config —
   do not fork 21 bespoke registry UIs. A new hub = a config object + a `products.js` entry.
9. **Private-first is a security boundary.** `status:'private'` must be enforced **server-side**
   in production (the prototype only hides a banner). Never expose a private hub's data publicly
   until it's flipped to `live`.
10. **Provenance is real, not decorative.** The signing / Rekor / in-toto / AI-BOM / Scorecard
    language across the hubs maps to actual standards (`BACKEND-STACK.md`) — implement them, don't
    fake the badges.
11. **The CSS files are production artifacts — copy them verbatim.** `oh-tokens.css`,
    `oh-components.css`, `oh-site.css`, `oh-hub.css` and every per-site css ship as-is.
    Re-authoring them "in your styling system" is how drift happens. (DESIGN-CONTRACT Rule 0.)
12. **All copy is final and verbatim** — headlines, ledes, labels, empty states, banner text.
    No rewording. (Rule 1.)
13. **Keep the prototype class names** (`oh-*`, `ohs-*`, `ohub-*`, `ce-*`, `pt-*`, …) in the
    rendered DOM — the verbatim CSS targets them and parity becomes diffable. (Rule 2.)
14. **No icon libraries, no UI-kit components, no font substitutions.** Glyphs are unicode
    characters; surfaces are the kit's own primitives; fonts are Hanken Grotesk + IBM Plex Mono.
15. **The A/B experiment engine ships** — sticky assignment, `?exp=` forcing, dataLayer events,
    and every declared variant with verbatim copy. (Rule 6, `EXPERIMENTS.md`.)
16. **Per-surface parity gate.** Every surface is screenshot-compared against `screens/` and the
    live prototype before it counts as done; mismatches are fixed, not waived. (Rule 7 —
    record results in `PARITY-REPORT.md`.)

## 🔧 FLEXIBLE — adapt to your codebase

These are prototype *implementation* choices, not the design. Swap freely.

- **Framework.** React (matching the prototypes) is strongly preferred — the JSX transplants
  directly. Another framework is acceptable ONLY if the rendered DOM keeps the prototype's
  element structure and class names so the verbatim CSS still applies (DESIGN-CONTRACT Rule 2).
- **Styling approach.** The shared + per-site CSS files ship **verbatim** (Rule 0). Your
  *additional* code (new glue, layout shims) may use any methodology — but it must consume the
  tokens. Do **not** convert the kit CSS to Tailwind/CSS-in-JS; do not generate a "close" theme.
- **Routing.** Hash routing is a prototype shim. Use your router — but route names/structure are
  the spec (`HANDOFF.md §3.5`), and every route in the prototype must exist.
- **State management.** `useState` + `Object.assign(window,…)` is a prototype shim. Use your
  store or local state — your call. (Migrate window-globals to real imports.)
- **Data fetching / API client.** Anything — the prototype has no network layer. Fixtures ship
  verbatim until real data replaces them.
- **Build tooling, file layout, naming.** Yours. The prototype's `-main.jsx` / `proto-*` names
  are not prescriptive.

**Removed from this list (now HARD):** styling re-authoring and component-library mapping.
Both caused real drift; see DESIGN-CONTRACT Rule 0's forbidden list.

## ⚖️ JUDGMENT CALLS — recommended, but yours to make

- **Precompiled JSX is required for production** (drop in-browser Babel) — not optional.
- **ESM imports vs `window` globals:** migrate to real imports; the window-export pattern is a
  prototype-only constraint of in-browser Babel.
- **`makeHub` as data vs code:** consider driving hubs from a CMS/DB config rather than a JS
  object literal — the shape in `HANDOFF.md §3.5` is the contract either way.
- **Shared `OhRegistry`:** OpenHubForAI's bespoke catalog and the `makeHub` browse grid could share one
  render component — optional consolidation noted in `HANDOFF.md §8`.
- **Legacy paths:** folders keep original names so cross-links don't break. In a fresh codebase
  you can rename freely — just keep `products.js` the single source of identity.

## Port order & effort (recommended)

| # | Port | Why first | Rough effort |
|---|---|---|---|
| 1 | `shared/oh-tokens.css` + `oh-components.css` | every pixel resolves from here | S |
| 2 | `shared/oh-site.jsx` kit (chrome + primitive pages) | all sites' chrome/account pages | M |
| 3 | `shared/oh-hub.jsx` `makeHub` | unlocks all 16 hubs at once | M |
| 4 | **Teleon** (cleanest kit site) | proves the kit end-to-end | S |
| 5 | The 9 live hubs (config) + bespoke `os2t`/`orh` pages | the open funnel | M |
| 6 | Parent + Demo Control Tower | the portfolio map | S |
| 7 | **Baltor** (`ce-*`) + 12 private-bench hubs | the moat + the bench | L |
| 8 | Backends per `BACKEND-STACK.md` | makes it real | XL |

## Definition of done (per surface)

Use `Design Acceptance Scorecard.html` as the gate **plus the DESIGN-CONTRACT Rule 7 parity
loop** (screenshot vs `screens/` reference — fonts, accent, layout, copy, glyphs, banner,
dark mode, routes). A surface ships when:
tokens-only color/scale · composes `.oh-card` · kit chrome (or documented in-house equivalent) ·
kit primitive pages (auth/billing/usage/settings/audit) · dark-mode clean · **zero horizontal
overflow** · a11y floors met · console clean · brand single-sourced · **parity row complete in
`PARITY-REPORT.md` with zero unwaived mismatches**. Family target ≥ 90%.

## Screens
See **`screens/`** in this bundle — a captured reference image per surface (and a few key
sub-states: the OpenSkillToTool architecture page + convert wizard, an OpenReviewHub review
report, a hub browse grid). `screens/INDEX.md` maps each image to its entry HTML.
