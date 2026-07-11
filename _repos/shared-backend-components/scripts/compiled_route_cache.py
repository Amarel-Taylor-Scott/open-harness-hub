#!/usr/bin/env python3
"""scripts.compiled_route_cache — COMPILE ONCE, EXECUTE MANY: the Compiled-AI amortization loop over OUR
composed primitive routes, with the break-even receipt the paper makes the headline operational metric.

The Compiled-AI paradigm (XY.AI Labs et al., 2026): an LLM pays tokens during a COMPILATION phase; the
compiled artifact then executes deterministically with ZERO further model invocation, breaking even with
runtime inference after ~17 transactions and reducing tokens ~57x at 1,000. Our system already has both
halves — ``primitive_runtime.compose_solution`` is the compilation phase (decompose -> retrieve -> wire a
route of EXISTING primitives) and the composed route executes deterministically — but nothing CACHED the
compilation or MEASURED the amortization curve. This module adds exactly that, preserving the setup:

  * compile_once(request)  — one compose_solution run, its proxy-token cost RECORDED as the compile cost;
                             the compact route view (signatures + edges, never bodies) is the artifact
  * execute(request)       — a cache HIT returns the compiled route with ZERO compose/model invocations
                             (reuse_count increments; the deterministic builder re-wires from the artifact)
  * amortization_receipt() — per route and in aggregate: compile cost, per-use cost, the RUNTIME-inference
                             cost it displaces, break_even_uses, and the reduction ratio at N uses

Every artifact is candidate/serves_truth=false — a cached route is a compiled CANDIDATE, never promoted by
caching. Deterministic: content-keyed by the canonicalized request, no RNG/clock in any key.

    PYTHONPATH=. python3 scripts/compiled_route_cache.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_CHARS_PER_TOKEN = 4  # the repo-wide proxy basis (TOKENS_BASIS in run_token_savings_experiments)


def _est_tokens(obj: Any) -> int:
    return max(1, len(json.dumps(obj, sort_keys=True, default=str)) // _CHARS_PER_TOKEN)


def _request_key(request: str) -> str:
    """Content key for a request: lowercased, whitespace-folded, sha256 — no RNG, no clock."""
    folded = " ".join(str(request).lower().split())
    return hashlib.sha256(folded.encode("utf-8")).hexdigest()[:16]


def corpus_fingerprint() -> str:
    """The corpus state a compiled route was compiled AGAINST: the persisted search-index manifest's content
    hash (already computed at index build — single source, never recomputed here). '' when no index exists
    (synthetic/self-test corpora). A route compiled against one corpus must MISS after the corpus drifts —
    the adversarial design panel caught cached routes silently surviving corpus drift on the serving seam."""
    try:
        from scripts._repo_paths import resource  # noqa: PLC0415
        manifest = resource("catalog") / "knowledge-packs" / "data" / "primitive-search-index" / "manifest.json"
        if manifest.exists():
            return str(json.loads(manifest.read_text()).get("content_sha256") or "")
    except Exception:  # noqa: BLE001 — fingerprint is a staleness guard, never a crash source
        pass
    return ""


class CompiledRouteCache:
    """The compile-once store. In-memory by default; a caller may persist ``entries`` as JSONL (append-only)."""

    def __init__(self) -> None:
        self.entries: dict[str, dict[str, Any]] = {}

    def compile_once(self, request: str, cards: Optional[list[dict[str, Any]]] = None,
                     solution: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Run the COMPILATION phase (one compose_solution) unless this request is already compiled. The
        compile cost = proxy tokens of the full solution record the model-facing side would have consumed;
        the stored artifact is the compact route view only. ``solution`` seeds the cache from a compose the
        caller ALREADY ran (never compose twice for one compilation)."""
        key = _request_key(request)
        if key in self.entries:
            return self.entries[key]
        if solution is not None:
            sol = solution
        else:
            from scripts.primitive_runtime import compose_solution  # noqa: PLC0415  the compilation phase

            sol = compose_solution(request, candidate_cards=cards)
        route = sol["route"]
        artifact = {
            "request_key": key,
            "request": request,
            "route_found": bool(route.get("route_found")),
            "ordered_route": [
                {"component_id": s.get("component_id") or s.get("primitive_id"),
                 "input_edge": s.get("input_edge"), "output_edge": s.get("output_edge")}
                for s in (route.get("ordered_route") or [])],
            "composer_path": route.get("composer_path"),
            "compile_cost_tokens": _est_tokens(sol),          # what compilation actually cost (once)
            "artifact_read_tokens": 0,                        # set below: what a HIT costs to read
            "runtime_inference_tokens": _est_tokens(sol) ,    # what a NO-cache run would spend EVERY time
            "reuse_count": 0,
            "model_calls_on_hit": 0,                          # the paradigm's core invariant
            "corpus_fingerprint": corpus_fingerprint(),       # staleness guard: drifted corpus -> MISS
            **BOUNDARY,
        }
        artifact["artifact_read_tokens"] = _est_tokens(artifact["ordered_route"]) + _est_tokens(request)
        self.entries[key] = artifact
        return artifact

    def execute(self, request: str, expected_corpus_fingerprint: Optional[str] = None) -> dict[str, Any]:
        """The EXECUTION phase: a hit returns the compiled artifact with zero compose/model invocation —
        the deterministic builder wires from the stored signature+edge view. A miss raises (compile first;
        implicit compile-on-miss would hide the cost the receipt exists to measure). When the caller supplies
        the CURRENT corpus fingerprint, a route compiled against a DRIFTED corpus is evicted and raises —
        stale compiled knowledge must never serve as if fresh."""
        key = _request_key(request)
        if key not in self.entries:
            raise KeyError(f"request not compiled: {request!r} — call compile_once first")
        entry = self.entries[key]
        if expected_corpus_fingerprint is not None \
                and entry["corpus_fingerprint"] != expected_corpus_fingerprint:
            del self.entries[key]  # evict; the caller recompiles against the current corpus
            raise KeyError(f"compiled route for {request!r} is STALE (corpus drifted) — recompile")
        entry["reuse_count"] += 1
        return {"request_key": key, "hit": True, "model_calls": 0,
                "tokens_spent": entry["artifact_read_tokens"],
                "ordered_route": entry["ordered_route"], **BOUNDARY}

    def amortization_receipt(self, at_uses: int = 1000) -> dict[str, Any]:
        """The paper's headline curve over OUR routes: cumulative compiled-path tokens (compile once + read
        per use) vs runtime-path tokens (full inference every use); break_even_uses = the first use count
        where the compiled path is cheaper; reduction ratio at ``at_uses``."""
        routes = []
        for entry in sorted(self.entries.values(), key=lambda e: e["request_key"]):
            compile_cost = entry["compile_cost_tokens"]
            per_use = entry["artifact_read_tokens"]
            runtime = entry["runtime_inference_tokens"]
            saved_per_use = runtime - per_use
            break_even = (compile_cost // saved_per_use + 1) if saved_per_use > 0 else None
            compiled_total = compile_cost + per_use * at_uses
            runtime_total = runtime * at_uses
            routes.append({
                "request_key": entry["request_key"],
                "route_found": entry["route_found"],
                "compile_cost_tokens": compile_cost,
                "tokens_per_use_compiled": per_use,
                "tokens_per_use_runtime": runtime,
                "break_even_uses": break_even,
                "reduction_ratio_at_n": round(runtime_total / compiled_total, 1) if compiled_total else None,
                "reuse_count": entry["reuse_count"],
                "model_calls_after_compile": 0,
            })
        return {"record_type": "compiled_route_amortization", "at_uses": at_uses, "routes": routes,
                "routes_compiled": len(routes),
                "mean_break_even_uses": round(sum(r["break_even_uses"] for r in routes if r["break_even_uses"])
                                              / max(1, sum(1 for r in routes if r["break_even_uses"])), 1)
                                        if routes else None,
                **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = [
        {"primitive_id": "p:norm", "title": "Normalize messy records",
         "blackbox": "Normalize and standardize messy raw records into a clean canonical schema.",
         "input_edge": "RawRecord", "output_edge": "NormalizedRecord", **BOUNDARY},
        {"primitive_id": "p:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate records by clustering near-identical normalized rows.",
         "input_edge": "NormalizedRecord", "output_edge": "DedupedRecord", **BOUNDARY},
    ]
    cache = CompiledRouteCache()
    request = "clean up and remove duplicate messy records"

    # (a) COMPILE once: pays the full compose cost, stores only the compact artifact.
    compiled = cache.compile_once(request, cards=cards)
    checks.append(("compilation composes a real route once", compiled["route_found"]
                   and compiled["compile_cost_tokens"] > compiled["artifact_read_tokens"]))
    checks.append(("recompiling the same request is a no-op (already compiled)",
                   cache.compile_once(request, cards=cards) is compiled and len(cache.entries) == 1))

    # (b) EXECUTE many: every hit is zero-model-call and reads only the artifact.
    runs = [cache.execute(request) for _ in range(20)]
    checks.append(("every execution is a zero-model-call hit",
                   all(r["hit"] and r["model_calls"] == 0 for r in runs)
                   and compiled["reuse_count"] == 20))
    checks.append(("execution reads ONLY the compact artifact (signatures+edges, never the full solution)",
                   all(r["tokens_spent"] == compiled["artifact_read_tokens"] for r in runs)))
    # a miss must be LOUD — implicit compile-on-miss would hide the compile cost from the receipt
    try:
        cache.execute("a request nobody compiled")
        checks.append(("a miss raises instead of silently compiling", False))
    except KeyError:
        checks.append(("a miss raises instead of silently compiling", True))
    # corpus drift: a route compiled against one corpus must EVICT+MISS when the fingerprint moves
    # (the adversarial panel caught stale compiled routes silently surviving corpus drift)
    try:
        cache.execute(request, expected_corpus_fingerprint="a-drifted-corpus-fingerprint")
        checks.append(("a corpus-drifted compiled route is evicted and misses", False))
    except KeyError:
        checks.append(("a corpus-drifted compiled route is evicted and misses",
                       _request_key(request) not in cache.entries))
    cache.compile_once(request, cards=cards)  # recompile for the receipt checks below
    for _ in range(20):
        cache.execute(request)

    # (c) the AMORTIZATION receipt: break-even exists and the compiled path wins at scale.
    receipt = cache.amortization_receipt(at_uses=1000)
    row = receipt["routes"][0]
    checks.append(("break-even is a small finite use count",
                   isinstance(row["break_even_uses"], int) and 1 <= row["break_even_uses"] <= 50))
    checks.append(("token reduction at 1000 uses is substantial (>5x)",
                   row["reduction_ratio_at_n"] and row["reduction_ratio_at_n"] > 5.0))

    # (d) determinism + governance.
    c2 = CompiledRouteCache()
    c2.compile_once(request, cards=cards)
    checks.append(("compilation is deterministic (byte-identical artifact twice)",
                   json.dumps({k: v for k, v in c2.entries[_request_key(request)].items() if k != "reuse_count"},
                              sort_keys=True)
                   == json.dumps({k: v for k, v in compiled.items() if k != "reuse_count"}, sort_keys=True)))
    checks.append(("artifacts + receipts are candidate/serves_truth=false",
                   compiled["serves_truth"] is False and receipt["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - compiled_route_cache: compile ONCE (cost {compiled['compile_cost_tokens']} proxy-tokens) -> "
          f"execute MANY at {compiled['artifact_read_tokens']} tokens/use with ZERO model calls; break-even at "
          f"{row['break_even_uses']} uses, {row['reduction_ratio_at_n']}x reduction at 1000 uses — the "
          f"Compiled-AI amortization loop over OUR composed primitive routes. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
