#!/usr/bin/env python3
"""scripts.build_edge_type_retrofit — canonicalize the REAL, uncontrolled edge namespace so edges can MATCH.

Red-team gap F2: <0.1% of the ~117k generated primitives carry a canonical edge type from
`build_canonical_edge_type_vocabulary` (AdjacencyGraph, RecordBatch, …). The edge namespace that primitives ACTUALLY
declare is ~4,409 free-text strings streamed off the edge foundry — `JsValue`, `JsArg`, `JsArgs`,
`NodeProject+TestFixture`, `dict[str, Any]`, `list[str] | None`, `tenant_id:str`, `RepoCheckout+ProofConfig`. Two
primitives can only compose when `output_edge` string-equals the next `input_edge` string, so an uncontrolled
namespace means the composition graph is almost fully disconnected. This module folds the raw strings down to a few
hundred canonical `type_id`s by ONE deterministic rule (no model, no network), records the raw→canonical map with
occurrence counts, and — critically — EXPOSES `canonicalize_edge(edge_string) -> type_id` as a pure importable
function so `primitive_match`/`registry_search` can normalize an edge at query time WITHOUT reading this pack.

This is the ADD-ONLY, flexible-multi-path way: it does not edit the contract-locked matchers; it builds a NEW
normalization path they can import and be benchmarked against. The synonym table intentionally lands on the same
`type_id`s the hand-authored `canonical-edge-type-vocabulary` uses (Graph/Adjacency→AdjacencyGraph, Record/Row→
RecordBatch), so the retrofitted real edges and the curated vocabulary share ONE namespace.

Offline + deterministic (no wall-clock/RNG in row bodies). `--self-test` (pure, over a frozen in-module fixture — no
data file needed) asserts `canonicalize_edge` is deterministic, folds known examples, and majority-coverage > 0.5.
`--write` streams the real edge foundry (capped, cap recorded in the manifest) and emits the pack. All rows
candidate=true / serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import collections
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "edge-type-retrofit"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# The real edge namespace lives in these two edge-foundry streams (input_edge + output_edge per card).
INPUT_FILES: list[Path] = [
    _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "primitive_edge_cards.jsonl",
    _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "verified_factory_primitive_cards.jsonl",
]
# Cap the stream for speed + determinism; recorded in the manifest so the coverage number is reproducible.
ROW_CAP = 40000

# ── the deterministic canonicalization rule (rule + tables live HERE, so callers need no pack) ──

# Multi-input strings join types with '+'. These trailing companion parts are policy/config side-channels, not the
# payload TYPE, so a part whose head token is one of these is dropped before picking the head type.
SUFFIX_DROP: frozenset[str] = frozenset({"policy", "context", "config", "options", "opts", "settings", "flags"})
# Generic wrappers that carry no type of their own — unwrap to the first inner type (Optional[Path] -> Path).
UNWRAP: frozenset[str] = frozenset({"optional", "awaitable", "coroutine", "final", "annotated", "async"})

# Head-token (lowercased, alnum-only) -> canonical type_id. Deliberately lands on the SAME ids the curated
# canonical-edge-type-vocabulary uses so real edges and curated edges share one namespace. member folding is
# lossless: every raw string is preserved in edge_type_map.jsonl, so this map is reversible.
SYNONYMS: dict[str, str] = {
    # graph family (task-named) -> curated vocabulary id
    "graph": "AdjacencyGraph", "adjacency": "AdjacencyGraph", "adjacencygraph": "AdjacencyGraph",
    "adjacencylist": "AdjacencyGraph", "digraph": "AdjacencyGraph",
    # record/row family (task-named) -> curated vocabulary id
    "record": "RecordBatch", "row": "RecordBatch", "records": "RecordBatch", "rows": "RecordBatch",
    "recordbatch": "RecordBatch", "rawrecordbatch": "RecordBatch",
    # JS runtime family (the single largest real cluster)
    "jsarg": "JsArgument", "jsargs": "JsArgument", "jsargument": "JsArgument", "jsarguments": "JsArgument",
    "jsvalue": "JsValue",
    # proof/receipt family
    "testproofreceipt": "ProofReceipt", "proofrunreceipt": "ProofReceipt", "proofreceipt": "ProofReceipt",
    "receipt": "ProofReceipt", "runreceipt": "ProofReceipt", "importreceipt": "ProofReceipt",
    # codebase-under-test family (all denote the snapshot/checkout of the code being proven)
    "nodeproject": "ProjectUnderTest", "projectundertest": "ProjectUnderTest", "repocheckout": "ProjectUnderTest",
    "reposnapshot": "ProjectUnderTest", "repository": "ProjectUnderTest", "repo": "ProjectUnderTest",
    "codebase": "ProjectUnderTest", "project": "ProjectUnderTest",
    # container types
    "dict": "Mapping", "mapping": "Mapping", "map": "Mapping", "dictionary": "Mapping", "defaultdict": "Mapping",
    "list": "Collection", "array": "Collection", "sequence": "Collection", "seq": "Collection",
    "tuple": "Collection", "set": "Collection", "frozenset": "Collection", "iterable": "Collection",
    # scalar types
    "str": "Text", "string": "Text", "text": "Text",
    "int": "Integer", "integer": "Integer",
    "float": "Number", "number": "Number", "decimal": "Number",
    "bool": "Boolean", "boolean": "Boolean",
    "bytes": "Bytes", "bytearray": "Bytes",
    "path": "Path", "pathlib": "Path",
    "none": "NoneType", "nonetype": "NoneType",
    "any": "Any", "object": "Any",
}


def _camel(token: str) -> str:
    """CamelCase-normalize a bare type token (already-camel tokens are preserved)."""
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", token) if p]
    if not parts:
        return ""
    if len(parts) == 1:
        p = parts[0]
        # already mixed-case (e.g. NodeProject / argparseNamespace) -> keep, just upper the first char
        return p[0].upper() + p[1:] if any(c.isupper() for c in p[1:]) else p[:1].upper() + p[1:]
    return "".join(p[:1].upper() + p[1:] for p in parts)


def _head_token(edge_string: str) -> str:
    """Reduce a raw edge string to its head type token, deterministically."""
    s = edge_string.strip()
    if not s:
        return ""
    # (1) union / optional: take the first alternative (X | None -> X)
    s = s.split("|")[0].strip()
    # (2) multi-input: drop policy/config side-channel parts, then take the head part
    parts = [p.strip() for p in s.split("+") if p.strip()]
    parts = [p for p in parts
             if re.sub(r"[^a-z0-9]", "", p.split(":")[-1].split("[")[0].lower()) not in SUFFIX_DROP]
    if not parts:
        return ""
    head = parts[0]
    # (3) named arg 'name:type' -> the type
    if ":" in head:
        head = head.split(":")[-1].strip()
    # (4) unwrap generic wrappers (Optional[X], Awaitable[X], ...) -> first inner type
    for _ in range(4):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*)\[(.+)\]$", head)
        if m and re.sub(r"[^a-z0-9]", "", m.group(1).split(".")[-1].lower()) in UNWRAP:
            head = [p.strip() for p in m.group(2).split(",") if p.strip()][0]
            continue
        break
    # (5) strip remaining generic/array markers: list[dict] -> list, Dict[str,Any] -> Dict
    head = head.split("[")[0].strip()
    # (6) drop module qualifier: argparse.Namespace -> Namespace
    if "." in head:
        head = head.split(".")[-1].strip()
    return head


def canonicalize_edge(edge_string: str) -> str:
    """Pure, importable: fold a raw edge string to a canonical type_id. No pack read, no I/O, no network.

    Rule: strip union/optional alternatives and '+Policy'/'+Context'-style side-channel parts, take the head type
    token, unwrap generic wrappers and strip generic params, CamelCase-normalize, then map through the synonym
    table onto the shared canonical namespace. Empty/unparseable -> "Unknown".
    """
    if not isinstance(edge_string, str) or not edge_string.strip():
        return "Unknown"
    head = _head_token(edge_string)
    if not head:
        return "Unknown"
    key = re.sub(r"[^a-z0-9]", "", head.lower())
    if key in SYNONYMS:
        return SYNONYMS[key]
    return _camel(head) or "Unknown"


# ── streaming the real namespace (write path only; self-test never touches disk) ──
def stream_edge_counts(*, cap: int = ROW_CAP) -> tuple[collections.Counter, collections.Counter, int]:
    """Return (input_edge counts, output_edge counts, rows_scanned) over the capped edge-foundry stream."""
    inc: collections.Counter = collections.Counter()
    outc: collections.Counter = collections.Counter()
    scanned = 0
    for path in INPUT_FILES:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if scanned >= cap:
                    return inc, outc, scanned
                scanned += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ie = row.get("input_edge")
                oe = row.get("output_edge")
                if isinstance(ie, str) and ie.strip():
                    inc[ie.strip()] += 1
                if isinstance(oe, str) and oe.strip():
                    outc[oe.strip()] += 1
    return inc, outc, scanned


# ── pack assembly (pure over the counts, so the same builder serves the write path AND the fixture self-test) ──
def build_pack_from_counts(inc: dict[str, int], outc: dict[str, int]) -> dict[str, list[dict[str, Any]]]:
    raws = set(inc) | set(outc)
    # aggregate per canonical type
    members: dict[str, set[str]] = collections.defaultdict(set)
    occ: dict[str, int] = collections.defaultdict(int)
    producer: dict[str, int] = collections.defaultdict(int)  # produced == appears as output_edge
    consumer: dict[str, int] = collections.defaultdict(int)  # consumed == appears as input_edge
    for raw in raws:
        c = canonicalize_edge(raw)
        i = int(inc.get(raw, 0))
        o = int(outc.get(raw, 0))
        members[c].add(raw)
        occ[c] += i + o
        producer[c] += o
        consumer[c] += i

    map_rows = [{
        "record_type": "edge_type_map",
        "raw_edge_string": raw,
        "canonical_type_id": canonicalize_edge(raw),
        "occurrence_count": int(inc.get(raw, 0)) + int(outc.get(raw, 0)),
        "as_input_count": int(inc.get(raw, 0)),
        "as_output_count": int(outc.get(raw, 0)),
        **BOUNDARY,
    } for raw in raws]
    map_rows.sort(key=lambda r: (-r["occurrence_count"], r["raw_edge_string"]))

    type_rows = [{
        "record_type": "edge_canonical_type",
        "type_id": c,
        "member_raw_strings_count": len(members[c]),
        "occurrence_count": occ[c],
        "producer_count": producer[c],   # how often a primitive PRODUCES this type (output_edge)
        "consumer_count": consumer[c],   # how often a primitive CONSUMES this type (input_edge)
        # source == nothing produces it, something consumes it (enters the graph from outside)
        "is_source": producer[c] == 0 and consumer[c] > 0,
        # sink == nothing consumes it, something produces it (terminal output of the graph)
        "is_sink": consumer[c] == 0 and producer[c] > 0,
        **BOUNDARY,
    } for c in occ]
    type_rows.sort(key=lambda r: (-r["occurrence_count"], r["type_id"]))

    return {"edge_type_map.jsonl": map_rows, "canonical_types.jsonl": type_rows}


def majority_coverage(type_rows: list[dict[str, Any]]) -> tuple[float, int]:
    """Coverage = share of occurrences landing in canonical types that FOLD >=2 distinct raw strings (i.e. edges that
    canonicalization actually made mutually matchable). Returns (coverage, total_occurrences)."""
    total = sum(r["occurrence_count"] for r in type_rows)
    if total == 0:
        return 0.0, 0
    folded = sum(r["occurrence_count"] for r in type_rows if r["member_raw_strings_count"] >= 2)
    return folded / total, total


def _vocabulary_alignment(type_ids: set[str]) -> dict[str, Any]:
    """Reuse the curated vocabulary builder to report how many retrofitted types land on the SAME namespace."""
    try:
        from scripts import build_canonical_edge_type_vocabulary as vocab
        curated = set(vocab._all_types().keys())
    except Exception:
        return {"available": False, "aligned_type_ids": [], "aligned_count": 0}
    aligned = sorted(type_ids & curated)
    return {"available": True, "aligned_type_ids": aligned, "aligned_count": len(aligned),
            "curated_type_count": len(curated)}


def build_manifest(pack: dict[str, list[dict[str, Any]]], *, date: str, row_cap: int,
                   rows_scanned: int) -> dict[str, Any]:
    type_rows = pack["canonical_types.jsonl"]
    map_rows = pack["edge_type_map.jsonl"]
    cov, total = majority_coverage(type_rows)
    type_ids = {r["type_id"] for r in type_rows}
    row_counts = {n: len(r) for n, r in pack.items()}
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False)
                          for n in sorted(pack) for r in pack[n])
    return {
        "record_type": "edge_type_retrofit_manifest",
        "pack_id": "edge-type-retrofit",
        "generator": "scripts/build_edge_type_retrofit.py",
        "generated_utc": date,
        "row_cap": row_cap,
        "rows_scanned": rows_scanned,
        "row_counts": row_counts,
        "total_rows": sum(row_counts.values()),
        "distinct_raw_edge_strings": len(map_rows),
        "canonical_type_count": len(type_ids),
        "occurrence_total": total,
        "coverage_definition": "share of edge occurrences whose canonical type folds >=2 distinct raw strings",
        "majority_coverage": round(cov, 6),
        "source_type_count": sum(1 for r in type_rows if r["is_source"]),
        "sink_type_count": sum(1 for r in type_rows if r["is_sink"]),
        "vocabulary_alignment": _vocabulary_alignment(type_ids),
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def write_pack(*, date: str, cap: int = ROW_CAP) -> dict[str, Any]:
    inc, outc, scanned = stream_edge_counts(cap=cap)
    pack = build_pack_from_counts(inc, outc)
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in pack.items():
        (PACK_DIR / name).write_text(
            "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(pack, date=date, row_cap=cap, rows_scanned=scanned)
    (PACK_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# Frozen fixture of the real head of the namespace (raw, as_input_count, as_output_count) — lets --self-test verify
# folding + majority-coverage PURELY, with no dependency on the (growing) data files.
FROZEN_SAMPLE: list[tuple[str, int, int]] = [
    ("JsValue", 0, 18322),
    ("TestProofReceipt", 0, 10178),
    ("JsArg", 8633, 0),
    ("NodeProject+TestFixture", 7031, 0),
    ("JsArgs", 6614, 0),
    ("None", 5601, 938),
    ("ProjectUnderTest+TestFixture", 3147, 0),
    ("str", 1205, 1143),
    ("dict", 511, 1708),
    ("int", 64, 976),
    ("dict[str, Any]", 157, 848),
    ("RepoCheckout+ProofConfig", 1004, 0),
    ("ProofRunReceipt", 0, 1004),
    ("Any", 363, 640),
    ("list[dict]", 85, 577),
    ("bool", 16, 450),
    ("list[str]", 89, 318),
    ("Path", 205, 92),
    ("list[str] | None", 288, 0),
    ("list[dict[str, Any]]", 42, 167),
    ("str+str", 196, 0),
    ("Mapping[str, Any]+Mapping[str, Any]", 182, 0),
    ("dict[str,object]", 0, 159),
    ("float", 15, 130),
    ("dict | None", 30, 109),
    ("str | None", 47, 83),
    ("Any+Any", 104, 0),
]

# Known folds the rule must honor (raw -> expected canonical type_id).
KNOWN_FOLDS: list[tuple[str, str]] = [
    ("JsArg", "JsArgument"), ("JsArgs", "JsArgument"),
    ("TestProofReceipt", "ProofReceipt"), ("ProofRunReceipt", "ProofReceipt"),
    ("list[dict]", "Collection"), ("dict[str, Any]", "Mapping"), ("str+str", "Text"),
    ("NodeProject+TestFixture", "ProjectUnderTest"), ("RepoCheckout+ProofConfig", "ProjectUnderTest"),
    ("list[str] | None", "Collection"), ("tenant_id:str", "Text"), ("Optional[Path]", "Path"),
    ("argparse.Namespace", "Namespace"), ("SourceEvidence -> PrimitiveRecordDraft", "SourceEvidencePrimitiveRecordDraft"),
    ("graph", "AdjacencyGraph"), ("Record", "RecordBatch"), ("None", "NoneType"), ("", "Unknown"),
]


def self_test() -> int:
    inc = {r: i for r, i, _o in FROZEN_SAMPLE}
    outc = {r: o for r, _i, o in FROZEN_SAMPLE}
    pack = build_pack_from_counts(inc, outc)
    type_rows = pack["canonical_types.jsonl"]
    cov, total = majority_coverage(type_rows)
    by_id = {r["type_id"]: r for r in type_rows}

    deterministic = all(canonicalize_edge(r) == canonicalize_edge(r) for r, _i, _o in FROZEN_SAMPLE)
    folds_ok = [(raw, want, canonicalize_edge(raw)) for raw, want in KNOWN_FOLDS]
    fold_fails = [f"{raw!r}->{got!r} (want {want!r})" for raw, want, got in folds_ok if got != want]

    checks = [
        ("canonicalize_edge is deterministic", deterministic),
        ("all known folds hold", not fold_fails),
        ("canonicalize_edge returns str for junk", isinstance(canonicalize_edge(None), str)  # type: ignore[arg-type]
         and canonicalize_edge(None) == "Unknown"),  # type: ignore[arg-type]
        ("majority-coverage > 0.5", cov > 0.5),
        ("folding really happened (fewer canonical than raw)", len(type_rows) < len(FROZEN_SAMPLE)),
        ("JsArgument folds >=2 raw members", by_id.get("JsArgument", {}).get("member_raw_strings_count", 0) >= 2),
        ("ProofReceipt folds >=2 raw members", by_id.get("ProofReceipt", {}).get("member_raw_strings_count", 0) >= 2),
        ("JsValue inferred is_sink (produced, never consumed)", by_id.get("JsValue", {}).get("is_sink") is True),
        ("JsArgument inferred is_source (consumed, never produced)",
         by_id.get("JsArgument", {}).get("is_source") is True),
        ("map+type rows carry candidate/serves_truth boundary",
         all(r["candidate"] is True and r["serves_truth"] is False for rows in pack.values() for r in rows)),
        ("every map row's canonical resolves to a defined type",
         all(r["canonical_type_id"] in by_id for r in pack["edge_type_map.jsonl"])),
        ("lands on curated vocabulary namespace (AdjacencyGraph/RecordBatch reachable)",
         canonicalize_edge("graph") == "AdjacencyGraph" and canonicalize_edge("Row") == "RecordBatch"),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - edge_type_retrofit:\n  " + "\n  ".join(failed)
              + ("\n  fold_fails: " + "; ".join(fold_fails) if fold_fails else ""))
        return 1
    print(f"PASS - edge_type_retrofit: fixture folds {len(FROZEN_SAMPLE)} raw edge strings -> {len(type_rows)} "
          f"canonical types, majority-coverage={cov:.3f} over {total} occurrences; canonicalize_edge is a pure, "
          f"deterministic importable that shares the curated canonical-edge-type namespace.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    parser.add_argument("--cap", type=int, default=ROW_CAP)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    manifest = write_pack(date=date, cap=args.cap)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
