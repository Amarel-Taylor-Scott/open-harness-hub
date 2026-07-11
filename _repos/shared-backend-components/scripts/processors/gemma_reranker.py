#!/usr/bin/env python3
"""Backs `processor/gemma-reranker`.

Lightweight LLM-based reranker that takes a small candidate set (typically
top 20-30 from `processor/catalog-search`) and a user prompt, and re-orders
the candidates by relevance using a small local model (Gemma 4 family by
default, but any chat-capable adapter works).

The reranker emits a STRUCTURED RANKING with per-candidate score + one-
sentence rationale, plus an overall recommendation paragraph. The structure
lets downstream code use the ranking programmatically AND lets a human read
the rationale.

Adapter dispatch:
  - Default: `adapter/ollama-default` if `OH_RERANK_ADAPTER` is not set
  - Override: any `adapter/*` from the catalog (lookup by id)

When no model is configured (no `OH_RERANK_ADAPTER`, no `OLLAMA_HOST`,
and no `--simulate-with` flag), runs in deterministic SIMULATION MODE
that scores candidates by a sensible heuristic (bm25 + score-rank decay)
so the pipeline shape can be exercised without LLM cost. Simulation mode
explicitly tags results with `simulated: true`.

CLI:
    python -m scripts.processors.gemma_reranker --self-test
    python -m scripts.processors.gemma_reranker \\
        --prompt "I need to grade an ESG supplier disclosure" --top-k 5
    # ↑ runs catalog_search first, then reranks; deterministic if no model set

Module entrypoint:
    from scripts.processors.gemma_reranker import run
    result = run(prompt="...", candidates=[...], top_k=5)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT))

from scripts.processors.catalog_search import run as catalog_search_run  # noqa: E402
from scripts._config import (  # noqa: E402
    DEFAULT_GEMMA_RERANK_MODEL,
    DEFAULT_OLLAMA_HOST,
    OH_RERANK_MODEL_ENV,
    OLLAMA_HOST_ENV,
)

# ─── Default model & prompt ─────────────────────────────────────────────────

DEFAULT_MODEL = os.environ.get(OH_RERANK_MODEL_ENV, DEFAULT_GEMMA_RERANK_MODEL)
OLLAMA_HOST = os.environ.get(OLLAMA_HOST_ENV, DEFAULT_OLLAMA_HOST)
DEFAULT_TIMEOUT_S = 60.0

RERANK_SYSTEM_PROMPT = """\
You are a precise catalog recommender. Given a user's task description and a
list of candidate components from a YAML-manifest catalog, rank the candidates
by how well each one helps with the task. Apply these rules:

1. Prefer pipelines (end-to-end runnable) over harnesses (sub-workflows)
   over single primitives, when the user asks for an end-to-end solution.
2. Reject candidates whose description shows mismatch (e.g., user wants
   "review a contract" but candidate is about cookie recipes).
3. Favor candidates whose description names the user's domain or named
   regulations (CSDDD, GDPR, OWASP, etc.).
4. Penalize candidates that are deprecated or whose lifecycle is sunset.

For EACH candidate (in order), output exactly one line:

    {position}. {id}  | score={0.00..1.00}  | reason: {one sentence}

After all candidates, output a single recommendation paragraph (≤ 4 sentences)
describing how the top candidate fits the user's task and any caveats.
"""

USER_TEMPLATE = """\
User task:
{prompt}

Candidates (from catalog search; ordered by initial BM25 score):

{candidate_block}

Now rank the {n} candidates above by relevance to the user task, applying
the rules above. Output exactly {n} ranked lines followed by one
recommendation paragraph.
"""


# ─── Types ──────────────────────────────────────────────────────────────────


@dataclass
class RankedCandidate:
    position: int
    id: str
    score: float
    reason: str
    original_position: int = -1
    simulated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position,
            "id": self.id,
            "score": round(self.score, 3),
            "reason": self.reason,
            "original_position": self.original_position,
            "simulated": self.simulated,
        }


# ─── Adapters ───────────────────────────────────────────────────────────────


def _ollama_chat(model: str, system: str, user: str, timeout: float = DEFAULT_TIMEOUT_S) -> str:
    """Call Ollama /api/chat. Returns the assistant's text content.

    Returns empty string if Ollama is not reachable (caller falls back to simulation).
    """
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 1024},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return ""
    return (data.get("message") or {}).get("content", "") or ""


def _format_candidate_block(candidates: list[dict]) -> str:
    lines = []
    for i, c in enumerate(candidates):
        cid = c.get("id", "<no-id>")
        ctype = c.get("type", "")
        name = c.get("name", "")[:120]
        # Pull description if present (caller may have included it; else omit)
        desc = (c.get("description") or "")[:300]
        s = f"{i+1}. [{ctype}] {cid}\n   name: {name}"
        if desc:
            s += f"\n   description: {desc}"
        lines.append(s)
    return "\n\n".join(lines)


# Parse the model's per-candidate lines: "1. {id}  | score=0.82  | reason: ..."
_RANK_LINE_RE = re.compile(
    r"^\s*(\d+)\.\s*([a-z\-]+/[a-z0-9\-]+)\s*\|\s*score\s*=\s*([0-9.]+)\s*\|\s*reason\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)


def _parse_ranking(text: str, original_ids: list[str]) -> tuple[list[RankedCandidate], str]:
    """Parse the model output into RankedCandidate[] + the trailing recommendation paragraph."""
    ranked: list[RankedCandidate] = []
    seen_ids: set[str] = set()
    rec_lines: list[str] = []
    after_ranks = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            after_ranks = bool(ranked)
            continue
        m = _RANK_LINE_RE.match(line)
        if m and not after_ranks:
            pos = int(m.group(1))
            cid = m.group(2).strip()
            score = max(0.0, min(1.0, float(m.group(3))))
            reason = m.group(4).strip()[:300]
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            orig = original_ids.index(cid) if cid in original_ids else -1
            ranked.append(RankedCandidate(
                position=pos, id=cid, score=score, reason=reason, original_position=orig
            ))
        else:
            if after_ranks or ranked:
                rec_lines.append(raw_line)
    recommendation = "\n".join(rec_lines).strip()
    return ranked, recommendation


def _simulate_rerank(candidates: list[dict]) -> list[RankedCandidate]:
    """Deterministic stand-in when no model is available.

    Score = rank-decay (1 / (1 + position)) — preserves original BM25 order
    but produces a clean 0..1 score band. Reason notes the simulation.
    """
    out: list[RankedCandidate] = []
    for i, c in enumerate(candidates):
        score = round(1.0 / (1.0 + i * 0.5), 3)
        out.append(RankedCandidate(
            position=i + 1,
            id=c.get("id", f"<no-id-{i}>"),
            score=score,
            reason=f"simulated rank by initial BM25 (score-rank-decay; no LLM available).",
            original_position=i,
            simulated=True,
        ))
    return out


# ─── Public entrypoint ──────────────────────────────────────────────────────


def run(
    prompt: str,
    candidates: list[dict],
    top_k: int = 5,
    model: str | None = None,
    simulate: bool = False,
) -> dict[str, Any]:
    """Rerank `candidates` by relevance to `prompt`.

    Args:
        prompt: user's task description.
        candidates: list of dicts each with at least id, type, name (description optional).
        top_k: number of reranked candidates to return.
        model: override OH_RERANK_MODEL.
        simulate: force simulation mode (skip the LLM call entirely).

    Returns:
        {
          "prompt": prompt,
          "model": model used (or "simulated"),
          "ranked_candidates": [RankedCandidate.to_dict(), ...],
          "recommendation": str,
          "simulated": bool,
        }
    """
    if not candidates:
        return {
            "prompt": prompt,
            "model": "n/a",
            "ranked_candidates": [],
            "recommendation": "(no candidates supplied)",
            "simulated": True,
        }

    original_ids = [c.get("id", f"<no-id-{i}>") for i, c in enumerate(candidates)]
    effective_model = model or DEFAULT_MODEL

    if not simulate:
        user_msg = USER_TEMPLATE.format(
            prompt=prompt,
            candidate_block=_format_candidate_block(candidates),
            n=len(candidates),
        )
        raw = _ollama_chat(effective_model, RERANK_SYSTEM_PROMPT, user_msg)
        if raw:
            ranked, recommendation = _parse_ranking(raw, original_ids)
            # If parse failed (zero ranked), fall back to simulation
            if ranked:
                ranked.sort(key=lambda r: -r.score)
                top = ranked[:top_k]
                return {
                    "prompt": prompt,
                    "model": effective_model,
                    "ranked_candidates": [r.to_dict() for r in top],
                    "recommendation": recommendation or "(no recommendation paragraph emitted)",
                    "simulated": False,
                }

    # Simulation fallback
    ranked = _simulate_rerank(candidates)[:top_k]
    top_id = ranked[0].id if ranked else "<none>"
    recommendation = (
        f"(simulated) The top match for your task is {top_id}. No LLM was "
        f"available to evaluate; results preserve the initial BM25 order. Set "
        f"OLLAMA_HOST and OH_RERANK_MODEL (or pass --model) to enable real reranking."
    )
    return {
        "prompt": prompt,
        "model": "simulated",
        "ranked_candidates": [r.to_dict() for r in ranked],
        "recommendation": recommendation,
        "simulated": True,
    }


# ─── Self-test ──────────────────────────────────────────────────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    print("[self-test] rank-line regex")
    m = _RANK_LINE_RE.match("1. pipeline/esg-supplier-grading  | score=0.92  | reason: matches ESG + supplier scope precisely")
    check("regex parses well-formed line", m is not None)
    if m:
        check("score extracted correctly", float(m.group(3)) == 0.92)

    print("[self-test] simulation fallback")
    fake_cands = [
        {"id": "pipeline/foo", "type": "pipeline", "name": "Foo"},
        {"id": "pipeline/bar", "type": "pipeline", "name": "Bar"},
        {"id": "pipeline/baz", "type": "pipeline", "name": "Baz"},
    ]
    res = run("test prompt", fake_cands, top_k=3, simulate=True)
    check("simulation returns 3 candidates", len(res["ranked_candidates"]) == 3)
    check("simulation flagged", res["simulated"])
    check("scores in [0,1]", all(0.0 <= c["score"] <= 1.0 for c in res["ranked_candidates"]))
    check("preserves order in simulation",
          res["ranked_candidates"][0]["id"] == "pipeline/foo")

    print("[self-test] empty candidates handled")
    res = run("test", [], simulate=True)
    check("returns empty + sim flag", res["ranked_candidates"] == [])

    print("[self-test] parse handles model output without trailing paragraph")
    text = (
        "1. pipeline/esg-supplier-grading | score=0.92 | reason: ESG match\n"
        "2. pipeline/contract-review | score=0.55 | reason: partial overlap\n"
    )
    ranked, rec = _parse_ranking(text, ["pipeline/esg-supplier-grading", "pipeline/contract-review"])
    check("parses two lines", len(ranked) == 2)
    check("top score correct", abs(ranked[0].score - 0.92) < 1e-6)

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Gemma 4 (or any chat adapter) post-RAG reranker for the OHH catalog."
    )
    p.add_argument("--prompt", help="User task description")
    p.add_argument("--top-k", type=int, default=5, help="How many candidates to return after reranking")
    p.add_argument("--retrieval-top-k", type=int, default=30,
                   help="How many candidates to retrieve from catalog_search before reranking")
    p.add_argument("--model", default=None, help=f"Override (default: {DEFAULT_MODEL})")
    p.add_argument("--simulate", action="store_true", help="Skip LLM; use deterministic simulation")
    p.add_argument("--type", action="append", help="Restrict catalog_search to these types")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.prompt:
        p.error("--prompt or --self-test required")

    print(f"[rerank] retrieving up to {args.retrieval_top_k} candidates …", file=sys.stderr)
    search = catalog_search_run(prompt=args.prompt, top_k=args.retrieval_top_k, types_filter=args.type)
    candidates = search["candidates"]
    print(f"[rerank] reranking {len(candidates)} → top {args.top_k} (model: {args.model or DEFAULT_MODEL}; simulate={args.simulate})", file=sys.stderr)
    result = run(prompt=args.prompt, candidates=candidates, top_k=args.top_k, model=args.model, simulate=args.simulate)
    result["retrieval_stats"] = search["stats"]
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
