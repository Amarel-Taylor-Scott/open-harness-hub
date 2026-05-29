---
description: Polish BOTH products to launch quality and keep BOTH trycloudflare tunnels live (autonomous, no-stop)
---

Adopt the autonomous **app-polish builder** role for **both** Open Harness Hub products and **begin
immediately**. Goal: drive both products to launch quality and keep both public tunnels live.

## The two products (one shared backend)

- **Open Harness Hub** — *bounded*: assemble a governed pipeline, run it, monitor I/O rules. Pinned
  brand `harness-hub`. Home `/`. Tunnel → `dist/showcase-share-url-harness-hub.txt`.
- **Context Enrichment (CEaaS)** — *unbounded* content refinery: ingest → raw/compressed/hyper-efficient
  tiers → host/download → serve corpora+tools into open agent loops. Pinned brand `context-enrichment`.
  Home `/context-enrichment`. Tunnel → `dist/showcase-share-url-context-enrichment.txt`.

Canonical: `docs/strategy/two-services-shared-infrastructure.md`, `docs/strategy/context-enrichment-service.md`,
`docs/concepts/context-layer-and-the-desk.md`, `web/products.js` (the brand single-source-of-truth).

## Standing contract (no terminal state)

Follow `docs/codex/app-polish-loop.md` + `.codex/prompts/direction.md` + `.claude/commands/goal.md`:
**decide autonomously, never ask, branch on any block, never end on a question.** Record each
assumption in `.research-notes/autonomous-session-ledger.md`. "Screen polished" → next screen;
"blocked/red" → roll back to green, switch paths, keep going.

## Launch + keep BOTH tunnels live

Run `bash scripts/serve_two_products.sh` at the start, and any time a tunnel is down. It brings up two
pinned servers (:8000 harness-hub, :8001 context-enrichment) each behind its own **persistent**
trycloudflare tunnel, sharing one token. Tunnels survive server restarts (URLs stay stable; the
launcher reuses a live one). Web assets serve with `Cache-Control: no-store` — HTML/JS/CSS edits go
live with **no restart**; only `server.py` changes need a relaunch.

## The loop (each pass)

1. **Pick the weakest surface across BOTH products** by the app-polish-loop rubric — alternate so
   neither lags:
   - OHH: `/` (entry box), `/app`, `/preview`, `/docs`, `/pricing`, `/trust`, `/compare`, `/catalog`…
   - CEaaS: `/context-enrichment` (hero, the three tiers, the four consumption surfaces, fidelity moat),
     the `/requests` "enrich your content" funnel, governed-corpora browse…
   Preview either brand locally with `?product=harness-hub` / `?product=context-enrichment`, or hit the
   pinned tunnel directly.
2. **Make it sell its value**: lead with **measured lift / fidelity**, **governance/provenance**, and
   **freezable = no recurring cost** (`docs/design/value-propositions.md`). Keep the two brands
   *distinct* but visually *consistent* (shared design tokens; never a parallel palette).
3. **Verify**: `node --check` every touched file; walk the funnel end-to-end; confirm **both** share
   URLs still serve the polished surface and resolve the right brand (`curl <tunnel>/ | grep __OH_PRODUCT__`,
   then check the surface renders). Keep `web/` no-build (vanilla JS + ported CSS only).
4. **No magic values**: brand/nav/title come from `web/products.js`; a page never hardcodes a product
   literal. New facets are attribute rows, not columns (`docs/codex/schema-extensibility.md`).
5. **Record** a ledger line, **branch** to the next weakest surface, **repeat**.

## Done-enough bar (then keep going)

Both landings lead with the value prop; both funnels complete end-to-end; both tunnels green with the
correct brand; no console errors; no placeholder copy; brands distinct + consistent. Then pick the next
surface — there is no stop.

$ARGUMENTS
