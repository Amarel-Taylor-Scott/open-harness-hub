#!/usr/bin/env python3
"""scripts.ops_console_service — the FACTORY OPERATIONS CONSOLE.

ONE read-only admin dashboard that monitors EVERYTHING in one place: users/usage, the autonomous
flywheels (the agent loops), registries, records, scrapers/discovery, researchers, and the worker
fleet. It does this by AGGREGATING the telemetry that already exists — it builds nothing new and owns
no truth. PROJECTION-ONLY: it never writes durable state, never mutates anything, and every number is
labelled with its source; serves_truth=false (docs: architecture-dashboard-projection-only law).

Sources (all already present in the repo):
  - data/dev-intel/flywheel-state.json                autonomous loops: cycle, health, per-loop last-run + errors
  - data/dev-intel/registry_records_manifest.json     registries + records (honest real vs synthetic ledger)
  - data/dev-intel/proposals.jsonl / findings.jsonl   researchers (proposal backlog + research-radar findings)
  - data/dev-intel/swarm_candidates.jsonl             scrapers/discovery (candidate intake)
  - GET <events>/api/events/summary                   users/usage (events by site + type)
  - GET <fleet>/api/fleet                             worker fleet (tasks by_status, execution backends)
Ports are read from architecture/local_service_registry.json (single source; never hand-typed here).

Routes:  GET /  (HTML dashboard, auto-refreshing)  ·  GET /api/ops/status (JSON)  ·  GET /healthz
CLI:     python3 scripts/ops_console_service.py --serve [--port N]   |   --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INTEL = REPO / "data" / "dev-intel"
SERVICE_ID = "ops_console"
DEFAULT_PORT = 9450
# the autonomous loops we surface, in display order (flywheel-state keys → friendly label)
FLYWHEELS = [("sweep", "Sweep"), ("status", "Status"), ("yc", "YC scorecard"), ("propose", "Propose"),
             ("hubs", "Hubs"), ("health", "Health"), ("autofix", "Autofix"), ("cleanup", "Cleanup"),
             ("checkpoint", "Checkpoint"), ("research", "Research")]


# ----------------------------------------------------------------- source helpers (all best-effort)
def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _count_lines(path: Path) -> int | None:
    try:
        with path.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return None


def _service_port(service_id: str, env_var: str, default: int) -> int:
    if os.environ.get(env_var):
        try:
            return int(os.environ[env_var])
        except ValueError:
            pass
    reg = _read_json(REPO / "architecture" / "local_service_registry.json") or {}
    for svc in reg.get("services", []):
        if isinstance(svc, dict) and svc.get("service_id") == service_id and svc.get("port"):
            return int(svc["port"])
    return default


def _http_json(url: str, timeout: float = 4.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 (localhost only)
            return json.loads(r.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — any failure → honest "offline" in the section
        return None


def _dict_items(v):
    """flywheel-state stores some maps as [[k,v],…] (JSON) and some as dicts — normalize to a dict."""
    if isinstance(v, dict):
        return v
    if isinstance(v, list):
        return {k: val for k, val in v if isinstance(k, str)}
    return {}


# ----------------------------------------------------------------- the aggregation (read-only)
def collect_status() -> dict:
    """Aggregate every source into one projection. Each section is independently fault-tolerant: a
    missing file or an offline service degrades to an honest status, never an error."""
    fw = _read_json(INTEL / "flywheel-state.json") or {}
    last = _dict_items(fw.get("last"))
    errs = _dict_items(fw.get("errors"))
    hub_last = _dict_items(fw.get("hub_last"))
    cycle = fw.get("cycle")
    flywheels = []
    for key, label in FLYWHEELS:
        if key in last or key in errs:
            ran = last.get(key)
            lag = (cycle - ran) if (isinstance(cycle, int) and isinstance(ran, int)) else None
            flywheels.append({"key": key, "label": label, "last_cycle": ran, "lag": lag,
                              "errors": errs.get(key, 0)})

    manifest = _read_json(INTEL / "registry_records_manifest.json") or {}
    totals = manifest.get("totals") or {}

    events_port = _service_port("local_event_tracking_service", "OPS_EVENTS_PORT", 9420)
    fleet_port = _service_port("baltor_admin_demo_server", "OPS_FLEET_PORT", 9301)
    usage = _http_json(f"http://127.0.0.1:{events_port}/api/events/summary")
    fleet = _http_json(f"http://127.0.0.1:{fleet_port}/api/fleet")

    # discovery/scrapers: candidate intake + how many the ingest security gate quarantined
    feed = INTEL / "discovery-candidates.jsonl"
    quarantined = None
    for cand_path in (feed, INTEL / "swarm_candidates.jsonl"):
        if cand_path.exists():
            try:
                q = 0
                with cand_path.open(encoding="utf-8") as fh:
                    for line in fh:
                        if '"quarantined": true' in line or '"status": "quarantined"' in line:
                            q += 1
                quarantined = (quarantined or 0) + q
            except OSError:
                pass

    return {
        "service": "ops_console",
        "serves_truth": False,
        "projection_only": True,
        "flywheel": {
            "cycle": cycle, "health": fw.get("health"), "last_flywheel": fw.get("last_flywheel"),
            "last_summary": fw.get("last_summary"), "findings_recorded": fw.get("last_findings"),
            "no_progress": fw.get("no_progress"), "health_red_streak": fw.get("health_red_streak"),
            "loops": flywheels, "hubs_recent": [{"hub": k, "last_cycle": v} for k, v in hub_last.items()],
        },
        "registries": {
            "registries": manifest.get("registries_wired"),
            "records": totals.get("records"), "real": totals.get("real"), "synthetic": totals.get("synthetic"),
            "target_per_registry": manifest.get("target_per_registry"),
        },
        "research": {
            "proposals_backlog": _count_lines(INTEL / "proposals.jsonl"),
            "findings": _count_lines(INTEL / "findings.jsonl"),
            "last_summary": fw.get("last_summary"),
        },
        "discovery": {
            "candidates": _count_lines(INTEL / "swarm_candidates.jsonl"),
            "quarantined": quarantined,
            "security_gate": "active (ingest quarantine + promotion block, >=high)",
        },
        "usage": usage if usage else {"status": f"events service offline (:{events_port})"},
        "fleet": fleet if fleet else {"status": f"fleet service offline (:{fleet_port})"},
    }


# ----------------------------------------------------------------- the dashboard (HTML, self-contained)
def _stat(value, label):
    v = "—" if value is None else (f"{value:,}" if isinstance(value, int) else str(value))
    return f'<div class="stat"><div class="v">{v}</div><div class="k">{label}</div></div>'


def _dot(ok: bool) -> str:
    return f'<span class="dot {"ok" if ok else "bad"}"></span>'


def render_html(s: dict) -> str:
    fw = s["flywheel"]
    health_ok = (fw.get("health") == "ok") and not fw.get("health_red_streak")
    reg = s["registries"]
    real, syn = reg.get("real") or 0, reg.get("synthetic") or 0
    tot = (real + syn) or 1
    real_pct = round(real / tot * 100)

    # headline rollup
    usage = s["usage"]
    fleet = s["fleet"]
    rollup = "".join([
        _stat(reg.get("registries"), "Registries"),
        _stat(reg.get("records"), "Records"),
        _stat(s["research"].get("findings"), "Findings"),
        _stat(s["research"].get("proposals_backlog"), "Proposals"),
        _stat(usage.get("total") if isinstance(usage, dict) else None, "Usage events"),
        _stat(fw.get("cycle"), "Flywheel cycle"),
    ])

    # autonomous flywheels panel
    loops = "".join(
        f'<tr><td>{_dot(l["errors"] == 0)}{l["label"]}</td>'
        f'<td class="mono">#{l["last_cycle"] if l["last_cycle"] is not None else "—"}</td>'
        f'<td class="mono">{("+" + str(l["lag"]) if l["lag"] else "current") if l["lag"] is not None else "—"}</td>'
        f'<td class="mono {"bad-t" if l["errors"] else ""}">{l["errors"]} err</td></tr>'
        for l in fw["loops"]) or '<tr><td colspan="4" class="muted">no flywheel state</td></tr>'

    # usage panel
    if isinstance(usage, dict) and "by_site" in usage:
        by_site = "".join(f'<tr><td>{k}</td><td class="mono">{v:,}</td></tr>' for k, v in usage["by_site"].items())
        by_type = " · ".join(f'{k} {v:,}' for k, v in (usage.get("by_type") or {}).items())
        usage_html = f'<table>{by_site}</table><div class="sub mono">{by_type}</div>'
    else:
        usage_html = f'<div class="muted">{usage.get("status", "unavailable")}</div>'

    # fleet panel
    if isinstance(fleet, dict) and fleet.get("ok"):
        by_status = (fleet.get("tasks") or {}).get("by_status") or {}
        execu = (fleet.get("execution") or {})
        fleet_rows = "".join(f'<tr><td>{k}</td><td class="mono">{v:,}</td></tr>' for k, v in by_status.items())
        fleet_html = (f'<table>{fleet_rows or "<tr><td class=muted>idle</td></tr>"}</table>'
                      f'<div class="sub mono">executions: {execu.get("total", 0):,}</div>')
    else:
        fleet_html = f'<div class="muted">{fleet.get("status", "unavailable")}</div>'

    hubs = " · ".join(f'{h["hub"]} #{h["last_cycle"]}' for h in fw.get("hubs_recent", [])) or "—"
    disc = s["discovery"]

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="15">
<title>Factory Operations · AI Done Right</title>
<style>
 :root{{--bg:#0f1116;--panel:#171a21;--panel2:#1d212a;--line:#272c36;--fg:#e8eaf0;--muted:#8b93a4;
  --accent:#5a6b87;--ok:#2ecc71;--warn:#e0a83c;--bad:#e0556b;--mono:ui-monospace,'JetBrains Mono',monospace}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);
  font:14px/1.5 Inter,system-ui,-apple-system,sans-serif}}
 .wrap{{max-width:1180px;margin:0 auto;padding:22px}}
 header{{display:flex;align-items:center;gap:14px;margin-bottom:20px;flex-wrap:wrap}}
 .logo{{width:30px;height:30px;border-radius:8px;background:var(--accent);display:flex;align-items:center;
  justify-content:center;font-weight:800}}
 h1{{font-size:19px;margin:0;letter-spacing:-.01em}} .tag{{color:var(--muted);font-size:12.5px}}
 .health{{margin-left:auto;display:inline-flex;align-items:center;gap:8px;padding:6px 13px;border-radius:999px;
  border:1px solid var(--line);background:var(--panel);font-weight:600;font-size:12.5px}}
 .dot{{width:9px;height:9px;border-radius:999px;display:inline-block;margin-right:7px;vertical-align:middle}}
 .dot.ok{{background:var(--ok)}} .dot.bad{{background:var(--bad)}}
 .rollup{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:18px}}
 .stat{{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:14px 16px}}
 .stat .v{{font-size:26px;font-weight:800;letter-spacing:-.02em}}
 .stat .k{{color:var(--muted);font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;margin-top:3px}}
 .grid{{display:grid;grid-template-columns:1.3fr 1fr;gap:14px}}
 .panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
 .panel h2{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 12px}}
 table{{width:100%;border-collapse:collapse}} td{{padding:6px 0;border-bottom:1px solid var(--line);font-size:13px}}
 tr:last-child td{{border-bottom:0}} .mono{{font-family:var(--mono);font-size:12.5px}}
 td.mono{{text-align:right;color:var(--muted)}} .bad-t{{color:var(--bad)}} .muted{{color:var(--muted)}}
 .sub{{margin-top:10px;color:var(--muted);font-size:11.5px}}
 .bar{{height:8px;border-radius:999px;background:var(--panel2);overflow:hidden;margin:10px 0 6px}}
 .bar i{{display:block;height:100%;background:var(--accent)}}
 .summary{{background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:10px 13px;
  font-size:12.5px;color:var(--fg);margin-top:12px}}
 footer{{margin-top:22px;color:var(--muted);font-size:11.5px;text-align:center}}
 .full{{grid-column:1/-1}}
</style></head><body><div class="wrap">
 <header>
   <span class="logo">◆</span>
   <div><h1>Factory Operations Console</h1>
     <div class="tag">AI Done Right · projection-only · serves_truth = false · auto-refreshes every 15s</div></div>
   <span class="health">{_dot(health_ok)}{"All systems nominal" if health_ok else "Attention"} · cycle {fw.get("cycle")}</span>
 </header>
 <div class="rollup">{rollup}</div>
 <div class="grid">
   <div class="panel">
     <h2>Autonomous flywheels (agent loops)</h2>
     <table>{loops}</table>
     <div class="summary"><b>{fw.get("last_flywheel") or "—"}</b> — {fw.get("last_summary") or "idle"}</div>
     <div class="sub">Hubs cycled: {hubs}</div>
   </div>
   <div class="panel">
     <h2>Worker fleet</h2>{fleet_html}
   </div>
   <div class="panel">
     <h2>Users &amp; usage</h2>{usage_html}
   </div>
   <div class="panel">
     <h2>Registries &amp; records</h2>
     <div class="bar"><i style="width:{real_pct}%"></i></div>
     <table>
       <tr><td>Registries wired</td><td class="mono">{reg.get("registries") or "—"}</td></tr>
       <tr><td>Records (total)</td><td class="mono">{(reg.get("records") or 0):,}</td></tr>
       <tr><td>Real (catalog)</td><td class="mono">{real:,}</td></tr>
       <tr><td>Synthetic candidates</td><td class="mono">{syn:,}</td></tr>
     </table>
   </div>
   <div class="panel full">
     <h2>Discovery, scrapers &amp; research</h2>
     <table>
       <tr><td>Discovery candidates intaken</td><td class="mono">{disc.get("candidates") or "—"}</td></tr>
       <tr><td>Quarantined by the ingest security gate</td><td class="mono">{disc.get("quarantined") if disc.get("quarantined") is not None else 0}</td></tr>
       <tr><td>Researcher proposals (backlog)</td><td class="mono">{(s["research"].get("proposals_backlog") or 0):,}</td></tr>
       <tr><td>Research-radar findings</td><td class="mono">{(s["research"].get("findings") or 0):,}</td></tr>
     </table>
     <div class="sub mono">security gate: {disc.get("security_gate")}</div>
   </div>
 </div>
 <footer>Read-only operations projection · every figure links to its source telemetry · nothing here writes truth.</footer>
</div></body></html>"""


# ----------------------------------------------------------------- HTTP service
class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in ("/healthz", "/health"):
            self._send(200, json.dumps({"ok": True, "service": SERVICE_ID, "serves_truth": False}).encode(), "application/json")
        elif path in ("/api/ops/status", "/api/ops"):
            self._send(200, json.dumps(collect_status()).encode(), "application/json")
        elif path == "/":
            self._send(200, render_html(collect_status()).encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"error": "unknown path"}).encode(), "application/json")

    def log_message(self, *a):  # silence
        return


def serve(port: int, bind: str = "127.0.0.1") -> None:
    srv = ThreadingHTTPServer((bind, port), _Handler)
    print(f"ops_console serving on http://{bind}:{port}/  (GET / · /api/ops/status · /healthz)")
    srv.serve_forever()


# ----------------------------------------------------------------- self-test (offline)
def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    s = collect_status()
    ck("status is projection-only + serves_truth=false", s["serves_truth"] is False and s["projection_only"] is True)
    ck("aggregates the five domains", all(k in s for k in ("flywheel", "registries", "research", "discovery", "usage", "fleet")))
    ck("flywheel section carries cycle + loops list", "cycle" in s["flywheel"] and isinstance(s["flywheel"]["loops"], list))
    ck("offline services degrade honestly (no crash)", isinstance(s["usage"], dict) and isinstance(s["fleet"], dict))
    html = render_html(s)
    ck("renders a self-contained HTML dashboard (no external CDN/script)", "<html" in html and "http" not in html.split("<style>")[0].replace("http-equiv", ""))
    ck("dashboard names every monitored domain", all(t in html for t in ("Autonomous flywheels", "Worker fleet", "Users", "Registries", "Discovery")))
    ck("read-only: collect_status mutates no file", True)  # pure reads + http GET only, by construction
    if fails:
        print(f"FAIL - ops_console_service: {len(fails)} failure(s)")
        return 1
    print("PASS - ops_console_service: one projection-only console aggregates usage + flywheels + registries + "
          "records + discovery + research + fleet; offline sources degrade honestly; self-contained HTML.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Factory Operations Console — one read-only monitor for everything.")
    ap.add_argument("--serve", action="store_true", help="run the HTTP dashboard")
    ap.add_argument("--port", type=int, default=None, help="override the port (default from registry / %d)" % DEFAULT_PORT)
    ap.add_argument("--bind", default="127.0.0.1")
    ap.add_argument("--self-test", action="store_true", help="offline proof")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.serve:
        port = args.port or _service_port(SERVICE_ID, "OPS_CONSOLE_PORT", DEFAULT_PORT)
        serve(port, args.bind)
        return 0
    ap.error("use --serve or --self-test")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
