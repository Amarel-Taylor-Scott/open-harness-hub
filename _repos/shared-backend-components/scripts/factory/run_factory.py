#!/usr/bin/env python3
"""Factory orchestrator — walk → propose → gate → dedup → emit → report.

This is the entrypoint Codex (or a human operator) calls to produce a batch
of draft manifests from an external knowledge source.

Pipeline:
  1. Resolve walker by --walker name → call its `run(...)`
  2. For each yielded node, propose 1-N draft manifests (currently via a
     deterministic stub; replace with LLM-backed `harness/draft-manifest-
     author` once the harness runtime exists)
  3. Run each draft through the deterministic quality gate
  4. Run each survivor through semantic dedup against the live catalog
  5. Emit survivors to `catalog/_inbox/{type}/{slug}.yaml` via the YAML
     emitter (single-file schema validation)
  6. Write a complete run report to `dist/factory-runs/{run_id}/`

CLI:
    python -m scripts.factory.run_factory --list-walkers
    python -m scripts.factory.run_factory \\
        --walker wikipedia --root-category "Money laundering" \\
        --max-nodes 20 --dry-run
    python -m scripts.factory.run_factory \\
        --walker wikidata --preset standards --max-nodes 20
    python -m scripts.factory.run_factory --self-test

The current draft-proposer is a deterministic stub that emits ONE
`knowledge-pack/` draft per node. This proves the pipeline shape end-to-end
without LLM cost; swap in LLM-backed proposal by passing a `--proposer`
plugin once the harness runtime exists.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT))

from scripts.factory.run_report import (  # noqa: E402
    RunReport,
    make_run_id,
    write_run_components,
)
from scripts.processors.draft_manifest_yaml_emitter import run as emit_draft  # noqa: E402
from scripts.processors.draft_quality_gate import run as quality_gate  # noqa: E402
from scripts.processors.semantic_dedup import load_live_corpus  # noqa: E402
from scripts.processors.semantic_dedup import run as semantic_dedup  # noqa: E402


# Walker registry — maps CLI name to module path + arg-mapping.
# Each entry's `arg_builder(args) -> dict` returns the kwargs for the walker's run().
WALKER_REGISTRY: dict[str, dict[str, Any]] = {
    "wikipedia": {
        "module": "scripts.processors.wikipedia_category_walker",
        "arg_builder": lambda args: {
            "root_category": args.root_category,
            "max_depth": args.max_depth,
            "max_nodes": args.max_nodes,
            "language_edition": args.language_edition,
            "fetch_wikitext": not args.skip_wikitext,
            "rate_limit_per_sec": args.rate_limit_per_sec,
        },
        "node_to_seed": lambda n: {
            "kind": "wikipedia",
            "title": n.get("title", ""),
            "canonical_url": n.get("canonical_url", ""),
            "is_category": n.get("is_category", False),
            "intro_text": n.get("intro_text", ""),
            "license": "CC-BY-SA-4.0",
        },
    },
    "uscode": {
        "module": "scripts.processors.uscode_section_walker",
        "arg_builder": lambda args: {
            "titles": [args.usc_title] if args.usc_title else None,
            "max_sections": args.max_nodes,
            "skip_repealed": True,
            "rate_limit_per_sec": args.rate_limit_per_sec,
        },
        "node_to_seed": lambda n: {
            "kind": "uscode",
            "title": n.get("heading", n.get("usc_citation", "")),
            "canonical_url": n.get("canonical_url", ""),
            "is_category": False,
            "intro_text": (n.get("full_text") or "")[:1500],
            "license": "Public Domain (US federal law)",
            "usc_citation": n.get("usc_citation", ""),
        },
    },
    "wikidata": {
        "module": "scripts.processors.wikidata_query_walker",
        "arg_builder": lambda args: {
            "preset": args.preset,
            "sparql": args.sparql,
            "max_nodes": args.max_nodes,
            "rate_limit_per_sec": args.rate_limit_per_sec,
        },
        "node_to_seed": lambda n: {
            "kind": "wikidata",
            "title": n.get("label", n.get("qid", "")),
            "canonical_url": n.get("wikidata_url", ""),
            "wikipedia_url": n.get("wikipedia_url", ""),
            "is_category": False,
            "intro_text": n.get("description", "")[:1500],
            "license": "CC0",
            "qid": n.get("qid", ""),
        },
    },
    "nist": {
        "module": "scripts.processors.nist_publications_walker",
        "arg_builder": lambda args: {
            "series": args.nist_series,
            "max_nodes": args.max_nodes,
            "rate_limit_per_sec": args.rate_limit_per_sec,
        },
        "node_to_seed": lambda n: {
            "kind": "nist",
            "title": f"{n.get('pub_id', '')} — {n.get('title', '')}",
            "canonical_url": n.get("canonical_url", ""),
            "is_category": False,
            "intro_text": n.get("summary", "")[:1500],
            "license": "Public Domain (NIST publication)",
            "pub_id": n.get("pub_id", ""),
        },
    },
}


def _resolve_walker(name: str) -> Callable:
    if name not in WALKER_REGISTRY:
        raise SystemExit(f"unknown walker {name!r}; choices: {sorted(WALKER_REGISTRY)}")
    spec = WALKER_REGISTRY[name]
    # Test/in-process override: a pre-resolved callable wins over module import.
    inline = spec.get("__callable__")
    if callable(inline):
        return inline
    import importlib
    mod = importlib.import_module(spec["module"])
    return mod.run


def _safe_slug(text: str, max_len: int = 64) -> str:
    """Conservative slug — lowercase, alnum + dashes, single-dash runs, length-capped."""
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len].rstrip("-") or "draft"


# ─── Deterministic stub draft proposer ──────────────────────────────────────
#
# This produces ONE knowledge-pack draft per walker node, using only the
# node's own data. Lets us prove the end-to-end pipeline without LLM cost.
# Swap with LLM-backed proposal by passing a different `propose_drafts_fn`.


def _stub_propose_drafts(seed: dict[str, Any]) -> list[dict[str, Any]]:
    """One knowledge-pack draft per seed. Lifecycle 'experimental'."""
    title = (seed.get("title") or "").strip() or "Untitled source"
    slug = _safe_slug(title)
    canonical_url = seed.get("canonical_url", "")
    if not canonical_url or not slug:
        return []
    description = seed.get("intro_text", "") or f"Reference knowledge node about {title}."
    if len(description.strip()) < 80:
        description = (
            description.strip()
            + f"\n\nSourced from {canonical_url}. Curator: expand this description with concrete "
            f"facts the catalog should index, or reject this draft."
        )
    license_str = seed.get("license", "CC-BY-4.0")
    if "Public Domain" in license_str:
        license_field = "CC0-1.0"
    elif "CC-BY-SA" in license_str:
        license_field = "CC-BY-SA-4.0"
    elif license_str == "CC0":
        license_field = "CC0-1.0"
    else:
        license_field = "CC-BY-4.0"
    source_kind = {
        "wikipedia": "other",
        "uscode": "other",
        "wikidata": "other",
        "nist": "other",
    }.get(seed.get("kind"), "other")
    return [
        {
            "id": f"knowledge-pack/{slug}",
            "type": "knowledge-pack",
            "version": "0.1.0",
            "name": title[:120],
            "description": description.strip()[:3000],
            "authors": [{"name": f"factory-stub ({seed.get('kind')})"}],
            "license": license_field,
            "industry": ["cross_industry"],
            "capability": ["retrieval"],
            "modality": ["text"],
            "lifecycle": "experimental",
            "trust_boundary": "local",
            "freshness": "dated",
            "tags": ["factory-draft", seed.get("kind", "unknown")],
            "created": time.strftime("%Y-%m-%d", time.gmtime()),
            "updated": time.strftime("%Y-%m-%d", time.gmtime()),
            "attribution": {
                "source_url": canonical_url,
                "source_kind": source_kind,
                "author": seed.get("kind", "external source"),
                "license": license_field,
            },
            "content_types": ["rag_doc"],
            "files": [{"path": f"data/factory-drafts/{slug}.jsonl", "format": "jsonl"}],
            "indexing": {"bm25": True, "dense": {"enabled": False}},
            "provenance": {
                "sources": [canonical_url],
                "collected_through": time.strftime("%Y-%m-%d", time.gmtime()),
            },
        }
    ]


# ─── The orchestrator ───────────────────────────────────────────────────────


def run_factory(
    walker_name: str,
    walker_kwargs: dict[str, Any],
    *,
    propose_drafts_fn: Callable[[dict], list[dict]] = _stub_propose_drafts,
    dry_run: bool = False,
) -> dict[str, Any]:
    """One factory pass: walk → propose → gate → dedup → emit → report.

    Returns the run report as a dict and the path of the persisted run dir.
    """
    run_id = make_run_id()
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    start = time.monotonic()

    report = RunReport(
        run_id=run_id,
        started_at=started_at,
        walker_kind=walker_name,
        walker_inputs=walker_kwargs,
    )

    walker_fn = _resolve_walker(walker_name)
    spec = WALKER_REGISTRY[walker_name]
    print(f"[factory:{run_id}] walking with {walker_name} …", file=sys.stderr)
    walk_result = walker_fn(**walker_kwargs)
    nodes = walk_result.get("nodes", []) or []
    walk_stats = walk_result.get("walk_stats", {}) or {}
    report.nodes_walked = len(nodes)
    if walk_stats.get("warnings"):
        report.warnings.extend(walk_stats["warnings"])
    report.extra["walk_stats"] = walk_stats

    print(f"[factory:{run_id}] walker emitted {len(nodes)} nodes", file=sys.stderr)

    live_corpus = load_live_corpus()
    print(
        f"[factory:{run_id}] loaded {len(live_corpus)} live-catalog entries for dedup",
        file=sys.stderr,
    )

    seeds = [spec["node_to_seed"](n) for n in nodes]

    rejected: list[dict[str, Any]] = []
    deduped: list[dict[str, Any]] = []
    emitted_drafts: list[dict[str, Any]] = []
    failed_validation: list[dict[str, Any]] = []

    for seed in seeds:
        proposals = propose_drafts_fn(seed)
        report.drafts_proposed += len(proposals)
        for draft in proposals:
            gate_result = quality_gate(draft, live_catalog_ids={c.id for c in live_corpus})
            if not gate_result["accepted"]:
                report.drafts_rejected_by_gate += 1
                rejected.append(
                    {
                        "draft_id": draft.get("id", "<no-id>"),
                        "seed_title": seed.get("title", ""),
                        "seed_url": seed.get("canonical_url", ""),
                        "reasons": gate_result["reasons"],
                        "warnings": gate_result["warnings"],
                    }
                )
                continue
            report.drafts_accepted_by_gate += 1
            dedup_result = semantic_dedup(draft, live_corpus=live_corpus)
            if dedup_result["is_duplicate"]:
                report.drafts_deduped += 1
                deduped.append(
                    {
                        "draft_id": draft.get("id", "<no-id>"),
                        "seed_title": seed.get("title", ""),
                        "best_match_id": dedup_result["best_match_id"],
                        "best_match_hamming": dedup_result["best_match_hamming"],
                        "best_match_jaccard": dedup_result["best_match_jaccard"],
                    }
                )
                continue
            if dry_run:
                emitted_drafts.append(draft)
                report.drafts_emitted_to_inbox += 1
                continue
            emit_result = emit_draft(draft, check_live_collision=False)
            if emit_result["validation_status"] == "ok":
                emitted_drafts.append(draft)
                report.drafts_emitted_to_inbox += 1
            else:
                failed_validation.append(
                    {
                        "draft_id": draft.get("id", "<no-id>"),
                        "validation_status": emit_result["validation_status"],
                        "validation_errors": emit_result["validation_errors"],
                        "written_path": emit_result.get("written_path", ""),
                    }
                )
                report.drafts_failed_validation += 1

    report.duration_s = time.monotonic() - start
    walks_payload = {walker_name: walk_result}
    run_dir = write_run_components(
        report,
        walks=walks_payload,
        drafts=emitted_drafts,
        rejected=rejected,
        deduped=deduped,
    )
    if failed_validation:
        (run_dir / "validation_failures.json").write_text(
            json.dumps(failed_validation, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(
        f"[factory:{run_id}] done in {report.duration_s:.1f}s — "
        f"walked {report.nodes_walked}, proposed {report.drafts_proposed}, "
        f"gate-rejected {report.drafts_rejected_by_gate}, deduped {report.drafts_deduped}, "
        f"emitted {report.drafts_emitted_to_inbox}, failed-validation {report.drafts_failed_validation}",
        file=sys.stderr,
    )
    print(f"[factory:{run_id}] run dir: {run_dir.relative_to(ROOT)}", file=sys.stderr)
    return {"run_id": run_id, "run_dir": str(run_dir.relative_to(ROOT)), "report": report.to_dict()}


# ─── Self-test (offline; uses a small fake walker) ──────────────────────────


def _self_test() -> int:
    """End-to-end orchestrator test with a synthetic walker — no network."""
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # Inject a fake walker using the __callable__ override path (no module import needed).
    fake_nodes = [
        {"title": f"Synthetic source {i}", "url": f"https://example.invalid/{i}",
         "description": "Synthetic test node " * 30}
        for i in range(3)
    ]
    WALKER_REGISTRY["_fake"] = {
        "module": "(inline)",
        "__callable__": lambda **kw: {"nodes": fake_nodes, "walk_stats": {"warnings": []}},
        "arg_builder": lambda args: {},
        "node_to_seed": lambda n: {
            "kind": "fake",
            "title": n["title"],
            "canonical_url": n["url"],
            "is_category": False,
            "intro_text": n.get("description", ""),
            "license": "CC0",
        },
    }
    try:
        result = run_factory(walker_name="_fake", walker_kwargs={}, dry_run=True)
        report = result["report"]
        check("nodes_walked equals fake input", report["totals"]["nodes_walked"] == 3)
        check("drafts_proposed > 0", report["totals"]["drafts_proposed"] > 0)
        check("run_id present", "run_id" in report and report["run_id"])
        check("dry-run still wrote run.json",
              (_resource(result["run_dir"]) / "run.json").exists())
    finally:
        WALKER_REGISTRY.pop("_fake", None)

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="OHH factory orchestrator — walk → gate → dedup → emit → report."
    )
    p.add_argument("--walker", choices=sorted(WALKER_REGISTRY.keys()))
    p.add_argument("--list-walkers", action="store_true")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--dry-run", action="store_true",
                   help="Run gate + dedup + report, but skip writing to catalog/_inbox/")

    # Common
    p.add_argument("--max-nodes", type=int, default=50)
    p.add_argument("--rate-limit-per-sec", type=float, default=1.0)

    # Wikipedia
    p.add_argument("--root-category", help="(wikipedia) e.g. 'Money laundering'")
    p.add_argument("--max-depth", type=int, default=1)
    p.add_argument("--language-edition", default="en")
    p.add_argument("--skip-wikitext", action="store_true",
                   help="(wikipedia) skip infobox + citation extraction")

    # USC
    p.add_argument("--usc-title", type=int, help="(uscode) USC title number, e.g. 31")

    # Wikidata
    p.add_argument("--preset", help="(wikidata) preset name; see --list-walkers for hint")
    p.add_argument("--sparql", help="(wikidata) inline SPARQL (mutually exclusive with --preset)")

    # NIST
    p.add_argument("--nist-series", action="append",
                   choices=["sp-800", "sp-1800", "sp-500", "ai", "ir", "fips"],
                   help="(nist) repeatable; default sp-800")

    args = p.parse_args(argv)

    if args.list_walkers:
        print("Available walkers:")
        for name, spec in sorted(WALKER_REGISTRY.items()):
            print(f"  {name:12s}  module={spec['module']}")
        return 0

    if args.self_test:
        return _self_test()

    if not args.walker:
        p.error("--walker NAME required (or --list-walkers / --self-test)")

    spec = WALKER_REGISTRY[args.walker]
    kwargs = spec["arg_builder"](args)
    result = run_factory(walker_name=args.walker, walker_kwargs=kwargs, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
