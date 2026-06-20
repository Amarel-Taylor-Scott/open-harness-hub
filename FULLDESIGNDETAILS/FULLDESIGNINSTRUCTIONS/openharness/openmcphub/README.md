# openmcphub/ · opencompressionhub/ · openbenchmarkhub/ — the three newest open hubs

Three open-registry `.io` sites added to complete the hub family. Each is built **entirely** on
the shared hub module (`../shared/oh-hub.jsx` via `makeHub`) — only a config object is local,
exactly like OpenContextHub/Skills/Tools. Domains are **proposed/unverified** (owner
trademark/domain clearance pending).

| Folder | Site | Accent | One-liner | Boundary law |
|---|---|---|---|---|
| `openmcphub/` | OpenMCPHub.io | blue-violet `#5b7cf0` | MCP server intelligence layer | MCP **discovery is not trust** — conformance + risk required |
| `opencompressionhub/` | OpenCompressionHub.io | acid/lime `#9bd61f` | Compression & context-budget intelligence | **Token reduction is not success unless fidelity survives** |
| `openbenchmarkhub/` | OpenBenchmarkHub.io | red/coral `#e0556a` | Benchmark intelligence layer | Benchmarks are **evidence, not authority** — a result cannot promote a candidate alone |

## Files (per folder)
- `<hub> Prototype.html` — shell: loads React/Babel + shared CSS/JS, then `<hub>-main.jsx`.
- `<hub>-main.jsx` — the local `makeHub({…})` config (brand, hero/lede + A/B `ledeVariants`,
  features, facets, entries). No bespoke CSS or components.

## What they inherit from the kit (free)
Top bar + portfolio switcher, `OhHero`/`OhSection`/`OhBand`/`OhFooter`, Browse (faceted +
search + zero-result), entry detail drawer, account pages (`OhAuth`/`OhBilling`/`OhUsage`/
`OhSettings`/`OhApiKeys`/`OhTeam`/`OhAuditLog`), `/about` → `OhAbout`, `/cases` → `OhCaseStudies`,
unknown → `OhNotFound`, the ⌘K `OhCommandK` palette, and the `<brand>_landing` + `<brand>_subhead`
A/B experiments. Identity is pulled from `shared/products.js` `PORTFOLIO.ENTITIES`.

## Registry & integration
- Entities live in `shared/products.js` (`openMCPHub`, `openCompressionHub`, `openBenchmarkHub`),
  added to the `open` layer so the **parent portfolio** renders all 7 hubs.
- They appear in the **Demo Control Tower** (`context-is-everything/Demo Control Tower.html`)
  under Open Hubs.
- Content honors the orientation doc: OpenBenchmarkHub leads with the first-party **Baltor CFPB
  Context-Governance** benchmark; OpenCompressionHub ties fidelity to surviving source handles /
  held-out warnings; OpenMCPHub gates a high-risk `shell-mcp` as quarantined.
