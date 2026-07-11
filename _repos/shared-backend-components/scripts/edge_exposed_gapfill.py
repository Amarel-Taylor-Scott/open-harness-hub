#!/usr/bin/env python3
"""scripts.edge_exposed_gapfill — the PARTIAL-COMPOSITION model: the primitive database solves the PORTIONS it
covers deterministically (0 model tokens, verified), EXPOSES their edges (typed interfaces), and the LLM fills ONLY
the task-specific GAP wired against those edges.

Owner (2026-07-09): "our database can't solve every single portion of a coding task, but it could at least solve
some of them, expose the edges and then let an LLM fill in the gap." This is the realistic middle ground between
"prompt the model to reuse the whole thing" (it re-implements + fails) and "deterministic compose the whole thing"
(only works at 100% coverage). Here the DB covers the HARD, error-prone infrastructure (tokenize · BM25 · HTTP serve)
verified-by-construction, and the model writes only the small BUSINESS-SPECIFIC rule the DB cannot have.

Demonstration task — a PRIORITY-BOOSTED search service:
  covered (mounted, verified): tokenize, BM25 ranking, and make_search_service(boost_fn) (full IR + HTTP)
  gap    (model writes):       boost_fn(doc, base_score)->float — a task-specific rule, wired against the exposed edge

Lanes measured (executed against the hidden oracle): `without` (model builds EVERYTHING incl. BM25+HTTP) vs
`edge_gapfill` (model writes ONLY the ~1-function gap over the verified covered pieces). Metrics: oracle_pass,
output tokens, coverage fraction. serves_truth=false.

    python3 scripts/edge_exposed_gapfill.py --self-test
    python3 scripts/edge_exposed_gapfill.py --live --provider openrouter --model z-ai/glm-4.6 --repeats 4
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import socket  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts.reuse_experiment_policy import (  # noqa: E402
    CODEX_OPENROUTER_KEY_COUNT,
    DEFAULT_LIVE_REPEATS,
    REPORTING_MIN_N,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"
TASK_FAMILY = "priority_boosted_bm25_search_service__stdlib_http"
COVERAGE_BASIS = "equal_task_stages"
VALID_LANES = frozenset({"without", "edge_gapfill"})

# ── the COVERED verified molecule (mounted verbatim): full IR + HTTP; calls a boost_fn(doc, base_score)->float ──
SEARCH_SERVICE_SOURCE = (
    "import argparse, json, math, re\n"
    "from collections import Counter\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
    "from urllib.parse import urlparse, parse_qs\n"
    "_WORD = re.compile(r'[a-z0-9]+')\n\n\n"
    "def tokenize(text):\n"
    "    return _WORD.findall(text.lower())\n\n\n"
    "def bm25_scores(docs, query, k1=1.5, b=0.75):\n"
    "    n = len(docs)\n"
    "    if n == 0:\n"
    "        return []\n"
    "    df = Counter()\n"
    "    for d in docs:\n"
    "        df.update(set(d))\n"
    "    avgdl = sum(len(d) for d in docs) / n\n"
    "    out = []\n"
    "    for d in docs:\n"
    "        dl = len(d); tf = Counter(d); s = 0.0\n"
    "        for q in query:\n"
    "            if q not in tf:\n"
    "                continue\n"
    "            idf = math.log(1 + (n - df[q] + 0.5) / (df[q] + 0.5))\n"
    "            s += idf * (tf[q] * (k1 + 1)) / (tf[q] + k1 * (1 - b + b * dl / avgdl))\n"
    "        out.append(s)\n"
    "    return out\n\n\n"
    "def make_search_service(boost_fn):\n"
    "    '''Full IR + HTTP search service. You supply boost_fn(doc, base_score)->float; the service applies it to\n"
    "    each doc's BM25 base score and ranks by the boosted score. Returns a handler class; serve with run().'''\n"
    "    corpus = {}  # id -> tokens\n"
    "    raw = {}     # id -> doc dict\n\n"
    "    class _H(BaseHTTPRequestHandler):\n"
    "        def _send(self, code, obj):\n"
    "            b = json.dumps(obj).encode(); self.send_response(code)\n"
    "            self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))\n"
    "            self.end_headers(); self.wfile.write(b)\n\n"
    "        def do_POST(self):\n"
    "            if urlparse(self.path).path != '/index':\n"
    "                return self._send(404, {'error': 'not_found'})\n"
    "            n = int(self.headers.get('Content-Length', 0) or 0)\n"
    "            for d in json.loads(self.rfile.read(n) or b'{}').get('docs', []):\n"
    "                corpus[d['id']] = tokenize(d['text']); raw[d['id']] = d\n"
    "            return self._send(200, {'indexed': len(corpus)})\n\n"
    "        def do_GET(self):\n"
    "            u = urlparse(self.path)\n"
    "            if u.path == '/health':\n"
    "                return self._send(200, {'status': 'ok', 'healthy': True, 'docs': len(corpus)})\n"
    "            if u.path == '/search':\n"
    "                qs = parse_qs(u.query); q = tokenize((qs.get('q') or [''])[0])\n"
    "                ids = list(corpus); base = bm25_scores([corpus[i] for i in ids], q)\n"
    "                scored = [(i, float(boost_fn(raw[i], bs))) for i, bs in zip(ids, base)]\n"
    "                scored.sort(key=lambda x: (-x[1], str(x[0])))\n"
    "                return self._send(200, {'results': [{'id': i, 'score': round(s, 4)} for i, s in scored]})\n"
    "            return self._send(404, {'error': 'not_found'})\n\n"
    "        def log_message(self, *a):\n"
    "            pass\n"
    "    return _H\n\n\n"
    "def run(handler, port=None):\n"
    "    if port is None:\n"
    "        ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8000); port = ap.parse_args().port\n"
    "    HTTPServer(('127.0.0.1', port), handler).serve_forever()\n"
)

# the GAP the model must write (the reference; also what a correct gap-fill looks like)
_GOOD_GAP_APP = (
    "from search_service import make_search_service, run\n\n\n"
    "def boost(doc, base_score):\n"
    "    # task rule: priority docs are boosted above non-priority\n"
    "    return base_score * 2.0 + 1.0 if doc.get('priority') else base_score\n\n\n"
    "Handler = make_search_service(boost)\n\n"
    "if __name__ == '__main__':\n"
    "    run(Handler)\n"
)

# the task's declared stages (coverage is COMPUTED from this, never asserted)
TASK_STAGES = [
    {"name": "tokenize", "covered": True, "edge": "tokenize(text) -> list[str]"},
    {"name": "bm25_rank", "covered": True, "edge": "bm25_scores(docs_tokens, query_tokens) -> list[float]"},
    {"name": "http_serve", "covered": True, "edge": "make_search_service(boost_fn) -> handler; run(handler)"},
    {"name": "priority_boost_rule", "covered": False,
     "edge": "boost_fn(doc: dict, base_score: float) -> float",
     "rule": "priority docs (doc['priority'] is true) must rank ABOVE equally-relevant non-priority docs"},
]
COVERED_MODULE = "search_service.py"

_GOAL_FULL = (
    "Build a PRIORITY-BOOSTED semantic search service (Python stdlib only; boots with `python app.py --port N`). "
    "JSON responses. Endpoints: GET /health -> 200 {status:ok, healthy:true, docs:<n>}; POST /index "
    "{docs:[{id,text,priority}]} -> 200 {indexed:<n>}; GET /search?q=<query> -> 200 {results:[{id,score}]} ranked by "
    "BM25 relevance, BUT documents with priority=true must be BOOSTED so they rank above equally-relevant "
    "non-priority documents. Use real BM25 (idf, tf saturation, length norm)."
)


def _oracle_source() -> str:
    return (
        "import json, os, sys, socket, subprocess, time, http.client\n"
        "from urllib.parse import urlencode\n"
        "def _fp():\n s=socket.socket(); s.bind(('127.0.0.1',0)); p=s.getsockname()[1]; s.close(); return p\n"
        "def _req(port,method,path,body=None):\n"
        " c=http.client.HTTPConnection('127.0.0.1',port,timeout=3)\n"
        " c.request(method,path,body=json.dumps(body) if body is not None else None,headers={'Content-Type':'application/json'})\n"
        " r=c.getresponse(); raw=r.read().decode() or '{}'; c.close()\n"
        " try:\n  return r.status, json.loads(raw)\n except Exception:\n  return r.status, {}\n"
        "port=_fp()\n"
        "proc=subprocess.Popen([sys.executable,'app.py','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,cwd=os.getcwd())\n"
        "checks={}; observations={}\n"
        "try:\n"
        " ready=False\n"
        " for _ in range(50):\n"
        "  try:\n"
        "   if _req(port,'GET','/health')[0]==200: ready=True; break\n"
        "  except Exception: time.sleep(0.1)\n"
        " checks['server_boots']=ready\n"
        " if ready:\n"
        "  st,b=_req(port,'POST','/index',{'docs':[{'id':'d1','text':'the cat sat on the mat','priority':False},{'id':'d2','text':'dense vector search with embeddings','priority':False},{'id':'d3','text':'dense vector search with embeddings','priority':True}]})\n"
        "  observations['index']=[st,b]; checks['index_200']=(st==200 and b=={'indexed':3})\n"
        "  st,b=_req(port,'GET','/search?'+urlencode({'q':'vector embeddings search'}))\n"
        "  res=b.get('results',[]); observations['search']=[st,[x.get('id') for x in res]]\n"
        "  checks['priority_boosted_first']=(st==200 and len(res)>=2 and res[0].get('id')=='d3')\n"
        "  checks['relevant_second']=(len(res)>=2 and res[1].get('id')=='d2')\n"
        "  checks['irrelevant_last']=(res[-1].get('id')=='d1')\n"
        "  hst,hb=_req(port,'GET','/health'); observations['health']=[hst,hb]\n"
        "  checks['health_ok']=(hst==200 and hb=={'status':'ok','healthy':True,'docs':3})\n"
        "finally:\n"
        " proc.terminate()\n"
        " try:\n  proc.wait(timeout=5)\n except Exception:\n  proc.kill()\n"
        "op=len(checks)>=5 and all(checks.values())\n"
        "print('ORACLE '+json.dumps({'checks':checks,'observations':observations,'oracle_pass':op}))\n"
    )


def _run_build(files: dict[str, str], extra: dict[str, str] | None = None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        for fn, content in {**(extra or {}), **files}.items():
            (wsp / fn).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fn).write_text(content, encoding="utf-8")
        (wsp / "oracle.py").write_text(_oracle_source(), encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "oracle.py"], cwd=ws, capture_output=True, text=True, timeout=90)
        except subprocess.TimeoutExpired:
            return {"oracle_pass": False, "checks": {}, "error": "timeout"}
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("ORACLE ")), None)
        res = json.loads(line[len("ORACLE "):]) if line else {"checks": {}, "oracle_pass": False}
        res["stderr_tail"] = (proc.stderr or "")[-200:] if not res["oracle_pass"] else ""
        return res


def coverage_fraction() -> float:
    return round(sum(1 for s in TASK_STAGES if s["covered"]) / len(TASK_STAGES), 3)


def _gapfill_prompt() -> str:
    edges = "\n".join(f"  - {s['name']}: {s['edge']}" + (f"  [YOU WRITE THIS: {s['rule']}]" if not s["covered"] else
                                                         "  (already provided, verified)") for s in TASK_STAGES)
    return (
        f"{_GOAL_FULL}\n\nThe hard infrastructure is ALREADY BUILT, TESTED, and in your workspace as "
        f"`{COVERED_MODULE}`. Do NOT re-implement tokenization, BM25, or the HTTP server. These pieces are provided "
        f"with these exact edges:\n{edges}\n\n`make_search_service(boost_fn)` returns a ready handler that does all "
        f"indexing, BM25, and HTTP; it calls YOUR `boost_fn(doc, base_score)` on each document to compute the final "
        f"ranking score. Write ONLY `app.py`: define the small `boost_fn` implementing the priority rule, then "
        f"`Handler = make_search_service(boost_fn)` and `run(Handler)` under `__main__`. Emit just app.py in a fenced "
        f"block starting `# filename: app.py`.\n"
    )


def _full_prompt() -> str:
    return (f"{_GOAL_FULL}\n\nBuild it from scratch as app.py (single file, Python stdlib only). Emit app.py in a "
            f"fenced block starting `# filename: app.py`.\n")


def _parse_app(text: str) -> str:
    import re  # noqa: PLC0415
    m = re.search(r"```(?:python)?[^\n]*\n(.*?)```", text or "", re.S)
    body = m.group(1) if m else (text or "")
    return re.sub(r"^#\s*filename:.*\n", "", body, flags=re.M).strip() + "\n"


def run_lane(lane: str, agent: Callable[[str], dict]) -> dict[str, Any]:
    """`without` = model writes everything; `edge_gapfill` = model writes only the gap over the mounted covered module."""
    if lane not in VALID_LANES:
        raise ValueError(f"unknown edge-gapfill lane {lane!r}; expected one of {sorted(VALID_LANES)}")
    prompt = _gapfill_prompt() if lane == "edge_gapfill" else _full_prompt()
    gen = agent(prompt)
    if gen.get("error"):
        # A provider/rate-limit/response-schema failure did not execute the
        # benchmark.  Preserve it as a retryable attempt and never feed an
        # empty fabricated program to the hidden oracle.
        return {"lane": lane, "family": TASK_FAMILY, "oracle_pass": None,
                "output_tokens": gen.get("completion_tokens", 0) or 0,
                "input_tokens": gen.get("input_tokens", 0) or 0, "app_chars": 0,
                "reimplemented_covered": None, "checks_passed": 0,
                "oracle_checks": {}, "oracle_observations": {},
                "input_token_source": gen.get("input_token_source") or "missing",
                "output_token_source": gen.get("output_token_source") or "missing",
                "coverage_fraction": coverage_fraction() if lane == "edge_gapfill" else 0.0,
                "coverage_basis": COVERAGE_BASIS, "error": str(gen["error"])[:140]}
    app = _parse_app(gen.get("code") or "")
    extra = {"search_service.py": SEARCH_SERVICE_SOURCE} if lane == "edge_gapfill" else None
    res = _run_build({"app.py": app}, extra=extra)
    reimpl = ("def bm25" in app.lower()) or ("BaseHTTPRequestHandler" in app)  # did it re-implement covered infra?
    return {"lane": lane, "family": TASK_FAMILY, "oracle_pass": bool(res["oracle_pass"]),
            "output_tokens": gen.get("completion_tokens", 0) or 0,
            "input_tokens": gen.get("input_tokens", 0) or 0, "app_chars": len(app),
            "reimplemented_covered": reimpl if lane == "edge_gapfill" else None,
            "checks_passed": sum(1 for v in res.get("checks", {}).values() if v),
            "oracle_checks": res.get("checks") or {},
            "oracle_observations": res.get("observations") or {},
            "input_token_source": (gen.get("input_token_source") or
                                   ("provider_unverified" if (gen.get("input_tokens", 0) or 0) > 0 else "missing")),
            "output_token_source": (gen.get("output_token_source") or
                                    ("provider_unverified" if (gen.get("completion_tokens", 0) or 0) > 0
                                     else "missing")),
            "coverage_fraction": coverage_fraction() if lane == "edge_gapfill" else 0.0,
            "coverage_basis": COVERAGE_BASIS, "error": None}


def self_test() -> bool:
    """Mutation-gated + REAL: (1) the covered module alone is verified — the reference gap-fill app boots + passes the
    hidden priority-boost oracle; (2) a GOOD mock in the edge_gapfill lane writes only the tiny gap and PASSES with
    reimplemented_covered=False; (3) the SAME good gap in the `without` lane FAILS (no covered module mounted -> the
    import is unresolved) proving the covered module is load-bearing; (4) a mock that omits the boost rule FAILS the
    oracle (the gap really matters); (5) coverage fraction computes from the stage list."""
    # (1) reference gap-fill over the verified covered module passes the real oracle
    ref = _run_build({"app.py": _GOOD_GAP_APP}, extra={"search_service.py": SEARCH_SERVICE_SOURCE})
    assert ref["oracle_pass"] is True, f"reference gap-fill must pass the priority-boost oracle: {ref}"

    # (2) edge_gapfill lane with a good mock (writes only the gap)
    def good_gap(prompt: str) -> dict:
        return {"code": f"# filename: app.py\n```python\n{_GOOD_GAP_APP}```", "completion_tokens": len(_GOOD_GAP_APP) // 4,
                "input_tokens": len(prompt) // 4}
    gf = run_lane("edge_gapfill", good_gap)
    assert gf["oracle_pass"] is True and gf["reimplemented_covered"] is False, gf

    # (3) the same gap app in `without` lane fails (no covered module mounted -> import fails)
    wo = run_lane("without", good_gap)
    assert wo["oracle_pass"] is False, "the gap app needs the covered module; without it, it must fail"

    # (4) a mock that ignores the boost rule (returns base only) -> priority doc NOT boosted -> oracle fails
    no_boost = ("from search_service import make_search_service, run\n"
                "Handler = make_search_service(lambda doc, base_score: base_score)\n"
                "if __name__ == '__main__':\n    run(Handler)\n")
    nb = _run_build({"app.py": no_boost}, extra={"search_service.py": SEARCH_SERVICE_SOURCE})
    assert nb["oracle_pass"] is False, "omitting the boost rule must FAIL (the gap is real + tested)"

    # (5) provider/transport failures are attempts, not executed benchmark
    # failures.  This is load-bearing for resumable grid integration.
    transport = run_lane(
        "edge_gapfill",
        lambda _prompt: {"code": "", "completion_tokens": 0, "input_tokens": 0, "error": "http503"},
    )
    assert transport["oracle_pass"] is None and transport["error"] == "http503", transport
    transport_ab = live_ab(
        lambda _prompt: {"code": "", "completion_tokens": 0, "input_tokens": 0, "error": "http503"}, 1,
    )
    assert all(cell["n"] == 0 and cell["n_retryable_errors"] == 1
               for cell in transport_ab["aggregates"].values())
    assert transport_ab["paired"]["n_both_pass"] == 0

    try:
        run_lane("not_a_lane", good_gap)
    except ValueError:
        pass
    else:
        raise AssertionError("an unknown edge-gapfill lane must fail loudly")

    cov = coverage_fraction()
    assert cov == 0.75, f"coverage should be 3/4 = 0.75, got {cov}"

    print(f"OK edge_exposed_gapfill self-test: covered module (tokenize+BM25+HTTP) verified — reference gap-fill "
          f"boots + passes the priority-boost oracle ({sum(1 for v in ref['checks'].values() if v)} checks); a good "
          f"gap-fill writes ONLY the {len(_GOOD_GAP_APP)}-char boost+wiring (reimpl=False) and PASSES; the same app "
          f"WITHOUT the covered module FAILS (module is load-bearing); omitting the boost rule FAILS (gap is real); "
          f"provider errors stay retryable (oracle_pass=None); coverage={cov} (3/4 equally weighted stages covered, "
          f"1 gap). serves_truth=false")
    return True


def live_ab(agent: Callable[[str], dict], repeats: int) -> dict[str, Any]:
    rows = []
    for repeat in range(repeats):
        for lane in ("without", "edge_gapfill"):
            rows.append({**run_lane(lane, agent), "repeat": repeat})
    import statistics  # noqa: PLC0415
    agg = {}
    for lane in ("without", "edge_gapfill"):
        rs = [r for r in rows if r["lane"] == lane]
        completed = [r for r in rs if not r.get("error") and isinstance(r.get("oracle_pass"), bool)]
        reimpls = [r["reimplemented_covered"] for r in completed
                   if isinstance(r.get("reimplemented_covered"), bool)]
        reportable = len(completed) >= REPORTING_MIN_N
        agg[lane] = {"n": len(completed), "n_attempts": len(rs),
                     "n_retryable_errors": len(rs) - len(completed),
                     "reportable": reportable, "headline_eligible": False,
                     "status": ("reportable sample; compare only matched both-pass arms" if reportable else
                                f"insufficient n (<{REPORTING_MIN_N})"),
                     "pass_rate": (round(sum(r["oracle_pass"] for r in completed) / len(completed), 3)
                                   if completed else None),
                     "median_out_tokens": (round(statistics.median([r["output_tokens"] for r in completed]), 1)
                                           if completed else None),
                     "reimpl_covered_rate": (round(sum(reimpls) / len(reimpls), 3) if reimpls else None)}
    by_key = {(r["lane"], r["repeat"]): r for r in rows if not r.get("error")}
    pairs = [(by_key.get(("without", repeat)), by_key.get(("edge_gapfill", repeat)))
             for repeat in range(repeats)]
    both_pass = [(baseline, treatment) for baseline, treatment in pairs
                 if baseline and treatment and baseline.get("oracle_pass") is True
                 and treatment.get("oracle_pass") is True]
    exact_both_pass = [
        (baseline, treatment) for baseline, treatment in both_pass
        if baseline.get("input_token_source") == baseline.get("output_token_source") == "provider"
        and treatment.get("input_token_source") == treatment.get("output_token_source") == "provider"
    ]
    median_total_saved = (round(statistics.median(
        (baseline["input_tokens"] + baseline["output_tokens"])
        - (treatment["input_tokens"] + treatment["output_tokens"])
        for baseline, treatment in exact_both_pass), 1) if exact_both_pass else None)
    reportable = len(exact_both_pass) >= REPORTING_MIN_N
    paired = {"n_pairs": sum(1 for baseline, treatment in pairs if baseline and treatment),
              "n_both_pass": len(both_pass),
              "n_both_pass_complete_token_accounting": len(exact_both_pass),
              "median_output_tokens_saved": (round(statistics.median(
                  baseline["output_tokens"] - treatment["output_tokens"]
                  for baseline, treatment in exact_both_pass), 1) if exact_both_pass else None),
              "median_total_tokens_saved": median_total_saved,
              "reportable": reportable,
              "headline_eligible": bool(reportable and median_total_saved is not None and median_total_saved > 0),
              "status": ("reportable matched both-pass sample" if reportable else
                         f"insufficient n (<{REPORTING_MIN_N} both-pass pairs with provider usage)")}
    return {"record_type": "edge_exposed_gapfill_ab", "benchmark_kind": BENCHMARK_KIND,
            "family": TASK_FAMILY, "coverage_fraction": coverage_fraction(),
            "coverage_basis": COVERAGE_BASIS, "aggregates": agg, "paired": paired, "rows": rows, **BOUNDARY}


def main() -> None:
    ap = argparse.ArgumentParser(description="Partial composition: DB covers portions + exposes edges, LLM fills gap.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--provider", default="openrouter")
    ap.add_argument("--model", default="")
    ap.add_argument("--repeats", type=int, default=DEFAULT_LIVE_REPEATS)
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.live:
        import scripts.run_large_project_ab as rlp  # noqa: PLC0415
        from scripts.primitive_token_savings_ab import live_model  # noqa: PLC0415
        base_url, keyfile, default_model = rlp._PROVIDERS[args.provider]
        pool = rlp._load_key_file(keyfile) if keyfile else rlp._load_key_file(f"{args.provider}_keys.txt")
        if args.provider == "openrouter":
            pool = pool[:CODEX_OPENROUTER_KEY_COUNT]
        model = args.model or default_model

        def agent(prompt: str) -> dict:
            return live_model(prompt, pool, model, max_tokens=16000, strip=False, base_url=base_url)
        rep = live_ab(agent, args.repeats)
        out = resource("data/dev-intel/edge_exposed_gapfill"); out.mkdir(parents=True, exist_ok=True)
        (out / f"ab_{args.provider}.json").write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({"coverage_fraction": rep["coverage_fraction"], "aggregates": rep["aggregates"]}, indent=2))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
