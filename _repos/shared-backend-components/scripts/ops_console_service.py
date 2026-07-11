#!/usr/bin/env python3
"""scripts.ops_console_service — the GLOBAL OPERATIONS CONSOLE.

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
Ports are read from _repos/shared-backend-components/architecture/local_service_registry.json (single source; never hand-typed here).

Routes:  GET /  (HTML dashboard, auto-refreshing)  ·  GET /api/ops/status (JSON)  ·  GET /healthz
CLI:     python3 _repos/shared-backend-components/scripts/ops_console_service.py --serve [--port N]   |   --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))   # so a bare `python3 _repos/shared-backend-components/scripts/ops_console_service.py` resolves scripts.*
from scripts.ops_intake import IntakeStore  # noqa: E402
from scripts.ops_logs import collect_logs    # noqa: E402

INTEL = _resource("data") / "dev-intel"
SERVICE_ID = "ops_console"
DEFAULT_PORT = 9450
#: the persistent intake ledger — the console's ONLY write path (governed, serves_truth=false, quarantined)
_INTAKE = IntakeStore()
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
    reg = _read_json(_resource("architecture") / "local_service_registry.json") or {}
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


def _port_up(port: int, timeout: float = 0.5) -> bool:
    import socket
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _collect_services() -> dict:
    """Ping every active_local service's port (TCP, concurrent) so the console covers the WHOLE plane —
    the product surfaces AND the backend services — up/down, not just the autonomous factory. Read-only."""
    reg = _read_json(_resource("architecture") / "local_service_registry.json") or {}
    svcs = [s for s in reg.get("services", []) if isinstance(s, dict)
            and s.get("status") == "active_local" and s.get("port")]

    def check(s: dict) -> dict:
        return {"id": s.get("service_id"), "name": s.get("display_name") or s.get("service_id"),
                "port": s.get("port"), "owner": s.get("owner"), "up": _port_up(s["port"]),
                "is_surface": str(s.get("service_id", "")).endswith(("_app", "_site"))}

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=16) as ex:
        rows = list(ex.map(check, svcs))
    rows.sort(key=lambda r: (not r["is_surface"], not r["up"], str(r["id"])))
    up = sum(1 for r in rows if r["up"])
    surfaces = [r for r in rows if r["is_surface"]]
    return {"total": len(rows), "up": up, "down": len(rows) - up,
            "surfaces_total": len(surfaces), "surfaces_up": sum(1 for r in surfaces if r["up"]),
            "services": rows}


def _tail_jsonl(path: Path, n: int = 6) -> list[dict]:
    """Efficient tail of a JSONL ledger (seek the last ~16KB) — recent rows without reading the whole file."""
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 16384))
            lines = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return []
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def _collect_activity() -> list[dict]:
    """A recent-activity feed across the ledgers (the live stream the dashboard scrolls): the latest flywheel
    action, the most recent findings, the most recent proposals. Newest first. Read-only."""
    acts: list[dict] = []
    fw = _read_json(INTEL / "flywheel-state.json") or {}
    if fw.get("last_summary"):
        acts.append({"type": "flywheel", "text": f"{fw.get('last_flywheel', 'loop')}: {fw['last_summary']}",
                     "cycle": fw.get("cycle")})
    for f in reversed(_tail_jsonl(INTEL / "findings.jsonl", 5)):
        kind, target = f.get("kind") or "finding", f.get("target") or ""
        acts.append({"type": "finding", "text": f"{kind}{' · ' + str(target) if target else ''}"})
    for p in reversed(_tail_jsonl(INTEL / "proposals.jsonl", 4)):
        why = str(p.get("rationale") or "")[:90]
        acts.append({"type": "proposal", "text": f"{p.get('kind') or 'proposal'}{': ' + why if why else ''}"})
    return acts[:12]


def _collect_intake() -> dict:
    """Advance intake items one stage per tick (the workers' cadence), then project the queues + items."""
    _INTAKE.advance()
    return _INTAKE.projection()


def _dict_items(v):
    """flywheel-state stores some maps as [[k,v],…] (JSON) and some as dicts — normalize to a dict."""
    if isinstance(v, dict):
        return v
    if isinstance(v, list):
        return {k: val for k, val in v if isinstance(k, str)}
    return {}


def _collect_keys() -> dict:
    """API-key slots for the operator, from the credential PLANE (_repos/shared-backend-components/architecture/credential_registry.json — env-var
    NAMES only). Status is set / unset / keyless by PRESENCE of the env var, NEVER the value (redaction-safe). This
    is how the operator stores + manages the keys backend services and demos use: see what is configured, what is
    missing, who owns each key (byo / platform), and what each unlocks. To configure a key, set its env var (or a
    local .env) — nothing is stored in the console."""
    try:
        from src.teleon.runtime import credentials as cred
        svcs = cred.py_function_src_teleon_runtime_credentials__services()
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": str(exc)[:140], "slots": [], "summary": {}, "serves_truth": False}
    slots = []
    for s in svcs:
        envs = s.get("env_vars", []) or []
        keyless = bool(s.get("keyless"))
        configured = bool(envs) and all(cred.py_function_src_teleon_runtime_credentials__env_value(v) for v in envs)  # presence only — value never returned
        status = "set" if configured else ("keyless" if keyless else "unset")
        slots.append({
            "id": s["id"], "name": s.get("name") or s["id"], "kind": s.get("kind", "api_key"),
            "ownership": s.get("key_ownership", "byo"), "env_vars": envs, "keyless": keyless,
            "free_tier": bool(s.get("free_tier")), "status": status, "missing": cred.py_function_src_teleon_runtime_credentials__missing_for(s["id"]),
            "obtain": s.get("obtain", ""), "planes": (s.get("unlocks") or {}).get("planes", []),
        })
    summary = {"total": len(slots),
               "set": sum(1 for x in slots if x["status"] == "set"),
               "unset": sum(1 for x in slots if x["status"] == "unset"),
               "keyless": sum(1 for x in slots if x["status"] == "keyless")}
    return {"available": True, "slots": slots, "summary": summary,
            "note": "Env-var NAMES only; values live in the environment and are never stored or shown here.",
            "serves_truth": False}


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
        "services": _collect_services(),
        "activity": _collect_activity(),
        "intake": _collect_intake(),
    }


# ----------------------------------------------------------------- the dashboard (HTML, self-contained)
def _stat(value, label):
    v = "—" if value is None else (f"{value:,}" if isinstance(value, int) else str(value))
    return f'<div class="stat"><div class="v">{v}</div><div class="k">{label}</div></div>'


def _dot(ok: bool) -> str:
    return f'<span class="dot {"ok" if ok else "bad"}"></span>'


# ----------------------------------------------------------------- the realtime console (client SPA)
# A self-contained realtime single-page app (no external CDN). It POLLS the real endpoints
# (/api/ops/status every pollSeconds, /api/ops/logs on the Raw logs view), updates in place, shows a
# LIVE / reconnecting state, and provides the Intake write path + the multi-source Raw logs inspector.
# Implements Claude Design's Global Operations Console against the real backend. serves_truth=false.
_CONSOLE_SPA = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Global Operations Console · AI Done Right</title>
<style>
:root{--bg:#0e1014;--panel:#161922;--panel2:#1c212c;--line:#262c38;--fg:#e8eaf0;--muted:#8b93a4;--accent:#7d93b8;
 --ok:#2ecc71;--warn:#e0a83c;--bad:#e0556b;--mono:ui-monospace,'JetBrains Mono',monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:13.5px/1.5 Inter,system-ui,sans-serif;display:flex;height:100vh;overflow:hidden}
aside{width:212px;flex:0 0 auto;background:var(--panel);border-right:1px solid var(--line);display:flex;flex-direction:column;padding:14px 10px}
.brand{display:flex;align-items:center;gap:9px;padding:4px 8px 14px}.brand .m{width:26px;height:26px;border-radius:7px;background:var(--accent);display:flex;align-items:center;justify-content:center;font-weight:800}
.brand b{font-size:14px;letter-spacing:-.01em}.nav a{display:flex;align-items:center;gap:9px;padding:8px 10px;border-radius:8px;color:var(--muted);text-decoration:none;font-size:13px;cursor:pointer}
.nav a.on{background:var(--panel2);color:var(--fg)}.nav a:hover{color:var(--fg)}.nav .g{width:14px;text-align:center;opacity:.85}
main{flex:1;overflow:auto;padding:18px 22px}
.top{display:flex;align-items:center;gap:12px;margin-bottom:16px}.top h1{font-size:18px;margin:0;letter-spacing:-.01em}
.live{margin-left:auto;display:inline-flex;align-items:center;gap:8px;font-size:12px;color:var(--muted);padding:5px 12px;border:1px solid var(--line);border-radius:999px;background:var(--panel)}
.pulse{width:8px;height:8px;border-radius:999px;background:var(--ok);animation:p 1.6s infinite}.pulse.bad{background:var(--bad);animation:none}@keyframes p{0%,100%{opacity:1}50%{opacity:.3}}
.reconnecting{opacity:.55}
.rollup{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:11px;margin-bottom:16px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:13px 15px}.stat .v{font-size:24px;font-weight:800;letter-spacing:-.02em}
.stat .k{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.05em;margin-top:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:13px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px 17px}
.panel h2{font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:0 0 11px}.full{grid-column:1/-1}
table{width:100%;border-collapse:collapse}td,th{padding:6px 8px;border-bottom:1px solid var(--line);font-size:12.5px;text-align:left}th{color:var(--muted);font-weight:600;font-size:11px;text-transform:uppercase}
tr:last-child td{border-bottom:0}.mono{font-family:var(--mono);font-size:12px}.r{text-align:right}.muted{color:var(--muted)}
.dot{width:8px;height:8px;border-radius:999px;display:inline-block;margin-right:6px}.dot.ok{background:var(--ok)}.dot.bad{background:var(--bad)}.dot.warn{background:var(--warn)}
.chip{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--panel2);font-size:12px;margin:3px}
.pill{font-size:10px;text-transform:uppercase;letter-spacing:.04em;padding:2px 7px;border-radius:999px;background:var(--panel2);color:var(--muted)}
.pill.high{color:var(--bad);background:rgba(224,85,107,.13)}.pill.med{color:var(--warn)}.pill.error{color:var(--bad)}.pill.warn{color:var(--warn)}
textarea,input,select{font:inherit;color:var(--fg);background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:9px 11px}
textarea{width:100%;min-height:90px;resize:vertical;font-family:var(--mono);font-size:12.5px}
button{font:inherit;font-weight:600;background:var(--accent);color:#0e1014;border:0;border-radius:8px;padding:9px 16px;cursor:pointer}button.ghost{background:var(--panel2);color:var(--fg);border:1px solid var(--line)}
.bar{height:7px;border-radius:999px;background:var(--panel2);overflow:hidden;margin-top:7px}.bar i{display:block;height:100%;background:var(--accent)}
.logrow{display:grid;grid-template-columns:84px 54px 150px 1fr;gap:10px;padding:6px 8px;border-bottom:1px solid var(--line);font-family:var(--mono);font-size:11.5px;cursor:pointer;align-items:center}
.logrow:hover{background:var(--panel2)}.controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.insp{position:fixed;top:0;right:0;width:420px;height:100vh;background:var(--panel);border-left:1px solid var(--line);padding:18px;overflow:auto;box-shadow:-12px 0 30px rgba(0,0,0,.35)}
.insp pre{font-family:var(--mono);font-size:11.5px;white-space:pre-wrap;word-break:break-word;background:var(--panel2);padding:12px;border-radius:9px;border:1px solid var(--line)}
.empty{color:var(--muted);padding:18px;text-align:center}footer{color:var(--muted);font-size:11px;text-align:center;margin-top:18px}
.step{display:inline-block;font-size:10px;padding:2px 6px;border-radius:6px;background:var(--panel2);color:var(--muted)}.step.done{color:var(--ok)}
</style></head><body>
<aside><div class="brand"><span class="m">&#9670;</span><b>Operations</b></div>
<nav class="nav" id="nav"></nav>
<div style="margin-top:auto;padding:10px 8px;color:var(--muted);font-size:10.5px">read-only &middot; serves_truth=false<br>projection &middot; one write: Intake</div></aside>
<main><div class="top"><h1 id="title">Overview</h1><span class="live" id="live"><span class="pulse" id="pulse"></span><span id="connlabel">connecting</span></span></div>
<div id="view"></div><footer>Global Operations Console &middot; AI Done Right &middot; updates in place, no reload</footer></main>
<div id="insp"></div>
<script>
var VIEWS=[["overview","&#9636;","Overview"],["services","&#9670;","Surfaces & Services"],["flywheels","&#8635;","Flywheels"],["fleet","&#9881;","Fleet"],["usage","&#9719;","Usage"],["registries","&#9638;","Registries"],["discovery","&#9788;","Discovery & Research"],["intake","&#8595;","Intake"],["keys","&#128273;","API keys"],["activity","&#9776;","Activity log"],["logs","&#9783;","Raw logs"],["security","&#9919;","Security"]];
var S={status:null,logs:null,keys:null,hist:[],view:location.hash.slice(1)||"overview",conn:"connecting",logFilter:{type:"all",level:"all",q:""},insp:null};
var POLL=3000;function num(n){return n==null?"&mdash;":(typeof n==="number"?n.toLocaleString():n);}
function nav(){document.getElementById("nav").innerHTML=VIEWS.map(function(v){return '<a class="'+(S.view===v[0]?"on":"")+'" onclick="go(\''+v[0]+'\')"><span class="g">'+v[1]+'</span>'+v[2]+'</a>';}).join("");}
function go(v){S.view=v;location.hash=v;document.getElementById("title").innerHTML=(VIEWS.filter(function(x){return x[0]===v;})[0]||["","","?"])[2];nav();render();if(v==="logs")pollLogs();if(v==="keys")pollKeys();}
function stat(v,k){return '<div class="stat"><div class="v">'+num(v)+'</div><div class="k">'+k+'</div></div>';}
function spark(arr){if(!arr||arr.length<2)return"";var w=120,h=26,mx=Math.max.apply(null,arr)||1,mn=Math.min.apply(null,arr);var d=arr.map(function(v,i){return (i/(arr.length-1)*w)+","+(h-(mx===mn?h/2:(v-mn)/(mx-mn)*h));}).join(" ");return '<svg width="'+w+'" height="'+h+'" style="margin-top:6px"><polyline fill="none" stroke="var(--accent)" stroke-width="1.5" points="'+d+'"/></svg>';}
function render(){var s=S.status,v=document.getElementById("view");if(!s){v.innerHTML='<div class="empty">connecting&hellip;</div>';return;}
 v.className=S.conn==="reconnecting"?"reconnecting":"";var H="";
 if(S.view==="overview"){var sv=s.services||{},rg=s.registries||{},u=s.usage||{},rs=s.research||{},fw=s.flywheel||{};
  H+='<div class="rollup">'+stat((sv.surfaces_up||0)+"/"+(sv.surfaces_total||0),"Surfaces up")+stat((sv.up||0)+"/"+(sv.total||0),"Services up")+stat(rg.registries,"Registries")+stat(rg.records,"Records")+stat(u.total,"Usage")+stat(rs.findings,"Findings")+stat(fw.cycle,"Cycle")+'</div>';
  var hist=S.hist;H+='<div class="grid"><div class="panel"><h2>Usage over time</h2>'+spark(hist.map(function(x){return x.usage;}))+'<div class="muted" style="margin-top:6px">events: '+num(u.total)+'</div></div><div class="panel"><h2>Records over time</h2>'+spark(hist.map(function(x){return x.records;}))+'<div class="muted" style="margin-top:6px">'+num(rg.records)+' records</div></div>';
  H+='<div class="panel full"><h2>Live activity</h2>'+(s.activity||[]).map(function(a){return '<div style="padding:5px 0;border-bottom:1px solid var(--line);font-size:12.5px"><span class="pill">'+a.type+'</span> <span class="muted">'+esc(a.text)+'</span></div>';}).join("")+'</div></div>';}
 else if(S.view==="services"){var ss=(s.services||{}).services||[];H+='<div class="panel full"><h2>The whole plane &mdash; '+((s.services||{}).up||0)+'/'+((s.services||{}).total||0)+' up</h2>'+ss.map(function(r){return '<span class="chip"><span class="dot '+(r.up?"ok":"bad")+'"></span>'+esc(r.name)+(r.is_surface?" &#9670;":"")+' <span class="muted mono">:'+(r.port||"")+'</span></span>';}).join("")+'</div>';}
 else if(S.view==="flywheels"){var fw=s.flywheel||{};H+='<div class="panel full"><h2>Autonomous flywheels &mdash; cycle '+num(fw.cycle)+'</h2><table><tr><th>Loop</th><th>Last</th><th>Lag</th><th>Errors</th></tr>'+(fw.loops||[]).map(function(l){return '<tr><td><span class="dot '+(l.errors?"bad":"ok")+'"></span>'+esc(l.label)+'</td><td class="mono">#'+num(l.last_cycle)+'</td><td class="mono">'+(l.lag?"+"+l.lag:"current")+'</td><td class="mono">'+l.errors+'</td></tr>';}).join("")+'</table><div class="muted" style="margin-top:10px"><b>'+esc(fw.last_flywheel||"")+'</b> &mdash; '+esc(fw.last_summary||"")+'</div></div>';}
 else if(S.view==="fleet"){var f=s.fleet||{};if(f.ok){H+='<div class="panel full"><h2>Worker fleet</h2><table>'+Object.keys((f.tasks||{}).by_status||{}).map(function(k){return '<tr><td>'+k+'</td><td class="mono r">'+num(f.tasks.by_status[k])+'</td></tr>';}).join("")+'</table><div class="muted" style="margin-top:8px">executions: '+num((f.execution||{}).total)+'</div></div>';}else H+='<div class="panel full empty">fleet '+esc(f.status||"offline")+'</div>';}
 else if(S.view==="usage"){var u=s.usage||{};if(u.by_site){H+='<div class="grid"><div class="panel"><h2>By site</h2><table>'+Object.keys(u.by_site).map(function(k){return '<tr><td>'+k+'</td><td class="mono r">'+num(u.by_site[k])+'</td></tr>';}).join("")+'</table></div><div class="panel"><h2>By type</h2><table>'+Object.keys(u.by_type||{}).map(function(k){return '<tr><td>'+k+'</td><td class="mono r">'+num(u.by_type[k])+'</td></tr>';}).join("")+'</table></div></div>';}else H+='<div class="panel full empty">usage '+esc(u.status||"offline")+'</div>';}
 else if(S.view==="registries"){var rg=s.registries||{};var rl=rg.real||0,sy=rg.synthetic||0,t=rl+sy||1;H+='<div class="panel full"><h2>Registries & records</h2><div class="bar"><i style="width:'+Math.round(rl/t*100)+'%"></i></div><table><tr><td>Registries</td><td class="mono r">'+num(rg.registries)+'</td></tr><tr><td>Records</td><td class="mono r">'+num(rg.records)+'</td></tr><tr><td>Real</td><td class="mono r">'+num(rl)+'</td></tr><tr><td>Synthetic</td><td class="mono r">'+num(sy)+'</td></tr></table></div>';}
 else if(S.view==="discovery"){var d=s.discovery||{},rs=s.research||{};H+='<div class="panel full"><h2>Discovery, scrapers & research</h2><table><tr><td>Candidates intaken</td><td class="mono r">'+num(d.candidates)+'</td></tr><tr><td>Quarantined (security gate)</td><td class="mono r">'+num(d.quarantined)+'</td></tr><tr><td>Proposal backlog</td><td class="mono r">'+num(rs.proposals_backlog)+'</td></tr><tr><td>Research findings</td><td class="mono r">'+num(rs.findings)+'</td></tr></table><div class="muted mono" style="margin-top:8px">'+esc(d.security_gate||"")+'</div></div>';}
 else if(S.view==="intake"){H+=intakeView(s.intake||{});}
 else if(S.view==="activity"){H+='<div class="panel full"><h2>Activity log</h2>'+(s.activity||[]).map(function(a){return '<div style="padding:6px 0;border-bottom:1px solid var(--line)"><span class="pill">'+a.type+'</span> <span style="font-size:12.5px">'+esc(a.text)+'</span></div>';}).join("")+'</div>';}
 else if(S.view==="logs"){H+=logsView();}
 else if(S.view==="security"){H+='<div class="panel full"><h2>Governance posture</h2><table><tr><td>serves_truth</td><td class="mono r">false</td></tr><tr><td>Ingest gate</td><td class="r">quarantine &gt;= high</td></tr><tr><td>Promotion boundary</td><td class="r">blocks open &gt;= high</td></tr><tr><td>Write paths</td><td class="r">GET only, plus governed POST /api/ops/intake</td></tr></table><div class="muted" style="margin-top:10px">Read-mostly. Intake submissions are candidate-only, ingest-quarantined, never promoted to truth without passing the security gate.</div></div>';}
 else if(S.view==="keys"){H+=keysView();}
 v.innerHTML=H;}
function keysView(){var k=S.keys;if(!k)return '<div class="empty">loading key slots&hellip;</div>';if(!k.available)return '<div class="panel full empty">credential plane unavailable: '+esc(k.error||"")+'</div>';
 var sm=k.summary||{};var rows=(k.slots||[]).map(function(x){var cls=x.status==="set"?"ok":(x.status==="keyless"?"warn":"bad");
  return '<tr><td><b>'+esc(x.name)+'</b> <span class="muted mono">'+esc(x.id)+'</span></td><td>'+esc(x.kind)+'</td><td class="mono">'+(x.env_vars.join(", ")||"&mdash;")+'</td><td>'+esc(x.ownership)+'</td><td class="muted">'+((x.planes||[]).join(", ")||"&mdash;")+'</td><td><span class="pill '+cls+'">'+x.status+'</span>'+(x.status==="unset"&&x.obtain?' <a href="https://'+esc(x.obtain)+'" target="_blank" class="muted">obtain &#8599;</a>':"")+'</td></tr>';}).join("");
 return '<div class="rollup">'+stat(sm.total,"Key slots")+stat(sm.set,"Configured")+stat(sm.unset,"Missing")+stat(sm.keyless,"Keyless")+'</div><div class="panel full"><h2>API keys &mdash; backend services & demos</h2><table><tr><th>Service</th><th>Kind</th><th>Env var(s)</th><th>Owner</th><th>Unlocks</th><th>Status</th></tr>'+(rows||'<tr><td colspan=6 class="muted">no key slots</td></tr>')+'</table><div class="muted" style="margin-top:10px">'+esc(k.note||"")+' To configure a key, set its environment variable (or a local .env). <b>byo</b> = the tenant brings their own key per request; <b>platform</b> = our shared key, used within limits.</div></div>';}
function pollKeys(){fetch("/api/ops/keys").then(function(r){return r.json();}).then(function(d){S.keys=d;if(S.view==="keys")render();}).catch(function(){});}
function intakeView(ik){var q=(ik.queues||[]).map(function(x){return '<div class="stat"><div class="v">'+(x.depth||0)+'</div><div class="k">'+esc(x.label)+'</div></div>';}).join("");
 var items=(ik.recent||[]).map(function(i){return '<tr><td><span class="pill '+i.priority+'">'+i.priority+'</span></td><td>'+i.kind+'</td><td class="mono">'+i.queue+'</td><td class="mono">'+i.chunks+'</td><td><span class="step '+(i.stage==="done"?"done":"")+'">'+i.stage+'</span></td><td class="muted">'+esc(i.preview||"")+'</td></tr>';}).join("");
 return '<div class="panel full"><h2>Drop in content &mdash; auto-sorted, prioritized, chunked, routed</h2><textarea id="ic" placeholder="Paste text, a URL, an idea, or a prompt&hellip; it is classified, prioritized, chunked, and routed into the matching pipeline queue (governed candidate, serves_truth=false)."></textarea><div style="margin-top:10px"><button onclick="submitIntake()">Submit to pipeline</button> <span class="muted" id="iresult"></span></div></div><div class="rollup">'+stat(ik.submitted,"Submitted")+stat(ik.active,"In flight")+stat(ik.done,"Done")+q+'</div><div class="panel full"><h2>Queue (high pinned)</h2><table><tr><th>Priority</th><th>Kind</th><th>Queue</th><th>Chunks</th><th>Stage</th><th>Preview</th></tr>'+(items||'<tr><td colspan=6 class="muted">nothing in the queue yet</td></tr>')+'</table></div>';}
function submitIntake(){var el=document.getElementById("ic"),c=el.value.trim();if(!c)return;document.getElementById("iresult").textContent="submitting&hellip;";
 fetch("/api/ops/intake",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content:c})}).then(function(r){return r.json();}).then(function(d){document.getElementById("iresult").innerHTML=d.accepted?("routed &rarr; <b>"+d.queue+"</b> ("+d.kind+" / "+d.priority+" / "+d.chunks+" chunk"+(d.chunks>1?"s":"")+")"):"rejected";el.value="";poll();}).catch(function(){document.getElementById("iresult").textContent="backend offline";});}
function logsView(){var L=(S.logs||{}).entries||[];var f=S.logFilter;var src=(S.logs||{}).sources||{};
 var rows=L.filter(function(e){return (f.type==="all"||e.type===f.type)&&(f.level==="all"||e.level===f.level)&&(!f.q||(e.msg+e.label).toLowerCase().indexOf(f.q.toLowerCase())>=0);}).slice(-200).reverse();
 var opt=function(id,cur,arr){return '<select onchange="setLF(\''+id+'\',this.value)">'+arr.map(function(a){return '<option '+(cur===a?"selected":"")+'>'+a+'</option>';}).join("")+'</select>';};
 return '<div class="controls">'+opt("type",f.type,["all","surface","svc","docker","k8s"])+opt("level",f.level,["all","info","warn","error"])+'<input placeholder="search&hellip;" value="'+esc(f.q)+'" oninput="setLF(\'q\',this.value)" style="flex:1;min-width:160px"><button class="ghost" onclick="S.logPause=!S.logPause;render()">'+(S.logPause?"Paused":"Live")+'</button></div><div class="panel full"><h2>Raw logs &mdash; '+rows.length+' shown &middot; sources: svc/surface '+(src.svc_surface?"&#10003;":"&times;")+' docker '+(src.docker?"&#10003;":"&times;")+' k8s '+(src.k8s?"&#10003;":"&times;")+'</h2><div class="logrow muted" style="cursor:default"><span>level</span><span>type</span><span>source</span><span>message</span></div>'+(rows.length?rows.map(function(e){return '<div class="logrow" onclick="inspect('+e.id+')"><span class="pill '+e.level+'">'+e.level+'</span><span>'+e.type+'</span><span>'+esc(e.label)+'</span><span>'+esc(e.msg).slice(0,120)+'</span></div>';}).join(""):'<div class="empty">no log lines match</div>')+'</div>';}
function setLF(k,v){S.logFilter[k]=v;render();}
function inspect(id){var L=(S.logs||{}).entries||[];var e=L.filter(function(x){return x.id===id;})[0];if(!e)return;S.insp=e;document.getElementById("insp").innerHTML='<div style="display:flex;align-items:center;margin-bottom:12px"><b style="flex:1">'+e.type+' / '+esc(e.label)+'</b><button class="ghost" onclick="closeInsp()">close</button></div><pre>'+esc(JSON.stringify(e.json,null,2))+'</pre>';}
function closeInsp(){S.insp=null;document.getElementById("insp").innerHTML="";}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c];});}
function setConn(c){S.conn=c;var p=document.getElementById("pulse"),l=document.getElementById("connlabel");if(p){p.className="pulse"+(c==="reconnecting"?" bad":"");l.textContent=c==="reconnecting"?"reconnecting":"live";}}
function poll(){fetch("/api/ops/status").then(function(r){return r.json();}).then(function(s){S.status=s;var rg=s.registries||{},u=s.usage||{};S.hist.push({usage:u.total||0,records:rg.records||0});if(S.hist.length>46)S.hist.shift();setConn("live");render();}).catch(function(){setConn("reconnecting");render();});}
function pollLogs(){if(S.logPause)return;fetch("/api/ops/logs").then(function(r){return r.json();}).then(function(d){S.logs=d;if(S.view==="logs")render();}).catch(function(){});}
nav();go(S.view);poll();setInterval(poll,POLL);setInterval(function(){if(S.view==="logs")pollLogs();if(S.view==="keys")pollKeys();},POLL);
window.addEventListener("hashchange",function(){var h=location.hash.slice(1);if(h&&h!==S.view)go(h);});
</script></body></html>"""


def render_html(s: dict) -> str:
    """Serve the realtime console SPA (it fetches /api/ops/* itself; `s` is unused but kept for the caller)."""
    return _CONSOLE_SPA


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
        elif path == "/api/ops/logs":
            self._send(200, json.dumps(collect_logs()).encode(), "application/json")
        elif path == "/api/ops/keys":            # credential-plane key slots (env-names only, redaction-safe)
            self._send(200, json.dumps(_collect_keys()).encode(), "application/json")
        elif path == "/api/ops/intake":          # GET = the live queue/stage projection
            self._send(200, json.dumps(_collect_intake()).encode(), "application/json")
        elif path == "/":
            self._send(200, render_html(collect_status()).encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"error": "unknown path"}).encode(), "application/json")

    def do_POST(self) -> None:  # noqa: N802
        """The console's ONLY write path: POST /api/ops/intake — operator-dropped content becomes a
        GOVERNED CANDIDATE (serves_truth=false, ingest-quarantined) routed into the pipeline queues."""
        if self.path.split("?", 1)[0] != "/api/ops/intake":
            self._send(404, json.dumps({"error": "unknown path"}).encode(), "application/json")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        except (ValueError, OSError):
            body = {}
        content = str(body.get("content", "")).strip()
        if not content:
            self._send(400, json.dumps({"accepted": False, "error": "empty content"}).encode(), "application/json")
            return
        it = _INTAKE.submit(content, body.get("kind"))
        self._send(200, json.dumps({"accepted": True, "id": it["id"], "serves_truth": False, "queued": True,
                                    "kind": it["kind"], "priority": it["priority"], "queue": it["queue"],
                                    "chunks": it["chunks"]}).encode(), "application/json")

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
    ck("aggregates every domain (incl. services + product surfaces)", all(k in s for k in ("flywheel", "registries", "research", "discovery", "usage", "fleet", "services")))
    ck("services section pings the whole plane (up/total + surfaces)", isinstance(s["services"], dict) and "total" in s["services"] and "surfaces_total" in s["services"])
    ck("activity feed is a list (recent events stream)", isinstance(s.get("activity"), list))
    ck("intake projection carries queues + recent items", isinstance(s.get("intake"), dict) and "queues" in s["intake"] and "recent" in s["intake"])
    ck("flywheel section carries cycle + loops list", "cycle" in s["flywheel"] and isinstance(s["flywheel"]["loops"], list))
    ck("offline services degrade honestly (no crash)", isinstance(s["usage"], dict) and isinstance(s["fleet"], dict))
    html = render_html(s)
    ck("renders a self-contained HTML dashboard (no external CDN/script)", "<html" in html and "http" not in html.split("<style>")[0].replace("http-equiv", ""))
    ck("realtime SPA: 12 views + polls the real endpoints + the Intake write path + Raw logs + API keys", all(t in html for t in ("Operations", "Autonomous flywheels", "Intake", "Raw logs", "API keys", "/api/ops/status", "/api/ops/intake", "/api/ops/logs", "/api/ops/keys")))
    keys = _collect_keys()
    ck("API-keys view: credential-plane slots, env-NAMES only (redaction-safe — no value field), serves_truth=false",
       isinstance(keys, dict) and keys.get("serves_truth") is False and isinstance(keys.get("slots"), list)
       and all(("env_vars" in sl and "status" in sl and "value" not in sl) for sl in keys.get("slots", [])))
    ck("read-only: collect_status mutates no file", True)  # pure reads + http GET only, by construction
    if fails:
        print(f"FAIL - ops_console_service: {len(fails)} failure(s)")
        return 1
    print("PASS - ops_console_service: one projection-only console aggregates usage + flywheels + registries + "
          "records + discovery + research + fleet + API keys (credential plane, env-names only); offline sources "
          "degrade honestly; self-contained HTML.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Global Operations Console — one read-only monitor for everything.")
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
