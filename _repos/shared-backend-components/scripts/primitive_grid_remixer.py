#!/usr/bin/env python3
"""scripts.primitive_grid_remixer — the exhaustive combinatorial primitive generator: enumerate every axis of
software work (data types · 1,000+ software operations · infrastructure tools · latency requirements · software
tools · hardware systems · data-entity types person/place/thing/logs/…) and REMIX them into a grid of BILLIONS
of combinations, minting a governed primitive candidate for each point of a strided walk.

Every operation lands on an entity of a data type, moved through an infra tool + software tool, under a latency
requirement, on a hardware system — a full "what × on-what × where × how-fast × on-what-metal" coordinate. The
1,000+ software operations are COMPUTED (verb × object), never hand-typed; the full grid size is computed from
the axes; the walk is a deterministic stride to ``--target`` (no RNG, no wall-clock). Ids are minted only by
``canonical_id``; every card is born ``candidate=true / serves_truth=false`` (generation is never promotion);
the staged file is a NEW file next to — never equal to — the verified corpus.

Quality is a NON-DESTRUCTIVE routing signal (owner law: nothing discarded): each mint is scored by the
usefulness gate and the placeholder/weak/pass split is reported; flagged cards route to enrichment, never
dropped. This is the SUPPLY side of the factory — millions of governed leads the enrichment + funnel govern.

    python3 scripts/primitive_grid_remixer.py --self-test
    python3 scripts/primitive_grid_remixer.py --mint --target 200000
    python3 scripts/primitive_grid_remixer.py --grid-size     # just print the computed grid size + axes
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/mint_idea_primitives.py) ─────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Iterator, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_grid_remixer requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

GRID_ID_PREFIX = "prim-grid"
GRID_RECORD_TYPE = "grid_primitive_candidate"
GRID_SCHEMA_VERSION = 1
STAGED_FILENAME = "grid_primitive_candidates.jsonl"
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
_READINESS_UNPROVEN = "grid_candidate_unproven"
_PROMOTION_BLOCKERS = ("source_evidence", "correctness_proof", "usefulness_or_enrichment", "license_review")
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")

# ── the AXES (single source; promotable to vocabularies/). Comprehensive, not exhaustive-of-the-universe — each
#    is extensible by adding a row, and every count below is COMPUTED from these tuples, never typed. ─────────

# every (common) DATA TYPE
_DATA_TYPES: tuple[str, ...] = (
    "int", "float", "decimal", "boolean", "string", "bytes", "uuid", "timestamp", "date", "duration",
    "enum", "json", "xml", "csv", "parquet", "avro", "protobuf", "array", "map", "set", "tuple", "tree",
    "graph", "vector", "tensor", "matrix", "image", "audio", "video", "geojson", "timeseries", "blob",
    "email", "url", "ip_address", "currency", "percentage", "coordinate",
)

# SOFTWARE OPERATIONS — 1,000+, COMPUTED from verb x object (never hand-typed; extend either list to grow).
_OP_VERBS: tuple[str, ...] = (
    "ingest", "extract", "parse", "validate", "normalize", "standardize", "conform", "transform", "enrich",
    "deduplicate", "aggregate", "join", "filter", "sort", "rank", "index", "search", "retrieve", "cache",
    "compress", "encrypt", "decrypt", "sign", "verify", "hash", "route", "schedule", "batch", "stream",
    "replicate", "reconcile", "migrate", "backfill", "snapshot", "rollback", "audit", "monitor", "alert",
    "throttle", "retry", "checkpoint", "shard", "partition", "replay", "classify", "cluster", "embed",
    "summarize", "translate", "redact", "anonymize", "annotate", "score", "sample", "impute", "forecast",
)
_OP_OBJECTS: tuple[str, ...] = (
    "records", "events", "requests", "responses", "files", "documents", "messages", "logs", "metrics",
    "embeddings", "models", "features", "transactions", "sessions", "users", "entities", "payloads",
    "streams", "batches", "tables", "indexes", "queues", "caches", "blobs", "images", "vectors", "graphs",
    "schemas", "configs", "secrets", "traces", "spans", "signals",
)

# INFRASTRUCTURE TOOLS
_INFRA_TOOLS: tuple[str, ...] = (
    "postgres", "mysql", "sqlite", "redis", "memcached", "kafka", "rabbitmq", "nats", "elasticsearch",
    "opensearch", "clickhouse", "bigquery", "snowflake", "s3", "gcs", "r2", "minio", "kubernetes", "docker",
    "nomad", "terraform", "pulumi", "prometheus", "grafana", "opentelemetry", "spark", "flink", "airflow",
    "dagster", "dbt", "pgvector", "faiss", "milvus", "cloudflare", "nginx",
)

# LATENCY REQUIREMENTS
_LATENCY: tuple[tuple[str, str], ...] = (
    ("ultra_low", "sub-millisecond, in-process"), ("realtime", "under 10ms"),
    ("interactive", "under 100ms"), ("near_realtime", "under 1s"), ("responsive", "under 5s"),
    ("batch", "minutes"), ("bulk", "hours, offline"),
)

# SOFTWARE TOOLS / libraries
_SOFTWARE_TOOLS: tuple[str, ...] = (
    "fastapi", "flask", "django", "pandas", "numpy", "polars", "pytorch", "tensorflow", "onnx",
    "scikit-learn", "playwright", "selenium", "beautifulsoup", "pydantic", "sqlalchemy", "celery",
    "grpc", "graphql", "openapi", "ffmpeg", "opencv", "tesseract", "duckdb", "arrow", "protobuf",
)

# HARDWARE SYSTEMS
_HARDWARE: tuple[str, ...] = (
    "cpu", "gpu", "tpu", "fpga", "arm_edge", "mobile", "embedded_mcu", "single_node", "cluster",
    "serverless", "raspberry_pi", "browser_wasm",
)

# DATA-ENTITY TYPES (person, place, thing, logs, ...)
_ENTITY_TYPES: tuple[tuple[str, str], ...] = (
    ("person", "people / customer / user records"), ("place", "geographic / location records"),
    ("thing", "physical asset / device / product records"), ("organization", "company / org records"),
    ("event", "occurrence / activity records"), ("transaction", "financial / exchange records"),
    ("log", "application / audit log lines"), ("metric", "time-series measurements"),
    ("document", "unstructured document / text"), ("message", "communication / chat messages"),
    ("sensor_reading", "IoT / telemetry readings"), ("media_asset", "image / audio / video assets"),
    ("relationship", "graph edges between entities"), ("configuration", "settings / policy records"),
    ("credential", "identity / secret references (names only)"),
)

_STOP = frozenset("a an the for of to in on with and or via using into from as is are be that this it one".split())

#: blackbox FRAMES cycled by axis so a huge mint does not collapse to one skeleton (the mint_idea lesson).
_FRAMES: tuple[str, ...] = (
    "A reusable primitive that {op} for {ent} represented as {dtype}, moving them through {infra} with {tool} "
    "under a {lat_name} latency budget ({lat_desc}) on {hw}. Emits a typed, composable result.",
    "Given {ent} as {dtype} on {hw}, this unit {op} them via {infra}+{tool}, meeting a {lat_name} budget "
    "({lat_desc}). Packaged as a typed step.",
    "To {op} for {ent} ({dtype}) at {lat_name} latency ({lat_desc}), this primitive uses {tool} over {infra} "
    "on {hw}. Composes by typed edges.",
    "{op}, specialized to {ent} stored as {dtype}: runs {tool} against {infra} on {hw} within a {lat_name} "
    "window ({lat_desc}).",
    "A {lat_name}-latency unit ({lat_desc}) that {op} for {ent} as {dtype} using {infra} and {tool}, deployed "
    "on {hw}. Typed input and output.",
    "Idea: {op} for {ent} ({dtype}) on {hw}. Path: {tool} over {infra}; budget: {lat_name} ({lat_desc}). "
    "A reusable typed primitive.",
)


def software_operations() -> list[str]:
    """The 1,000+ software operations, COMPUTED from verb x object (deduped, deterministic order)."""
    seen: list[str] = []
    s: set = set()
    for v in _OP_VERBS:
        for o in _OP_OBJECTS:
            op = f"{v} {o}"
            if op not in s:
                s.add(op)
                seen.append(op)
    return seen


_OPERATIONS = software_operations()  # computed once


def axis_sizes() -> dict[str, int]:
    return {"operations": len(_OPERATIONS), "data_types": len(_DATA_TYPES), "infra_tools": len(_INFRA_TOOLS),
            "latency": len(_LATENCY), "software_tools": len(_SOFTWARE_TOOLS), "hardware": len(_HARDWARE),
            "entity_types": len(_ENTITY_TYPES),
            "op_verbs": len(_OP_VERBS), "op_objects": len(_OP_OBJECTS)}


def grid_size() -> int:
    s = axis_sizes()
    return (s["operations"] * s["data_types"] * s["infra_tools"] * s["latency"] * s["software_tools"]
            * s["hardware"] * s["entity_types"])


def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    return ("".join(p[:1].upper() + p[1:] for p in parts if p) or "X")[:60]


def _tokens(op: str, dtype: str, infra: str, ent: str) -> list[str]:
    seen: list[str] = []
    for t in (op, dtype, infra.replace("_", " "), ent.replace("_", " ")):
        for w in str(t).split():
            wl = w.lower()
            if wl not in _STOP and wl not in seen:
                seen.append(wl)
    return seen


_AXIS_SIZES_ORDER = ("operations", "data_types", "infra_tools", "latency", "software_tools", "hardware",
                     "entity_types")


def _grid_card(idx: tuple[int, int, int, int, int, int, int]) -> dict[str, Any]:
    oi, di, fi, li, si, hi, ei = idx
    op = _OPERATIONS[oi]
    dtype = _DATA_TYPES[di]
    infra = _INFRA_TOOLS[fi]
    lat_name, lat_desc = _LATENCY[li]
    tool = _SOFTWARE_TOOLS[si]
    hw = _HARDWARE[hi]
    ent_slug, ent_desc = _ENTITY_TYPES[ei]

    title = f"{op.capitalize()} for {ent_slug} as {dtype} via {infra} on {hw} ({lat_name})"
    frame = _FRAMES[(oi * 7 + di * 5 + fi * 3 + li + ei) % len(_FRAMES)]
    blackbox = frame.format(op=op, ent=ent_desc, dtype=dtype, infra=infra, tool=tool, lat_name=lat_name,
                            lat_desc=lat_desc, hw=hw)
    tokens = _tokens(op, dtype, infra, ent_slug)
    input_edge = _camel(ent_slug, op.split()[-1], "input")
    output_edge = _camel(op.split()[0], infra, "result")
    pid = canonical_id(GRID_ID_PREFIX, title, blackbox)
    return {
        "record_type": GRID_RECORD_TYPE, "schema_version": GRID_SCHEMA_VERSION, "kind": "route.primitive",
        "primitive_id": pid, "title": title[:180], "blackbox": blackbox[:1200],
        "input_edge": input_edge, "output_edge": output_edge, "blocking_keys": tokens,
        "capability_tags": [f"op:{op.replace(' ', '_')}", f"dtype:{dtype}", f"infra:{infra}",
                            f"latency:{lat_name}", f"tool:{tool}", f"hardware:{hw}", f"entity:{ent_slug}"],
        "contract": {"input": f"{ent_desc} as {dtype} (concepts: {', '.join(tokens)})",
                     "output": f"a typed result of {op} via {infra} under {lat_name} latency"},
        "axes": {"operation": op, "data_type": dtype, "infra_tool": infra, "latency": lat_name,
                 "software_tool": tool, "hardware": hw, "entity_type": ent_slug},
        "readiness": _READINESS_UNPROVEN, "promotion_blockers": list(_PROMOTION_BLOCKERS),
        "provenance": {"minter": "scripts.primitive_grid_remixer", "grid_size": grid_size()},
        **BOUNDARY,
    }


#: a large Mersenne prime, coprime to the grid size (whose only prime factors are 2,3,5,7,11,19) — so
#: ``(i * _COPRIME_STRIDE) % total`` is a BIJECTION over 0..total-1 (a full-period LCG). A plain arithmetic
#: stride aliases the low-order axes (they share factors with the step); the coprime walk visits DISTINCT
#: flat indices AND spreads across every axis. Deterministic, no RNG.
_COPRIME_STRIDE = 2147483647  # 2**31 - 1, prime


def _strided_indices(target: int, start: int = 0) -> Iterator[tuple[int, int, int, int, int, int, int]]:
    """Walk the 7-axis grid via a coprime multiplicative sequence so `target` cards are DISTINCT and spread
    evenly across every axis, deterministic (no RNG, no wall-clock). ``start`` RESUMES the walk (i in
    [start, start+target)) so chunked minting accumulates DISJOINT cards toward millions without OOM — the
    coprime stride guarantees distinct flats across the whole [0, total) range."""
    total = grid_size()
    sizes = [axis_sizes()[k] for k in _AXIS_SIZES_ORDER]
    hi = min(start + target, total)
    for i in range(start, hi):
        flat = (i * _COPRIME_STRIDE) % total
        idx = []
        rem = flat
        for sz in reversed(sizes):
            idx.append(rem % sz)
            rem //= sz
        yield tuple(reversed(idx))  # type: ignore[misc]


def mint_grid(target: int, start: int = 0) -> list[dict[str, Any]]:
    if target < 1:
        raise ValueError("target must be >= 1")
    cards: list[dict[str, Any]] = []
    seen: set = set()
    for idx in _strided_indices(target, start):
        card = _grid_card(idx)
        if card["primitive_id"] in seen:
            raise ValueError(f"duplicate grid mint for {card['title']!r} — axis collision")
        seen.add(card["primitive_id"])
        cards.append(card)
    return cards


def validate_grid_card(card: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if card.get("primitive_id") != canonical_id(GRID_ID_PREFIX, card.get("title", ""), card.get("blackbox", "")):
        problems.append("primitive_id does not recompute")
    for ef in ("input_edge", "output_edge"):
        if not _CAMEL_EDGE_RE.match(str(card.get(ef) or "")):
            problems.append(f"{ef} not CamelCase")
    if not card.get("blocking_keys"):
        problems.append("blocking_keys empty")
    if card.get("serves_truth") is not False or card.get("candidate") is not True:
        problems.append("candidate boundary not stamped")
    text = f"{card.get('title','')} {card.get('blackbox','')}".lower()
    if not all(t in text for t in card.get("blocking_keys", [])[:2]):
        problems.append("blackbox does not carry its leading concept tokens")
    return problems


def staged_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / STAGED_FILENAME


def write_staged(cards: list[dict[str, Any]], target_path: Optional[Path] = None) -> dict[str, Any]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = target_path or staged_path()
    if p.name != STAGED_FILENAME:
        raise ValueError(f"refusing to write to {p.name!r} — only {STAGED_FILENAME!r} allowed")
    if p.is_symlink():
        raise ValueError(f"refusing to write through a symlink at {p}")
    if p.exists() and (p.resolve().name in _VERIFIED_CORPUS_FILENAMES or p.resolve().name != STAGED_FILENAME):
        raise ValueError(f"resolved target {p.resolve()} is not the staged file — refused")
    for c in cards:
        probs = validate_grid_card(c)
        if probs:
            raise ValueError(f"card {c.get('primitive_id')} failed validation: {probs}")
    existing = {str(r.get("primitive_id")) for r in (read_jsonl_tolerant(p) if p.exists() else [])}
    appended = 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for c in cards:
            pid = str(c["primitive_id"])
            if pid in existing:
                continue
            existing.add(pid)
            fh.write(json.dumps(c, sort_keys=True) + "\n")
            appended += 1
    return {"appended": appended, "on_file": len(existing), "path": str(p), **BOUNDARY}


def quality_report(cards: list[dict[str, Any]]) -> dict[str, Any]:
    from scripts.primitive_usefulness_gate import measure_pool  # noqa: PLC0415
    m = measure_pool(cards, "grid_primitive_mint")
    return {k: m[k] for k in ("n_cards_scored", "placeholder_rate", "weak_rate", "verdict_counts",
                              "stamped_clusters")}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("1,000+ software operations are COMPUTED (verb x object)",
                   len(_OPERATIONS) >= 1000 and _OPERATIONS == software_operations()))
    checks.append(("grid size is COMPUTED and in the MILLIONS+ (billions)",
                   grid_size() == len(_OPERATIONS) * len(_DATA_TYPES) * len(_INFRA_TOOLS) * len(_LATENCY)
                   * len(_SOFTWARE_TOOLS) * len(_HARDWARE) * len(_ENTITY_TYPES) and grid_size() > 1_000_000_000))
    cards = mint_grid(800)
    checks.append(("mints the requested count deterministically", len(cards) == 800))
    checks.append(("byte-identical remint (no RNG / no wall-clock)",
                   json.dumps(cards, sort_keys=True) == json.dumps(mint_grid(800), sort_keys=True)))
    checks.append(("every id recomputes from canonical_id + edges CamelCase + boundary stamped",
                   all(not validate_grid_card(c) for c in cards)))
    checks.append(("ids unique across the mint", len({c["primitive_id"] for c in cards}) == len(cards)))

    def _distinct(axis: str) -> int:
        return len({c["axes"][axis] for c in cards})
    checks.append(("the stride spreads across every axis (operations, entity, infra, latency, hardware)",
                   _distinct("operation") >= 20 and _distinct("entity_type") >= 8 and _distinct("infra_tool") >= 10
                   and _distinct("latency") >= 4 and _distinct("hardware") >= 6))
    import tempfile  # noqa: PLC0415
    refused = False
    try:
        write_staged(cards[:1], target_path=Path(tempfile.gettempdir()) / "verified_factory_primitive_cards.jsonl")
    except ValueError:
        refused = True
    checks.append(("write_staged REFUSES a verified corpus filename", refused))
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / STAGED_FILENAME
        a = write_staged(cards[:50], target_path=tp)
        b = write_staged(cards[:50], target_path=tp)
        checks.append(("append-dedupe: first N, second 0", a["appended"] == 50 and b["appended"] == 0))
    qr = quality_report(cards)
    checks.append(("usefulness gate scores the mint as a routing signal (verdict split present)",
                   set(qr["verdict_counts"]) == {"pass", "weak", "placeholder"}))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - primitive_grid_remixer: {len(_OPERATIONS):,} computed software operations x 6 more axes = a "
          f"{grid_size():,}-point grid; deterministic strided mint; canonical ids recompute; CamelCase edges; "
          f"candidate/serves_truth=false; write refuses verified corpus; usefulness gate scores as a "
          f"NON-DESTRUCTIVE routing signal. Generation is not promotion. serves_truth=false.")
    return 0


def _mint(target: int, start: int = 0) -> int:
    cards = mint_grid(target, start)
    qr = quality_report(cards)
    wrote = write_staged(cards)
    rec = {"record_type": "grid_primitive_mint_receipt", "schema_version": 1, "target": target,
           "minted": len(cards), "appended": wrote["appended"], "on_file": wrote["on_file"],
           "grid_size": grid_size(), "axis_sizes": axis_sizes(),
           "distinct_axis_values": {ax: len({c["axes"][ax] for c in cards}) for ax in
                                    ("operation", "data_type", "infra_tool", "latency", "software_tool",
                                     "hardware", "entity_type")},
           "quality_gate": qr,
           "routing": "placeholder/weak route to scripts.enrich_minted_primitives; NONE discarded", **BOUNDARY}
    out = resource("data") / "dev-intel" / "session_emulation" / "grid_primitive_mint_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("target", "minted", "appended", "grid_size", "distinct_axis_values",
                                          "quality_gate")}, indent=2, sort_keys=True))
    print(f"\nstaged: {wrote['path']}\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mint", action="store_true")
    ap.add_argument("--target", type=int, default=200_000)
    ap.add_argument("--start", type=int, default=0, help="resume the coprime walk at this index (chunked millions)")
    ap.add_argument("--grid-size", action="store_true", help="print the computed grid size + axis sizes")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.grid_size:
        print(json.dumps({"grid_size": grid_size(), "software_operations": len(_OPERATIONS),
                          "axis_sizes": axis_sizes()}, indent=2))
        return 0
    if args.mint:
        return _mint(args.target, args.start)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
