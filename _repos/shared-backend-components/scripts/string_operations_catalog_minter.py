#!/usr/bin/env python3
"""scripts.string_operations_catalog_minter — the owner's 1,000-operation string catalog (50 categories x
20 operations, 2026-07-07) minted into primitive candidates, REUSE-FIRST:

  * the catalog file is the verbatim source of truth
    (data/dev-intel/string_operations_catalog/owner-string-operations-catalog.md — do not renumber);
  * every operation -> ONE primitive candidate with typed edges from a small category->edge table (shared
    vocabulary, so candidates chain);
  * operations our packs ALREADY IMPLEMENT are cross-linked to the executable impl (string-standardization
    pack, UI pack) — reuse-first: map onto what exists before minting what doesn't;
  * operations the REPO already provides at scale (MinHash/LSH blocking = primitive_multi_index; embedding
    ops = capability_embedding/build_primitive_embeddings; FTS = primitive_database) are linked to those
    modules as repo_capability;
  * every category -> ONE system candidate (primitive_group whose plan is its 20 operations).

Deterministic; ids via the canonical_id authority; candidate=true, serves_truth=false.

    python3 scripts/string_operations_catalog_minter.py --self-test
    python3 scripts/string_operations_catalog_minter.py --run
"""
from __future__ import annotations

import sys
from pathlib import Path

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
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"string_operations_catalog_minter requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-strop"
_CATALOG_REL = "data/dev-intel/string_operations_catalog/owner-string-operations-catalog.md"
_CAT_RE = re.compile(r"^# (\d+)\. (.+)$")
_OP_RE = re.compile(r"^(\d+)\. (.+)$")
_EXPECT_CATEGORIES = 50
_EXPECT_OPS = 1000

#: operation number -> impl_name ALREADY EXECUTABLE in our packs (reuse-first cross-links)
_EXEC_LINKS: dict[int, str] = {
    41: "unicode_normalize_nfc", 81: "trim_collapse_whitespace", 82: "trim_collapse_whitespace",
    83: "trim_collapse_whitespace", 92: "trim_collapse_whitespace", 95: "trim_collapse_whitespace",
    103: "casefold_for_match", 119: "casefold_for_match", 124: "normalize_apostrophes",
    126: "normalize_apostrophes", 137: "normalize_ampersand", 141: "normalize_ampersand",
    161: "strip_diacritics_for_match", 178: "strip_diacritics_for_match", 197: "tokenize_alnum",
    198: "ngram_key", 202: "extract_legal_suffix", 203: "standardize_person_name",
    223: "normalize_postal_code_us", 224: "normalize_postal_code_us", 301: "standardize_us_address",
    302: "standardize_us_address", 303: "standardize_us_address", 304: "standardize_us_address",
    320: "standardize_us_address", 341: "standardize_us_address", 381: "standardize_person_name",
    390: "standardize_person_name", 395: "standardize_person_name", 399: "soundex_key",
    441: "standardize_company_name", 454: "standardize_company_name", 458: "standardize_company_name",
    459: "standardize_company_name", 472: "token_sorted_key", 621: "soundex_key",
    627: "soundex_key", 628: "soundex_key", 629: "soundex_key", 654: "token_sorted_key",
}
#: operation number -> repo module that already provides the capability at scale
_REPO_LINKS: dict[int, str] = {
    647: "scripts/primitive_multi_index.py", 648: "scripts/primitive_multi_index.py",
    656: "scripts/primitive_multi_index.py", 657: "scripts/primitive_multi_index.py",
    681: "scripts/primitive_multi_index.py", 683: "scripts/primitive_multi_index.py",
    686: "scripts/primitive_database.py", 687: "scripts/primitive_database.py",
    694: "scripts/primitive_multi_index.py", 696: "scripts/build_primitive_embeddings.py",
    707: "scripts/primitive_database.py", 721: "scripts/capability_embedding.py",
    726: "scripts/capability_embedding.py", 729: "scripts/build_primitive_embeddings.py",
    730: "scripts/capability_embedding.py", 731: "scripts/pipeline_path_graph.py",
    732: "scripts/rank_fusion_zoo.py", 739: "scripts/path_graph_bench.py",
    752: "scripts/primitive_multi_index.py", 754: "scripts/primitive_multi_index.py",
}
#: category number -> (input_edge, output_edge); default = (RawStringValue, ProcessedStringResult)
_CATEGORY_EDGES: dict[int, tuple[str, str]] = {
    1: ("SourceRecordPayload", "RawStringValue"), 2: ("RawStringValue", "MissingValueVerdict"),
    12: ("RawStringValue", "ExtractedFieldValue"), 13: ("RawStringValue", "ValidationVerdict"),
    14: ("RawStringValue", "StringShapeProfile"), 15: ("RawStringValue", "ParsedAddressComponents"),
    16: ("ParsedAddressComponents", "CanonicalAddressDisplay"),
    17: ("ParsedAddressComponents", "AddressValidationVerdict"),
    18: ("CanonicalAddressDisplay", "AddressMatchCandidate"),
    19: ("RawStringValue", "ParsedPersonNameComponents"),
    20: ("ParsedPersonNameComponents", "CanonicalPersonNameRecord"),
    21: ("CanonicalPersonNameRecord", "PersonMatchCandidate"),
    22: ("RawStringValue", "ParsedCompanyNameComponents"),
    23: ("ParsedCompanyNameComponents", "CanonicalCompanyNameRecord"),
    24: ("CanonicalCompanyNameRecord", "CompanyMatchCandidate"),
    31: ("NormalizedStringValue", "SimilarityScore"), 32: ("NormalizedStringValue", "PhoneticKey"),
    33: ("NormalizedStringValue", "BlockingKey"), 34: ("BlockingKey", "DuplicateClusterAssignment"),
    35: ("NormalizedStringValue", "SearchIndexEntry"), 36: ("SearchIndexEntry", "RankedSearchResult"),
    37: ("NormalizedStringValue", "EmbeddingVector"), 38: ("EmbeddingVector", "ReducedRepresentation"),
    41: ("RawStringValue", "RedactedStringValue"), 42: ("ProcessedStringResult", "LineageAuditRecord"),
    48: ("UnstructuredText", "ExtractedStructuredFields"),
    49: ("ProcessedStringResult", "HumanReviewDecision"), 50: ("ProcessedStringResult", "QualityMetricRecord"),
}


def parse_catalog(text: str) -> list[dict[str, Any]]:
    """md -> [{n, category_n, category, op}] with strict structure validation."""
    ops: list[dict[str, Any]] = []
    cat_n, cat = 0, ""
    for line in text.splitlines():
        m = _CAT_RE.match(line.strip())
        if m and not line.startswith("# Owner"):
            cat_n, cat = int(m.group(1)), m.group(2).strip()
            continue
        m = _OP_RE.match(line.strip())
        if m and cat_n:
            ops.append({"n": int(m.group(1)), "category_n": cat_n, "category": cat,
                        "op": m.group(2).strip()})
    return ops


def validate_catalog(ops: list[dict[str, Any]]) -> list[str]:
    problems = []
    if len(ops) != _EXPECT_OPS:
        problems.append(f"expected {_EXPECT_OPS} operations, parsed {len(ops)}")
    if [o["n"] for o in ops] != list(range(1, len(ops) + 1)):
        problems.append("operation numbering is not contiguous 1..N")
    cats = {o["category_n"] for o in ops}
    if len(cats) != _EXPECT_CATEGORIES:
        problems.append(f"expected {_EXPECT_CATEGORIES} categories, saw {len(cats)}")
    from collections import Counter  # noqa: PLC0415
    bad = [c for c, k in Counter(o["category_n"] for o in ops).items() if k != 20]
    if bad:
        problems.append(f"categories without exactly 20 ops: {bad}")
    return problems


def mint_rows(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for o in ops:
        ie, oe = _CATEGORY_EDGES.get(o["category_n"], ("RawStringValue", "ProcessedStringResult"))
        exec_link = _EXEC_LINKS.get(o["n"], "")
        repo_link = _REPO_LINKS.get(o["n"], "")
        rows.append({
            "primitive_id": canonical_id(CARD_PREFIX, str(o["n"]), o["op"]),
            "record_type": "string_operation_primitive_candidate", "kind": "primitive",
            "catalog_number": o["n"], "category_number": o["category_n"], "category": o["category"],
            "title": o["op"][:160],
            "blackbox": (f"{o['op']} (string-operations catalog #{o['n']}, category: {o['category']}). "
                         f"Input: a {ie}. Output: a {oe}."),
            "input_edge": ie, "output_edge": oe,
            "executable_link": exec_link, "repo_capability": repo_link,
            "status": "already_executable" if exec_link else ("repo_capability" if repo_link else "to_build"),
            "tags": f"strop:{o['n']} category:{o['category_n']}", **BOUNDARY})
    seen_cat = {}
    for o in ops:
        seen_cat.setdefault(o["category_n"], {"category": o["category"], "ops": []})["ops"].append(o["op"])
    for cn in sorted(seen_cat):
        c = seen_cat[cn]
        title = f"String-operations system: {c['category']}"
        rows.append({
            "primitive_id": canonical_id(CARD_PREFIX, title, str(cn)), "kind": "primitive_group",
            "record_type": "string_operation_system_candidate", "category_number": cn,
            "category": c["category"], "title": title[:160],
            "blackbox": (f"Composite system for '{c['category']}' — composes its 20 catalog operations as a "
                         f"pipeline stage. Input: RawStringValue. Output: ProcessedStringResult."),
            "plan_steps": c["ops"], "input_edge": "RawStringValue", "output_edge": "ProcessedStringResult",
            "tags": f"category:{cn} kind:category_system", **BOUNDARY})
    return rows


def run_minter(catalog_path: Path) -> dict[str, Any]:
    ops = parse_catalog(catalog_path.read_text())
    problems = validate_catalog(ops)
    if problems:
        return {"error": "; ".join(problems), **BOUNDARY}
    rows = mint_rows(ops)
    out_dir = catalog_path.parent
    (out_dir / "string_operation_primitive_candidates.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    status = {"already_executable": 0, "repo_capability": 0, "to_build": 0}
    for r in rows:
        if r["kind"] == "primitive":
            status[r["status"]] += 1
    rec = {"record_type": "string_operations_minter_receipt", "operations": len(ops),
           "categories": _EXPECT_CATEGORIES, "candidates": len(rows), "status_split": status,
           "staged_path": str(out_dir / "string_operation_primitive_candidates.jsonl"), **BOUNDARY}
    (out_dir / "string_operations_minter_receipt.json").write_text(json.dumps(rec, indent=2, sort_keys=True))
    return rec


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    catalog = resource(_CATALOG_REL)
    ops = parse_catalog(catalog.read_text())
    problems = validate_catalog(ops)
    checks.append(("owner catalog parses: exactly 1,000 ops, 50 categories x 20, contiguous numbering",
                   problems == []))
    checks.append(("MUTATION GATE: a corrupted catalog (dropped line) FAILS validation",
                   validate_catalog(ops[:-1]) != []))
    rows = mint_rows(ops)
    prim = [r for r in rows if r["kind"] == "primitive"]
    checks.append(("mints 1 candidate per op + 1 system per category, unique canonical ids",
                   len(prim) == 1000 and len(rows) == 1050
                   and len({r["primitive_id"] for r in rows}) == len(rows)))
    checks.append(("REUSE-FIRST: >=40 ops cross-linked to already-EXECUTABLE pack primitives",
                   sum(1 for r in prim if r["status"] == "already_executable") >= 40))
    checks.append(("repo capabilities linked (LSH blocking -> primitive_multi_index; embeddings -> "
                   "capability_embedding; FTS -> primitive_database)",
                   sum(1 for r in prim if r["status"] == "repo_capability") >= 15
                   and next(r for r in prim if r["catalog_number"] == 657)["repo_capability"]
                   == "scripts/primitive_multi_index.py"))
    checks.append(("typed edges per category so candidates CHAIN (address parse -> standardize -> match)",
                   next(r for r in prim if r["catalog_number"] == 285)["output_edge"] == "ParsedAddressComponents"
                   and next(r for r in prim if r["catalog_number"] == 305)["input_edge"] == "ParsedAddressComponents"
                   and next(r for r in prim if r["catalog_number"] == 345)["input_edge"] == "CanonicalAddressDisplay"))
    checks.append(("deterministic minting (byte-identical)",
                   json.dumps(mint_rows(ops), sort_keys=True) == json.dumps(mint_rows(ops), sort_keys=True)))
    checks.append(("boundary everywhere", all(r.get("serves_truth") is False for r in rows)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - string_operations_catalog_minter: 1,000 owner-catalog operations -> 1,050 candidates "
          "(reuse-first: executable links + repo capabilities marked; typed edges chain). serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        rec = run_minter(resource(_CATALOG_REL))
        print(json.dumps(rec, indent=2, sort_keys=True))
        return 0 if "error" not in rec else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
