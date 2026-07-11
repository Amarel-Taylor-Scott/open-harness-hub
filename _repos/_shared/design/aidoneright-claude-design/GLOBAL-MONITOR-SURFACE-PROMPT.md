# Global Operations Monitor — the clear Claude Design build prompt

> Paste everything below the line into Claude Design. It builds the **Global Operations Monitor**, the internal
> "mission control" surface for AI Done Right. A working backend already serves the live data
> (`scripts/ops_console_service.py` → `GET /api/ops/status`); the exact shape is in section 4, so you design against
> real data. Companion files in this folder: `DESIGN-ASSETS.md` (the shared kit), `CONSISTENCY-CONTRACT.md` (the family
> rules). Copy from the line below to the end.
>
> *(This is the single monitor prompt for the family: it absorbed the near-duplicate `ADMIN-MONITOR-PROMPT.md`
> — same surface, same live contract — which is retained for lineage under
> `_repos/_shared/archive/legacy/aidoneright/`.)*

---

# Build the Global Operations Monitor (AI Done Right)

## 1. What this is — in one paragraph
A **realtime internal operations console**: one surface that shows, live, the health of the *entire* AI Done Right
system. It is the screen a staff operator leaves open on a wall display. It monitors, in real time: the **product
surfaces + backend services** (up/down), the **autonomous agent loops** (the flywheels that run the factory), the
**registries + records** being produced, **usage** (humans + agents + pipelines), **discovery / research** activity,
the **worker fleet**, and the **security gates**. It is **read-only** — it observes, it never controls. It works by
polling one JSON endpoint every few seconds and **updating the screen in place**.

## 2. The shape — this is a SURFACE, not a single page
Build it as a full app on the shared kit, the same family as the other surfaces:
- A **left-sidebar shell** (`OhAppShell`), **dark-first**, dense and calm.
- **Sidebar views** (each is its own realtime screen):
  `Overview` · `Surfaces & Services` · `Flywheels` · `Fleet` · `Usage` · `Registries` · `Discovery & Research` · `Security`
- A **persistent top strip** visible on every view: a pulsing **LIVE** dot · "updated 2s ago" · an overall **health
  badge** (green / amber / red) · the current flywheel cycle number climbing.
- One self-contained `.html` file (React 18 + in-browser Babel is fine). Output every line — no truncation, no
  placeholders, no "coming soon".

## 3. How "realtime" must work (the core behavior — get this right first)
1. On load, start a **poll loop**: `GET /api/ops/status` **every 3 seconds**.
2. On each response, **update the DOM in place** — never reload the page, never blank it, no flicker.
3. **Animate change:** a number that changed **counts up** to its new value and **flashes** briefly. Status dots
   recolor smoothly.
4. **Keep a rolling history** (the last ~60 polls) in memory and draw **live charts** from it (see views).
5. **A live activity feed** updates as things happen: a new finding, a new flywheel action, a quarantine, a
   conversion — newest on top, animating in, with a relative timestamp.
6. **Connection states:** show `live` normally; on a failed poll show `reconnecting` and **dim the last-known values**
   (keep them on screen); recover automatically when polls resume. Never show an error page.

## 4. The data contract — `GET /api/ops/status` returns exactly this
Render from these fields. Numbers below are a real sample.
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
  "services": { "total":28, "up":28, "surfaces_total":12, "surfaces_up":12,
    "services":[ {"name":"OpenHubForAI app","port":8000,"up":true,"is_surface":true} ] },
  "registries": { "registries":159, "records":159000, "real":2473, "synthetic":156527, "target_per_registry":1000 },
  "usage": { "total":2295, "by_site":{"openhubforai":436,"aidoneright":1859},
             "by_type":{"page":1355,"exposure":921,"conversion":19} },
  "discovery": { "candidates":636, "quarantined":0, "security_gate":"active (ingest quarantine + promotion block, >=high)" },
  "research": { "proposals_backlog":5253, "findings":45128 },
  "fleet": { "ok":true, "tasks":{"by_status":{"done":120,"running":3,"queued":8}}, "execution":{"total":4210} }
}
```
**Degrade honestly:** `usage` or `fleet` may instead be `{"status":"… offline"}` when that service is down — show the
panel as "offline", keep its last chart dimmed, and recover when it returns. Never invent data.

## 5. The views (what each screen shows)
| View | Shows |
|---|---|
| **Overview** | The headline rollup — surfaces up, services up, registries, records, usage, flywheel cycle — each with a sparkline; the health badge; the live activity feed. The one screen that says "is everything OK?" |
| **Surfaces & Services** | A live grid of status chips, one per service from `services.services` (name · port · up/down dot). Product surfaces (`is_surface:true`) marked `◆` and grouped first. Header: `surfaces_up/surfaces_total` and `up/total`. |
| **Flywheels** | One row per loop in `flywheel.loops` (the loop set: Sweep · Status · YC · Propose · Hubs · Health · Autofix · Cleanup): health dot (green if `errors==0`), `last_cycle`, `lag` (cycle − last_cycle), error count. Above: `last_flywheel` + `last_summary`, the cycle climbing live, and `hubs_recent`. |
| **Fleet** | `fleet.tasks.by_status` as a live bar or donut; `fleet.execution.total` ticking; a throughput sparkline. |
| **Usage** | `usage.total` big and live; `usage.by_site` as bars; `usage.by_type` (page / exposure / conversion) with a conversion-rate readout; a usage-over-time area chart from rolling history. |
| **Registries** | `registries` and `records` big; a real-vs-synthetic split bar (`real` / `synthetic`); `target_per_registry`; a records-growth sparkline. |
| **Discovery & Research** | `discovery.candidates` intaken; `discovery.quarantined` (red if > 0); `research.proposals_backlog`; `research.findings`; the `security_gate` status line. |
| **Security** | The governance posture: ingest quarantines + the promotion block, `serves_truth=false`, read-only. Make it obvious the platform is governed. |

## 6. Design rules (family-consistent)
- Use the **shared kit** only (`OhAppShell`, `OhRollup`, `OhTable`, `oh-card`, `oh-badge`, mono font for figures) — do
  not fork it or add a second CSS system. **Dark-first**, dense, calm.
- **One accent** (`#5a6b87`, ops slate). Reserve **green / amber / red** for health and status only.
- **Charts are token-built inline SVG** (sparklines + area charts) — no external chart library, no external CDN. The
  file stays self-contained.

## 7. Demo shim (so it runs live in preview with no backend)
Add a `window.fetch` shim that answers `/api/ops/status` with the section-4 JSON **but mutates it a little each call** —
bump `cycle`, `usage.total`, `findings_recorded`, `registries.records`, `fleet.execution.total` by small random
amounts; occasionally tick a loop's `last_cycle` and push a line to the activity feed; rarely flip one service to
down and back. With a real backend present it answers instead — the UI code is identical either way. This makes the
dashboard visibly *alive* in preview.

## 8. Acceptance — it is done when ALL of these pass (check before returning)
- [ ] Within 3s of opening, numbers are moving and the **LIVE** dot pulses; "updated Ns ago" counts up.
- [ ] All 8 sidebar views render complete, real panels — no blanks, no placeholders, no "coming soon".
- [ ] Charts draw from rolling history and keep updating; status dots/badges recolor by health.
- [ ] Simulating a failed poll shows **reconnecting**, keeps last values dimmed, and recovers — never blanks, never errors.
- [ ] It is **read-only**: no fetch other than GET, no button that mutates anything.
- [ ] One self-contained file; shared kit only; no external CDN; a search of the output for `coming soon` / `TODO` /
      `placeholder` / `href="#"` / `// ...` returns nothing.

Output the complete, self-contained, realtime Global Operations Monitor now. If you run low on space, continue in the
next message until the ENTIRE surface is emitted.
