# START HERE — Claude design (AI Done Right · one screen)

You are the designer ("Claude design"). There is **ONE design system, one renderer, one stylesheet.** Read in this
order, then design.

## Read order (top to bottom)

1. **`docs/DESIGN-BIBLE.md`** — THE design system: tokens · type scale · every component · routes · governance ·
   the SAFE-vs-LOCKED handoff (§11). This is the #1 read; everything else is orientation.
2. **`scripts/surface_server.py`** — THE live renderer. Its `_CSS_TEMPLATE` constant is the single stylesheet every
   surface ships **byte-identical** (~7959 chars); only the per-surface `--accent` + copy differ. The `render_*`
   helpers emit the HTML.
3. **The 5 live URLs** (below) — see it rendered. Or run `python3 scripts/surface_server.py <surface-id>` locally.
4. **`dist/sites/openharness-design/`** — the richer, high-fidelity REFERENCE bundle the canonical tokens derive
   from (start at `START-HERE-CLAUDE-CODE.md`). This is what you elevate *toward*.

Then: `FAMILY-README.md` + `HANDOFF.md` (next to this file) for family shape, the Baltor method spine, and
production gaps.

## The 5 surfaces + accents + live URLs

(single source: `architecture/surface_capability_spec.json` → `scripts/_surface_accents.py`; URLs in `dist/surface-urls.json`)

| Surface | `--accent` | live URL (ephemeral TryCloudflare tunnel) |
|---|---|---|
| **AI Done Right** (hub) | `#5a6b87` | https://flags-employee-robinson-nevada.trycloudflare.com |
| **Teleon** | `#6d5ef0` | https://commodities-cleaner-entities-dangerous.trycloudflare.com |
| **Baltor** | `#0e7c86` | https://marathon-crop-moore-logistics.trycloudflare.com |
| **AIDevObserver** | `#b25fd6` | https://somerset-evaluations-schedules-copying.trycloudflare.com |
| **OpenHubForAI** (carries `/browse`) | `#3b6fd4` | https://chancellor-photography-coins-cir.trycloudflare.com |

> URLs rotate every launch — `dist/surface-urls.json` is the live record; production uses the stable domains.

## Your job

Elevate the live `surface_server` pages toward the richness of the `dist/sites/openharness-design/` bundle —
**WHILE keeping the byte-identical-CSS law.** You never style a single surface. You edit `_CSS_TEMPLATE` once and the
change propagates to all 5. After any change: `python3 scripts/check_surface_server.py --self-test` (122 assertions).

## SAFE to change (single-source — propagates to all 5)

- A surface's **accent** or **copy** → `architecture/surface_capability_spec.json`.
- **Type scale, spacing, color tokens, component CSS** → `_CSS_TEMPLATE` in `scripts/surface_server.py` (ONE place;
  use `var(--token)`s, never raw hexes).
- **Add a component** → add its CSS to `_CSS_TEMPLATE` **and** emit its HTML in the relevant `render_*` helper.

## LOCKED (owner law — do not break)

- The **byte-identical-CSS law**: accent + copy are the ONLY per-surface variables. No per-surface stylesheet, no
  surface-varying inline style, no second accent-like token.
- The **5-surface model**, and that only **OpenHubForAI** owns `/browse`.
- The **governance footer** + **`serves_truth = false`** + the never-store / never-echo BYO-key contract.
- **Inter UI + `ui-monospace`** as the canonical fonts (resizing within the scale is fine; changing the type
  *system* needs owner intent).

Full detail for every line above: **`docs/DESIGN-BIBLE.md`** §11. `serves_truth = false` (candidate output, not
verified truth; a BYO key is used only for the request, never stored or logged).
