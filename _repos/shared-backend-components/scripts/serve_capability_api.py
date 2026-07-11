#!/usr/bin/env python3
"""scripts.serve_capability_api — the retrieval front door as a deployable HTTP JSON service: the STORED
lanes (blackbox + 3-register matrices, mmap'd once) + lexical + fusion + the compose engines behind three
endpoints, stdlib-only (no framework), cheap enough for tonight's hosting and shaped for tomorrow's scale
(the store artifacts are immutable + content-hashed, so replicas just mmap the same files — the single-node
form of segment-swapped serving).

  GET  /health              -> {ok, corpus_cards, store, uptime_s}
  GET  /retrieve?q=...&k=5  -> verified multi-lane retrieval (stored dense + registers + lexical + RRF fusion)
  GET  /compose?q=...       -> retrieve + edge_chain wiring (the 0-token answer path)
  GET  /stats               -> the live receipts (savings, coverage) for the landing surface

Service-plane service (this is the seam a frontend calls via /api/...); serves CANDIDATES only —
serves_truth=false on every payload. Not a replacement for any product surface.

    PYTHONPATH=. python3 scripts/serve_capability_api.py --self-test
    PYTHONPATH=. python3 scripts/serve_capability_api.py --serve --port 9631
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # noqa: E402
from typing import Any, Optional  # noqa: E402
from urllib.parse import parse_qs, urlparse  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_DEFAULT_PORT = 9631
_DEFAULT_K = 5
#: receipts surfaced on /stats (absent ones reported, never faked — same tolerance as savings_statistics)
_STATS_RECEIPTS: tuple[str, ...] = ("savings_statistics_receipt.json", "real_generation_token_receipt.json",
                                    "real_dev_session_receipt.json", "saas_requirements_receipt.json",
                                    "agentic_workflow_suite_receipt.json")


class CapabilityService:
    """Loads the corpus + indexes ONCE; every request is a lookup (stored matmuls + inverted index)."""

    def __init__(self, cards: Optional[list[dict[str, Any]]] = None, *, include_staged: bool = True) -> None:
        from scripts import capability_embedding as _emb  # noqa: PLC0415
        from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
        self.staged_count = 0
        if cards is None:
            from scripts import path_graph_bench as _bench  # noqa: PLC0415
            cards = list(_bench._load_scale_corpus(None))  # noqa: SLF001
            if include_staged:
                # the staged candidate pool serves too (candidate-labelled; serving is not promotion)
                from scripts import build_primitive_embeddings as _stored  # noqa: PLC0415
                from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
                staged_file = (resource("data") / "dev-intel" / "aidevobserver_edge_foundry"
                               / _stored._STAGED_SOURCE)  # noqa: SLF001 — single-source staged filename
                staged = read_jsonl_tolerant(staged_file) if staged_file.exists() else []
                self.staged_count = len(staged)
                cards = cards + staged
        self.cards = cards
        self.by_id = {c.get("primitive_id"): c for c in cards}
        self.index = build_index(cards)
        self.embed_path = _emb.real_text_path()
        self.started = time.time()

    def retrieve(self, q: str, k: int = _DEFAULT_K, lanes: str = "full") -> dict[str, Any]:
        """``lanes``: "full" = stored dense + stored registers + lexical (best coverage; the lexical index
        walk dominates latency at 10^6); "fast" = the two stored lanes only (~0.3s at 1M) — a serving-mode
        zoo row, chosen per request."""
        from scripts import capability_embedding as _emb  # noqa: PLC0415
        from scripts import rank_fusion_zoo as _fusion  # noqa: PLC0415
        from scripts.build_primitive_search_index import search_with_stats  # noqa: PLC0415
        dense = _emb.intent_query(q, self.cards, k=k * 4, path=self.embed_path)
        registers = _emb.intent_query_registers(q, self.cards, k=k * 4, path=self.embed_path)
        pools = {"dense": [h["primitive_id"] for h in dense],
                 "registers": [h["primitive_id"] for h in registers]}
        if lanes != "fast":
            lex_hits, _stats = search_with_stats(q, k * 4, self.index)
            pools["lexical"] = [h["primitive_id"] for h in lex_hits]
        fused = _fusion.fuse(pools, method="rrf", k=k)["results"]
        out = []
        for r in fused:
            card = self.by_id.get(r.get("primitive_id")) or {}
            out.append({"primitive_id": r.get("primitive_id"), "title": card.get("title"),
                        "input_edge": card.get("input_edge"), "output_edge": card.get("output_edge"),
                        "blackbox": str(_emb.blackbox_text(card))[:200]})
        return {"query": q, "k": k, "results": out,
                "lanes": sorted(pools) if lanes == "fast" else ["dense", "lexical", "registers"],
                "lane_mode": lanes, "embed_path": self.embed_path, **BOUNDARY}

    def compose(self, q: str, k: int = _DEFAULT_K) -> dict[str, Any]:
        from scripts import pipeline_path_graph as _graph  # noqa: PLC0415
        path = {"analyze": "skip", "preprocess": "det_minimal", "expand": "none", "secondary": "none",
                "search": "semantic_registers", "fuse": "combmnz", "rerank": "none", "compose": "edge_chain"}
        run = _graph.run_path(q, self.cards, path, index=self.index)
        return {"query": q, "wiring": run.get("wiring"), "composition": run.get("composition"),
                "results": run.get("results", [])[:k], "llm_calls": run.get("llm_calls", 0), **BOUNDARY}

    def stats(self) -> dict[str, Any]:
        base = resource("data") / "dev-intel" / "session_emulation"
        found: dict[str, Any] = {}
        absent: list[str] = []
        for name in _STATS_RECEIPTS:
            try:
                found[name] = json.loads((base / name).read_text())
            except OSError:
                absent.append(name)
        return {"receipts": found, "absent": absent, "corpus_cards": len(self.cards), **BOUNDARY}

    def health(self) -> dict[str, Any]:
        return {"ok": True, "corpus_cards": len(self.cards), "staged_candidates": self.staged_count,
                "embed_path": self.embed_path,
                "uptime_s": round(time.time() - self.started, 1), **BOUNDARY}


def make_handler(service: CapabilityService):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:  # quiet by default; receipts carry the signal
            pass

        def _send(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 — http.server contract
            try:
                url = urlparse(self.path)
                qs = parse_qs(url.query)
                q = (qs.get("q") or [""])[0].strip()
                k = max(1, min(50, int((qs.get("k") or [str(_DEFAULT_K)])[0])))
                if url.path == "/health":
                    return self._send(service.health())
                if url.path == "/stats":
                    return self._send(service.stats())
                if url.path == "/retrieve":
                    if not q:
                        return self._send({"error": "missing q", **BOUNDARY}, 400)
                    lanes = (qs.get("lanes") or ["full"])[0]
                    return self._send(service.retrieve(q, k, lanes="fast" if lanes == "fast" else "full"))
                if url.path == "/compose":
                    if not q:
                        return self._send({"error": "missing q", **BOUNDARY}, 400)
                    return self._send(service.compose(q, k))
                return self._send({"error": "unknown path", "paths": ["/health", "/retrieve", "/compose",
                                                                      "/stats"], **BOUNDARY}, 404)
            except Exception as exc:  # noqa: BLE001 — a request error is a 500 payload, never a dead worker
                return self._send({"error": str(exc)[:200], **BOUNDARY}, 500)
    return Handler


def serve(port: int = _DEFAULT_PORT, cards: Optional[list[dict[str, Any]]] = None) -> ThreadingHTTPServer:
    service = CapabilityService(cards)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), make_handler(service))
    print(f"capability api on :{port} — corpus {len(service.cards)} cards, embed {service.embed_path}")
    return httpd


def _self_test() -> int:
    import urllib.request  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    cards = [{"primitive_id": "a:dedup", "title": "Deduplicate records",
              "blackbox": "Remove duplicate customer records by clustering.", "input_edge": "Batch",
              "output_edge": "Deduped", **BOUNDARY},
             {"primitive_id": "a:store", "title": "Store records",
              "blackbox": "Write deduped records into a datastore.", "input_edge": "Deduped",
              "output_edge": "Stored", **BOUNDARY}]
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(CapabilityService(cards)))
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    def _get(path: str) -> tuple[int, dict[str, Any]]:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:  # noqa: PERF203
            return e.code, json.loads(e.read())

    try:
        s, health = _get("/health")
        checks.append(("/health serves ok with the corpus size", s == 200 and health["ok"]
                       and health["corpus_cards"] == 2))
        s, ret = _get("/retrieve?q=remove+duplicate+customer+rows&k=2")
        checks.append(("/retrieve fuses the stored+lexical lanes and returns typed candidates",
                       s == 200 and ret["results"] and ret["results"][0]["primitive_id"] == "a:dedup"
                       and set(ret["lanes"]) == {"dense", "registers", "lexical"}))
        s, fast = _get("/retrieve?q=remove+duplicate+customer+rows&k=2&lanes=fast")
        checks.append(("lanes=fast serves the two STORED lanes only (the low-latency serving mode row)",
                       s == 200 and fast["lane_mode"] == "fast" and set(fast["lanes"]) == {"dense", "registers"}
                       and fast["results"]))
        s, comp = _get("/compose?q=dedupe+the+records+then+store+them")
        checks.append(("/compose runs the 0-token retrieve+edge_chain path end to end",
                       s == 200 and comp["llm_calls"] == 0 and comp.get("composition") is not None))
        s, err = _get("/retrieve")
        checks.append(("a missing query is a clean 400, never a dead worker", s == 400 and "error" in err))
        s, stats = _get("/stats")
        checks.append(("/stats reports found receipts AND names absent ones (never fakes)",
                       s == 200 and "absent" in stats))
        checks.append(("every payload carries the candidate boundary",
                       all(p.get("serves_truth") is False for p in (health, ret, comp, stats))))
    finally:
        httpd.shutdown()

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - serve_capability_api: the stored-lane retrieval front door as a deployable stdlib HTTP "
          "service — /health /retrieve /compose /stats proven over a real socket round-trip, fused stored "
          "dense + registers + lexical lanes, 0-token compose path, clean 400s, candidate boundary on every "
          "payload. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--serve", action="store_true", help="serve the full corpus")
    ap.add_argument("--port", type=int, default=_DEFAULT_PORT)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.serve:
        httpd = serve(args.port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
