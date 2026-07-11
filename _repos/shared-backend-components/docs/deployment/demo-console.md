# Baltor demo console — operator guide

The "view everything" surface: a single dark, dependency-free console that plays back a **real**
Baltor pipeline run end-to-end, plus a human-review queue. Linked from the Baltor site nav
("Live demo" / "Review queue"). For the 1-minute tour of the whole app, see
[`docs/baltor-full-app-quickstart.md`](../baltor-full-app-quickstart.md).

## Run it

```bash
cd _repos/baltor/frontend
python3 -m http.server 8000
# open http://localhost:8000/demo-console.html
```

Serve over HTTP — browsers block `file://` `fetch()`, and the pages load their data via fetch. The
data files are committed and kept in sync by a drift-check (`scripts/demo_run_export.py --check-fresh`,
gated in CI); regenerate them with `python3 scripts/demo_run_export.py --write`.

## What each surface shows

### `demo-console.html` — the pipeline console
- **Corpus selector**: **Acme Billing** (synthetic engineering KB) or **CFPB sample** (synthetic
  consumer-finance KB). Both run a real, deterministic, **offline** motion. The live CFPB API
  (`scripts/demo_cfpb_context_pack.py`) is a *separate* path and is not what this plays.
- **▶ Run**: animates the 7 stages (Source → Reconciliation → Anti-Fragility → Enhancement →
  Optimization → Consumption → Verification rail). This is a **deterministic replay of a real run**
  (`scripts/demo_run_export.py` runs the actual engines and writes `demo-run.json`) — not a fake loader.
- **Context graph**: nodes/edges from the run. The stale doc pulses red, the authority is gold, the
  `CONTRADICTS` edge is red-dashed. **Click a node** → its object detail, claims, **version timeline**
  (v1 stale → v2 proposed-pending-review), and a policy-gated **Expand source** (real excerpt) /
  **Try restricted** (deny reason, no raw bytes).
- **Lift bars**: the condition×model matrix — governed pack ≫ no-context, harness ≥ pack, and a raw
  dump *underperforms* the pack (raw ≠ lift).

### `reviews.html` — human-in-the-loop queue
The steward-review-requests the context-object swarm routed across both corpora (each conforming to
`schemas/governance/steward-review-request.schema.json`), with the proposed (not applied) fix
(3→5 / 30→10) and evidence handles. **Approve / reject / needs-info** record a
`steward-review-decision` **client-side only** — decisions are demo-local, there is **no server and no
canonical mutation**; applying a fix stays a separate human/policy-gated step (the promotion boundary).

## Data files (generated, drift-checked)
`demo-run.json` (acme) · `demo-run.cfpb.json` (cfpb) · `review-queue.json` · `version-timeline.json`.
Regenerate all: `python3 scripts/demo_run_export.py --write`. The committed copies must byte-match the
export — `scripts/check_demo_console_links.py` and `demo_run_export --check-fresh` enforce this.

## Honest scope
Synthetic data only (no real PII/complaints). LLM use is a seam (deterministic mock by default; a
`model_gateway` route only phrases, never changes facts). Everything shown is produced by the same
modules the flywheel watchdog keeps green.
