# DESIGN CONTRACT — enforcement rules (read before writing ANY code)

**This document overrides anything more permissive elsewhere in this repo.** Previous
implementations deviated from the prototypes. These rules exist to make that impossible.
Treat every rule as a failing test: if the implementation violates one, the work is not done.

The prototypes are not "inspiration" or a "starting point." They are **the spec, at final
fidelity**. The correct mental model is **transplant, not translate**.

---

## RULE 0 — Port, don't re-create

The prototype's CSS and config ARE production artifacts. They are plain CSS and plain JS
with zero framework coupling. You MUST copy these files into the codebase **verbatim**
(byte-identical, minus the file header comments if you must):

| File | Status |
|---|---|
| `shared/oh-tokens.css` | **copy verbatim** — never re-author, never "convert to Tailwind config" |
| `shared/oh-components.css` | **copy verbatim** |
| `shared/oh-site.css` | **copy verbatim** |
| `shared/oh-hub.css` | **copy verbatim** |
| every per-site css (`cie.css`, `ce-*.css`, `os2t.css`, `orh.css`, …) | **copy verbatim** |
| `shared/products.js` (BRAND/GROUP/ENTITIES/LAYERS data) | **copy verbatim** (re-export as a typed module is fine; values unchanged) |
| `shared/cases.js`, all entry fixtures in `*-main.jsx` | **copy verbatim** until real data replaces them |
| `shared/oh-experiments.js` (A/B engine) | **port with identical behavior** (see Rule 6) |

JSX components (`oh-site.jsx`, `oh-hub.jsx`, site pages): transplant the JSX structure —
same element tree, same classNames, same conditional logic. Converting `window` globals to
imports and adding TypeScript types is expected; **changing markup, classNames, or styles is
not**.

**Forbidden re-interpretations** (each of these caused real drift — all are violations):
- ❌ Rebuilding components in a UI library (shadcn/MUI/Chakra/Ant/Radix themes)
- ❌ Converting the CSS to Tailwind utilities or generating a "close" Tailwind theme
- ❌ Swapping Hanken Grotesk / IBM Plex Mono for Inter, Roboto, system-ui, or anything else
- ❌ Replacing unicode glyphs (◆ ⊨ ⇌ ✦ …) with an icon library (lucide/heroicons/fontawesome)
- ❌ "Modernizing" spacing, radii, shadows, or type scale (`rounded-2xl`, `shadow-lg`, …)
- ❌ Inventing new colors, gradients, or per-hub palette variations beyond the one `--accent`
- ❌ Rewriting copy (headlines, ledes, button labels, empty states — all copy is final)
- ❌ Dropping routes, pages, A/B variants, ⌘K palette, theme toggle, or the private-preview banner
- ❌ Collapsing the 21 hubs into "a few examples" — all 21 ship, from one engine

## RULE 1 — Copy is verbatim
Every string a user sees — hero titles, ledes, feature blurbs, button labels, table headers,
empty states, footer links, banner text — is **final copy**. Reproduce it character-for-
character (including the · separators, — dashes, and ≠/⌘ glyphs). If a string seems wrong,
ask; do not silently "improve" it.

## RULE 2 — The class names are the API
Keep the prototype's class names (`oh-card`, `oh-btn`, `ohs-*`, `ohub-*`, `ce-*`, `pt-*`,
`os2t-*`, `orh-*`, `dct-*`). The verbatim CSS targets them; keeping them makes visual parity
automatic and diffable. CSS Modules/scoping wrappers are acceptable only if the rendered
DOM still carries these exact class names.

## RULE 3 — Tokens-only color & scale (unchanged, now enforced)
No hex/rgb/hsl/oklch literal and no font-size/radius/shadow literal may appear in any new
site code — values come from `var(--…)` tokens. The ONLY sanctioned inline style is the
per-brand `--accent` / `--accent-ink` / `--accent-weak` set on the site root (as the
prototypes do) and explicitly-listed exceptions already present in the prototype files.
**Audit:** `grep -rn "#[0-9a-fA-F]\{3,8\}\|rgb(\|oklch(" <new site code>` must return only
the sanctioned root-accent lines and verbatim-copied files.

## RULE 4 — One engine for 21 hubs
`makeHub(cfg)` is ported ONCE. Each hub is its config object + a `products.js` entity.
If you find yourself writing hub-specific page markup outside the gated hooks
(`entryExtra` / `extraRoutes` / `convert.render`), stop — you are forking the engine.
Bespoke hub code lives in the hub's folder and attaches only through those hooks
(reference: `openskilltotool/os2t-pages.jsx`, `openreviewhub/orh-pages.jsx`).

## RULE 5 — Chrome & account flows come from the kit
`OhTopBar`, `OhAppShell`, `OhFooter`, `OhAuth` (signin/signup/forgot), `OhDashboard`,
`OhApiKeys`, `OhTeam`, `OhAuditLog`, `OhBilling`, `OhUsage`, `OhSettings`, `OhDocs`,
`OhPricing` are implemented once and reused by every surface. Baltor and OpenHubForAI wrap them in
their own shells (`ce-*`, `pt-*`) — they do not reimplement them.

## RULE 6 — The A/B experiment engine is part of the design
Port `oh-experiments.js` with identical semantics: sticky per-visitor assignment
(localStorage), consistency across pages, `?exp=key:Variant` forcing, events to
`window.dataLayer` carrying the active variant. All declared experiments ship:
`teleon_hero`, `baltor_hero`+`baltor_subhead`+`baltor_cta`, `ohh_hero`+`ohh_subhead`,
and per-hub `<hub>_landing` + `<hub>_subhead` (every makeHub hub with `ledeVariants` —
A/B/C copy verbatim). Dropping variants or the forcing mechanism is a violation.
Spec: `EXPERIMENTS.md`.

## RULE 7 — Per-surface parity gate (the loop that catches drift)
A surface is NOT done until this passes:
1. Render the implementation at **1280px wide, light theme, default route**.
2. Screenshot it and place it side-by-side with the reference in `screens/` (and, for
   sub-states, the live prototype at the same route).
3. Walk this checklist — every line must match the prototype:
   - [ ] same fonts (Hanken Grotesk display, IBM Plex Mono code) at the same sizes
   - [ ] same accent color (the entity's `accent` from `products.js`, muted for private bench)
   - [ ] same layout structure: nav items, hero composition, card grid columns, footer columns
   - [ ] same copy, verbatim (spot-check hero, 3 cards, footer)
   - [ ] same glyphs (unicode, not icon-library icons)
   - [ ] private-bench hubs: "Private preview" banner present with dashed badge
   - [ ] dark theme toggles correctly; zero horizontal overflow at 390px and 1280px
   - [ ] routes from `HANDOFF.md §3.5` all resolve (marketing + app console + auth)
4. Fix every mismatch **by changing the implementation, never by declaring the difference
   acceptable**. Only the design owner can waive a mismatch — in writing, per instance.
Record the result per surface in `PARITY-REPORT.md` (template at the bottom of this file).

## RULE 9 — Recognize before you build (reuse-first)
The #1 failure mode observed: **rebuilding things that already exist** and missing whole
subsystems (the A/B engine, the light/dark infrastructure, account flows, entire hubs).
Therefore, BEFORE writing any code:
1. Read `SYSTEM-INVENTORY.md` — the manifest of every surface, module, export, experiment
   key, and theme key.
2. Produce the **recognition table** at the bottom of that file (24 surfaces, 23 entities,
   21 hubs from one engine, 12 private, 39 kit exports, 6 experiment-API methods, 8 bespoke
   + 42 per-hub experiment keys, 24 theme keys). Print it. **On any mismatch, do not stop
   and do not guess**: sweep the ENTIRE repo (every folder, every `shared/` module, every
   `*-main.jsx`, every css, every doc), gather the full context, and resolve the mismatch
   from source — the repo is the truth and this manifest is the index. Always proceed from
   the most complete, most fully-realized design + backend spec you find (newest surfaces,
   the gated-hook patterns, the full account layer — never a reduced subset). Log every
   discrepancy + resolution in PARITY-REPORT.md, then continue.
3. For every component/hook/util/page you are about to create, first search the inventory
   and the `shared/` source. If a same-purpose item exists, you port/reuse it — writing a
   parallel implementation is a violation.
4. Subsystems that are easy to miss and are NOT optional: `oh-experiments.js` (sticky A/B +
   `?exp=` forcing + dataLayer), `useSiteTheme`/`OhThemeToggle` light-dark on every surface
   (24 distinct localStorage keys), `OhCommandK`, `OhExperimentsPanel`, the private-preview
   banner, the status-aware accent resolver in `products.js`, and the full account layer
   (`OhAuth`/`OhDashboard`/`OhApiKeys`/`OhTeam`/`OhAuditLog`/`OhBilling`/`OhUsage`/`OhSettings`).

## RULE 8 — When in doubt, the prototype wins
Any gap, ambiguity, or conflict between docs resolves by opening the prototype HTML and
matching what it renders. If the prototype and a doc disagree, the prototype is right.
If something genuinely cannot be matched in the target stack, STOP and ask the design
owner — do not substitute.

---

## Machine-checkable acceptance (run before claiming done)

```bash
# 1. No unsanctioned color literals in new site code (see Rule 3)
# 2. No banned fonts:
grep -rni "font-family.*\(inter\|roboto\|system-ui\|helvetica\|arial\)" src/ && echo VIOLATION
# 3. No icon libraries:
grep -rni "lucide\|heroicons\|fontawesome\|react-icons\|@mui/icons" package.json src/ && echo VIOLATION
# 4. No UI-kit components rendering design surfaces:
grep -rni "@mui/material\|chakra-ui\|antd\|shadcn" package.json src/ && echo VIOLATION
# 5. Tokens file is byte-identical to the prototype's:
diff <your tokens css> openharness/shared/oh-tokens.css && echo TOKENS-OK
# 6. Every brand string resolves from products data, not literals:
grep -rn "AI Done Right\|Baltor\|Teleon" src/ --include="*.tsx" | grep -v products && echo CHECK-THESE
# 7. All 21 hub configs present; count must be 21:
#    (9 live + 12 private bench — enumerate against products.js ENTITIES)
# 8. Recognition table from SYSTEM-INVENTORY.md printed and reconciled (Rule 9) BEFORE coding;
#    re-run after build: every inventory item maps to a ported implementation, none duplicated.
```

## PARITY-REPORT.md template

```md
| Surface | Ref image | Routes pass | Copy verbatim | Tokens diff clean | Dark OK | Parity | Waivers |
|---|---|---|---|---|---|---|---|
| Teleon | 04-teleon.png | 24/24 | ✓ | ✓ | ✓ | ✓ | — |
| …all 24 surfaces… |
```
Every row must be complete before the implementation is accepted.
