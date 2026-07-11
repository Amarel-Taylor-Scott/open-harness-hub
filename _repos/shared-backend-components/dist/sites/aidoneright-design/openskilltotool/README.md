# openskilltotool/ — OpenSkillToTool.io

The **skill→tool conversion** registry — the bridge between **OpenSkillsHub** (know-how) and
**OpenToolsHub** (callable actions). Each entry is a *converter* that wraps a governed skill in
a typed tool contract (schema, least-privilege scopes, carried-over eval + provenance) so any
agent can call it over MCP or HTTP, including from Teleon.

Entry: **`OpenSkillToTool.html`** → open in a browser.

## Built entirely on the shared hub module
Like the other six `.io` registries, this site is **config only** — one `makeHub({…})` object
in `openskilltotool-main.jsx`. No bespoke CSS or components. It inherits the whole registry
site: landing + browse graph + entry detail + the "Built on the open supply-chain stack"
section + per-artifact "Provenance & trust" block + account/primitive pages + ⌘K + A/B + tracking.

## Identity (single source: `shared/products.js` → `PORTFOLIO.ENTITIES.openSkillToTool`)
- Accent: **rose** (`#cf5a96`) — distinct from every other hub.
- Glyph `⇋`; domain `OpenSkillToTool.io`; kind "Skill→tool conversion".
- Listed in the parent portfolio's **Open resources** layer (renders automatically from `PORTFOLIO`).

## Config shape (`openskilltotool-main.jsx`)
- `noun: 'converter'` · facets `Research / Data / Code / Comms / Ops`.
- `entries[]` — each a converter wrapping a named skill into a tool, with `deps: ['skill:<id>@<ver>']`
  pointing back at the OpenSkillsHub skill it converts.
- `installCmd` → `s2t convert <id>@<ver>` (emits a typed tool contract + requests scopes).

## Positioning (keep consistent)
*Skills describe how; tools do.* Lead with the conversion value (typed contract, scopes carried
across, eval + provenance preserved). **Discovery is not trust** — the converted tool inherits the
skill's eval score and signed provenance, never a blind wrapper.
