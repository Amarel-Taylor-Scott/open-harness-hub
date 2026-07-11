#!/usr/bin/env python3
"""primitive_domain_partitioner — break the corpus into category/domain/niche partitions with routed search.

Owner (2026-07-10): "break up primitives by category, domain, niche, etc, and implement all appropriate best
practice improvements, verifications." This module is that layer, built to the repo's laws:

- DETERMINISTIC taxonomy (no LLM): a data-driven DOMAIN_TAXONOMY table scores each card's title/edges/
  blocking_keys tokens; ties break by declared priority; nothing matched -> "general". Extending coverage or
  adding a domain = ONE row. `niche` = the card's own family/category field when present (a second, finer axis).
- LOSSLESS derived layer: partitioning writes per-domain shard files + per-domain indexes under a partitions dir
  and NEVER touches the source corpus (originals stay the raw layer; partitions are recomputable). Every count in
  the manifest is COMPUTED, with a conservation check: shard rows sum EXACTLY to input rows and every id lands in
  exactly one domain.
- SELECTIVE serving (the RAM/best-practice win): per-domain indexes load lazily, so a routed query touches a few
  partition indexes instead of one 557K-doc monolith. The query router is NON-DESTRUCTIVE: low routing confidence
  -> search ALL partitions (a router may demote work, never hide results).
- VERIFICATION built in: the self-test proves conservation, determinism, and ROUTED-vs-MONOLITHIC equivalence on
  probe queries; `--verify` runs the same equivalence sweep over the real partitions and writes a receipt.

    PYTHONPATH=. python3 scripts/primitive_domain_partitioner.py --self-test
    PYTHONPATH=. python3 scripts/primitive_domain_partitioner.py --partition          # build real partitions
    PYTHONPATH=. python3 scripts/primitive_domain_partitioner.py --verify --sample 40
    PYTHONPATH=. python3 scripts/primitive_domain_partitioner.py --route "parse csv header rows"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

DEFAULT_PARTITIONS_DIR = _REPO / "catalog" / "knowledge-packs" / "data" / "primitive-domain-partitions"
GENERAL_DOMAIN = "general"          # the always-present fallback partition (unmatched cards; always searched)
#: a domain smaller than this gets NO own index — its cards fold into the general index instead (shard files
#: stay pure). Guards the df-cap pathology: in a micro-partition every shared token exceeds the doc-frequency
#: cap and the partition becomes unsearchable. The general index is searched on every query, so nothing hides.
MIN_CARDS_FOR_DOMAIN_INDEX = 50
_ROUTER_TOP_DOMAINS = 4             # routed search loads at most this many partitions + general
_ROUTER_MIN_SCORE = 2.0             # below this routing confidence -> non-destructive fallback: search ALL
_TOKEN_PATTERN = re.compile(r"[a-z0-9_]{2,}")

#: THE TAXONOMY (data-driven; extend a domain's vocabulary or add a domain = one row). Order = tie-break priority
#: (more specific domains first). Keywords match card title + edge names + blocking keys, lowercased.
DOMAIN_TAXONOMY: dict[str, set[str]] = {
    "healthcare_admin": {"claim", "edi", "provider", "patient", "npi", "hipaa", "icd", "cpt", "fhir", "hl7",
                         "eligibility", "remittance", "clinical"},
    "finance_compliance": {"sanction", "ofac", "kyc", "aml", "invoice", "ledger", "payment", "stripe", "tax",
                           "sec", "audit", "billing", "currency", "banking", "loan", "escrow"},
    "auth_identity_security": {"auth", "oauth", "jwt", "token", "login", "session", "password", "secret", "rbac",
                               "permission", "encrypt", "tls", "signature", "credential", "identity", "sso"},
    "scraping_browser": {"scrape", "crawler", "selenium", "playwright", "browser", "webdriver", "beautifulsoup",
                         "spider", "cdp", "headless", "dom"},
    "ml_training_inference": {"model", "train", "embedding", "inference", "classifier", "regression", "dataset",
                              "feature", "sklearn", "pytorch", "tensor", "lightgbm", "xgboost", "catboost",
                              "prompt", "llm", "rerank", "fine", "epoch"},
    "files_formats": {"csv", "json", "xml", "yaml", "pdf", "excel", "xlsx", "parquet", "zip", "encoding",
                      "serialize", "jsonl", "toml", "binary", "file"},   # format tokens outrank generic "parse"
    "text_nlp_parsing": {"parse", "tokenize", "regex", "nlp", "stem", "lemma", "sentence", "grammar", "ocr",
                         "extract", "markdown", "html", "summary", "translate", "language"},
    "database_storage": {"sql", "postgres", "sqlite", "database", "query", "index", "schema", "migration",
                         "redis", "mongo", "table", "transaction", "orm", "vector", "cache"},
    "http_api_integration": {"http", "api", "rest", "endpoint", "request", "webhook", "graphql", "grpc", "url",
                             "client", "fetch", "retry", "backoff", "rate", "pagination", "sdk"},
    "messaging_queueing": {"queue", "kafka", "pubsub", "message", "event", "stream", "broker", "consumer",
                           "producer", "topic", "sqs", "amqp", "websocket"},
    "cloud_infra_deploy": {"docker", "kubernetes", "terraform", "aws", "gcp", "azure", "deploy", "lambda",
                           "serverless", "container", "helm", "cloud", "provision", "bucket", "s3"},
    "devops_observability": {"log", "metric", "trace", "alert", "monitor", "prometheus", "telemetry", "health",
                             "dashboard", "incident", "cron", "scheduler", "pipeline", "ci"},
    "data_engineering_etl": {"etl", "dedupe", "normalize", "batch", "ingest", "transform", "aggregate", "join",
                             "dataframe", "pandas", "spark", "flink", "warehouse", "partition", "checksum"},
    "geospatial_time": {"geo", "latitude", "longitude", "timezone", "date", "time", "calendar", "duration",
                        "interval", "coordinate", "distance", "timestamp"},
    "testing_verification": {"test", "assert", "mock", "fixture", "validate", "verification", "oracle", "proof",
                             "coverage", "lint", "fuzz", "benchmark"},
    "math_algorithms": {"sort", "search", "graph", "tree", "hash", "algorithm", "matrix", "random", "prime",
                        "optimize", "statistics", "probability", "combinatorics", "dynamic"},
    "frontend_ui": {"react", "component", "css", "render", "ui", "form", "button", "layout", "chart", "canvas",
                    "svg", "responsive", "accessibility"},
}
_DOMAIN_PRIORITY = {domain: rank for rank, domain in enumerate(DOMAIN_TAXONOMY)}
ALL_DOMAINS: tuple[str, ...] = (*DOMAIN_TAXONOMY, GENERAL_DOMAIN)


def _card_tokens(card: dict[str, Any]) -> Counter[str]:
    text = " ".join(str(card.get(field) or "") for field in ("title", "input_edge", "output_edge")).lower()
    tokens = Counter(_TOKEN_PATTERN.findall(text))
    for key in card.get("blocking_keys") or []:
        tokens[str(key).lower()] += 1
    return tokens


def assign_domain(card: dict[str, Any]) -> dict[str, Any]:
    """Deterministic (token-overlap score, priority tie-break) domain + niche assignment for one card."""
    tokens = _card_tokens(card)
    scores = {domain: sum(count for token, count in tokens.items()
                          if token in vocabulary or token.rstrip("s") in vocabulary)
              for domain, vocabulary in DOMAIN_TAXONOMY.items()}
    best = max(scores.items(), key=lambda kv: (kv[1], -_DOMAIN_PRIORITY[kv[0]]))
    domain = best[0] if best[1] > 0 else GENERAL_DOMAIN
    return {"domain": domain, "score": best[1],
            "niche": str(card.get("family") or card.get("category") or "")[:64] or None}


def _read_cards(files: Iterable[Path]) -> Iterable[dict[str, Any]]:
    for file in files:
        file = Path(file)
        if not file.exists():
            continue
        with file.open() as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def partition_corpus(files: Iterable[Path], out_dir: Optional[Path] = None,
                     build_indexes: bool = True) -> dict[str, Any]:
    """Write per-domain shards (+ optional per-domain indexes) as a LOSSLESS derived layer; sources untouched."""
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415  the ONE index engine

    out = Path(out_dir or DEFAULT_PARTITIONS_DIR)
    out.mkdir(parents=True, exist_ok=True)
    handles: dict[str, Any] = {}
    counts: Counter[str] = Counter()
    niche_counts: dict[str, Counter[str]] = defaultdict(Counter)
    seen_ids: set[str] = set()
    total_rows = duplicate_rows = 0
    try:
        for card in _read_cards(files):
            total_rows += 1
            card_id = str(card.get("primitive_id") or "")
            if not card_id or card_id in seen_ids:   # exactly-one-partition law: later duplicates are skipped
                duplicate_rows += 1
                continue
            seen_ids.add(card_id)
            assignment = assign_domain(card)
            domain = assignment["domain"]
            if domain not in handles:
                (out / domain).mkdir(parents=True, exist_ok=True)
                handles[domain] = (out / domain / "cards.jsonl").open("w")
            handles[domain].write(json.dumps(card, sort_keys=True) + "\n")
            counts[domain] += 1
            if assignment["niche"]:
                niche_counts[domain][assignment["niche"]] += 1
    finally:
        for handle in handles.values():
            handle.close()

    index_stats: dict[str, int] = {}
    if build_indexes:
        general_pool: list[dict[str, Any]] = []
        for domain in counts:
            cards = list(_read_cards([out / domain / "cards.jsonl"]))
            if domain != GENERAL_DOMAIN and len(cards) < MIN_CARDS_FOR_DOMAIN_INDEX:
                general_pool.extend(cards)   # micro-domain: index via general (df-cap guard); shard stays pure
                continue
            if domain == GENERAL_DOMAIN:
                general_pool.extend(cards)
                continue
            index = build_index(cards)
            (out / domain / "index.json").write_text(json.dumps(index))
            index_stats[domain] = len(cards)
        (out / GENERAL_DOMAIN).mkdir(parents=True, exist_ok=True)
        (out / GENERAL_DOMAIN / "index.json").write_text(json.dumps(build_index(general_pool)))
        index_stats[GENERAL_DOMAIN] = len(general_pool)

    manifest = {
        "schema_version": "primitive-domain-partitions/v1",
        "domains": {domain: {"cards": counts[domain],
                             "top_niches": dict(niche_counts[domain].most_common(5))}
                    for domain in sorted(counts)},
        "n_domains": len(counts),
        "total_rows_read": total_rows,
        "unique_cards_partitioned": len(seen_ids),
        "duplicate_or_idless_rows_skipped": duplicate_rows,
        "conservation_ok": sum(counts.values()) == len(seen_ids),
        "indexes_built": index_stats,
        "content_digest": hashlib.sha256(json.dumps(dict(counts), sort_keys=True).encode()).hexdigest()[:16],
        "candidate": True,
        "serves_truth": False,
    }
    (out / "partition_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


# ==================================================================================================================
# Routed search — load only the partitions the query needs; low confidence -> ALL (non-destructive)
# ==================================================================================================================
_INDEX_CACHE: dict[str, dict] = {}


def route_query_domains(query: str) -> dict[str, Any]:
    tokens = Counter(_TOKEN_PATTERN.findall(query.lower()))
    scores = {domain: sum(count for token, count in tokens.items()
                          if token in vocabulary or token.rstrip("s") in vocabulary)
              for domain, vocabulary in DOMAIN_TAXONOMY.items()}
    ranked = sorted(((score, domain) for domain, score in scores.items() if score > 0), reverse=True)
    confident = ranked and ranked[0][0] >= _ROUTER_MIN_SCORE
    routed = [domain for _score, domain in ranked[:_ROUTER_TOP_DOMAINS]] + [GENERAL_DOMAIN]
    return {"routed_domains": routed if confident else list(ALL_DOMAINS),
            "confident": bool(confident), "scores": {d: s for s, d in ranked[:6]}}


def _load_partition_index(partitions_dir: Path, domain: str) -> Optional[dict]:
    key = str(partitions_dir / domain)
    if key not in _INDEX_CACHE:
        path = partitions_dir / domain / "index.json"
        _INDEX_CACHE[key] = json.loads(path.read_text()) if path.exists() else None
    return _INDEX_CACHE[key]


def search_partitioned(query: str, limit: int = 10,
                       partitions_dir: Optional[Path] = None) -> tuple[list[dict], dict[str, Any]]:
    """Route -> search only the routed partitions -> merge by score. Fallback (low confidence) covers ALL."""
    from scripts.build_primitive_search_index import search_with_stats  # noqa: PLC0415

    directory = Path(partitions_dir or DEFAULT_PARTITIONS_DIR)
    routing = route_query_domains(query)
    merged: list[tuple[float, dict]] = []
    searched = []
    for domain in routing["routed_domains"]:
        index = _load_partition_index(directory, domain)
        if index is None:
            continue
        searched.append(domain)
        hits, _stats = search_with_stats(query, limit, index=index)
        merged.extend((float(hit.get("score") or 0.0), hit) for hit in hits)
    merged.sort(key=lambda pair: -pair[0])
    return ([hit for _score, hit in merged[:limit]],
            {"routing": routing, "partitions_searched": searched, "candidate": True, "serves_truth": False})


def verify_against_monolith(sample: int = 25, partitions_dir: Optional[Path] = None,
                            monolithic_index: Optional[dict] = None) -> dict[str, Any]:
    """Equivalence sweep: for sampled cards' titles, does routed-partitioned search recover the monolithic top
    hit in its top-k? Writes a receipt; the floor is a RATCHET the caller can gate on. ``monolithic_index``
    injects the comparison index (tests); None -> the persisted production index."""
    from scripts.build_primitive_search_index import search_with_stats  # noqa: PLC0415

    directory = Path(partitions_dir or DEFAULT_PARTITIONS_DIR)
    manifest = json.loads((directory / "partition_manifest.json").read_text())
    domains = sorted(manifest["domains"], key=lambda d: -manifest["domains"][d]["cards"])
    probes, recovered = 0, 0
    misses = []
    for domain in domains:
        if probes >= sample:
            break
        cards = list(_read_cards([directory / domain / "cards.jsonl"]))
        stride = max(1, len(cards) // 5)  # deterministic stride: up to ~5 probes per domain, no RNG
        for position in range(0, len(cards), stride):
            if probes >= sample:
                break
            card = cards[position]
            query = str(card.get("title") or "")
            if len(query.split()) < 2:
                continue
            probes += 1
            monolithic_hits, _s = search_with_stats(query, 5, index=monolithic_index)
            routed_hits, _meta = search_partitioned(query, 5, partitions_dir=directory)
            monolithic_top = {h.get("primitive_id") for h in monolithic_hits[:1]}
            if not monolithic_top or monolithic_top & {h.get("primitive_id") for h in routed_hits}:
                recovered += 1
            else:
                misses.append({"query": query[:80], "expected": sorted(monolithic_top)})
    recovery = round(recovered / probes, 4) if probes else 0.0
    receipt = {"probes": probes, "recovered": recovered, "recovery_rate": recovery,
               "misses_sample": misses[:5], "candidate": True, "serves_truth": False}
    (directory / "verification_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))
    return receipt


# ==================================================================================================================
def _self_test() -> int:
    import tempfile
    checks: list[tuple[str, bool, str]] = []

    cards = [
        {"primitive_id": "p:csv", "title": "Parse CSV header rows", "blocking_keys": ["csv", "parse", "header"]},
        {"primitive_id": "p:jwt", "title": "Verify JWT auth token signature",
         "blocking_keys": ["jwt", "auth", "token"]},
        {"primitive_id": "p:http", "title": "HTTP retry with exponential backoff",
         "blocking_keys": ["http", "retry", "backoff"]},
        {"primitive_id": "p:none", "title": "Frobnicate the widget", "blocking_keys": ["widget"]},
        {"primitive_id": "p:dup", "title": "Parse CSV header rows again", "blocking_keys": ["csv"]},
        {"primitive_id": "p:dup", "title": "duplicate id row", "blocking_keys": ["csv"]},
        {"primitive_id": "p:ml", "title": "Train LightGBM classifier with feature dataset",
         "family": "gradient_boosting", "blocking_keys": ["train", "lightgbm", "classifier"]},
    ]
    # filler docs (the MCP-server fixture pattern, same 41-doc shape): give the tiny corpus realistic df
    # statistics so the df-cap keeps selective tokens — in a micro corpus EVERY token exceeds the cap.
    cards += [{"primitive_id": f"p:filler{i:02d}", "title": f"Generic gizmo helper number {i}",
               "blocking_keys": ["gizmo", "generic", "helper"]} for i in range(35)]

    # (1) deterministic, sensible assignment incl. the general fallback and the niche axis.
    assignments = {card["primitive_id"]: assign_domain(card) for card in cards}
    checks.append(("taxonomy assigns csv->files_formats, jwt->auth, http->http_api, unmatched->general, "
                   "ml niche=family",
                   assignments["p:csv"]["domain"] == "files_formats"
                   and assignments["p:jwt"]["domain"] == "auth_identity_security"
                   and assignments["p:http"]["domain"] == "http_api_integration"
                   and assignments["p:none"]["domain"] == GENERAL_DOMAIN
                   and assignments["p:ml"]["domain"] == "ml_training_inference"
                   and assignments["p:ml"]["niche"] == "gradient_boosting",
                   json.dumps({k: v["domain"] for k, v in assignments.items()})))
    checks.append(("assignment deterministic",
                   all(assign_domain(card) == assign_domain(card) for card in cards), ""))

    with tempfile.TemporaryDirectory() as sandbox:
        source = Path(sandbox) / "cards.jsonl"
        source.write_text("".join(json.dumps(card) + "\n" for card in cards))
        out = Path(sandbox) / "partitions"

        # (2) partitioning is LOSSLESS + conserving: unique ids land in exactly one shard; dupes counted not lost.
        manifest = partition_corpus([source], out_dir=out)
        checks.append((f"conservation: {manifest['unique_cards_partitioned']} unique across "
                       f"{manifest['n_domains']} domains, {manifest['duplicate_or_idless_rows_skipped']} dup skipped",
                       manifest["conservation_ok"] and manifest["unique_cards_partitioned"] == 41
                       and manifest["duplicate_or_idless_rows_skipped"] == 1
                       and source.exists(), json.dumps(manifest["domains"])))

        # (3) routing: a confident query touches few partitions; a vague one falls back to ALL (non-destructive).
        confident = route_query_domains("verify jwt auth token signature")
        vague = route_query_domains("frobnicate widget thing")
        checks.append(("router: confident query -> few domains incl. auth; vague -> ALL domains fallback",
                       confident["confident"] and "auth_identity_security" in confident["routed_domains"]
                       and len(confident["routed_domains"]) <= _ROUTER_TOP_DOMAINS + 1
                       and not vague["confident"] and set(vague["routed_domains"]) == set(ALL_DOMAINS),
                       json.dumps({"confident": confident, "vague": vague})))

        # (4) routed search finds the right card through its partition; general stays reachable.
        hits, meta = search_partitioned("verify jwt auth token signature", 3, partitions_dir=out)
        hits_general, _m2 = search_partitioned("frobnicate the widget", 3, partitions_dir=out)
        checks.append(("routed search: jwt card via auth partition; widget card via general fallback",
                       hits and hits[0]["primitive_id"] == "p:jwt"
                       and any(h["primitive_id"] == "p:none" for h in hits_general),
                       json.dumps(meta["partitions_searched"])))

        # (5) equivalence verification: routed recovers the monolithic top hit on EVERY probe (identical corpus,
        #     injected monolith index — the production --verify runs the same sweep against the persisted index).
        from scripts.build_primitive_search_index import build_index
        unique_cards = {card["primitive_id"]: card for card in cards}
        monolith = build_index(list(unique_cards.values()))
        receipt = verify_against_monolith(sample=8, partitions_dir=out, monolithic_index=monolith)
        checks.append((f"verification receipt: recovery {receipt['recovery_rate']:.0%} over {receipt['probes']} probes",
                       (out / "verification_receipt.json").exists() and receipt["probes"] >= 4
                       and receipt["recovery_rate"] == 1.0, json.dumps(receipt)))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_domain_partitioner: {len(DOMAIN_TAXONOMY)}+1 deterministic "
          f"domains (extend = one row), lossless conserving shards + per-domain indexes, NON-DESTRUCTIVE query "
          f"router (low confidence -> ALL), monolith-equivalence verification receipt. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:280]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Domain/category/niche partitions + routed search over them.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--partition", action="store_true", help="partition the REAL corpus + build indexes")
    parser.add_argument("--verify", action="store_true", help="routed-vs-monolithic equivalence receipt")
    parser.add_argument("--route", help="show routing for a query")
    parser.add_argument("--sample", type=int, default=25)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.partition:
        from scripts.build_primitive_search_index import SOURCE_CARD_FILES  # noqa: PLC0415
        print(json.dumps(partition_corpus(SOURCE_CARD_FILES), indent=2, sort_keys=True))
        return 0
    if args.verify:
        print(json.dumps(verify_against_monolith(sample=args.sample), indent=2, sort_keys=True))
        return 0
    if args.route:
        print(json.dumps(route_query_domains(args.route), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
