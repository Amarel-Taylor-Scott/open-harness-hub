# Experiments & Tracking — AI Done Right

A small, framework-agnostic A/B-testing + event-tracking engine shared by every site.
Engine: **`shared/oh-experiments.js`** (plain script → `window.OHExp`). React glue
(`useExperiment`, `OhExperimentsPanel`) lives in `shared/oh-site.jsx`. Loaded on all 7 sites
(after `products.js`).

Design goals: **sticky** per-visitor assignment, **consistent** across pages, events that
**carry the active variant**, and a **single seam** to wire real analytics — no app rewrites.

---

## Concepts
- **Experiment** — a key with 2+ weighted variants: `define('hero', ['A','B','C'])` or
  `define('hero', [{id:'A',weight:3},{id:'B',weight:1}])`.
- **Assignment** — the variant THIS visitor gets. Weighted-random, **sticky** in
  `localStorage('oh-exp')`, overridable by URL `?exp=key:Variant` (legacy `?flags=` also works).
- **Event** — `{event, ts, vid, props, exp:{…all current assignments}}`. `$exposure` is emitted
  automatically the first time a variant is shown; you emit conversions yourself.
- **Visitor id** — anonymous, persisted in `localStorage('oh-vid')`, attached to every event.

## Vanilla usage
```js
OHExp.define('hero', ['A','B','C']);
const v = OHExp.variant('hero');          // 'A' | 'B' | 'C' (sticky)
OHExp.exposure('hero');                    // count the impression (deduped per pageload)
ctaEl.onclick = () => OHExp.track('cta_click', { cta: 'start_free' });
```

## React usage (the kit)
```jsx
const [variant, { track, assign }] = useExperiment('teleon_hero', ['A','B','C','D']);
// fires $exposure on mount; re-renders if the variant is forced.
<h1>{HERO_LINES[variant]}</h1>
<button onClick={() => { track('cta_click', { cta: 'start_free' }); navigate('/signup'); }}>Start free</button>
```
Drop **`<OhExperimentsPanel />`** anywhere on the page for a floating dev panel: it lists every
registered experiment, lets you **force** a variant (live), and shows **exposures · conversions ·
rate** per variant. Renders nothing if `oh-experiments.js` isn't loaded.

**Live example:** Teleon's hero second line is experiment `teleon_hero` (A "We prove the rest." ·
B "Skip the agent." · C "We build the capability." · D "We make it dependable."). The hero CTA
emits `cta_click`; the panel is on the Teleon landing. Force one with
`…/Teleon.html?exp=teleon_hero:C#/`.

**Also live:** `baltor_hero` (Baltor landing; **8 variants A–H** from `BRANDCE.hooks`; CTA →
`cta_click`), `baltor_subhead` (A–D) + `baltor_cta` (A–D); `openhubforai_hero` (A/B headline) + `openhubforai_subhead`
(A–C); landing-LAYOUT tests `baltor_landing`, `teleon_landing`, and per-hub `<brand>_landing`
(e.g. `opencontexthub_landing` — `default`/`trust-first`) plus per-hub `<brand>_subhead` (A/B/C) — **active on all 21 makeHub hubs** (9 live + 12 private bench; e.g. `openreviewhub_subhead`, `openreceipthub_landing`, `openstatehub_subhead`); plus `teleon_hero` (A–D). `cmdk_select`
fires from the shared ⌘K palette on Teleon/Baltor/hubs. Every marketing landing mounts
`OhExperimentsPanel`; “Cases” sits in every marketing nav. Baltor's legacy `useFlag`/`setFlag`
delegate to `OHExp`, so there is a single source of truth.

**Pattern — landing-LAYOUT experiments (multiple homepages without forking the router):** keep
one `Landing` component; read a layout variant and re-order/swap sections from a small map. See
`LANDING_LAYOUTS` in `context-enrichment/ce-landing.jsx` — four orderings of the same sections,
each a tracked variant. Reuse the shape for any site (`<site>_landing`).

## Wiring real analytics (pick one — no app changes)
Every `track()` (and `$exposure`) is pushed to **`window.dataLayer`** (GA4 / GTM standard) AND
fanned out to any sink you register:
```js
// GA4 / GTM: just add the GTM container snippet — events are already on dataLayer.
// Segment / PostHog / custom:
OHExp.onTrack(({ event, props, exp, vid }) => {
  analytics.track(event, { ...props, ...exp, vid });   // Segment
  // posthog.capture(event, { ...props, ...exp });
});
```
For a real backend, also assign variants server-side and pass them in via `?exp=` or a bootstrap
`OHExp.assign(key, variant)` so assignment survives the first paint.

## API (window.OHExp)
`define(key, variants, opts)` · `variant(key)` · `assign(key, id)` · `clear(key)` ·
`track(event, props)` · `exposure(key)` · `events()` · `experiments()` · `visitorId()` ·
`onTrack(fn)` → unsub · `onChange(fn)` → unsub · `reset()` · `clearEvents()`.

## Adding a new experiment (anywhere)
1. `const [v, {track}] = useExperiment('my_test', ['A','B'])` (or vanilla `define`/`variant`).
2. Render per-`v` content; call `track('…')` on the action you're optimizing.
3. (Optional) add `<OhExperimentsPanel/>` to that page to drive it in QA.
That's it — assignment, persistence, exposure, dataLayer push and the panel are automatic.

## Notes for production
- In-browser persistence is `localStorage` (prototype). A real build assigns server-side +
  dedupes exposures server-side; keep the same event shape so dashboards don't change.
- `$exposure` dedupes per pageload only — fine for SPAs; revisit for long-lived sessions.
- The dev panel is a *tool*; gate it behind a flag/role before shipping to end users.
