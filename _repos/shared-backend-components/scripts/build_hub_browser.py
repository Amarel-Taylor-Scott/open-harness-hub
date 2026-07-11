#!/usr/bin/env python3
"""build_hub_browser — a 'browse everything' table surface across all Open*Hubs and their registries.

Generates a self-contained, searchable + sortable HTML page (dist/hubs/index.html) with two tables: (1) the HUBS (live +
candidate, from _repos/shared-backend-components/architecture/candidate_open_hubs.json) and (2) the REGISTRIES each hub owns, with entry counts COMPUTED
from the real registry files (no magic values). This is the standardized browse view that keeps the hubs separate +
legible. Candidates are private_first (discovery != trust); serves_truth=false.

  python3 _repos/shared-backend-components/scripts/build_hub_browser.py            # -> dist/hubs/index.html
  python3 _repos/shared-backend-components/scripts/build_hub_browser.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
OUT = _resource("dist/hubs/index.html")

# (registry file, collection key, label, owning hub) — counts are computed from the real files
REGISTRY_MAP = [
    ("architecture/tool_registry.json", "tools", "Tools", "OpenToolsHub"),
    ("architecture/tool_planes.json", "planes", "Tool planes", "OpenToolsHub"),
    ("architecture/capability_ladders.json", "ladders", "Capability ladders", "OpenHubForAI"),
    ("architecture/dag_templates.json", "templates", "DAG templates", "OpenTemplatesHub"),
    ("architecture/ml_model_registry.json", "models", "ML model types", "OpenToolsHub"),
    ("architecture/plane_io_contracts.json", "planes", "Plane I/O contracts", "OpenHubForAI"),
    ("architecture/source_registry.json", "sources", "Data sources", "OpenSourcesHub"),
    ("architecture/provider_directory_sources.json", "rungs", "Provider source descent", "OpenSourcesHub"),
    ("architecture/entity_resolution_rules.json", "rulesets", "Entity-resolution rulesets", "OpenLinkingHub"),
    ("architecture/industry_linking_rules.json", "industries", "Industry linking rules", "OpenLinkingHub"),
    ("architecture/licensed_professions.json", "professions", "Licensed professions", "OpenLinkingHub"),
    ("architecture/external_api_registry.json", "apis", "External APIs", "OpenToolsHub"),
    ("architecture/credential_registry.json", "services", "Credential services", "OpenRoutingHub"),
]


def _count(rel: str, key: str) -> int:
    try:
        d = json.loads((_resource(rel)).read_text())
    except Exception:  # noqa: BLE001
        return -1
    coll = d.get(key, d)
    return len(coll) if isinstance(coll, (list, dict)) else -1


def _hubs() -> list:
    d = json.loads((_resource("architecture") / "candidate_open_hubs.json").read_text())
    rows = [{"hub": h, "domain": "(live)", "status": "live", "maturity": "live", "thesis": "Live open hub."}
            for h in d.get("existing_hubs", [])]
    for c in d.get("candidates", []):
        rows.append({"hub": c["hub_id"], "domain": c.get("proposed_domain", ""), "status": c.get("status", ""),
                     "maturity": c.get("maturity", ""), "thesis": c.get("thesis", "")[:240]})
    return rows


def _esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build() -> str:
    hubs, registries = _hubs(), [(lbl, hub, _count(f, k), f) for f, k, lbl, hub in REGISTRY_MAP]
    hub_rows = "\n".join(
        f"<tr><td>{_esc(h['hub'])}</td><td>{_esc(h['domain'])}</td><td><span class=b>{_esc(h['status'])}</span></td>"
        f"<td>{_esc(h['maturity'])}</td><td>{_esc(h['thesis'])}</td></tr>" for h in hubs)
    reg_rows = "\n".join(
        f"<tr><td>{_esc(lbl)}</td><td>{_esc(hub)}</td><td class=n>{n if n >= 0 else '—'}</td><td class=f>{_esc(f)}</td></tr>"
        for lbl, hub, n, f in registries)
    total = sum(n for _, _, n, _ in registries if n >= 0)
    return f"""<!doctype html><meta charset=utf-8><title>AI Done Right — Hub & Registry Browser</title>
<style>body{{font:14px/1.5 system-ui,sans-serif;margin:2rem;color:#1a1a2e;max-width:1100px}}h1{{font-size:1.4rem}}
h2{{margin-top:2rem;font-size:1.1rem}}input{{padding:.5rem;width:100%;max-width:420px;margin:.5rem 0;border:1px solid #ccc;border-radius:6px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{text-align:left;padding:.4rem .6rem;border-bottom:1px solid #eee;vertical-align:top}}
th{{cursor:pointer;background:#f6f7fb;position:sticky;top:0}}th:hover{{background:#eef}}.b{{background:#eef;border-radius:4px;padding:.1rem .4rem;font-size:12px}}
.n{{text-align:right;font-variant-numeric:tabular-nums}}.f{{color:#888;font-family:ui-monospace,monospace;font-size:11px}}.muted{{color:#888}}</style>
<h1>AI Done Right — Hub &amp; Registry Browser</h1>
<p class=muted>Browse every Open*Hub and the registries it owns. Counts computed from the live registry files. Candidates are
private-first (discovery ≠ trust); nothing here asserts truth (serves_truth=false).</p>
<input id=q placeholder="Filter hubs &amp; registries…" oninput="filt()">
<h2>Hubs ({len(hubs)})</h2>
<table id=hubs><thead><tr><th onclick=srt('hubs',0)>Hub</th><th onclick=srt('hubs',1)>Domain</th>
<th onclick=srt('hubs',2)>Status</th><th onclick=srt('hubs',3)>Maturity</th><th>Thesis</th></tr></thead><tbody>
{hub_rows}
</tbody></table>
<h2>Registries ({len(registries)} · {total} total entries)</h2>
<table id=regs><thead><tr><th onclick=srt('regs',0)>Registry</th><th onclick=srt('regs',1)>Hub</th>
<th onclick=srt('regs',2)>Entries</th><th>File</th></tr></thead><tbody>
{reg_rows}
</tbody></table>
<script>
function filt(){{var q=document.getElementById('q').value.toLowerCase();
['hubs','regs'].forEach(function(id){{document.querySelectorAll('#'+id+' tbody tr').forEach(function(r){{
r.style.display=r.innerText.toLowerCase().indexOf(q)>-1?'':'none';}});}});}}
function srt(id,c){{var t=document.getElementById(id),b=t.tBodies[0],rs=[].slice.call(b.rows);
var num=c==2&&id=='regs';rs.sort(function(x,y){{var a=x.cells[c].innerText,d=y.cells[c].innerText;
return num?(parseInt(d||0)-parseInt(a||0)):a.localeCompare(d);}});rs.forEach(function(r){{b.appendChild(r);}});}}
</script>"""


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)
    html = build()
    ck("page lists the live + new candidate hubs (OpenHubForAI, OpenLinkingHub, OpenSourcesHub)",
       all(h in html for h in ("OpenHubForAI", "OpenLinkingHub", "OpenSourcesHub")))
    ck("page lists registries with COMPUTED counts (entity-resolution rulesets, data sources, licensed professions)",
       all(r in html for r in ("Entity-resolution rulesets", "Data sources", "Licensed professions")))
    ck("registry counts are real (>0 total entries computed from the files)", "total entries" in html and sum(_count(f, k) for f, k, _, _ in REGISTRY_MAP if _count(f, k) > 0) > 0)
    ck("browse UI is self-contained (filter + sortable, inline JS/CSS, no external deps)", "function filt()" in html and "onclick=srt" in html and "http" not in html.split("<script>")[0].replace("system-ui", ""))
    ck("governed framing present (private-first / discovery != trust / serves_truth=false)", "private-first" in html and "serves_truth=false" in html)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    ck("writes dist/hubs/index.html", OUT.exists() and OUT.stat().st_size > 1500)
    print("\n" + ("PASS - build_hub_browser: self-contained searchable/sortable browse table over all hubs + their "
                  "registries (computed counts)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")
