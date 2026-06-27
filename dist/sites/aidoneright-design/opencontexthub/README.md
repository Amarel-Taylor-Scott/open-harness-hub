# opencontexthub / openskillshub / opentoolshub — the OpenHubForAI registries

Three open-registry sites, each **built entirely on the shared hub module**
(`../shared/oh-hub.jsx` + `oh-hub.css`, which sit on the site kit `oh-site.*`). A hub is
just a **config object** — no bespoke chrome or pages.

| Folder | Site | Noun | Accent |
|---|---|---|---|
| `opencontexthub/` | OpenContextHub.io | context pack | green `#2f8f6b` |
| `openskillshub/` | OpenSkillsHub.io | skill | teal-blue `#2f7d8f` |
| `opentoolshub/` | OpenToolsHub.io | tool | amber `#8f6f2f` |

## Files (per hub)
- `<Hub> Prototype.html` — shell: loads shared tokens/components/oh-site.css/oh-hub.css,
  then React/Babel, `products.js`, `../shared/oh-site.jsx`, `../shared/oh-hub.jsx`, `<hub>-main.jsx`.
- `<hub>-main.jsx` — **just the config** passed to `makeHub({…})`: brand `{name,tld,glyph,accent}`,
  noun/plural, hero copy, `features`, `facets`, `installCmd`, and the `entries` (the registry items).

## What the hub module gives you (identical across all three)
Landing (hero + proof card + how-it-works + open/governed trust + CTA + footer), a **Browse**
graph (search + facet chips + entry cards), **entry detail** (install command, eval/provenance
badges, deps), **Installed**, **Publish**, and the kit's primitive pages (Billing, Usage,
Settings, Sign in/up). Dark mode + hash routing come from the kit.

## To add another hub
Copy any of these folders, swap the config in `<hub>-main.jsx`, add the entity to
`shared/products.js` PORTFOLIO. ~15 minutes, fully on-brand.
