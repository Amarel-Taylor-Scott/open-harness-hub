#!/usr/bin/env python3
"""serve_document_cascade_demo — a FULLY WORKING local page for the document→schema cheapest-that-meets cascade.

Write in a capability (the schema fields + the document profile + whether you have an LLM key) and the page runs the
REAL src.teleon.extraction.document_extraction_cascade engine and shows the cheapest path that meets the requirement:
the per-step method + cost, deterministic-vs-LLM, the fields filled, total cost, and the savings vs sending the whole
document to a frontier LLM. Stdlib-only (no deps), runs offline, never serves truth (extraction output is a candidate).

  --serve [--port 8088]   run the local page (open http://localhost:8088)
  --self-test             prove the page + the /extract engine work in-process (the registered proof)

CLI: PYTHONPATH=. python3 scripts/serve_document_cascade_demo.py --serve
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.extraction.document_extraction_cascade import extract

_VALID_CLASSES = ("structured", "semi", "unstructured")
_FRONTIER_ONLY_COST = 0.302   # the naive baseline: acquire + send the whole doc to a frontier LLM


def _parse_schema(text: str) -> dict:
    """One field per line: 'field_name: structured|semi|unstructured' (unknown class -> unstructured, so it escalates)."""
    fields = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        name, _, cls = line.partition(":")
        name, cls = name.strip(), cls.strip().lower()
        if name:
            fields[name] = cls if cls in _VALID_CLASSES else "unstructured"
    return fields


def run_extract(spec: dict) -> dict:
    """Run the REAL cascade on the written-in capability and add the savings-vs-frontier comparison."""
    required = _parse_schema(spec.get("schema", ""))
    doc = {"has_text_layer": bool(spec.get("has_text_layer", True)), "scanned": bool(spec.get("scanned", False))}
    keys = ("LLM_API_KEY",) if spec.get("has_llm_key", True) else ()
    if not required:
        return {"error": "write at least one schema field, e.g. 'agency_license_no: structured'", "serves_truth": False}
    r = extract(required, doc, available_keys=keys)
    r["frontier_only_cost"] = _FRONTIER_ONLY_COST
    r["savings_vs_frontier"] = round(_FRONTIER_ONLY_COST - r["total_cost"], 4)
    r["savings_pct"] = round(100.0 * (_FRONTIER_ONLY_COST - r["total_cost"]) / _FRONTIER_ONLY_COST, 1)
    return r


_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Teleon · document→schema cascade (write in a capability)</title>
<style>
 :root{--bg:#0d1117;--panel:#161b22;--line:#21262d;--fg:#e6edf3;--mut:#8b949e;--ok:#3fb950;--bad:#f85149;--acc:#58a6ff;}
 *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 ui-monospace,Menlo,Consolas,monospace}
 header{padding:16px 20px;border-bottom:1px solid var(--line)} h1{font-size:16px;margin:0 0 4px} .sub{color:var(--mut);font-size:12px}
 main{display:grid;grid-template-columns:360px 1fr;gap:16px;padding:16px;max-width:1100px}
 .panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px}
 label{display:block;color:var(--mut);font-size:12px;margin:10px 0 4px} textarea,select{width:100%;background:#0d1117;color:var(--fg);
  border:1px solid var(--line);border-radius:6px;padding:8px;font:13px ui-monospace,monospace} textarea{height:150px;resize:vertical}
 .chk{display:flex;align-items:center;gap:8px;margin:8px 0;color:var(--fg)}
 button{margin-top:12px;background:var(--acc);color:#0d1117;border:0;border-radius:6px;padding:10px 16px;font-weight:700;cursor:pointer;width:100%}
 .big{font-size:22px} .ok{color:var(--ok)} .bad{color:var(--bad)} code{color:var(--acc)}
 table{width:100%;border-collapse:collapse;margin-top:8px} td,th{text-align:left;padding:4px 6px;border-bottom:1px dashed var(--line);font-size:12px}
 .pill{padding:1px 7px;border-radius:999px;font-size:11px} .pill.det{background:rgba(63,185,80,.15);color:var(--ok)} .pill.llm{background:rgba(248,81,73,.15);color:var(--bad)}
 .note{color:var(--mut);font-size:11px;margin-top:10px}
</style></head><body>
<header><h1>Teleon · document → schema cascade</h1>
<div class="sub">Write in a capability. The page runs the REAL cheapest-that-meets cascade (deterministic rules before LLM, escalate only as far as the requirement forces) and shows the path + cost. Extraction is a candidate — never served as truth.</div></header>
<main>
 <div class="panel">
  <label>Schema fields (one per line — <code>name: structured|semi|unstructured</code>)</label>
  <textarea id="schema">agency_license_no: structured
agency_name: structured
issue_date: structured
address: semi
authorized_destinations: semi
recruiter_obligations: unstructured
fee_terms: unstructured</textarea>
  <div class="chk"><input type="checkbox" id="textlayer" checked><label style="margin:0">document has a text layer (else OCR)</label></div>
  <div class="chk"><input type="checkbox" id="scanned"><label style="margin:0">document is a scan</label></div>
  <div class="chk"><input type="checkbox" id="llmkey" checked><label style="margin:0">an LLM key is available</label></div>
  <button onclick="runCascade()">Run cascade ▶</button>
  <div class="note">Tip: an all-<code>structured</code> schema fills by regex with NO LLM. Uncheck the LLM key to see unstructured fields reported missing honestly.</div>
 </div>
 <div class="panel" id="out"><div class="sub">Results will appear here.</div></div>
</main>
<script>
async function runCascade(){
 const spec={schema:document.getElementById('schema').value,
   has_text_layer:document.getElementById('textlayer').checked,
   scanned:document.getElementById('scanned').checked,
   has_llm_key:document.getElementById('llmkey').checked};
 const out=document.getElementById('out'); out.innerHTML='<div class="sub">running…</div>';
 try{
  const res=await fetch('/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(spec)});
  const r=await res.json();
  if(r.error){out.innerHTML='<div class="bad">'+r.error+'</div>';return;}
  let rows=r.receipt.map(s=>'<tr><td>'+s.stage+'</td><td><code>'+s.method+'</code></td><td>$'+(s.cost||0)+'</td>'
    +'<td>'+(s.skipped?('<span class=bad>skipped: '+s.skipped+'</span>'):(s.deterministic===false?'<span class="pill llm">LLM</span>':'<span class="pill det">deterministic</span>'))+'</td>'
    +'<td>'+((s.filled||[]).join(', '))+'</td></tr>').join('');
  out.innerHTML=
   '<div class="big '+(r.met_requirement?'ok':'bad')+'">'+(r.met_requirement?'✓ requirement met':'✗ requirement NOT met')+'</div>'
   +'<div class="sub">total cost <b>$'+r.total_cost+'</b> · vs frontier-only $'+r.frontier_only_cost+' → <span class=ok>'+r.savings_pct+'% cheaper</span> · used LLM: '+r.used_llm+'</div>'
   +(r.missing.length?'<div class="bad">missing (no available method could fill, not fabricated): '+r.missing.join(', ')+'</div>':'')
   +'<table><tr><th>stage</th><th>method</th><th>cost</th><th>type</th><th>filled</th></tr>'+rows+'</table>'
   +'<div class="note">serves_truth='+r.serves_truth+' · the cheapest variation that meets the schema; escalates only as far as needed.</div>';
 }catch(e){out.innerHTML='<div class="bad">'+e+'</div>';}
}
window.onload=runCascade;
</script></body></html>"""


def _make_handler():
    class _H(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code); self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

        def do_GET(self):  # noqa: N802
            self._send(200, _PAGE, "text/html; charset=utf-8") if self.path.rstrip("/") in ("", "/") else self._send(404, json.dumps({"error": "not found"}))

        def do_POST(self):  # noqa: N802
            if self.path.rstrip("/") != "/extract":
                self._send(404, json.dumps({"error": "not found"})); return
            n = int(self.headers.get("Content-Length", 0) or 0)
            spec = json.loads(self.rfile.read(n) or b"{}") if n else {}
            self._send(200, json.dumps(run_extract(spec)))

        def log_message(self, *_a):
            return
    return _H


def serve(*, host="127.0.0.1", port=8088):  # pragma: no cover
    print(f"Teleon document→schema cascade demo: http://{host}:{port}  (Ctrl-C to stop)")
    HTTPServer((host, port), _make_handler()).serve_forever()


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ck("the page renders the write-in form (schema textarea + run button + doc-profile toggles)",
       "<textarea id=\"schema\">" in _PAGE and "Run cascade" in _PAGE and "textlayer" in _PAGE and "llmkey" in _PAGE)
    # the REAL engine runs on written-in input: all-structured -> NO LLM, cheap, big savings
    r1 = run_extract({"schema": "a: structured\nb: structured", "has_text_layer": True, "has_llm_key": True})
    ck("all-structured capability runs the real cascade: met, no LLM, huge savings vs frontier",
       r1["met_requirement"] and not r1["used_llm"] and r1["savings_pct"] > 90, str(r1.get("total_cost")))
    # a mixed schema escalates to the LLM but stays far under frontier-only
    r2 = run_extract({"schema": "a: structured\nc: unstructured", "has_text_layer": True, "has_llm_key": True})
    ck("a schema with an unstructured field escalates to the LLM but beats frontier-only",
       r2["met_requirement"] and r2["used_llm"] and r2["total_cost"] < r2["frontier_only_cost"])
    # honesty: no LLM key -> unstructured field reported missing, not fabricated
    r3 = run_extract({"schema": "a: structured\nc: unstructured", "has_llm_key": False})
    ck("no LLM key -> the unstructured field is reported MISSING (not fabricated)",
       r3["met_requirement"] is False and "c" in r3["missing"])
    ck("empty schema returns a helpful error (no crash)", "error" in run_extract({"schema": ""}))
    ck("the receipt never serves truth", r1["serves_truth"] is False)
    ck("deterministic", run_extract({"schema": "a: structured\nb: structured"}) == r1)

    print("\n" + ("PASS - serve_document_cascade_demo: a fully-working local page (stdlib http.server) where you write "
                  "in a capability (schema + doc profile + key) and the REAL document→schema cascade runs — cheapest "
                  "path, per-step cost, deterministic-vs-LLM, savings vs frontier, missing fields reported honestly. "
                  "Run: PYTHONPATH=. python3 scripts/serve_document_cascade_demo.py --serve. Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--serve", action="store_true"); p.add_argument("--self-test", action="store_true")
    p.add_argument("--port", type=int, default=8088)
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    if a.serve:
        serve(port=a.port); return 0
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
