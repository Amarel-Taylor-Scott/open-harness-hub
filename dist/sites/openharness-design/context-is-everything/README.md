# context-is-everything/ — AI Done Right (parent / portfolio)

The **holding-company / portfolio** site above the whole family. A single-page editorial
site with anchor navigation. Cool **white / light-blue** identity.

Renders the portfolio from `shared/products.js` → `window.PORTFOLIO` (`GROUP`, `ENTITIES`,
`LAYERS`, `PORTS`). Sections: Hero · Thesis · **Architecture** (the capability-lifecycle
spine: purpose → contract → runtime selection → candidate → evidence → eval-gated
promotion/rollback) · **Portfolio** (3-layer stack: open supply graphs → Teleon runtime →
governed products) · **How it fits** (the ports between entities). Live entities (Baltor,
OpenHarnessHub) link to their sites; Teleon + the three new OpenHubForAI registries are portfolio cards
with status pills (`building`/`planned`) until their sites exist.

Entry: **`Context is Everything.html`** → open in a browser.

## Files
| File | Responsibility |
|---|---|
| `Context is Everything.html` | Shell: loads React/Babel, fonts, shared CSS + `cie.css`, then `cie-main.jsx`. |
| `cie.css` | Parent layout (`.cie-*`). Overrides `dir-s` neutrals + fonts under `.oh.dir-s.cie` / `.oh.dir-s.theme-{light\|dark}.cie` (keep that specificity). Cards compose shared `.oh-card`. |
| `cie-main.jsx` | Whole page: `Top`, `Hero`, `Problem` (4 failure modes), `Products` (Baltor + OHH cards, each in its own accent), `Story` (Balto), `Band`, `Footer`. Theme state + toggle. Mounts `#root`. |

## Sections (anchor nav)
`#top` hero ("AI, done right.") · `#thesis` the problem · `#products` the two
products + the "one corpus, two ways" join · `#story` the Balto narrative · CTA · footer.

## House style
- Scope `oh dir-s theme-{light|dark} cie`. Identity color = `--cie-blue` (`#2f6fed`).
- Product cards use the product accents: `--cie-baltor` (teal), `--cie-ohh` (ember).
- Display font Hanken Grotesk (matches Baltor); scale from shared `--fs-*`.
- Dark mode: ☾/☀ toggle, persisted `localStorage('cie-theme')`.

## Notes for implementation
- Pure marketing/brand page — no app, no data.
- Cross-links to the two product sites via relative paths (`../context-enrichment/…`,
  `../openharnesshub/…`); swap for real subdomains in production.
- The Balto narrative draws on the **1925 historical event** (public domain). Keep visuals
  clear of any film IP.
