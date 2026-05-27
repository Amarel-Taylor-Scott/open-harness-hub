#!/usr/bin/env python3
"""Local showcase site for the paste-to-flow conversational builder.

Zero-dependency (stdlib ``http.server``). It demonstrates the headline product
interaction from ``docs/codex/master-goal.md``:

    paste a task  ->  hybrid-retrieve components  ->  assemble a flow
                  ->  estimate cost  ->  explain (optional local model)

Retrieval is **hybrid** (keyword + label + vector), so it returns sensible
results offline on the placeholder hash vectors, and gets sharper the moment a
real embedding backend is configured (``OH_EMBED_*``; see scripts/embeddings.py).
The "explain" narrative uses a local model (Gemma via Ollama) when one is
reachable (``OH_LLM_*``; see scripts/model_routes.py) and falls back to a
deterministic explanation otherwise — local now, cloud later, by env var only.

Run:
    python3 -m scripts.serve_builder            # http://127.0.0.1:8000
    python3 -m scripts.serve_builder --port 9000 --self-test
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts.db import build_vector_store as vs
from scripts.embeddings import describe_backend, resolve_backend
from scripts.model_routes import resolve_route

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.+-]{1,40}")
# Order in which an assembled flow is presented (rough pre-LLM -> model -> post).
FLOW_ORDER = [
    "persona", "knowledge-pack", "rule-pack", "tool", "processor", "harness",
    "adapter", "logic-pack", "pattern", "pipeline", "rubric", "benchmark", "dataset",
]
ROLE_BLURB = {
    "persona": "frames the role the model adopts",
    "knowledge-pack": "grounds answers in citeable facts (retrieval)",
    "rule-pack": "deterministic checks/filters applied before the model",
    "tool": "function-call capability the model invokes",
    "processor": "deterministic pre/post transform (no model call)",
    "harness": "runs the model behind a trust boundary",
    "adapter": "model transport — swap local <-> hosted here",
    "logic-pack": "prompts / schemas / response policy",
    "pattern": "reusable workflow shape",
    "pipeline": "an end-to-end backbone you can deploy",
    "rubric": "scores the output (the benchmark contract)",
    "benchmark": "proves the capability lift vs a bare model",
    "dataset": "labeled inputs/outputs for evaluation",
}


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


class Index:
    """In-memory hybrid index loaded once from the vector store."""

    def __init__(self) -> None:
        self.backend = resolve_backend()
        store = vs.DEFAULT_STORE
        if not store.exists():
            vs.build(store=store, model=self.backend.model_id)
        con = sqlite3.connect(store)
        rows = con.execute(
            "SELECT subject_id, subject_type, text, embedding FROM object_embedding WHERE embedding_model=?",
            (self.backend.model_id,),
        ).fetchall()
        if not rows:  # store built with a different model — (re)build for this one
            con.close()
            vs.build(store=store, model=self.backend.model_id)
            con = sqlite3.connect(store)
            rows = con.execute(
                "SELECT subject_id, subject_type, text, embedding FROM object_embedding WHERE embedding_model=?",
                (self.backend.model_id,),
            ).fetchall()
        self.labels: dict[str, list[str]] = {}
        for sid, label in con.execute("SELECT subject_id, label FROM label_assignment"):
            self.labels.setdefault(sid, []).append(label)
        con.close()
        self.items = []
        for sid, stype, text, emb in rows:
            name, desc = (text.split(" · ", 2) + ["", ""])[:2]
            self.items.append({
                "id": sid, "type": stype, "name": name.strip() or sid,
                "desc": desc.strip(), "text": text, "tokens": _tokens(text),
                "vec": json.loads(emb), "labels": self.labels.get(sid, []),
            })

    def search(self, task: str, k: int = 40) -> list[dict]:
        qtok = _tokens(task)
        qvec = self.backend.embed_one(task)
        out = []
        for it in self.items:
            lex = len(qtok & it["tokens"]) / (len(qtok) + 1)         # keyword overlap
            vec = sum(a * b for a, b in zip(qvec, it["vec"]))         # cosine (both L2)
            lab = 0.05 * len(set(it["labels"]) & qtok)               # label boost
            score = 0.6 * lex + 0.35 * max(0.0, vec) + lab
            if score > 0:
                shared = sorted(qtok & it["tokens"])[:6]
                out.append({**{x: it[x] for x in ("id", "type", "name", "desc", "labels")},
                            "score": round(score, 4), "matched": shared})
        out.sort(key=lambda r: r["score"], reverse=True)
        return out[:k]


def assemble_flow(candidates: list[dict]) -> dict:
    by_type: dict[str, list[dict]] = {}
    for c in candidates:
        by_type.setdefault(c["type"], []).append(c)
    caps = {"persona": 1, "knowledge-pack": 2, "rule-pack": 2, "tool": 3, "processor": 2,
            "harness": 2, "adapter": 1, "logic-pack": 1, "pattern": 2, "pipeline": 1,
            "rubric": 1, "benchmark": 1, "dataset": 1}
    flow = []
    for t in FLOW_ORDER:
        for c in by_type.get(t, [])[:caps.get(t, 1)]:
            flow.append({**c, "role": ROLE_BLURB.get(t, "")})
    return {"steps": flow, "by_type_counts": {t: len(v) for t, v in sorted(by_type.items())}}


def estimate_cost(flow: dict) -> dict:
    n_model = sum(1 for s in flow["steps"] if s["type"] in {"harness", "pipeline"})
    n_rules = sum(1 for s in flow["steps"] if s["type"] in {"rule-pack", "processor"})
    return {
        "cheap":    {"per_task_usd": "0.00–0.02", "how": f"local model + {n_rules} deterministic gate(s) run first; model only on the residual"},
        "balanced": {"per_task_usd": "0.01–0.10", "how": f"small hosted model for {n_model} model step(s); rules/retrieval pre-filter"},
        "quality":  {"per_task_usd": "0.10–0.60", "how": "frontier model on the final step; full retrieval + review gate"},
        "note": "Illustrative; calibrate against real runs. Rules/retrieval before the model is the main lever.",
    }


def deterministic_narrative(task: str, flow: dict, cost: dict) -> str:
    parts = [f"For your task, I composed a flow of {len(flow['steps'])} components:"]
    for s in flow["steps"]:
        parts.append(f" • {s['type']}/{s['id'].split('/')[-1]} — {s['role']}.")
    parts.append("Deterministic rules and retrieval run before the model to cut cost; "
                 "swap the model via the adapter without touching the rest. "
                 f"Estimated cost ~{cost['balanced']['per_task_usd']} per task (balanced). "
                 "Refine with: \"make it cheaper\" (force local model + more rules-first) or "
                 "\"stricter\" (add a review gate + tighter rubric).")
    return "\n".join(parts)


def llm_narrative(task: str, flow: dict, cost: dict) -> tuple[str, bool]:
    route = resolve_route()
    if not route.health():
        return deterministic_narrative(task, flow, cost), False
    comp_lines = "\n".join(f"- {s['type']}/{s['id'].split('/')[-1]}: {s['role']}" for s in flow["steps"])
    system = ("You are the Open Harness Hub builder. Explain, in 4–6 sentences, the assembled "
              "pipeline of EXISTING components for the user's task: what each layer does, why "
              "rules/retrieval run before the model to cut cost, and how to swap the model. "
              "Then give two one-line refinements (cheaper / stricter). Do not invent components.")
    user = f"Task: {task}\n\nAssembled components:\n{comp_lines}\n\nBalanced cost ~{cost['balanced']['per_task_usd']}/task."
    text = route.complete(system, user, max_tokens=500)
    return (text, True) if text else (deterministic_narrative(task, flow, cost), False)


def build_flow(task: str, index: Index) -> dict:
    candidates = index.search(task, k=40)
    flow = assemble_flow(candidates)
    cost = estimate_cost(flow)
    narrative, llm_used = llm_narrative(task, flow, cost)
    return {
        "task": task,
        "flow": flow,
        "cost": cost,
        "narrative": narrative,
        "llm_used": llm_used,
        "top_matches": candidates[:8],
        "embedding": describe_backend(),
    }


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
HTML = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Open Harness Hub — paste a task, get a flow</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#fb7714;--good:#3fb950}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:28px 22px 10px;max-width:980px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);font-size:14px}
main{max-width:980px;margin:0 auto;padding:12px 22px 60px}
textarea{width:100%;min-height:96px;background:var(--panel);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:12px;font:inherit;resize:vertical}
.row{display:flex;gap:10px;align-items:center;margin:10px 0}
button{background:var(--acc);color:#1a1300;border:0;border-radius:9px;padding:11px 18px;font-weight:650;cursor:pointer}
button:disabled{opacity:.5;cursor:wait}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin:6px 0 2px}
.chip{font-size:12.5px;color:var(--mut);border:1px solid var(--line);border-radius:20px;padding:4px 11px;cursor:pointer;background:var(--panel)}
.banner{font-size:13px;border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:8px;padding:9px 12px;color:var(--mut);margin:12px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:14px 16px;margin:14px 0}
.step{display:flex;gap:11px;padding:9px 0;border-bottom:1px solid var(--line)}.step:last-child{border:0}
.badge{font-size:11px;font-weight:700;letter-spacing:.3px;text-transform:uppercase;color:var(--acc);min-width:118px}
.sid{font-weight:600}.role{color:var(--mut);font-size:13.5px}
.matched{color:var(--good);font-size:12px}
.costs{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.cost{border:1px solid var(--line);border-radius:9px;padding:10px}.cost b{color:var(--acc)}
pre.narr{white-space:pre-wrap;background:transparent;color:var(--fg);margin:0;font:inherit}
.muted{color:var(--mut);font-size:12.5px}h3{margin:0 0 8px;font-size:15px}
a{color:var(--acc)}
</style></head><body>
<header><h1>Open Harness Hub <span style="color:var(--acc)">·</span> paste a task, get a flow</h1>
<div class=sub>Describe a task in plain language. The builder hybrid-searches the component registry and assembles a costed, deployable pipeline of existing components.</div></header>
<main>
<textarea id=task placeholder="e.g. Screen supplier disclosures for forced-labor risk, cite the relevant regulations, and route high-risk cases to human review."></textarea>
<div class=chips id=examples></div>
<div class=row><button id=go>Build pipeline</button><span class=muted id=status></span></div>
<div id=banner></div>
<div id=out></div>
</main>
<script>
const EX=["Screen supplier disclosures for forced-labor risk and cite the regulations",
"Turn a maintenance SOP into an AI checklist with a deterministic safety gate",
"Grade essays with an LLM judge and a rubric, with citations",
"Extract structured fields from contracts and flag risky clauses",
"Build a RAG pipeline over policy docs that refuses when evidence is missing"];
const exDiv=document.getElementById('examples');
EX.forEach(t=>{const c=document.createElement('span');c.className='chip';c.textContent=t;c.onclick=()=>{task.value=t;build()};exDiv.appendChild(c)});
const task=document.getElementById('task'),go=document.getElementById('go'),out=document.getElementById('out'),status=document.getElementById('status'),banner=document.getElementById('banner');
async function health(){try{const h=await (await fetch('/api/health')).json();
 banner.innerHTML='<div class=banner>'+(h.embedding.promotable?'✓ semantic embeddings active ('+h.embedding.embedding_model+')':'⚠ offline <b>placeholder</b> embeddings ('+h.embedding.embedding_model+') — hybrid keyword+label search is doing the work; set OH_EMBED_* for semantic ranking.')+' · '+h.components+' components · model polish: '+(h.llm_reachable?('on ('+h.llm.model+')'):'off (deterministic)')+'</div>';}catch(e){}}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function build(){const t=task.value.trim();if(!t)return;go.disabled=true;status.textContent='retrieving + assembling…';out.innerHTML='';
 try{const r=await (await fetch('/api/build?task='+encodeURIComponent(t))).json();render(r)}catch(e){out.innerHTML='<div class=card>Error: '+esc(''+e)+'</div>'}
 go.disabled=false;status.textContent='';}
function render(r){let h='';
 h+='<div class=card><h3>Assembled flow ('+r.flow.steps.length+' components)</h3>';
 r.flow.steps.forEach(s=>{h+='<div class=step><span class=badge>'+esc(s.type)+'</span><div><div class=sid>'+esc(s.name)+' <span class=muted>'+esc(s.id)+'</span></div><div class=role>'+esc(s.role)+(s.matched&&s.matched.length?' · <span class=matched>matches: '+s.matched.map(esc).join(', ')+'</span>':'')+'</div></div></div>'});
 h+='</div>';
 h+='<div class=card><h3>Cost profile (per task)</h3><div class=costs>';
 ['cheap','balanced','quality'].forEach(k=>{h+='<div class=cost><b>'+k+'</b><br>$'+esc(r.cost[k].per_task_usd)+'<br><span class=muted>'+esc(r.cost[k].how)+'</span></div>'});
 h+='</div><div class=muted style=margin-top:8px>'+esc(r.cost.note)+'</div></div>';
 h+='<div class=card><h3>Why this flow '+(r.llm_used?'<span class=muted>(explained by local model)</span>':'<span class=muted>(deterministic)</span>')+'</h3><pre class=narr>'+esc(r.narrative)+'</pre></div>';
 out.innerHTML=h;}
go.onclick=build;health();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    index: Index = None  # type: ignore

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif parsed.path == "/api/health":
            route = resolve_route()
            payload = {"embedding": self.index.backend.provenance(),
                       "components": len(self.index.items),
                       "llm": route.summary(), "llm_reachable": route.health()}
            self._send(200, json.dumps(payload).encode(), "application/json")
        elif parsed.path == "/api/build":
            task = (parse_qs(parsed.query).get("task") or [""])[0]
            if not task.strip():
                self._send(400, b'{"error":"task required"}', "application/json")
                return
            result = build_flow(task, self.index)
            self._send(200, json.dumps(result).encode(), "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *args) -> None:  # quiet
        pass


def serve(port: int = 8000) -> None:
    Handler.index = Index()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Open Harness Hub showcase → http://127.0.0.1:{port}  "
          f"({len(Handler.index.items)} components, embeddings={Handler.index.backend.name}, "
          f"promotable={Handler.index.backend.promotable})")
    httpd.serve_forever()


def _self_test() -> int:
    idx = Index()
    assert idx.items, "no components loaded"
    res = build_flow("screen suppliers for forced labor and cite regulations", idx)
    assert res["flow"]["steps"], "empty flow"
    assert res["cost"]["balanced"]["per_task_usd"]
    print(json.dumps({
        "ok": True, "components": len(idx.items),
        "embedding_backend": idx.backend.name, "promotable": idx.backend.promotable,
        "flow_size": len(res["flow"]["steps"]),
        "llm_used": res["llm_used"],
        "flow_types": res["flow"]["by_type_counts"],
        "top": [f"{m['type']}/{m['id'].split('/')[-1]} ({m['score']})" for m in res["top_matches"][:5]],
    }, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Local paste-to-flow showcase site.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    serve(args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
