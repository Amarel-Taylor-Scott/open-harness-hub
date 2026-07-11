#!/usr/bin/env python3
"""scripts.primitive_behavior_signature — behavioral identity + dedupe/shadowing detection (2026-07-08).
The owner's "underused field": a primitive's identity is not its name (names lie), its embedding (drifts), or
its source hash (formatting churns) — it is WHAT IT DOES on canonical fixtures. A behavior signature hashes the
ordered (input -> normalized output) pairs, so two primitives are "the same" iff they behave the same. This is
the substrate for dedupe, regression detection, and supersession before 141 cards becomes 14,100.

Three signatures, none requiring us to execute an arbitrary/unknown-signature body:
  - source_hash        : content hash of the body (exact duplicate)
  - normalized_ast_hash: AST STRUCTURE with identifiers/constants stripped (structural near-duplicate)
  - io_signature       : input_edge + output_edge + record_type (contract-shape duplicate)
plus an EXECUTED behavior_signature for primitives we can safely call (the scalar kernel as the worked example).
Reports clusters only — NEVER deletes (owner + ARCHIVAL law: move/report, never destroy). candidate;
serves_truth=false.

    python3 scripts/primitive_behavior_signature.py --self-test
    python3 scripts/primitive_behavior_signature.py --dedupe-report
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import ast  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"primitive_behavior_signature requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}


def normalized_ast_hash(body: str) -> str:
    """Structural fingerprint: the sequence of AST node types + operators, with identifiers, constants, and
    docstrings STRIPPED. Two functions with the same shape but different names/literals collide -> a
    near-duplicate SIGNAL (candidate, for review — not proof of equivalence)."""
    try:
        tree = ast.parse(body or "")
    except SyntaxError:
        return canonical_id("nast", "UNPARSEABLE", body or "")
    skeleton: list[str] = []
    for node in ast.walk(tree):
        t = type(node).__name__
        if t in ("Name", "arg"):
            skeleton.append("ID")            # collapse all identifiers
        elif t == "Constant":
            skeleton.append("CONST")         # collapse all literals
        elif t in ("BinOp", "BoolOp", "UnaryOp", "Compare"):
            skeleton.append(t)               # keep operator structure
        elif t not in ("Load", "Store", "Del", "Expr"):
            skeleton.append(t)
    return canonical_id("nast", "|".join(skeleton))


def card_signatures(card: dict[str, Any]) -> dict[str, str]:
    """The three non-executing signatures every card gets (dedupe/shadow inputs)."""
    body = card.get("executable_body") or ""
    return {"source_hash": canonical_id("src", body),
            "normalized_ast_hash": normalized_ast_hash(body),
            "io_signature": canonical_id("io", str(card.get("input_edge")), str(card.get("output_edge")),
                                         str(card.get("record_type")))}


def behavior_signature(fn: Callable[[str], Any], probes: list[str]) -> str:
    """EXECUTED behavioral identity: hash the ordered (probe -> normalized output) pairs. Deterministic fn ->
    stable signature; a change in behavior on any probe changes the signature (regression/supersession sensor)."""
    pairs = []
    for p in probes:
        try:
            out = fn(p)
        except Exception as exc:  # a raise is itself behavior
            out = {"__error__": type(exc).__name__}
        pairs.append([p, json.dumps(out, sort_keys=True, default=str)])
    return canonical_id("behsig", json.dumps(pairs, sort_keys=True))


def dedupe_report(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Group cards by each signature; report clusters with >1 member as duplicate/shadow CANDIDATES. Never
    deletes — this is evidence for a human/next-stage supersession decision (owner + ARCHIVAL law)."""
    def _cluster(key: str) -> list[dict[str, Any]]:
        groups: dict[str, list[str]] = {}
        for c in cards:
            sig = card_signatures(c)[key]
            groups.setdefault(sig, []).append(str(c.get("impl_name") or c.get("primitive_id")))
        return [{"signature": s, "members": sorted(m)} for s, m in sorted(groups.items()) if len(m) > 1]
    exact = _cluster("source_hash")
    structural = _cluster("normalized_ast_hash")
    io_shape = _cluster("io_signature")
    return {"record_type": "primitive_dedupe_report", "n_cards": len(cards),
            "exact_duplicate_clusters": exact,
            "structural_near_duplicate_clusters": structural[:25],
            "io_shape_clusters_count": len(io_shape),
            "note": "clusters are CANDIDATES for supersession review; structural = same AST shape (diff "
                    "names/literals) so many are legitimately distinct primitives; nothing is deleted", **BOUNDARY}


def scalar_behavior_signature() -> str:
    """The worked example: the scalar kernel's executed behavioral identity on canonical fixtures."""
    from scripts.scalar_standardization_primitives import standardize_scalar  # noqa: PLC0415
    probes = ["  5 ft. ", "60 in", "$1.2M", "(1,234.56)", "12%", "YES", "N/A", "00123", "José García"]
    return behavior_signature(standardize_scalar, probes)


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # normalized AST: same structure, different names/constants -> SAME hash; different structure -> different
    a = "def f(x):\n    return x.strip()\n"
    b = "def g(y):\n    return y.strip()\n"
    c = "def h(x):\n    return x.upper().strip()\n"
    checks.append(("normalized_ast_hash: rename-only is identical; extra call differs",
                   normalized_ast_hash(a) == normalized_ast_hash(b)
                   and normalized_ast_hash(a) != normalized_ast_hash(c)))
    checks.append(("source_hash: identical body same, whitespace change differs (exact-dup detector)",
                   card_signatures({"executable_body": a})["source_hash"]
                   == card_signatures({"executable_body": a})["source_hash"]
                   and card_signatures({"executable_body": a})["source_hash"]
                   != card_signatures({"executable_body": a + "\n"})["source_hash"]))
    # behavior signature: deterministic fn -> stable; behavior change -> different
    sig1 = behavior_signature(lambda x: {"v": x.strip()}, ["  a  ", "b"])
    sig2 = behavior_signature(lambda x: {"v": x.strip()}, ["  a  ", "b"])
    sig3 = behavior_signature(lambda x: {"v": x.upper()}, ["  a  ", "b"])
    checks.append(("behavior_signature: stable across runs, changes when behavior changes",
                   sig1 == sig2 and sig1 != sig3 and sig1.startswith("behsig-")))
    ss1 = scalar_behavior_signature()
    ss2 = scalar_behavior_signature()
    checks.append(("scalar kernel behavior signature is stable (deterministic identity)", ss1 == ss2))
    # dedupe over the live pool
    from scripts.executable_pack_pool_sync import collect_pack_cards  # noqa: PLC0415
    rep = dedupe_report(collect_pack_cards())
    checks.append(("dedupe report runs over the live pool; 0 EXACT duplicates (ids are canonical)",
                   rep["n_cards"] >= 100 and rep["exact_duplicate_clusters"] == []))
    checks.append(("report is report-only (a dedupe_report record, boundary set) — no destructive fields",
                   rep["record_type"] == "primitive_dedupe_report" and rep["serves_truth"] is False
                   and not any(k in rep for k in ("delete", "removed_ids", "purge"))))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - primitive_behavior_signature: source + normalized-AST + io + EXECUTED behavior signatures; "
          f"dedupe/shadow report (report-only, never deletes). {rep['n_cards']} cards, 0 exact duplicates. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--dedupe-report", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.dedupe_report:
        from scripts.executable_pack_pool_sync import collect_pack_cards  # noqa: PLC0415
        print(json.dumps(dedupe_report(collect_pack_cards()), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
