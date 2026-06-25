#!/usr/bin/env python3
"""scripts.byo_demo_server — one CONSISTENT /demo per surface, each with a BRING-YOUR-OWN-KEY input.

Owner 2026-06-25. Serves a consistent demo page for each product surface (AIDevObserver · Teleon · Baltor · Open*Hubs):
the user pastes their API key + a prompt, clicks Run, and the demo runs with THEIR key via
src.teleon.demos.byo_key_demo (transient env scope, redaction-safe, NEVER stored). Same layout/CSS/fonts; only the
accent + copy differ. serves_truth=false.

  python3 scripts/byo_demo_server.py [--port 8120]    then tunnel it
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

from src.teleon.demos.byo_key_demo import DEMOS, run_byo_demo  # noqa: E402

ACCENT = {"aidevobserver": "#c98bdb", "teleon": "#56d4c4", "baltor": "#e0a458", "open-star-hubs": "#7aa2ff"}
TITLE = {"aidevobserver": "AIDevObserver", "teleon": "Teleon.dev", "baltor": "Baltor.ai", "open-star-hubs": "Open*Hubs"}
EXAMPLE = {
    "aidevobserver": "(loads an example AI session — no key needed)",
    "teleon": "summarize server logs into a cited incident report",
    "baltor": "What is the max legal interest rate in Texas? Source: (paste a statute)",
    "open-star-hubs": "extract renewal + liability clauses from contracts",
}

_CSS = """*{box-sizing:border-box}body{font-family:'Hanken Grotesk',system-ui,sans-serif;background:#0b0e14;color:#e6edf3;margin:0;padding:2.2rem 1.2rem;line-height:1.5}
.wrap{max-width:760px;margin:0 auto}a{color:var(--a);text-decoration:none}h1{font-size:1.6rem;margin:0 0 .2rem}
.tag{display:inline-block;border:1px solid #21262d;border-radius:999px;padding:3px 11px;color:#9aa7b4;font-size:12px;margin-bottom:1.1rem}
.sub{color:#9aa7b4;margin:.2rem 0 1.3rem}label{font-size:.84rem;color:#9aa7b4;display:block;margin:.9rem 0 .3rem}
input,textarea,select{width:100%;background:#11161d;color:#e6edf3;border:1px solid #21262d;border-radius:9px;padding:.6rem .7rem;font:13px ui-monospace,monospace}
textarea{height:90px}.key{border-color:var(--a)}.note{font-size:.74rem;color:#6b7682;margin:.3rem 0 0}
button{margin-top:1rem;color:#0b0e14;background:var(--a);border:0;border-radius:9px;padding:.6rem 1.1rem;font-weight:700;cursor:pointer}
.out{margin-top:1.4rem;border:1px solid #21262d;border-radius:12px;background:#11161d;padding:1rem 1.1rem;display:none;white-space:pre-wrap;font:12.5px ui-monospace,monospace}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.9rem;margin-top:1.2rem}
.card{border:1px solid #21262d;border-radius:12px;background:#11161d;padding:1rem}.card h2{font-size:1.05rem;margin:0 0 .3rem}"""


def _index() -> str:
    cards = "".join(
        f'<a class="card" style="--a:{ACCENT[s]}" href="/demo/{s}"><h2 style="color:{ACCENT[s]}">{TITLE[s]}</h2>'
        f'<div class="sub">{d["label"]}</div><span class="tag">try it with your key →</span></a>'
        for s, d in DEMOS.items())
    return (f"<!doctype html><meta charset=utf-8><title>Demos — bring your own key</title><style>{_CSS}</style>"
            f'<div class="wrap" style="--a:#7aa2ff"><h1>Demos — bring your own key</h1>'
            f'<p class="sub">Every surface runs with <b>your</b> API key. The key is used only for that one call and '
            f'is never stored or logged.</p><div class="cards">{cards}</div></div>')


def _page(surface: str) -> str:
    a = ACCENT[surface]
    needs = DEMOS[surface]["needs_key"]
    keyfield = (f'<label>Your API key {"(required)" if needs else "(optional)"}</label>'
                f'<input class="key" id="key" type="password" placeholder="sk-… or your provider key" autocomplete="off">'
                f'<p class="note">Used only for this request · never stored · only a redacted status (sk-…1234) is shown.</p>')
    return (f"<!doctype html><meta charset=utf-8><title>{TITLE[surface]} — /demo</title><style>{_CSS}</style>"
            f'<div class="wrap" style="--a:{a}"><a href="/">← all demos</a><h1 style="color:{a}">{TITLE[surface]}</h1>'
            f'<div class="tag">/demo · bring your own key</div><p class="sub">{DEMOS[surface]["label"]}.</p>'
            f'{keyfield}<label>Prompt</label><textarea id="prompt">{EXAMPLE[surface]}</textarea>'
            f'<button onclick="run()">Run with my key →</button><div class="out" id="out"></div>'
            "<script>async function run(){"
            "const key=document.getElementById('key').value,prompt=document.getElementById('prompt').value,o=document.getElementById('out');"
            "o.style.display='block';o.textContent='running…';"
            f"const r=await fetch('/run',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{demo:'{surface}',byo_key:key,inputs:{{prompt}}}})}});"
            "const j=await r.json();o.textContent=JSON.stringify(j,null,2);}</script></div>")


class _H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        p = self.path.rstrip("/")
        if p in ("", "/demo"):
            self._send(200, _index())
        elif p.startswith("/demo/") and p[6:] in DEMOS:
            self._send(200, _page(p[6:]))
        else:
            self._send(404, "not found")

    def do_POST(self):
        if self.path != "/run":
            self._send(404, "not found")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            out = run_byo_demo(req.get("demo", ""), byo_key=req.get("byo_key") or None, inputs=req.get("inputs") or {})
        except Exception as e:  # noqa: BLE001
            out = {"ok": False, "error": str(e)}
        self._send(200, json.dumps(out), "application/json")

    def log_message(self, *a):
        pass


def self_test() -> int:
    idx = _index()
    assert all(f"/demo/{s}" in idx for s in DEMOS), "index links every surface demo"
    for s in DEMOS:
        pg = _page(s)
        assert "bring your own key" in pg and 'id="key"' in pg and "never stored" in pg, f"{s} page has a governed BYO-key input"
    # the POST path actually runs the governed plane (no key → honest, key → redacted, never leaked)
    out = run_byo_demo("teleon", byo_key="sk-secret-9999ZZZZ", inputs={"prompt": "x"})
    assert out["used_byo"] and "sk-secret-9999ZZZZ" not in json.dumps(out), "BYO key honored + never leaked"
    print(f"byo_demo_server self-test: OK ({len(DEMOS)} consistent /demo pages, governed BYO-key input)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8120
    print(f"BYO-key demos on http://127.0.0.1:{port}")
    http.server.HTTPServer(("127.0.0.1", port), _H).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
