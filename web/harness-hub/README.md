# web/ — Open Harness Hub product front-end

This is the **implementation of the Claude Design handoff** (claude.ai/design) for the
Open Harness Hub product UI. The design medium was a React/Babel prototype; per the
handoff's own instruction ("recreate pixel-perfectly in whatever technology fits the
target codebase") this is a **no-build static front-end** — plain HTML + one vanilla JS
file + the prototype's own CSS, ported verbatim. No Node toolchain, deployable as static
files or behind the existing showcase server.

Open Harness Hub is the open builder/catalog surface in the three-site platform story:
**AI Done Right** is the parent platform site, **Baltor** is the paid context-control
product, and **Open Harness Hub** is the open funnel for governed harnesses that can consume
Baltor context when live verified facts are needed. Keep OHH navigation linked to both
family sites so users understand when they are building a workflow versus subscribing to or
serving verified context.

The locked design direction is **Scheme S · Harness House** (Space Grotesk display · Inter
UI · JetBrains Mono · refined-ember accent coupled to the Action primitive · verified-teal
moat color). The bottom-left switcher previews all 9 directions (A–H, S) × light/dark.

## Layout

```
web/
  index.html        landing (#/) + logged-out preview (#/preview) + route fallback
  app.js            modality tabs, example chips, hash router, the build→preview funnel,
                    the 9-scheme/theme switcher — all vanilla, no framework
  styles/           the design system, ported verbatim from the handoff (the pixel spec):
    oh-tokens.css       9 scheme token sets × light/dark (the --bg/--fg/--accent/--p-* contract)
    oh-components.css   shared atoms: buttons, badges, cards, flow nodes, legend
    oh-explorations.css designed states (skeleton/empty/blocked/error/toast), lift-evidence
    proto.css           app + marketing shell, landing hero/entry, modality tabs
    proto-{deep,byo,admin,sdg,value,ops,wide}.css   per-surface styles (for the pages below)
  design/           the design decision record (read these before porting more pages):
    HANDOFF.md          file inventory, route→component→shell→theme map, token contract, data shapes
    PAGES.md            every route + its purpose
```

## How it is served

The existing showcase server (`scripts/showcase/server.py`) serves this directory:

- `/` → `web/index.html` (this front-end)
- `/app.js`, `/styles/*.css` → static assets
- `/api/build`, `/api/export`, `/api/health`, `/api/components`, `/api/primitives` → the **real
  backend** (Gemma-backed flow assembly over 2,400+ indexed components; deterministic
  fallback when no model is reachable). The landing's **Build** calls `/api/build` for real.
- `/classic` → the previous paste-to-flow UI (preserved)

Run it locally and expose a public Cloudflare URL with the established script:

```bash
bash scripts/serve_showcase.sh          # serves web/ on :8000 + a persistent trycloudflare.com tunnel
# share URL (token-gated) is written to dist/showcase-share-url.txt
```

## Implemented vs. pending

**Implemented & wired:** the marketing **landing** (`PLanding` — bare entry box, modality
tabs Text·Image·Audio·Video with swapping placeholder + example chips, hero A/B via
`?flags=heroVariant:B`) and the logged-out **preview** funnel (`PPreview`), which calls the
real `/api/build` and renders the returned flow (graceful sample fallback offline). The full
9-scheme/theme system is live.

**Pending (specced, ready to port):** the ~40 app routes in `design/PAGES.md` — Explore
(`/pipelines`,`/components`,`/c/:slug`), Build/Flow/Run, Foundry/Workers, Govern
(`/freshness`,`/attest`,`/trust`,`/audit-log`), Connect (`/improve`,`/connect`,`/sources`),
Account, etc. The CSS for every one of these is already present in `styles/`.

**To add a page** (mirrors the prototype's own extensibility): add one
`<div data-route="/x" hidden>…</div>` section to `index.html` (or render it in `app.js`),
add a nav/`data-nav` entry, and the router shows it. The atoms (`oh-btn`, `oh-badge`,
`oh-comp-card`, flow nodes) and per-surface classes (`pt-*`) are already styled.

## Open vs. governed (build note)

Per `design/HANDOFF.md §9`: the spec/schemas, seven-primitive grammar, export emitters, and
the build/simulate path are **open (Apache-2.0, free)**; vetted components, live knowledge
corpora (CDC freshness + revocation), build-on-demand, and attestation renewal are the
**governed (subscription)** layer. The front-end reflects this boundary in pricing/preview.
