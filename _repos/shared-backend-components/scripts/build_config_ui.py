#!/usr/bin/env python3
"""build_config_ui — render the MEDIUM CONFIG UI: connect preferred mediums (compute/llm/search) per function.

A self-contained config surface so a client (or a demo operator) can see + set, per function, which compute backend /
LLM lane / search provider to use — and connect their tokens. Dropdown options come from the LIVE registries (via the
resolver's available_mediums), so the UI is always in sync. The page builds the medium_config JSON client-side from the
selects (copy/save) — a save-to-disk endpoint is the documented next step. serves_truth=false.

  --self-test   prove the UI renders every function with per-medium selects + token status
  --emit        write dist/teleon-config/index.html
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/build_config_ui.py --emit
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.config.medium_resolver import available_mediums, resolve_mediums, configured_functions, load_config

OUT = _resource("dist") / "teleon-config" / "index.html"


def _token_status() -> dict:
    env = (REPO / ".env").read_text(encoding="utf-8", errors="replace") if (REPO / ".env").exists() else ""
    def set_(k):
        for ln in env.splitlines():
            if ln.startswith(f"{k}="):
                v = ln.split("=", 1)[1].strip()
                return bool(v) and not v.startswith("replace-with")
        return False
    return {"Cloudflare": set_("CLOUDFLARE_API_TOKEN") and set_("CLOUDFLARE_ACCOUNT_ID"),
            "Ollama": set_("OH_LLM_API_KEY"), "OpenRouter": set_("OPENROUTER_API_KEY")}


def render(tenant: str = "demo") -> str:
    avail = available_mediums()
    funcs = configured_functions(tenant) or ["default"]
    if "default" not in funcs:
        funcs = ["default"] + funcs
    tokens = _token_status()

    def sel(kind, current):
        opts = "".join(f'<option {"selected" if o == current else ""}>{o}</option>' for o in avail.get(kind, []))
        return f'<select data-kind="{kind}">{opts}</select>'

    rows = []
    for fn in funcs:
        r = resolve_mediums(tenant, fn)
        rows.append(f"""<tr data-fn="{fn}"><td class=fn>{fn}</td>
          <td>{sel('compute', r['compute'])}</td>
          <td>{sel('llm', r['llm'])}</td>
          <td>{sel('search', r['search'])}</td>
          <td class=src>{r['sources'].get('llm','default')}</td></tr>""")
    tok = "".join(f'<span class="tok {"on" if v else "off"}">{k}: {"connected" if v else "not connected"}</span>' for k, v in tokens.items())
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Teleon — Medium Config</title>
<style>
 body{{font-family:'Hanken Grotesk',system-ui,sans-serif;margin:0;background:#fafbfc;color:#0d1117}}
 header{{padding:32px}} h1{{margin:0;font-size:26px;letter-spacing:-.02em}}
 .sub{{color:#5b6470;max-width:760px;margin:8px 0 0;font-size:14px;line-height:1.5}}
 .toks{{margin:14px 32px}} .tok{{font:600 12px 'IBM Plex Mono',monospace;padding:4px 9px;border-radius:6px;margin-right:8px}}
 .tok.on{{background:#e6f4ea;color:#0a7d3c}} .tok.off{{background:#fdecec;color:#b3261e}}
 table{{border-collapse:collapse;margin:8px 32px 24px;background:#fff;border:1px solid #e6e8eb;border-radius:12px;overflow:hidden}}
 th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #eef0f2;font-size:13.5px}}
 th{{background:#f6f8fa;font:600 12px 'IBM Plex Mono',monospace;color:#5b6470}}
 td.fn{{font:600 13px 'IBM Plex Mono',monospace}} td.src{{color:#5b6470;font-size:11px}}
 select{{font:13px 'IBM Plex Mono',monospace;padding:4px 6px;border:1px solid #d6d9dd;border-radius:6px;background:#fff}}
 .bar{{margin:0 32px 32px}} button{{font:600 13px 'Hanken Grotesk',sans-serif;background:#1f6feb;color:#fff;border:0;border-radius:8px;padding:9px 16px;cursor:pointer}}
 pre{{background:#0d1117;color:#c9d1d9;padding:14px;border-radius:10px;margin:12px 32px;overflow:auto;font:12px 'IBM Plex Mono',monospace}}
</style></head><body>
<header><h1>Teleon — connect your mediums</h1>
<p class=sub>Pick the compute backend, LLM lane, and search provider for each function — set <b>different mediums for
different functions</b>. Options come live from the registries. Connect tokens in <code>.env</code> (or your secrets
store); Teleon dispatches to your chosen mediums and only tracks results + metadata.</p></header>
<div class=toks>{tok}</div>
<table><thead><tr><th>function</th><th>compute</th><th>LLM lane</th><th>search</th><th>source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<div class=bar><button onclick="gen()">Preview config</button> <button onclick="save()">Save to server</button> <span id=msg></span></div>
<pre id=out>// pick mediums, then Preview (build JSON) or Save (POST /save when served by config_ui_server.py)</pre>
<script>
function collect(){{
  const pf={{}};
  document.querySelectorAll('tr[data-fn]').forEach(tr=>{{
    const fn=tr.dataset.fn, o={{}};
    tr.querySelectorAll('select').forEach(s=>o[s.dataset.kind]=s.value);
    pf[fn]=o;
  }});
  return {{tenant:'{tenant}',per_function:pf}};
}}
function gen(){{ document.getElementById('out').textContent=JSON.stringify(collect(),null,2); }}
async function save(){{
  const m=document.getElementById('msg'); m.textContent='saving…';
  try{{
    const r=await fetch('/save',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(collect())}});
    const j=await r.json();
    m.textContent = j.saved ? '✓ saved to architecture/medium_config.json' : ('✗ '+(j.errors||[]).join('; '));
    document.getElementById('out').textContent=JSON.stringify(j,null,2);
  }}catch(e){{ m.textContent='✗ save needs config_ui_server.py --serve ('+e+')'; }}
}}
</script></body></html>"""


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    html = render("demo")
    ck("UI renders a row per configured function", 'data-fn="extraction"' in html and 'data-fn="enrichment"' in html)
    ck("UI has per-medium selects (compute/llm/search dropdowns)", html.count('data-kind="compute"') >= 1 and 'data-kind="llm"' in html and 'data-kind="search"' in html)
    ck("dropdown options come from the live registries (cloudflare_workers + ollama present)", "cloudflare_workers" in html and "ollama" in html)
    ck("UI shows token connection status", "connected" in html or "not connected" in html)
    ck("UI can preview AND save the config (POST /save) — configurable", "Preview config" in html and "Save to server" in html and "/save" in html and "per_function" in html)
    print("\n" + ("PASS - build_config_ui: a medium-config UI — per-function compute/LLM/search selects (options from the "
                  "live registries), token-connection status, and client-side config-JSON generation. Different mediums "
                  "per function, configurable from the UI."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--emit" in argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(render("demo"), encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO)}")
    else:
        print("usage: build_config_ui.py --self-test | --emit")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
