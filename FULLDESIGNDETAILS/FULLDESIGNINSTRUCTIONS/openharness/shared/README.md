# shared/ — design system + brand registry

The single foundation all three sites consume. **Change something here and every site
updates** — that's the point. Never hardcode colors or sizes in a site stylesheet; pull
from these tokens/primitives.

## Shared site kit — `oh-site.css` + `oh-site.jsx`
A new brand (Teleon, the Open*Hubs) should be **config + a few unique pages**, never a
re-implemented shell. The kit provides identical chrome, page skeletons, and primitive
pages; only the accent color differs.

**Recipe for a new site:**
1. Create `mybrand/` with an HTML shell that loads (in order): `../shared/oh-tokens.css`,
   `oh-components.css`, `oh-site.css`, your `mybrand.css`; then React/Babel, `products.js`,
   `../shared/oh-site.jsx`, `mybrand-main.jsx`.
2. Root element: `class="oh dir-s theme-{light|dark} oh-site"` with `style="--accent:#HEX"`.
   That one accent var re-themes the whole kit (`--accent-weak/-deep/-ink` derive from it;
   `--accent-weak` is a translucent tint so it keeps hue in light **and** dark).
3. Compose kit components from `oh-site.jsx`:
   - Chrome: `OhTopBar`, `OhAppShell`, `OhFooter`, `OhThemeToggle`, `OhLogo`.
   - Skeletons: `OhHero`, `OhSection`, `OhFeatures`, `OhBand`, `OhPageHead`, `OhRollup`.
   - **Primitive pages** (identical house-wide): `OhAuth` (sign in/up), `OhBilling`,
     `OhUsage`, `OhSettings` (+ `OhSwitch`).
   - Shared hooks: `useHashRoute`, `navigate`, `useSiteTheme('mybrand-theme')`.
4. Write only your brand-specific pages + a small `mybrand.css` for bespoke bits.

**Reference implementation:** `teleon/` (Teleon.dev) is built entirely this way — copy its
shape. The brand object is `{ name, tld, glyph, accent }`.

## Files
| File | What it is |
|---|---|
| `oh-tokens.css` | All design tokens (color, space, radii, shadow, type), scoped by `{dir-d \| dir-s \| …} × {theme-light \| theme-dark}`. Source of truth for every color. |
| `oh-components.css` | Canonical primitives + the canonical scale variables. |
| `oh-explorations.css` | Supplementary styles for OHH exploration/component cards. |
| `products.js` | Brand registry — `window.BRAND` + `window.PRODUCTS`. One-line brand renames. |

## Token scopes (`oh-tokens.css`)
Apply a scope by putting classes on a root element, e.g. `<div class="oh dir-d theme-light">`.
- `dir-d` → Baltor (teal accent)
- `dir-s` → OHH (ember) and the parent (parent overrides neutrals/fonts under `.oh.dir-s.cie`)
- `theme-light` / `theme-dark` → light/dark neutral sets
Key tokens: `--bg`, `--bg-subtle`, `--panel`, `--panel-2`, `--line`, `--line-strong`,
`--fg`, `--fg-muted`, `--fg-faint`, `--accent`, `--accent-weak`, `--accent-ink`,
`--success`/`--verified`, `--warning`, `--danger`, `--info`, radii `--r-sm…--r-pill`,
shadows `--e1…--e3`, fonts `--font-display`/`--font-mono`.

## Canonical primitives & scale (`oh-components.css`)
- **Surface**: `.oh-card` (+ `.oh-card--pad`, `.oh-card--interactive`). `.pt-panel` (OHH) is
  a compatibility alias listed alongside `.oh-card`.
- **Controls**: `.oh-btn` (`--primary`/`--ghost`/`--sm`), `.oh-badge`
  (`--verified`/`--warn`/`--muted`/`--danger`/`--sm`).
- **Account/interactive layer**: `.oh-tabs`/`.oh-tab`, `.oh-table`, `.oh-segment`,
  `.oh-field`, `.oh-input`, `.oh-switch`, `.oh-setrow`.
- **Headings/labels**: `.oh-eyebrow`, `.oh-section-label`, `.oh-h1`, `.oh-h2`, `.oh-lead`.
- **Scale vars (on `.oh`)**: `--fs-eyebrow`, `--fs-h1`, `--fs-h2`, `--fs-h3`,
  `--fs-page-title`, `--fs-lead`, `--fs-body`, `--fs-small`, `--pad-card`, `--pad-panel`,
  `--h-topbar`, `--maxw-site`. **All sites must size against these — never raw px.**

## products.js
```
window.BRAND = { name, legal, mission, missionHome, thesis, … }   // company / parent
window.PRODUCTS = {
  openHarnessHub:     { name, dir, … },
  contextEnrichment:  { id:'baltor', name:'Baltor', wordmark:'Baltor.ai', tagline,
                        hook, hooks:[A,B,C], subhead, soul, pillars, dir:'dir-d', supportedBy, … },
}
```
**Rename a brand** → edit `name` (+ `wordmark`). **Re-theme** → change its `dir` scope.
The enrichment product key is historically `contextEnrichment`; its brand is **Baltor**.

## Rules
- Sites compose these classes/tokens; they do **not** re-declare surface/scale.
- Keep `.pt-panel` in the `.oh-card` alias group so OHH stays on the shared surface.
