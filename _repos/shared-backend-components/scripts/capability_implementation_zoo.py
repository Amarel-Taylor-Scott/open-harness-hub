#!/usr/bin/env python3
"""capability_implementation_zoo — a capability keeps an IMMUTABLE zoo of implementations (review §4).

The external review's most emphasized structural change: a logical capability is not one mutable "current
code" record. It is a `CapabilityFamily` holding a non-destructive, append-only set of `ImplementationVariant`s
(functions, libraries, services, source slices, WASM/OCI, deployments) across many cost/quality/licensing/
runtime trade-offs. Ranking is a QUERY-TIME view under a policy; it NEVER deletes or overwrites an alternative.
Two implementations can be incomparable (faster vs leaner, permissive-license vs higher-accuracy), so the zoo
retains a Pareto set + a diversity archive, not a single global winner.

This module is that object model, with the invariants the review calls essential PROVEN by self-test:
append-only (a "better" implementation never removes the old), Pareto non-dominance (incomparable variants
both survive), rank-as-a-view (different policy → different top, identical zoo), and novelty preservation (an
unusual delivery-mode/license variant is retained even if numerically dominated).

    PYTHONPATH=. python3 scripts/capability_implementation_zoo.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"capability_implementation_zoo requires canonical_id; import failed: {exc}")

FAMILY_ID_PREFIX = "pcap"
#: the numeric objectives implementations are compared on (lower is better for all). Categorical attributes
#: (license, delivery_mode, runtime) are NOT dominance objectives — they are diversity axes (novelty preserved).
_OBJECTIVES = ("latency_ms", "memory_mb", "tokens")
_DIVERSITY_AXES = ("delivery_mode", "license", "runtime")


def new_family(capability_id: str, description: str = "") -> dict[str, Any]:
    return {"family_id": canonical_id(FAMILY_ID_PREFIX, capability_id), "capability_id": capability_id,
            "description": description, "record_type": "capability_family", "implementations": [],
            "candidate": True, "serves_truth": False}


def add_implementation(family: dict[str, Any], impl: dict[str, Any]) -> dict[str, Any]:
    """APPEND-ONLY: add an implementation without ever overwriting a prior one. Exact-duplicate CONTENT shares
    a content digest but keeps its own lineage/alias; nothing is deleted. Returns a NEW family (immutable-ish)."""
    content_digest = canonical_id("impl-content", impl.get("body") or impl.get("impl_id") or "",
                                  json.dumps(impl.get("cost", {}), sort_keys=True))
    stamped = {**impl, "impl_id": impl.get("impl_id") or canonical_id("impl", family["capability_id"],
                                                                      json.dumps(impl, sort_keys=True)),
               "content_digest": content_digest, "lifecycle": impl.get("lifecycle", "candidate"),
               "candidate": True, "serves_truth": False}
    return {**family, "implementations": [*family["implementations"], stamped]}


def _dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """a dominates b iff a is <= b on every objective and < on at least one (lower is better)."""
    ca, cb = a.get("cost", {}), b.get("cost", {})
    le_all = all(ca.get(o, float("inf")) <= cb.get(o, float("inf")) for o in _OBJECTIVES)
    lt_any = any(ca.get(o, float("inf")) < cb.get(o, float("inf")) for o in _OBJECTIVES)
    return le_all and lt_any


def pareto_set(implementations: list[dict[str, Any]]) -> list[str]:
    """The non-dominated implementation ids. Two incomparable variants both appear."""
    live = [i for i in implementations if i.get("lifecycle") not in ("revoked", "quarantined")]
    front = [i for i in live if not any(o is not i and _dominates(o, i) for o in live)]
    return sorted(i["impl_id"] for i in front)


def diversity_archive(implementations: list[dict[str, Any]]) -> list[str]:
    """One representative implementation id per distinct diversity bucket (delivery_mode × license × runtime),
    so an unusual approach survives even when numerically dominated (novelty preservation)."""
    seen: dict[tuple, str] = {}
    for impl in sorted(implementations, key=lambda i: i["impl_id"]):
        bucket = tuple(str(impl.get(ax) or "") for ax in _DIVERSITY_AXES)
        if bucket not in seen:
            seen[bucket] = impl["impl_id"]
    return sorted(seen.values())


def rank(family: dict[str, Any], weights: Optional[dict[str, float]] = None) -> dict[str, Any]:
    """A NON-DESTRUCTIVE ranking VIEW under a policy's objective weights. Returns every implementation ordered
    by weighted score (lower=better), each flagged pareto/dominated — the zoo is never mutated or pruned."""
    weights = weights or {o: 1.0 for o in _OBJECTIVES}
    impls = family["implementations"]
    front = set(pareto_set(impls))
    archive = set(diversity_archive(impls))

    def score(impl: dict[str, Any]) -> float:
        cost = impl.get("cost", {})
        return sum(weights.get(o, 1.0) * float(cost.get(o, 0)) for o in _OBJECTIVES)

    ranked = sorted(impls, key=lambda i: (score(i), i["impl_id"]))
    return {"capability_id": family["capability_id"], "n_implementations": len(impls),
            "weights": weights, "pareto_front": sorted(front), "diversity_archive": sorted(archive),
            "ranking": [{"impl_id": i["impl_id"], "score": round(score(i), 4),
                         "on_pareto_front": i["impl_id"] in front, "in_diversity_archive": i["impl_id"] in archive,
                         "lifecycle": i.get("lifecycle")} for i in ranked],
            "note": "ranking is a query-time VIEW; no implementation is deleted, overwritten, or pruned",
            "candidate": True, "serves_truth": False}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    fam = new_family("text.normalize-person-name", "normalize a person name")
    # three implementations with a genuine trade-off: fast-but-heavy, lean-but-slow, and a middling one; plus a
    # dominated one and a novel-delivery-mode one.
    fam = add_implementation(fam, {"impl_id": "fast", "cost": {"latency_ms": 5, "memory_mb": 900, "tokens": 0},
                                   "delivery_mode": "python_import", "license": "MIT", "runtime": "python"})
    fam = add_implementation(fam, {"impl_id": "lean", "cost": {"latency_ms": 40, "memory_mb": 64, "tokens": 0},
                                   "delivery_mode": "python_import", "license": "MIT", "runtime": "python"})
    fam = add_implementation(fam, {"impl_id": "dominated", "cost": {"latency_ms": 50, "memory_mb": 950, "tokens": 0},
                                   "delivery_mode": "python_import", "license": "MIT", "runtime": "python"})
    fam = add_implementation(fam, {"impl_id": "wasm_novel", "cost": {"latency_ms": 60, "memory_mb": 70, "tokens": 0},
                                   "delivery_mode": "wasm", "license": "Apache-2.0", "runtime": "wasi"})

    # (1) APPEND-ONLY: all four are present; adding never removed one.
    checks.append(("append-only: every added implementation is retained (nothing overwritten or deleted)",
                   len(fam["implementations"]) == 4
                   and {i["impl_id"] for i in fam["implementations"]} == {"fast", "lean", "dominated", "wasm_novel"},
                   ""))

    # (2) PARETO: fast (best latency) and lean (best memory) are BOTH on the front — incomparable variants both
    #     survive; `dominated` (worse than fast on both its axes) is NOT on the front but is NOT deleted.
    front = set(pareto_set(fam["implementations"]))
    checks.append(("Pareto non-dominance: incomparable fast + lean both on the front; dominated is off the "
                   "front yet still present in the zoo (never deleted)",
                   {"fast", "lean"} <= front and "dominated" not in front
                   and any(i["impl_id"] == "dominated" for i in fam["implementations"]),
                   f"front={sorted(front)}"))

    # (3) RANK IS A VIEW: weighting memory heavily makes `lean` #1; weighting latency heavily makes `fast` #1 —
    #     SAME zoo, different top; the ranking never mutates the family.
    by_memory = rank(fam, {"memory_mb": 1.0, "latency_ms": 0.0, "tokens": 0.0})
    by_latency = rank(fam, {"latency_ms": 1.0, "memory_mb": 0.0, "tokens": 0.0})
    checks.append(("ranking is a query-time VIEW: memory-weighted -> lean #1; latency-weighted -> fast #1; "
                   "same zoo, no mutation",
                   by_memory["ranking"][0]["impl_id"] == "lean"
                   and by_latency["ranking"][0]["impl_id"] == "fast"
                   and by_memory["n_implementations"] == by_latency["n_implementations"] == 4
                   and len(fam["implementations"]) == 4, ""))

    # (4) NOVELTY PRESERVED: the wasm/Apache/wasi variant is in the diversity archive even though it is
    #     numerically dominated by lean on memory-close axes — an unusual approach is not optimized away.
    archive = set(diversity_archive(fam["implementations"]))
    checks.append(("novelty preservation: the wasm/Apache/wasi variant is kept in the diversity archive "
                   "(distinct delivery/license/runtime), not optimized away",
                   "wasm_novel" in archive, f"archive={sorted(archive)}"))

    # (5) a revoked implementation drops off the PARETO front (lifecycle) but remains in the zoo as history.
    fam2 = add_implementation(fam, {"impl_id": "old", "cost": {"latency_ms": 1, "memory_mb": 1, "tokens": 0},
                                    "delivery_mode": "python_import", "license": "MIT", "runtime": "python",
                                    "lifecycle": "revoked"})
    checks.append(("a revoked implementation is excluded from the serving front but PRESERVED in the zoo as "
                   "history (revoked != deleted)",
                   "old" not in set(pareto_set(fam2["implementations"]))
                   and any(i["impl_id"] == "old" for i in fam2["implementations"]), ""))

    # (6) reuse-first: the corporate pack's cards form real capability families keyed by output_edge, each a
    #     zoo of the primitives that produce that capability.
    from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
    from scripts.primitive_groups_frameworks_and_remixers import build_remixes  # noqa: PLC0415
    cards = build_cards() + build_remixes(build_cards())
    officer_family = new_family("OfficerRowBatch")
    for c in cards:
        if c.get("output_edge") == "OfficerRowBatch":
            officer_family = add_implementation(officer_family, {"impl_id": c["card_id"],
                                                                 "cost": {"latency_ms": 10, "memory_mb": 128, "tokens": 0},
                                                                 "delivery_mode": "python_import", "license": "internal",
                                                                 "runtime": "python", "title": c["title"]})
    checks.append(("real capability family: OfficerRowBatch has a zoo of >=3 producing implementations "
                   "(the aligned officer extractors) — a capability is a family, not one card",
                   len(officer_family["implementations"]) >= 3, f"{len(officer_family['implementations'])} impls"))

    # (7) determinism + candidate-only.
    checks.append(("deterministic ranking + candidate-only everywhere",
                   rank(fam)["ranking"] == rank(fam)["ranking"]
                   and all(i["serves_truth"] is False for i in fam["implementations"]), ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - capability_implementation_zoo: a capability keeps an IMMUTABLE, "
          f"append-only zoo of implementations (review §4) — Pareto non-dominance (incomparable variants both "
          f"survive), ranking is a non-destructive query-time view (different policy → different top, identical "
          f"zoo), novelty preserved in a diversity archive, revoked != deleted. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Capability family with an immutable implementation zoo.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
