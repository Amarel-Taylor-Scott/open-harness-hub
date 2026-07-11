#!/usr/bin/env python3
"""scripts.bench_domain_token_savings — per-DOMAIN benchmark of the token-savings thesis: leetcode/algorithms,
AI/LLM-agent tasks, DAG/workflow, data engineering, scraping, web browser, agentic loops, image/media,
document extraction, devops — measured on BOTH lanes, then mined for what each domain NEEDS.

Two lanes per domain, both pure reuse of proof-gated engines (this module owns NO new mechanism):
  * RETRIEVAL lane — ``run_token_savings_experiments._external_experiment`` over labeled domain probes
    against the real index: coverage, VERIFIED precision (expected-concept hit), net proxy-tokens saved.
  * COMPOSITION/DAG lane — ``primitive_runtime.compose_solution`` per probe over the verified corpus:
    route_found rate (can we actually WIRE a graph?), mean route length, gap model_steps (what the corpus
    cannot compose deterministically), engine fallbacks.

The rollup answers the owner's asks per domain: where we need MORE DAGS (low route rate), MORE FORMATS /
INPUTS+OUTPUTS (top unmet edges named per domain), MORE FLEXIBILITY (gap/model-step rate), and WHAT TOKEN
SAVINGS we experience (net proxy-tokens, hit-only reduction). Receipts are written to distinct per-mode
files and never overwrite a different mode's run (lossless). serves_truth=false everywhere.

    PYTHONPATH=. python3 scripts/bench_domain_token_savings.py --self-test
    PYTHONPATH=. python3 scripts/bench_domain_token_savings.py --run [--compose-probes N]
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
import json  # noqa: E402
from typing import Any  # noqa: E402

from scripts.build_primitive_search_index import build_index  # noqa: E402  REUSE: the ONE inverted index
from scripts.run_token_savings_experiments import (  # noqa: E402  REUSE: the token-savings experiment engine
    _external_experiment,
    _load_cards,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_ROUTE_RATE_NEEDS_DAGS = 0.5     # below this route_found rate a domain "needs more DAGs"
_GAP_RATE_NEEDS_FLEX = 0.5       # above this model-step/gap rate a domain "needs more flexibility"
_COVERAGE_NEEDS_CARDS = 0.7      # below this retrieval coverage a domain "needs more cards"
_TOP_UNMET_EDGES = 5             # unmet input edges named per domain (the missing formats/IO)
_DEFAULT_COMPOSE_PROBES = 6      # compose lane probes per domain (each is a full pipeline run)

#: per-domain labeled probes: intent + the concept token a RIGHT answer must carry (verified precision).
#: Deterministic, curated, spanning the owner-named areas. Each probe is one experiment on each lane.
DOMAIN_PROBES: dict[str, list[dict[str, str]]] = {
    "leetcode_algorithms": [
        {"intent": "find the longest palindromic substring in a string", "expected": "palindrom"},
        {"intent": "merge two sorted linked lists into one sorted list", "expected": "merge"},
        {"intent": "detect a cycle in a directed graph", "expected": "cycle"},
        {"intent": "compute the edit distance between two strings", "expected": "distance"},
        {"intent": "find two numbers in an array that sum to a target", "expected": "sum"},
        {"intent": "binary search a sorted array for a target value", "expected": "search"},
        {"intent": "topologically sort a dependency graph", "expected": "topolog"},
        {"intent": "find the shortest path between two nodes in a weighted graph", "expected": "path"},
        {"intent": "compute the maximum subarray sum", "expected": "subarray"},
        {"intent": "check whether two strings are anagrams", "expected": "anagram"},
    ],
    "ai_llm_tasks": [
        {"intent": "chunk a document for retrieval augmented generation", "expected": "chunk"},
        {"intent": "embed text into a vector for semantic search", "expected": "embed"},
        {"intent": "rerank retrieved passages by relevance to a query", "expected": "rerank"},
        {"intent": "route a prompt to the cheapest capable model", "expected": "rout"},
        {"intent": "extract structured json from a model response", "expected": "json"},
        {"intent": "build a prompt template with few shot examples", "expected": "prompt"},
        {"intent": "detect hallucinated claims in generated text", "expected": "halluc"},
        {"intent": "summarize a long conversation into a compact context", "expected": "summar"},
        {"intent": "count tokens in a prompt before sending it", "expected": "token"},
        {"intent": "cache identical llm calls to avoid repeat cost", "expected": "cache"},
    ],
    "dag_workflow": [
        {"intent": "compose a pipeline of steps into a directed acyclic graph", "expected": "dag"},
        {"intent": "run workflow steps in dependency order", "expected": "order"},
        {"intent": "retry a failed pipeline step with exponential backoff", "expected": "retry"},
        {"intent": "fan out a batch of items to parallel workers and collect results", "expected": "fan"},
        {"intent": "checkpoint pipeline state so a run can resume after a crash", "expected": "checkpoint"},
        {"intent": "schedule a recurring job with a cron expression", "expected": "cron"},
        {"intent": "gate a deployment step on a passing test suite", "expected": "gate"},
        {"intent": "propagate typed outputs from one step into the next step's inputs", "expected": "output"},
        {"intent": "detect and break a cycle in a workflow definition", "expected": "cycle"},
        {"intent": "emit a lineage record for every artifact a pipeline produces", "expected": "lineage"},
    ],
    "data_engineering": [
        {"intent": "deduplicate rows in a large csv by fuzzy key", "expected": "dedup"},
        {"intent": "normalize messy records into a canonical schema", "expected": "normal"},
        {"intent": "validate a json document against a schema", "expected": "schema"},
        {"intent": "partition a dataset by date for incremental loads", "expected": "partition"},
        {"intent": "upsert rows into a postgres table idempotently", "expected": "upsert"},
        {"intent": "convert a csv file into parquet", "expected": "parquet"},
        {"intent": "profile a dataset for null rates and outliers", "expected": "profil"},
        {"intent": "build a slowly changing dimension from change events", "expected": "dimension"},
        {"intent": "reconcile two ledgers and report the differences", "expected": "reconcil"},
        {"intent": "mask personally identifiable information in a dataset", "expected": "mask"},
    ],
    "scraping": [
        {"intent": "scrape a paginated listing site into structured rows", "expected": "pagina"},
        {"intent": "extract a table from an html page", "expected": "table"},
        {"intent": "respect robots txt and rate limits while crawling", "expected": "robots"},
        {"intent": "parse rss and atom feeds into items", "expected": "feed"},
        {"intent": "rotate user agents and proxies for resilient scraping", "expected": "proxy"},
        {"intent": "extract open graph metadata from a web page", "expected": "metadata"},
        {"intent": "diff a scraped page against its previous snapshot", "expected": "diff"},
        {"intent": "render a javascript heavy page before extracting content", "expected": "render"},
        {"intent": "follow sitemap xml to enumerate site urls", "expected": "sitemap"},
        {"intent": "dedupe scraped documents by content hash", "expected": "hash"},
    ],
    "web_browser": [
        {"intent": "automate a login form in a headless browser", "expected": "login"},
        {"intent": "click a button and wait for the page to settle", "expected": "click"},
        {"intent": "take a full page screenshot of a url", "expected": "screenshot"},
        {"intent": "fill and submit a multi step web form", "expected": "form"},
        {"intent": "intercept network requests made by a page", "expected": "network"},
        {"intent": "assert a page has zero console errors", "expected": "console"},
        {"intent": "extract text from the accessibility tree of a page", "expected": "accessib"},
        {"intent": "wait for a selector to appear before acting", "expected": "selector"},
        {"intent": "download a file triggered by a browser click", "expected": "download"},
        {"intent": "run a browser action behind a persistent session cookie", "expected": "cookie"},
    ],
    "agentic_tasks": [
        {"intent": "supervise an autonomous agent loop for thrash and stalls", "expected": "agent"},
        {"intent": "budget an agent's tool calls and halt on overrun", "expected": "budget"},
        {"intent": "review an ai coding session for wasted context", "expected": "session"},
        {"intent": "ground an agent's plan in a registry of existing capabilities", "expected": "registr"},
        {"intent": "record tool call outcomes for later replay", "expected": "replay"},
        {"intent": "decompose a natural language request into sub capabilities", "expected": "decompos"},
        {"intent": "detect when an agent is reinventing an existing component", "expected": "reinvent"},
        {"intent": "hand off a task between two agents with typed context", "expected": "handoff"},
        {"intent": "score an agent run against its stated goal", "expected": "goal"},
        {"intent": "compile a task into a deterministic route before calling a model", "expected": "route"},
    ],
    "image_media": [
        {"intent": "resize an image to target dimensions preserving aspect ratio", "expected": "resize"},
        {"intent": "extract text from a scanned document image with ocr", "expected": "ocr"},
        {"intent": "generate a thumbnail for a video file", "expected": "thumbnail"},
        {"intent": "transcribe an audio recording to text", "expected": "transcri"},
        {"intent": "strip exif metadata from an uploaded photo", "expected": "exif"},
        {"intent": "detect faces in an image and blur them", "expected": "face"},
        {"intent": "convert an image between png and webp formats", "expected": "convert"},
        {"intent": "caption an image with a short description", "expected": "caption"},
        {"intent": "normalize audio loudness across clips", "expected": "audio"},
        {"intent": "split a video into scenes by shot detection", "expected": "scene"},
    ],
    "document_extraction": [
        {"intent": "extract line items from a pdf invoice", "expected": "invoice"},
        {"intent": "parse a resume into structured fields", "expected": "resume"},
        {"intent": "pull tables out of a pdf report", "expected": "table"},
        {"intent": "classify a document by type before routing it", "expected": "classif"},
        {"intent": "redact names and addresses from a contract", "expected": "redact"},
        {"intent": "split a scanned bundle into individual documents", "expected": "split"},
        {"intent": "extract key value pairs from a form", "expected": "form"},
        {"intent": "detect the language of a document", "expected": "language"},
    ],
    "devops_cloud": [
        {"intent": "build a docker image and push it to a registry", "expected": "docker"},
        {"intent": "deploy a service to kubernetes with a health check", "expected": "kubernetes"},
        {"intent": "tail structured logs and alert on error spikes", "expected": "log"},
        {"intent": "rotate a secret without downtime", "expected": "secret"},
        {"intent": "provision infrastructure from a terraform plan", "expected": "terraform"},
        {"intent": "roll back a deployment when error rates rise", "expected": "roll"},
        {"intent": "expose a service through a reverse proxy with tls", "expected": "proxy"},
        {"intent": "run a canary release and compare metrics", "expected": "canary"},
    ],
}


def run_retrieval_lane(cards: list[dict], *, k: int = 5) -> dict[str, list[dict]]:
    """Every domain probe through the REAL token-savings experiment (index built once)."""
    index = build_index(cards)
    by_id = {c.get("primitive_id"): c for c in cards if c.get("primitive_id")}
    out: dict[str, list[dict]] = {}
    for domain, probes in DOMAIN_PROBES.items():
        rows = []
        for p in probes:
            task = {"intent": p["intent"], "domain": domain, "expected": p["expected"], "labeled": True}
            rows.append(_external_experiment(task, index, by_id, k))
        out[domain] = rows
    return out


def run_composition_lane(cards: list[dict], *, probes_per_domain: int = _DEFAULT_COMPOSE_PROBES) -> dict[str, list[dict]]:
    """Domain probes through the FULL compose pipeline (decompose -> search -> classify -> route -> peel-back
    -> remix -> prove) over one shared card list — can the corpus actually WIRE a graph for this domain?"""
    from scripts.primitive_runtime import compose_solution  # noqa: PLC0415  heavy import, compose lane only

    out: dict[str, list[dict]] = {}
    for domain, probes in DOMAIN_PROBES.items():
        rows = []
        for p in probes[:probes_per_domain]:
            sol = compose_solution(p["intent"], candidate_cards=cards)
            route = sol["route"]
            remix = sol["remix"]
            rows.append({
                "intent": p["intent"],
                "route_found": bool(route.get("route_found")),
                "route_len": len(route.get("ordered_route") or []),
                "composer_path": route.get("composer_path"),
                "remix_steps": len(remix.get("remix_steps") or []),
                "model_steps": len(remix.get("model_steps") or []),
                "needed_edges": [str(m.get("needed_output_type") or "")
                                 for m in (remix.get("model_steps") or [])],
                "fell_back": sol.get("fell_back") or [],
                **BOUNDARY,
            })
        out[domain] = rows
    return out


def _domain_card_counts(cards: list[dict]) -> dict[str, int]:
    """How many corpus cards claim each probe domain (via the foundry ``domains`` tags). NOTE: the verified
    corpus carries id-prefix debris in ``domains`` ('edge', 'prim', 'grp', ...), so the caller should pass the
    union of verified + EDGE cards — the edge foundry stamps real semantic domain tags."""
    counts = {d: 0 for d in DOMAIN_PROBES}
    aliases = {
        "leetcode_algorithms": ("software_engineering", "general_software"),
        "ai_llm_tasks": ("llm_agent_tools", "data_science_ml"),
        "dag_workflow": ("workflow_automation",),
        "data_engineering": ("data_engineering",),
        "scraping": ("browser_automation", "data_engineering"),
        "web_browser": ("browser_automation", "app_building_frontend"),
        "agentic_tasks": ("llm_agent_tools", "observability_replay"),
        "image_media": ("document_extraction", "data_science_ml"),
        "document_extraction": ("document_extraction",),
        "devops_cloud": ("devops_cloud_k8s",),
    }
    for c in cards:
        tags = set(c.get("domains") or [])
        for d, alias in aliases.items():
            if tags & set(alias):
                counts[d] += 1
    return counts


def aggregate_domains(retrieval: dict[str, list[dict]], composition: dict[str, list[dict]],
                      card_counts: dict[str, int]) -> dict[str, Any]:
    """The owner's asks, per domain: token savings, DAG-ability, and the ranked NEEDS."""
    domains: list[dict[str, Any]] = []
    for domain in DOMAIN_PROBES:
        r = retrieval.get(domain, [])
        c = composition.get(domain, [])
        covered = [x for x in r if x["covered"]]
        hits = [x for x in r if x.get("label_hit")]
        routes = [x for x in c if x["route_found"]]
        gaps = [x for x in c if x["model_steps"] > 0]
        needed: dict[str, int] = {}
        for x in c:
            for e in x["needed_edges"]:
                if e:
                    needed[e] = needed.get(e, 0) + 1
        needs: list[str] = []
        coverage = round(len(covered) / len(r), 3) if r else 0.0
        precision = round(len(hits) / len(r), 3) if r else 0.0
        route_rate = round(len(routes) / len(c), 3) if c else 0.0
        gap_rate = round(len(gaps) / len(c), 3) if c else 0.0
        if route_rate < _ROUTE_RATE_NEEDS_DAGS:
            needs.append("more_dags")
        if coverage < _COVERAGE_NEEDS_CARDS:
            needs.append("more_cards")
        if gap_rate > _GAP_RATE_NEEDS_FLEX:
            needs.append("more_flexibility")
        if needed:
            needs.append("more_inputs_outputs")
        domains.append({
            "domain": domain,
            "corpus_cards": card_counts.get(domain, 0),
            "retrieval": {
                "probes": len(r), "coverage": coverage, "verified_precision": precision,
                "avg_net_saved_tokens": round(sum(x["net_saved_tokens"] for x in r) / len(r), 1) if r else 0.0,
                "avg_saved_on_covered": round(sum(x["net_saved_tokens"] for x in covered) / len(covered), 1)
                                        if covered else 0.0,
            },
            "composition": {
                "probes": len(c), "route_found_rate": route_rate, "gap_rate": gap_rate,
                "mean_route_len": round(sum(x["route_len"] for x in routes) / len(routes), 2) if routes else 0.0,
                "top_unmet_edges": sorted(needed, key=lambda e: (-needed[e], e))[:_TOP_UNMET_EDGES],
            },
            "needs": needs,
            **BOUNDARY,
        })
    ranked = sorted(domains, key=lambda d: (len(d["needs"]), -d["retrieval"]["avg_net_saved_tokens"]))
    return {"record_type": "domain_token_savings_benchmark", "domains": ranked,
            "domains_benchmarked": len(ranked),
            "healthiest_first": [d["domain"] for d in ranked], **BOUNDARY}


# ──────────────────────────────────────────────────────────────────────────────
# Verify the verifier (hermetic: synthetic corpus, no persisted index, no network).
# ──────────────────────────────────────────────────────────────────────────────
def _synthetic_cards() -> list[dict]:
    mk = lambda pid, title, bb, ie, oe, doms: {  # noqa: E731
        "primitive_id": pid, "title": title, "blackbox": bb, "input_edge": ie, "output_edge": oe,
        "domains": doms, **BOUNDARY}
    return [
        mk("p:dedup", "Deduplicate csv rows by fuzzy key",
           "Remove duplicate rows in a large csv using fuzzy key matching and keep one canonical row.",
           "CsvRows", "DedupedCsvRows", ["data_engineering"]),
        mk("p:normalize", "Normalize records to canonical schema",
           "Normalize messy records into a clean canonical schema for loading.",
           "RawRecord", "NormalizedRecord", ["data_engineering"]),
        mk("p:ocr", "OCR scanned document", "Extract text from a scanned document image with ocr.",
           "ScannedDocument", "ExtractedText", ["document_extraction"]),
        mk("p:resize", "Resize image", "Resize an image to target dimensions preserving aspect ratio.",
           "Image", "ResizedImage", ["data_science_ml"]),
    ]


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = _synthetic_cards()
    retrieval = run_retrieval_lane(cards, k=3)
    checks.append(("retrieval lane covers every probe domain", set(retrieval) == set(DOMAIN_PROBES)))
    de = retrieval["data_engineering"]
    dedup_row = next(x for x in de if "deduplicate rows" in x["intent"])
    checks.append(("a matching domain probe is covered + verified (dedup -> the dedup card)",
                   dedup_row["covered"] and dedup_row["label_hit"] and dedup_row["net_saved_tokens"] != 0))
    checks.append(("an unmatched domain probe is an HONEST gap, not a fake save",
                   any(x["coverage_gap"] and x["net_saved_tokens"] < 0 for x in retrieval["web_browser"])))
    composition = run_composition_lane(cards, probes_per_domain=2)
    checks.append(("composition lane runs the full pipeline per probe",
                   set(composition) == set(DOMAIN_PROBES)
                   and all("route_found" in x for rows in composition.values() for x in rows)))
    counts = _domain_card_counts(cards)
    checks.append(("domain card counts read the foundry domains tags",
                   counts["data_engineering"] == 2 and counts["document_extraction"] == 1))
    summary = aggregate_domains(retrieval, composition, counts)
    checks.append(("aggregate emits one row per domain with needs + savings",
                   summary["domains_benchmarked"] == len(DOMAIN_PROBES)
                   and all({"domain", "retrieval", "composition", "needs"} <= set(d) for d in summary["domains"])))
    checks.append(("a domain with no matching cards is flagged as needing more",
                   "more_cards" in next(d for d in summary["domains"] if d["domain"] == "web_browser")["needs"]))
    checks.append(("deterministic (byte-identical twice)",
                   json.dumps(aggregate_domains(retrieval, composition, counts), sort_keys=True)
                   == json.dumps(aggregate_domains(retrieval, composition, counts), sort_keys=True)))
    checks.append(("everything is candidate/serves_truth=false",
                   summary["serves_truth"] is False
                   and all(d["serves_truth"] is False for d in summary["domains"])))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - bench_domain_token_savings: {len(DOMAIN_PROBES)} owner-named domains x two lanes "
          f"(retrieval token-savings via the REAL experiment engine + full compose-pipeline DAG-ability), "
          f"rolled up into per-domain savings + ranked NEEDS (more_dags / more_cards / more_flexibility / "
          f"more_inputs_outputs with the unmet edges NAMED). Hermetic, deterministic, serves_truth=false.")
    return 0


def _run(compose_probes: int, k: int) -> int:
    cards = _load_cards(0)  # 0 = FULL corpus (caps are opt-in)
    if not cards:
        print("no corpus on this checkout")
        return 0
    # domain COUNTS read the edge-foundry cards too — the verified corpus's `domains` field is id-prefix
    # debris, while the foundry stamps real semantic tags (data_engineering, browser_automation, ...)
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    edge_path = _sbc / "data" / "dev-intel" / "aidevobserver_edge_foundry" / "primitive_edge_cards.jsonl"
    count_cards = cards + (read_jsonl_tolerant(edge_path) if edge_path.exists() else [])
    print(f"corpus: {len(cards)} cards; retrieval lane ({sum(len(p) for p in DOMAIN_PROBES.values())} probes) ...")
    retrieval = run_retrieval_lane(cards, k=k)
    print(f"composition lane ({compose_probes} probes/domain) ...")
    composition = run_composition_lane(cards, probes_per_domain=compose_probes)
    summary = aggregate_domains(retrieval, composition, _domain_card_counts(count_cards))
    out_dir = _sbc / "data" / "dev-intel" / "domain_token_savings"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "summary.json"
    out.write_text(json.dumps(summary, indent=2, sort_keys=True))
    rows_path = out_dir / "rows.jsonl"
    with rows_path.open("a", encoding="utf-8") as fh:  # APPEND — earlier runs are never overwritten (lossless)
        for domain in DOMAIN_PROBES:
            for row in retrieval[domain] + composition.get(domain, []):
                fh.write(json.dumps({"domain": domain, **row}, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"\nwritten: {out} (+ rows appended to {rows_path})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="run both lanes over the real corpus")
    ap.add_argument("--compose-probes", type=int, default=_DEFAULT_COMPOSE_PROBES,
                    help=f"compose-lane probes per domain (default {_DEFAULT_COMPOSE_PROBES})")
    ap.add_argument("--k", type=int, default=5, help="retrieval depth per probe")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.compose_probes, args.k)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
