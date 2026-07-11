#!/usr/bin/env python3
"""scripts.buildout_forge_search_rag — three LARGE project genomes for the WITH/WITHOUT primitive-database A/B:
an advanced semantic SEARCH ENGINE (BM25), a rule-based LABELING service (+confidence gate), and a deterministic
RAG SEARCH tool (ingest->chunk->retrieve->assemble+cite). Each is a realistic multi-file build with a hidden oracle
that BOOTS it + drives real behavior over HTTP.

Owner (2026-07-09): build these WITH and WITHOUT the primitive database and measure input/output token savings. The
verified molecules live in search_rag_primitive_pack; the compiled_route lane mounts the relevant molecule VERBATIM
(0 generation tokens) so the model writes only the thin entry, and deterministic composition can build it at 0 model
tokens. Registered into run_large_project_ab (both-arms A/B, netted input+output tokens). serves_truth=false.

    python3 scripts/buildout_forge_search_rag.py --self-test
    python3 scripts/buildout_forge_search_rag.py --solution good --genome semantic_search_engine__stdlib_http__v0
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any  # noqa: E402

from scripts.search_rag_primitive_pack import (  # noqa: E402  single source of truth for the molecules
    LABELER_SOURCE, RAG_TOOL_SOURCE, SEARCH_ENGINE_SOURCE,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"
BUILDOUT_REALISM = "B5_search_rag_project"

# ── shared HTTP-oracle helpers (boot app.py on a free port, drive JSON HTTP) ──────────────────────────────────
_ORACLE_PRELUDE = r'''
import json, os, sys, socket, subprocess, time, http.client
from urllib.parse import urlencode


def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def _req(port, method, path, body=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    payload = json.dumps(body) if body is not None else None
    c.request(method, path, body=payload, headers={"Content-Type": "application/json"})
    r = c.getresponse(); raw = r.read().decode() or "{}"; c.close()
    try:
        return r.status, json.loads(raw)
    except Exception:
        return r.status, {}


def _boot(port):
    proc = subprocess.Popen([sys.executable, "app.py", "--port", str(port)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.getcwd())
    for _ in range(50):
        try:
            if _req(port, "GET", "/health")[0] == 200:
                return proc, True
        except Exception:
            time.sleep(0.1)
    return proc, False
'''

_SEARCH_ORACLE = _ORACLE_PRELUDE + r'''
port = _free_port(); proc, ready = _boot(port); checks = {"server_boots": ready}
try:
    if ready:
        st, b = _req(port, "POST", "/index", {"docs": [
            {"id": "d1", "text": "the cat sat quietly on the warm mat"},
            {"id": "d2", "text": "advanced vector search with dense embeddings and neural rerankers"},
            {"id": "d3", "text": "a happy dog ran across the green park"}]})
        checks["index_200"] = (st == 200 and b.get("indexed") == 3)
        st, b = _req(port, "GET", "/search?" + urlencode({"q": "vector embeddings rerankers", "k": 2}))
        res = b.get("results", [])
        checks["search_ranks_relevant_first"] = (st == 200 and len(res) >= 1 and res[0].get("id") == "d2")
        checks["search_k_limit"] = (len(res) <= 2)
        st, b = _req(port, "GET", "/search?" + urlencode({"q": "dog park", "k": 1}))
        checks["search_second_query"] = (st == 200 and b.get("results", [{}])[0].get("id") == "d3")
        checks["health_ok"] = (_req(port, "GET", "/health")[1].get("healthy") is True)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
oracle_pass = len(checks) >= 5 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

_LABEL_ORACLE = _ORACLE_PRELUDE + r'''
port = _free_port(); proc, ready = _boot(port); checks = {"server_boots": ready}
try:
    if ready:
        st, b = _req(port, "POST", "/label", {"text": "please handle this ASAP", "amount": 5000})
        checks["labels_urgent_and_big"] = (st == 200 and "urgent" in b.get("labels", []) and "big" in b.get("labels", []))
        checks["gate_accept"] = (b.get("decision") == "accept")
        st, b = _req(port, "POST", "/label", {"text": "just a normal note", "amount": 5})
        checks["labels_empty"] = (st == 200 and b.get("labels") == [])
        checks["gate_review"] = (b.get("decision") == "review")
        checks["health_ok"] = (_req(port, "GET", "/health")[1].get("healthy") is True)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
oracle_pass = len(checks) >= 5 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

_RAG_ORACLE = _ORACLE_PRELUDE + r'''
port = _free_port(); proc, ready = _boot(port); checks = {"server_boots": ready}
try:
    if ready:
        text = ("Python is a high level programming language used widely. " * 2
                + "A reranker reorders retrieved passages by their relevance to the query. " * 2
                + "Kubernetes orchestrates containers across a cluster of nodes. " * 2)
        st, b = _req(port, "POST", "/ingest", {"docs": [{"id": "doc1", "text": text}]})
        checks["ingest_chunks"] = (st == 200 and b.get("chunks", 0) >= 2)
        st, b = _req(port, "POST", "/query", {"q": "reranker relevance passages", "k": 2})
        chunks = b.get("chunks", [])
        checks["query_retrieves"] = (st == 200 and len(chunks) >= 1)
        checks["retrieves_relevant"] = any("rerank" in c.get("text", "").lower() for c in chunks)
        checks["citations_present"] = (len(b.get("citations", [])) >= 1 and b.get("context", "") != "")
        checks["health_ok"] = (_req(port, "GET", "/health")[1].get("healthy") is True)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
oracle_pass = len(checks) >= 5 and all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

# ── thin GOOD entries (what the model should write; also what deterministic composition emits) ────────────────
_GOOD_SEARCH_APP = (
    "from search_engine import make_search_engine, run\n\n"
    "Handler = make_search_engine()\n\n"
    "if __name__ == '__main__':\n"
    "    run(Handler)\n"
)
_GOOD_LABEL_APP = (
    "from labeler import make_labeler, run\n\n"
    "RULES = [{'label': 'urgent', 'field': 'text', 'any': ['asap', 'urgent']},\n"
    "         {'label': 'big', 'field': 'amount', 'gt': 1000}]\n\n"
    "Handler = make_labeler(RULES)\n\n"
    "if __name__ == '__main__':\n"
    "    run(Handler)\n"
)
_GOOD_RAG_APP = (
    "from rag_tool import make_rag_tool, run\n\n"
    "Handler = make_rag_tool()\n\n"
    "if __name__ == '__main__':\n"
    "    run(Handler)\n"
)

# a generic BAD build (boots, but returns 200/{} for everything -> fails behavior) + a STUB (never boots)
_BAD_APP = (
    "import argparse, json\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n\n"
    "class Handler(BaseHTTPRequestHandler):\n"
    "    def _s(self, obj):\n"
    "        b = json.dumps(obj).encode(); self.send_response(200)\n"
    "        self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)\n"
    "    def do_GET(self):\n"
    "        self._s({'status': 'ok', 'healthy': True} if self.path == '/health' else {})\n"
    "    def do_POST(self):\n"
    "        self._s({})\n"
    "    def log_message(self, *a):\n"
    "        pass\n\n"
    "def main():\n"
    "    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8000)\n"
    "    HTTPServer(('127.0.0.1', ap.parse_args().port), Handler).serve_forever()\n\n"
    "if __name__ == '__main__':\n"
    "    main()\n"
)
_STUB_APP = "raise NotImplementedError('not built')\n"

_GENOMES: dict[str, dict[str, Any]] = {
    "semantic_search_engine__stdlib_http__v0": {
        "product_family": "semantic_search_engine", "prompt_style": "search_infra_brief",
        "stack": "python_stdlib_http", "solution_file": "app.py", "http_oracle": _SEARCH_ORACLE,
        "realism_level": BUILDOUT_REALISM,
        "goal": ("Build an advanced in-memory SEMANTIC SEARCH ENGINE (multi-file: app.py + a search_engine module; "
                 "Python stdlib only; boots with `python app.py --port N`). Every response body is JSON. Endpoints:\n"
                 "- GET /health -> 200 {\"status\": \"ok\", \"healthy\": true, \"docs\": <corpus size>}.\n"
                 "- POST /index {\"docs\": [{\"id\", \"text\"}]} -> 200 {\"indexed\": <corpus size>}; add docs to the "
                 "in-memory corpus (tokenize on lowercase word/number tokens).\n"
                 "- GET /search?q=<query>&k=<n> -> 200 {\"results\": [{\"id\", \"score\"}]} — the top-k docs ranked by "
                 "**BM25** relevance to the query, most relevant first (use real BM25: idf, tf saturation k1=1.5, "
                 "length normalization b=0.75), score rounded to 4 dp. Default k=5.\n"
                 "- Any other path -> 404."),
        "primitive_targets": ["make_search_engine", "tokenize", "bm25_scores"],
        "good": {"search_engine.py": SEARCH_ENGINE_SOURCE, "app.py": _GOOD_SEARCH_APP},
        "bad": {"app.py": _BAD_APP}, "stub": {"app.py": _STUB_APP}},
    "labeling_service__stdlib_http__v0": {
        "product_family": "labeling_service", "prompt_style": "data_labeling_brief",
        "stack": "python_stdlib_http", "solution_file": "app.py", "http_oracle": _LABEL_ORACLE,
        "realism_level": BUILDOUT_REALISM,
        "goal": ("Build a rule-based LABELING SERVICE (multi-file: app.py + a labeler module; Python stdlib only; "
                 "boots with `python app.py --port N`). JSON responses. A record is labeled by rules and routed by a "
                 "confidence gate. Rules: label \"urgent\" if the `text` field contains \"asap\" or \"urgent\" "
                 "(case-insensitive); label \"big\" if the `amount` field > 1000. Confidence score = matched_rules / "
                 "total_rules. Endpoints:\n"
                 "- GET /health -> 200 {\"status\": \"ok\", \"healthy\": true}.\n"
                 "- POST /label {record} -> 200 {\"labels\": [sorted unique], \"score\": <float rounded 4dp>, "
                 "\"decision\": \"accept\" if score >= 0.5 else \"review\"}.\n"
                 "- Any other path -> 404."),
        "primitive_targets": ["make_labeler", "label_by_rules", "confidence_gate"],
        "good": {"labeler.py": LABELER_SOURCE, "app.py": _GOOD_LABEL_APP},
        "bad": {"app.py": _BAD_APP}, "stub": {"app.py": _STUB_APP}},
    "rag_search_tool__stdlib_http__v0": {
        "product_family": "rag_search_tool", "prompt_style": "rag_infra_brief",
        "stack": "python_stdlib_http", "solution_file": "app.py", "http_oracle": _RAG_ORACLE,
        "realism_level": BUILDOUT_REALISM,
        "goal": ("Build a deterministic RAG SEARCH TOOL (multi-file: app.py + a rag_tool module; Python stdlib only; "
                 "NO external LLM; boots with `python app.py --port N`). JSON responses. It ingests documents, chunks "
                 "them, indexes chunk tokens, and answers a query by retrieving the most relevant chunks (BM25) and "
                 "assembling a bounded context with citations. Endpoints:\n"
                 "- GET /health -> 200 {\"status\": \"ok\", \"healthy\": true, \"chunks\": <count>}.\n"
                 "- POST /ingest {\"docs\": [{\"id\", \"text\"}]} -> 200 {\"chunks\": <count>}; chunk each doc "
                 "(overlapping windows) and index each chunk's tokens.\n"
                 "- POST /query {\"q\", \"k\"} -> 200 {\"chunks\": [{\"id\", \"text\"}], \"context\": <str>, "
                 "\"citations\": [<chunk id>]} — the top-k chunks by BM25 (score>0), a concatenated bounded context "
                 "with each chunk prefixed by its id, and the chunk ids as citations.\n"
                 "- Any other path -> 404."),
        "primitive_targets": ["make_rag_tool", "chunk_text", "bm25_scores", "assemble_context"],
        "good": {"rag_tool.py": RAG_TOOL_SOURCE, "app.py": _GOOD_RAG_APP},
        "bad": {"app.py": _BAD_APP}, "stub": {"app.py": _STUB_APP}},
}


def run_buildout(genome_id: str, files: dict[str, str], lane: str = "harness_alone",
                 extra_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Write the build to an ephemeral workspace, BOOT it, run the HIDDEN project oracle, receipt."""
    genome = _GENOMES[genome_id]
    t0 = time.time()
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        for fname, content in (extra_files or {}).items():
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        for fname, content in files.items():
            (wsp / fname).parent.mkdir(parents=True, exist_ok=True)
            (wsp / fname).write_text(content, encoding="utf-8")
        (wsp / "oracle.py").write_text(genome["http_oracle"], encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "oracle.py"], cwd=ws, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return {"record_type": "buildout_run_receipt", "genome_id": genome_id, "lane": lane,
                    "benchmark_kind": BENCHMARK_KIND, "realism_level": genome["realism_level"],
                    "oracle_pass": False, "error": "timeout", **BOUNDARY}
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("ORACLE ")), None)
        result = json.loads(line[len("ORACLE "):]) if line else {"checks": {}, "oracle_pass": False}
    return {"record_type": "buildout_run_receipt", "genome_id": genome_id,
            "product_family": genome["product_family"], "lane": lane, "benchmark_kind": BENCHMARK_KIND,
            "realism_level": genome["realism_level"], "n_files": len(files),
            "commands_run": [f"{Path(sys.executable).name} oracle.py (boots app.py + HTTP probes)"],
            "oracle_checks": result["checks"], "oracle_pass": bool(result["oracle_pass"]),
            "wall_time_s": round(time.time() - t0, 3),
            "stderr_tail": (proc.stderr or "")[-200:] if not result["oracle_pass"] else "", **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL: each of the 3 project GOOD builds (thin app over the verified molecule) BOOTS + passes
    its hidden oracle; a BAD build (returns {} for everything) FAILS; a STUB FAILS; the molecule-mounted reuse lane
    passes writing ONLY app.py."""
    results = {}
    for gid, g in _GENOMES.items():
        good = run_buildout(gid, g["good"])
        assert good["oracle_pass"] is True, f"{gid} GOOD must boot + pass its oracle: {good}"
        assert all(good["oracle_checks"].values()) and len(good["oracle_checks"]) >= 5, good["oracle_checks"]
        bad = run_buildout(gid, g["bad"])
        assert bad["oracle_checks"].get("server_boots") is True and bad["oracle_pass"] is False, f"{gid} BAD: {bad}"
        stub = run_buildout(gid, g["stub"])
        assert stub["oracle_pass"] is False and stub["oracle_checks"].get("server_boots") is False, f"{gid} STUB"
        entry = g["solution_file"]
        molecule = {fn: s for fn, s in g["good"].items() if fn != entry}
        reuse = run_buildout(gid, {entry: g["good"][entry]}, lane="compiled_route", extra_files=molecule)
        assert reuse["oracle_pass"] is True, f"{gid} molecule-mounted reuse must pass writing only app.py: {reuse}"
        results[gid] = {"checks": len(good["oracle_checks"]), "good_app_chars": len(g["good"][entry]),
                        "molecule_chars": sum(len(s) for s in molecule.values()), "wall_s": good["wall_time_s"]}
    print("OK buildout_forge_search_rag self-test: 3 LARGE projects (semantic search / labeling / RAG) — each GOOD "
          "build BOOTS + passes its hidden oracle, BAD + STUB FAIL, molecule-mounted reuse passes writing ONLY "
          "app.py. Per project (checks, app_chars over molecule_chars): "
          + "; ".join(f"{k.split('__')[0]}({v['checks']}, {v['good_app_chars']}/{v['molecule_chars']})"
                      for k, v in results.items()) + f"; benchmark_kind={BENCHMARK_KIND}; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Large search/labeling/RAG project genomes (WITH/WITHOUT primitives).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--genome", default="semantic_search_engine__stdlib_http__v0", choices=list(_GENOMES))
    ap.add_argument("--solution", default="good", choices=["good", "bad", "stub"])
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    print(json.dumps(run_buildout(args.genome, _GENOMES[args.genome][args.solution]), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
