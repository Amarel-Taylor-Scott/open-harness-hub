# App-Polish Loop — make the product undeniable, one surface at a time

Runnable goal for `/polish`. The job: take the Open Harness Hub product front-end (`web/`,
implemented from the Claude Design handoff) from "works" to **acquirer-grade** — every screen,
funnel, gate, and endpoint polished, and every surface *selling the value proposition*. This
is a loop with no terminal state; pick the weakest surface, polish it, verify, repeat.

## 0. Boot (once per session)

```bash
bash scripts/serve_showcase.sh            # serves web/ on :8000 + a persistent Cloudflare URL
cat dist/showcase-share-url.txt           # the live, token-gated share URL (verify it serves web/)
node --check web/app.js web/data.js       # core must parse
ls web/pages/                             # the self-registering screen modules
```

The front-end contract (do not break it): `web/app.js` defines `window.OHH`; screens live in
`web/pages/*.js` and self-register via `OHH.register(route, render, onMount, {theme})`; shared
data is `OHH.data` (never redeclare); styling is the ported design system in `web/styles/*.css`
(reuse classes, add none). Full map: `web/README.md`, `web/design/PAGES.md`, `web/design/HANDOFF.md`.

## 1. The two things every surface must do

1. **Work** — renders, navigates, has its empty/loading/blocked/error states, no dead `data-nav`.
2. **Sell** — in the first screenful it makes the value proposition unmissable. The canonical
   props live in `docs/design/value-propositions.md`. The spine on every surface:
   - **Measured lift** over a bare model (▲ +Δ), never asserted — pipeline-level only.
   - **Governance**: provenance/signed/verified, freshness (CDC + revocation), accountable.
   - **Freezable = no recurring cost**: most lift is deterministic and frozen into the export.
   - **Open-core**: spec/SDK/export free; vetted components + live knowledge are the paid layer.

## 2. The polish rubric (score each surface 1–5; fix anything < 5)

- **Value clarity** — does the headline + first card state the lift/governance/cost story?
- **Seven-primitive language** — Input ⌖ · Knowledge ⛁ · Conditional ◈ · Action ⚡ · Loop ↻ ·
  Stop ⊘ · Output ⎘ · Operator ◇, correct hues; **Conditionals open indented branches** with
  their Knowledge/Action "then" steps nested under them (not a flat list).
- **Gates visible, never silent** — unproven lift, unsourced provenance, placeholder embeddings,
  over-quota: each shows the *reason* + the *fix*, not a blank or a crash.
- **Funnel** — the path in and the path out are obvious; CTAs lead somewhere real.
- **States** — empty teaches the next action; loading is a skeleton; error offers retry.
- **Copy** — concrete, benefit-led, no lorem, no "manifest/artifact" (use components/Knowledge
  Corpus/Conditional/Action); numbers are real or clearly sample-labelled.
- **Responsive + a11y** — works narrow; focus states; alt/aria on controls; contrast holds in
  both light and dark (toggle the bottom-left switcher).

## 3. The funnels to walk end-to-end (fix any break)

- **Build**: `/` → (enter task) → `/preview` (logged-out) or `/build` → `/results` → `/flow` → `/run`.
- **Explore**: `/pipelines` (lift, modality tabs, Source filter) · `/components` (no lift) → `/c/:slug`.
- **Demand**: zero-result → `/requests` → `/requests/:id` (fulfillment).
- **Govern / moat**: `/freshness` · `/attest` · `/p/:id` · `/trust` · `/k/:id`.
- **Wedge**: `/improve` (paste a pipeline → measured before/after).
- **Account**: `/pricing` → `/signup` → `/onboarding` → `/app`; `/admin` quota → `/upgrade` → `/checkout`.
- **Operator credibility**: `/foundry` (probed→…→**promoted, never generated**) · `/workers`.

Every `data-nav`/`navigate` target must be a registered route — no link into the 404.

## 4. Endpoints (the live backend behind the design)

`/api/build` `/api/export` `/api/health` `/api/components` `/api/primitives` (see
`scripts/showcase/server.py`). Polish: the front-end consumes real shapes; failures degrade
gracefully (the preview already falls back to a sample); the build result shows the structural
flow (if→then nesting), real cost, and whether it was model- or deterministically-assembled.

## 5. Loop

1. Score each surface against §2 (start with whatever a visitor hits first: `/`, `/preview`,
   `/results`, `/pipelines`, `/c/:slug`, `/pricing`).
2. Take the lowest score; make surgical edits to its `web/pages/*.js` (vanilla, no new CSS/deps).
3. `node --check` it; reload the live URL; re-walk the funnel it sits in.
4. Record in `.research-notes/autonomous-session-ledger.md`; commit per milestone.
5. Repeat. When all surfaces ≥ 4, raise the bar (motion, micro-copy, the demo script an acquirer sees).

## 6. Guardrails

No-build (`web/` stays vanilla + ported CSS). No PII, no `_reference/` republish, no faked
lift numbers (label samples). Don't edit `web/app.js`/`data.js`/`index.html` except for a real
router/nav fix. Keep the live URL serving the latest `web/` (static — no restart needed).
Cross-link: [[../design/value-propositions.md]], `web/README.md`, `archive/legacy/docs/strategy/acquihire-roadmap.md`.
