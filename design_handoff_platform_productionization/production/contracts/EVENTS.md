# Events & A/B — the standardized analytics contract

One event shape across all 24 surfaces. The prototypes already emit experiment events
through `shared/oh-experiments.js` (`OHExp` → `window.dataLayer`); this contract gives
that stream a real sink and extends it to page/action events.

## 1. Event shape

```json
{ "site": "baltor", "event": "page|action|exposure|conversion|llm",
  "name": "signup_submitted", "experiment": "hero_copy", "variant": "B",
  "anon": "a_9f2c…", "props": { "path": "/#/pricing" } }
```

- `site` — folder key (baltor, teleon, opencontexthub, …). Single source: `products.js`.
- `anon` — random per-browser id (localStorage), never an email. PII stays out of events.
- `exposure`/`conversion` — exactly what `OHExp` already emits; `experiment`+`variant` required.

## 2. Sink

```
POST /api/v1/events            # single event, an array, or {events:[…]}
GET  /api/v1/events/summary    # counts by site · type · experiment:variant
```

Local storage is the core's JSON file (capped at 50k events). Production: point the same
POST at PostHog/GA4/Segment — the shape maps 1:1 (BACKEND-STACK.md already names these).

## 3. Wiring plan (Pass 2)

Add ~10 lines to `oh-experiments.js`: after each `dataLayer.push`, also
`navigator.sendBeacon('/api/v1/events', JSON.stringify(evt))` when the platform is
reachable. Zero behavior change when core is down (beacon fails silently) — the
prototypes keep working as pure static files.

## 4. What counts as "A/B working end-to-end"

1. Variant assignment (already shipped: `useExperiment` + `OhExperimentsPanel`).
2. Exposure logged in core (`/v1/events/summary` shows `exposure · hero_copy:B`).
3. Conversion logged on the CTA.
4. A readout — conversion/exposure per variant. (Readout UI queued; summary endpoint
   already returns the counts.)
