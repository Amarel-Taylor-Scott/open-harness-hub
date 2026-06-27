# teleon/ — Teleon.dev

The **purpose-driven runtime**: runs and evolves capabilities (purpose → contract → runtime
selection → candidate → evidence → eval-gated promotion / rollback). Part of
AI Done Right.

**This is the reference site for the shared site kit** — it is built almost entirely from
`shared/oh-site.*`. Use it as the template when scaffolding the OpenHubForAI registries.

Entry: **`Teleon Prototype.html`** → open in a browser.

## Files
| File | Responsibility |
|---|---|
| `Teleon Prototype.html` | Shell: loads shared tokens/components/**oh-site.css** + `teleon.css`, then React/Babel, `products.js`, **`../shared/oh-site.jsx`**, `teleon-main.jsx`. |
| `teleon-main.jsx` | Brand config (`{name:'Teleon', tld:'.dev', glyph:'⟳', accent}`) + router + the **Teleon-specific** pages (Landing, Capabilities, Runs, Evidence, Registry). Account pages (`/billing`,`/usage`,`/settings`) and auth (`/signin`,`/signup`) come straight from the kit's `OhBilling`/`OhUsage`/`OhSettings`/`OhAuth`. |
| `teleon.css` | Only the bespoke bits the kit doesn't cover: the lifecycle rail, ecosystem ports, run progress. Everything else is shared. |

## House style
- Scope `oh dir-s theme-{light|dark} oh-site tln`; accent = violet `#6d5ef0` (set inline via `--accent`, sourced from `PORTFOLIO.ENTITIES.teleon.accent`).
- Hanken Grotesk + IBM Plex Mono; scale + primitives all shared.
- Dark mode: kit `useSiteTheme('teleon-theme')` + `OhThemeToggle`.

## Routes (hash)
`/` landing · `/signin` · `/signup` · `/app` Capabilities · `/runs` (lifecycle runner) ·
`/evidence` · `/registry` · `/billing` · `/usage` · `/settings` · `/docs` · `/pricing` · 404.
