#!/usr/bin/env python3
"""scripts.aidevobserver_demo_server — the AIDevObserver /demo: a WORKING session-review walk-through.

Owner 2026-06-25: "AIDevObserver definitely needs a demo … all surfaces should have a /demo that shows everything
working with example configurations but lets someone go through the process." This is that demo for AIDevObserver
(the pillar with no web surface yet): load an example AI-coding session (or paste your own) → "Review" → the real
post-session report from src/teleon/observer/review.review_session (reinvention / waste / footgun findings, governed
candidate findings, serves_truth=false). No mock data — it runs the actual reviewer.

  python3 scripts/aidevobserver_demo_server.py [--port 8110]    then tunnel it
  --self-test
"""
from __future__ import annotations

import http.server
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.observer.review import review_session  # noqa: E402

#: example configurations the user can load + run (synthetic, public-shaped — no PII)
EXAMPLES = {
    "reinvention-heavy": {
        "label": "A session full of reinventions",
        "messages": [
            {"role": "user", "content": "let me write a pdf parser from scratch"},
            {"role": "user", "content": "I'll implement my own address validation and email regex"},
            {"role": "user", "content": "and a custom retry/backoff loop for the http client"},
            {"role": "assistant", "content": "sure, here is a hand-rolled exponential backoff…"},
        ],
    },
    "wasteful-context": {
        "label": "A session wasting context",
        "messages": [
            {"role": "user", "content": "company quarterly report 2026 " * 60},
            {"role": "user", "content": "company quarterly report 2026 " * 60},
            {"role": "user", "content": "now summarize the key risks"},
        ],
    },
    "clean": {
        "label": "A clean session (should be quiet)",
        "messages": [
            {"role": "user", "content": "genuinely novel research with no solved off-the-shelf domain"},
            {"role": "assistant", "content": "agreed, this is new ground; proceeding carefully"},
        ],
    },
}


def _page() -> str:
    opts = "".join(f'<option value="{k}">{v["label"]}</option>' for k, v in EXAMPLES.items())
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><meta name=robots content=noindex>
<title>AIDevObserver — /demo</title><style>
body{{font-family:'Hanken Grotesk',system-ui,sans-serif;max-width:920px;margin:2.2rem auto;padding:0 1.2rem;background:#0b0e14;color:#e6edf3;line-height:1.5}}
h1{{font-size:1.7rem;margin:0 0 .2rem}}.tag{{display:inline-block;border:1px solid #21262d;border-radius:999px;padding:3px 11px;color:#9aa7b4;font-size:12px;margin-bottom:1.2rem}}
.sub{{color:#9aa7b4;margin:.2rem 0 1.4rem;max-width:680px}}
label{{font-size:.85rem;color:#9aa7b4;display:block;margin:.8rem 0 .3rem}}
select,textarea{{width:100%;box-sizing:border-box;background:#11161d;color:#e6edf3;border:1px solid #21262d;border-radius:9px;padding:.6rem .7rem;font:13px ui-monospace,monospace}}
textarea{{height:170px;resize:vertical}}
button{{margin-top:.9rem;color:#0b0e14;background:#7aa2ff;border:0;border-radius:9px;padding:.6rem 1rem;font-weight:700;cursor:pointer}}
.report{{margin-top:1.6rem;border:1px solid #21262d;border-radius:12px;background:#11161d;padding:1rem 1.2rem;display:none}}
.kpi{{display:flex;gap:1.4rem;flex-wrap:wrap;margin:.4rem 0 1rem}}.kpi div{{font-size:1.5rem;font-weight:700;color:#7aa2ff}}.kpi span{{display:block;font-size:.72rem;color:#9aa7b4;font-weight:400}}
.f{{border-top:1px solid #1b2230;padding:.55rem 0;font-size:.88rem}}.f b{{color:#e0a458}}.gov{{color:#6b7682;font-size:.74rem;margin-top:1rem}}</style></head>
<body><h1>AIDevObserver</h1><div class=tag>/demo · watches AI usage · reviews the session</div>
<p class=sub>Load an example AI-coding session (or paste your own transcript), then run the real reviewer. It flags
reinvention, wasted context, and footguns — the same engine that powers the live intra-session coach.</p>
<label>Example configuration</label><select id=ex>{opts}</select>
<label>Session transcript (JSON array of {{role, content}})</label><textarea id=msgs></textarea>
<button onclick=review()>Review session →</button>
<div class=report id=report></div>
<script>
const EX = {json.dumps({k: v["messages"] for k, v in EXAMPLES.items()})};
const exSel = document.getElementById('ex'), ta = document.getElementById('msgs');
function load() {{ ta.value = JSON.stringify(EX[exSel.value], null, 2); }}
exSel.onchange = load; load();
async function review() {{
  let messages; try {{ messages = JSON.parse(ta.value); }} catch (e) {{ alert('Invalid JSON: ' + e.message); return; }}
  const r = await fetch('/review', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{messages}})}});
  const rep = await r.json(), s = rep.summary || {{}}, box = document.getElementById('report');
  const findings = (rep.report || []).map(f => `<div class=f><b>${{f.type||'finding'}}</b> — ${{(f.message||f.detail||JSON.stringify(f)).toString().slice(0,200)}}</div>`).join('') || '<div class=f>No findings — clean session.</div>';
  box.innerHTML = `<div class=kpi><div>${{s.findings||0}}<span>findings</span></div><div>${{s.reinventions||0}}<span>reinventions</span></div><div>${{s.waste_signals||0}}<span>waste signals</span></div><div>${{s.messages_reviewed||0}}<span>messages</span></div></div>${{findings}}<div class=gov>governed candidate findings · discovery ≠ trust · serves_truth=false</div>`;
  box.style.display = 'block';
}}
</script></body></html>"""


class _H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/demo"):
            self._send(200, _page())
        else:
            self._send(404, "not found")

    def do_POST(self):
        if self.path != "/review":
            self._send(404, "not found")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
            messages = payload.get("messages", [])
            assert isinstance(messages, list)
            report = review_session(messages)
        except Exception as e:  # noqa: BLE001
            self._send(400, json.dumps({"error": str(e)}), "application/json")
            return
        self._send(200, json.dumps(report), "application/json")

    def log_message(self, *a):
        pass


def self_test() -> int:
    # the demo runs the REAL reviewer over an example config
    rep = review_session(EXAMPLES["reinvention-heavy"]["messages"])
    assert rep["serves_truth"] is False and "report" in rep, "governed report"
    assert rep["summary"]["by_type"].get("reinvention", 0) >= 2, f"catches reinventions: {rep['summary']['by_type']}"
    assert review_session(EXAMPLES["clean"]["messages"])["summary"]["findings"] == 0, "clean session is quiet"
    assert "AIDevObserver" in _page() and "/review" in _page(), "page renders + wires the endpoint"
    print("aidevobserver_demo_server self-test: OK (real reviewer over example configs; reinvention-heavy≥2, clean=0)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8110
    print(f"AIDevObserver /demo on http://127.0.0.1:{port}")
    http.server.HTTPServer(("127.0.0.1", port), _H).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
