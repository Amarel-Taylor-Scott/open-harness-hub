# ADMIN-MONITOR-PROMPT — paste this whole block into Claude Design

> The single, paste-ready prompt for building the **realtime Admin Monitor** (the "Global Operations Console")
> for AI Done Right. It monitors the ENTIRE system live. There is a working backend already
> (`scripts/ops_console_service.py` serving `GET /api/ops/status`) — the exact JSON it returns is embedded below,
> so design against real data, not guesses. Copy from the line below to the end.

---

STOP. Read this entire instruction before you build, and follow it literally.

Build the **COMPLETE, REALTIME Admin Monitor** for **AI Done Right** — one internal operations console that monitors
the entire system **live**: users/usage, the autonomous agent loops (flywheels), the worker fleet, registries,
records, scrapers/discovery, researchers, and the security gates. Not a static page, not a mockup, not a subset — a
living dashboard whose numbers, charts, and status badges **update in place every few seconds** without a full reload.

## OUTPUT (non-negotiable)
- **ONE self-contained `.html` artifact** that renders the full monitor and **polls live data**, opening directly in a
  browser. React 18 + in-browser Babel is fine (no build step), or plain JS — your call — but it must be one file.
- **Emit every line.** No `// …`, no "rest is similar", no truncation, no placeholders, no "coming soon". Build it all.

## IT IS REALTIME (this is the whole point — do not ship a static page)
- **Poll `GET /api/ops/status` every 3 seconds** and update the UI **in place** (no full-page reload, no flicker).
  A demo-data shim (below) makes it run with realistic, *moving* numbers when no backend is present — keep the poll
  loop; the shim just answers it.
- **Numbers tick/animate** when they change (count-up transitions); a value that just changed flashes briefly.
- **Live charts** for anything that moves over time: usage events, the flywheel cycle climbing, records growth,
  fleet throughput. Build them as **token-built inline SVG sparklines/area charts** (no heavy external chart library,
  no external CDN) so the file stays self-contained. Keep a rolling in-memory history (last ~60 polls) to draw them.
- **A live activity stream** (a scrolling feed): newest flywheel action, new findings, new quarantines, new
  conversions — newest on top, with a relative timestamp, animating in.
- **A "LIVE" indicator**: a pulsing dot + "updated 2s ago" + a connection state (live / reconnecting / offline). When a
  poll fails, show "reconnecting", keep the last values dimmed, and recover automatically — never blank the screen.

## DESIGN (this is AI Done Right — use the family design language)
- It is an **internal ops console**: dense, calm, **dark-first**, information-rich. Use the shared kit's tokens, type
  scale, spacing, and primitives (`OhAppShell` left sidebar, `OhRollup` stat cards, `OhTable`, `oh-card`, `oh-badge`,
  the mono font for figures). See `DESIGN-ASSETS.md` + `CONSISTENCY-CONTRACT.md` in this folder. Do not fork the kit
  or invent a second CSS system. One accent for the console (a neutral ops slate, `#5a6b87`); green/amber/red are
  reserved for **health/status** only.
- Left sidebar nav across the views: **Overview** (the wall of panels), **Flywheels**, **Fleet**, **Usage**,
  **Registries**, **Discovery & Research**, **Security**. Every view is realtime.

## THE PANELS (each maps to a field in the live contract below — build all of them)
1. **Overview** — a rollup of the headline figures (registries, records, findings, proposals, usage events, flywheel
   cycle, fleet tasks) with sparklines, the health badge, and the live activity stream.
2. **Autonomous flywheels (agent loops)** — a row per loop (Sweep, Status, YC, Propose, Hubs, Health, Autofix,
   Cleanup, …): a health dot (green if `errors == 0`), `last_cycle`, `lag` (current cycle − last_cycle), error count.
   Show `last_flywheel` + `last_summary` prominently, and the cycle number climbing live. List `hubs_recent`.
3. **Worker fleet** — `fleet.tasks.by_status` as a live bar/donut, `fleet.execution.total` ticking, recent executions.
4. **Users & usage** — `usage.total` big and live, `usage.by_site` (bars), `usage.by_type` (page / exposure /
   conversion) with a conversion-rate readout, and a usage-over-time area chart from your rolling history.
5. **Registries & records** — `registries`, `records`, a real-vs-synthetic split bar (`real` / `synthetic`),
   `target_per_registry`, and a records-growth sparkline.
6. **Discovery & research** — `discovery.candidates` intaken, `discovery.quarantined` (flag in red if > 0),
   `research.proposals_backlog`, `research.findings`, and `discovery.security_gate` status text.
7. **Security** — surface the scan-gate posture: ingest quarantines and the promotion block, `serves_truth=false`,
   read-only. Make it obvious the platform is governed.
8. **Services & product surfaces** — `services.surfaces_up`/`surfaces_total` and `services.up`/`total` as a live
   grid of status chips (one per service: name, port, up/down dot); surfaces marked with `◆`. This is the WHOLE plane,
   not just the factory — product surfaces AND backend services.

## THE LIVE DATA CONTRACT — `GET /api/ops/status` returns exactly this shape (real, from the running backend)
```json
{
  "service": "ops_console", "serves_truth": false, "projection_only": true,
  "flywheel": {
    "cycle": 9661, "health": "ok", "last_flywheel": "propose",
    "last_summary": "distilled 24 new proposal(s); backlog now 5253",
    "findings_recorded": 45126, "no_progress": 0, "health_red_streak": 0,
    "loops": [ {"key":"sweep","label":"Sweep","last_cycle":9658,"lag":3,"errors":0},
               {"key":"propose","label":"Propose","last_cycle":9660,"lag":1,"errors":0} ],
    "hubs_recent": [ {"hub":"OpenCompressionHub","last_cycle":9655} ]
  },
  "registries": { "registries": 155, "records": 155000, "real": 2448, "synthetic": 152552, "target_per_registry": 1000 },
  "research":   { "proposals_backlog": 5253, "findings": 45128 },
  "discovery":  { "candidates": 636, "quarantined": 0, "security_gate": "active (ingest quarantine + promotion block, >=high)" },
  "usage":      { "total": 2295, "by_site": {"openhubforai": 436, "aidoneright": 1859},
                  "by_type": {"page": 1355, "exposure": 921, "conversion": 19} },
  "fleet":      { "ok": true, "tasks": {"by_status": {"done": 120, "running": 3, "queued": 8}},
                  "execution": {"total": 4210} },
  "services":   { "total": 28, "up": 28, "surfaces_total": 12, "surfaces_up": 12,
                  "services": [ {"id":"openhubforai_app","name":"OpenHubForAI app","port":8000,"up":true,"is_surface":true} ] }
}
```
A section can degrade: `usage`/`fleet` may instead be `{"status": "… offline"}` when that service is down — render
that honestly (the panel shows "offline", keeps its last sparkline dimmed), never an error.

## DEMO SHIM (so it runs live in the browser with no backend)
Include a `window.fetch` shim that answers `/api/ops/status` with the JSON above, but **mutates it a little on every
call** so the dashboard is visibly alive in preview: bump `cycle`, `usage.total`, `findings_recorded`,
`registries.records`, and `fleet.execution.total` by small random amounts; occasionally tick a loop's `last_cycle` and
push a line to the activity stream. Real backend present → it answers instead; the UI code is identical either way.

## BANNED (will get the output rejected)
- ❌ A static page. If it doesn't poll and update in place, it's wrong.
- ❌ Dead controls, missing panels, "coming soon", TODO, placeholder, `href="#"` no-ops, truncated output.
- ❌ A second CSS system or a forked kit; an external chart CDN; fake/made-up metrics not in the contract.
- ❌ Any write action — this console is **read-only / projection-only / `serves_truth=false`**. No buttons that mutate.

## SELF-AUDIT — run this on your own output and FIX every failure before returning
1. Open it. Within 3s the numbers start moving and the "LIVE" dot pulses; "updated Ns ago" counts.
2. Every sidebar view renders a real, complete panel set — no blank, no placeholder.
3. Each chart draws from rolling history and updates; each status badge colors by health.
4. Kill the data (simulate a failed poll) → it shows "reconnecting", keeps last values dimmed, recovers — never blanks.
5. Search your output for `coming soon`, `TODO`, `placeholder`, `href="#"`, `// ...`, `rest of` → zero matches.
6. Confirm it is read-only: no fetch with a method other than GET, no mutating control.

Output the complete, self-contained, **realtime** Admin Monitor now — every panel, every chart, every live update,
every line. If you run low on space, keep going in the next message until the ENTIRE console is emitted.
