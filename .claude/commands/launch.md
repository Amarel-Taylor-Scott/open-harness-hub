---
description: Polish BOTH products to launch quality and keep BOTH trycloudflare tunnels live (autonomous, no-stop)
---

Adopt the autonomous **app-polish builder** role for **both** OpenHubForAI products and **begin
immediately**. Goal: drive both products to launch quality and keep both public tunnels live.

## The two products (one shared backend)

- **OpenHubForAI** — *bounded*: assemble a governed pipeline, run it, monitor I/O rules. Pinned
  brand `openhubforai`. Home `/`. Tunnel → `dist/showcase-share-url-openhubforai.txt`.
- **Baltor** — *unbounded* content refinery: ingest → raw/compressed/hyper-efficient
  tiers → host/download → serve corpora+tools into open agent loops. Pinned brand `baltor`.
  Home `/baltor`. Tunnel → `dist/showcase-share-url-baltor.txt`.

Canonical: `docs/strategy/two-services-shared-infrastructure.md`, `docs/strategy/context-enrichment-service.md`,
`docs/concepts/context-layer-and-the-desk.md`. Each product has its OWN self-contained front-end folder
(`web/openhubforai/`, `web/baltor/`); only the backend is shared, and `server.py` serves
`web/<OH_PRODUCT>/` (default openhubforai).

## Standing contract (no terminal state)

Follow `docs/codex/app-polish-loop.md` + `.codex/prompts/direction.md` + `.claude/commands/goal.md`:
**decide autonomously, never ask, branch on any block, never end on a question.** Record each
assumption in `.research-notes/autonomous-session-ledger.md`. "Screen polished" → next screen;
"blocked/red" → roll back to green, switch paths, keep going. Every change carries a **warrant**
before commit — clear user intent, ≥2 agreeing sources, or an established principle
(`docs/codex/change-verification-contract.md`); design/brand changes need intent or strong
corroboration, never a unilateral single-agent call.

## Launch + keep BOTH tunnels live

Run `bash scripts/serve_all_sites.sh` at the start, and any time a tunnel is down. It brings up the
pinned servers (:8000 openhubforai, :8001 baltor, :8002 context-is-everything) each behind its own
**persistent** trycloudflare tunnel, sharing one token, and **heals until all are live** (gate:
`python3 -m scripts.showcase.verify_tunnels`). Tunnels survive server restarts (URLs stay stable; the
launcher reuses a live one). For the dedicated no-stop tunnel loop see `/sites-live`
(`docs/codex/three-sites-live-goal.md`); it supersedes the two-product `serve_two_products.sh`. Web
assets serve with `Cache-Control: no-store` — HTML/JS/CSS edits go live with **no restart**; only
`server.py` changes need a relaunch.

## The loop (each pass)

1. **Pick the weakest surface across BOTH products** by the app-polish-loop rubric — alternate so
   neither lags:
   - OHH: `/` (entry box), `/app`, `/preview`, `/docs`, `/pricing`, `/trust`, `/compare`, `/catalog`…
   - Baltor: `/baltor` (hero, the three tiers, the four consumption surfaces, fidelity moat),
     the `/requests` "enrich your content" funnel, governed-corpora browse…
   Preview a product locally with `OH_PRODUCT=<id> python3 -m scripts.showcase --port <p>` (or
   `bash scripts/serve_two_products.sh`), or hit its pinned tunnel directly.
2. **Make it sell its value**: lead with **measured lift / fidelity**, **governance/provenance**, and
   **freezable = no recurring cost** (`docs/design/value-propositions.md`). Keep the two brands
   *distinct* but visually *consistent* (shared design tokens; never a parallel palette).
3. **Verify**: `node --check` every touched file; walk the funnel end-to-end; confirm **both** share
   URLs still serve their OWN product's front-end (`curl <tunnel>/` shows that product's index/markers)
   and render. Keep each `web/<product>/` no-build (vanilla JS + ported CSS only).
4. **Separation + no magic values**: the two front-end folders are self-contained — never cross-import
   between them; only the backend is shared. New facets are attribute rows, not columns
   (`docs/codex/schema-extensibility.md`).
5. **Record** a ledger line, **branch** to the next weakest surface, **repeat**.

## Done-enough bar (then keep going)

Both landings lead with the value prop; both funnels complete end-to-end; both tunnels green with the
correct brand; no console errors; no placeholder copy; brands distinct + consistent. Then pick the next
surface — there is no stop.

$ARGUMENTS
