#!/usr/bin/env python3
"""Backs `processor/pipeline-recommender`.

End-to-end orchestrator for the "I need a pipeline to do XYZ" flow:

    user prompt
       │
       ▼
    1. catalog_search   (BM25 + tag-set Jaccard)   ← stage 1: cheap retrieval
       │                                              top 30 candidates
       ▼
    2. gemma_reranker   (Gemma 4 or any LLM)       ← stage 2: semantic rerank
       │                                              top 5 ranked candidates
       ▼
    3. composition sketch  (deterministic)         ← stage 3: usability hint
       │                                              "use X with Y; pipe to Z"
       ▼
    final recommendation: top_k candidates + rationale + composition sketch

CLI:
    python -m scripts.processors.pipeline_recommender --self-test
    python -m scripts.processors.pipeline_recommender \\
        --prompt "I need to grade an ESG supplier disclosure under CSDDD"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.processors.catalog_search import run as catalog_search_run  # noqa: E402
from scripts.processors.gemma_reranker import run as gemma_rerank_run  # noqa: E402

# Type-coupling map: when the top reranked component is type X, suggest these companions.
COMPANION_SUGGESTIONS = {
    "pipeline": [
        "use the pipeline as-is via `python scripts/run_pipeline.py {id} --inputs inputs.json`",
        "or compose it as a sub-pipeline step in a larger workflow",
    ],
    "harness": [
        "wrap this harness in a small pipeline with your own pre/post steps",
        "common pre: `processor/redact-pii-text`; common post: `processor/audit-trace-emitter`",
    ],
    "tool": [
        "expose via MCP server: `python scripts/emit/mcp_server.py` then point Claude Desktop at it",
        "or call directly from a harness as a `step.kind: tool`",
    ],
    "knowledge-pack": [
        "attach to a harness's `knowledge_packs[]` and reach it via `rule-pack/hybrid-retrieval-policy`",
        "or RAG-index it directly with the embedder of your choice",
    ],
    "rule-pack": [
        "invoke as a `step.kind: rule_pack` in a pipeline",
        "GREP rule-packs are deterministic; combine with one or more in series for layered detection",
    ],
    "rubric": [
        "use as a `success_criteria[].rubric` in a pipeline",
        "pair with `processor/llm-judge` to score outputs deterministically",
    ],
    "persona": [
        "attach to a harness's `persona` field, OR inject via `step.kind: persona` at pipeline start",
    ],
    "adapter": [
        "register in your pipeline's `defaults.model_adapter` or per-harness `model_targets[]`",
    ],
    "processor": [
        "invoke as a `step.kind: processor` in a pipeline; deterministic, model-free transform",
    ],
    "pattern": [
        "patterns are reference design specs; implement as a new pipeline using the listed primitives",
    ],
    "dataset": [
        "reference in a benchmark's `dataset` field, or as a knowledge-pack `files[]` input",
    ],
    "benchmark": [
        "execute via `python scripts/bench_pipelines.py` (or your custom benchmark runner)",
    ],
}


def _composition_sketch(ranked: list[dict]) -> dict[str, Any]:
    """Heuristic composition hint based on the top candidate's type."""
    if not ranked:
        return {"top_id": None, "hints": ["(no candidates)"]}
    top = ranked[0]
    return {
        "top_id": top["id"],
        "top_type": "",  # filled by caller if known
        "hints": COMPANION_SUGGESTIONS.get(_type_from_id(top["id"]), []),
    }


def _type_from_id(component_id: str) -> str:
    return component_id.split("/", 1)[0] if "/" in component_id else ""


# ─── Public entrypoint ──────────────────────────────────────────────────────


def run(
    prompt: str,
    retrieval_top_k: int = 30,
    rerank_top_k: int = 5,
    types_filter: list[str] | None = None,
    intent_tags: list[str] | None = None,
    model: str | None = None,
    simulate_rerank: bool = False,
) -> dict[str, Any]:
    """End-to-end pipeline recommendation."""
    if not prompt or not prompt.strip():
        return {
            "prompt": prompt,
            "stage_1_retrieval": {"candidates": [], "stats": {"reason": "empty_prompt"}},
            "stage_2_rerank": {"ranked_candidates": [], "recommendation": "(no prompt)"},
            "stage_3_composition_sketch": {"top_id": None, "hints": []},
        }

    # Stage 1
    search = catalog_search_run(
        prompt=prompt,
        top_k=retrieval_top_k,
        types_filter=types_filter,
        intent_tags=intent_tags,
    )

    # Stage 2
    rerank = gemma_rerank_run(
        prompt=prompt,
        candidates=search["candidates"],
        top_k=rerank_top_k,
        model=model,
        simulate=simulate_rerank,
    )

    # Stage 3
    sketch = _composition_sketch(rerank["ranked_candidates"])

    return {
        "prompt": prompt,
        "stage_1_retrieval": {
            "candidates": search["candidates"],
            "stats": search["stats"],
        },
        "stage_2_rerank": {
            "model": rerank["model"],
            "ranked_candidates": rerank["ranked_candidates"],
            "recommendation": rerank["recommendation"],
            "simulated": rerank["simulated"],
        },
        "stage_3_composition_sketch": sketch,
    }


# ─── Self-test ──────────────────────────────────────────────────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    print("[self-test] _type_from_id")
    check("parses standard id", _type_from_id("pipeline/foo-bar") == "pipeline")
    check("empty on malformed", _type_from_id("malformed") == "")

    print("[self-test] composition sketch knows pipeline type")
    sketch = _composition_sketch([{"id": "pipeline/x"}])
    check("returns hints for pipeline", len(sketch["hints"]) >= 1)
    check("hint mentions run_pipeline.py", any("run_pipeline" in h for h in sketch["hints"]))

    print("[self-test] end-to-end (simulated) against live catalog")
    res = run("I need a pipeline to review a Wikipedia article for NPOV violations",
              simulate_rerank=True, retrieval_top_k=10, rerank_top_k=3)
    check("stage_1 returned candidates", len(res["stage_1_retrieval"]["candidates"]) > 0)
    check("stage_2 reranked candidates", len(res["stage_2_rerank"]["ranked_candidates"]) > 0)
    check("stage_3 has composition sketch", res["stage_3_composition_sketch"]["top_id"] is not None)
    # Either wikipedia-page-review pipeline OR wikipedia-quality-review harness should appear
    top_ids = [c["id"] for c in res["stage_2_rerank"]["ranked_candidates"]]
    check("Wikipedia-related candidate in top 3",
          any("wikipedia" in t.lower() for t in top_ids),
          detail=str(top_ids))

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="End-to-end pipeline recommender: search → rerank → composition sketch."
    )
    p.add_argument("--prompt", help="User task description (e.g., 'I need a pipeline to do X')")
    p.add_argument("--retrieval-top-k", type=int, default=30)
    p.add_argument("--rerank-top-k", type=int, default=5)
    p.add_argument("--type", action="append")
    p.add_argument("--intent-tag", action="append")
    p.add_argument("--model", default=None)
    p.add_argument("--simulate-rerank", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.prompt:
        p.error("--prompt or --self-test required")

    result = run(
        prompt=args.prompt,
        retrieval_top_k=args.retrieval_top_k,
        rerank_top_k=args.rerank_top_k,
        types_filter=args.type,
        intent_tags=args.intent_tag,
        model=args.model,
        simulate_rerank=args.simulate_rerank,
    )

    # Pretty-print a human-readable summary alongside the JSON
    print("\n# Pipeline recommendation\n")
    print(f"**Prompt**: {args.prompt}\n")
    print("## Top reranked candidates\n")
    for c in result["stage_2_rerank"]["ranked_candidates"]:
        print(f"- **{c['position']}. `{c['id']}`** (score {c['score']}) — {c['reason']}")
    print("\n## Recommendation\n")
    print(result["stage_2_rerank"]["recommendation"])
    print("\n## How to use the top candidate\n")
    for h in result["stage_3_composition_sketch"]["hints"]:
        print(f"- {h}")
    print("\n---\n## Full JSON\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
