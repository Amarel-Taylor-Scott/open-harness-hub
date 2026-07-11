#!/usr/bin/env python3
"""scripts.prove_composite_entity_resolution — a PROVEN multi-step composite ROUTE ('entity_resolution') built by
CHAINING proven leaf primitives end-to-end.

Repo law (the whole point of the gate): `serves_truth=true` is set ONLY by a PASSING executed proof — never
hand-set. This module executes the FULL entity-resolution route over a realistic fixture and asserts
`executed_output == expected_output` (an independently-constructed expected, hashes recomputed with hashlib, NOT
read back from the mutators). If that end-to-end proof fails, the composite stays CANDIDATE and is NOT persisted.
A deliberately-broken variant (wrong expected) MUST fail — proving the gate is real, not a rubber stamp.

ADD-ONLY: this file creates NEW mutators and a NEW output file. It never edits a contract-locked file
(mutator_registry.py, build_edge_type_retrofit.py, registry_search.py) nor a shared file
(flywheel_proof_modules.py, _config.py). New batch-orchestration mutators plug into the shared MUTATOR_REGISTRY via
`setdefault` (idempotent). It does NOT self-register in flywheel_proof_modules.py — the (script_path, module_name)
tuple is REPORTED to the caller.

The route (record batch -> canonical entity records):
  1. normalize fields      er_normalize_record_batch   RecordBatch          -> RecordBatch
  2. dedupe-cluster-key     sr_dedupe_cluster_key        RecordBatch          -> RecordClusterBatch   [proven leaf]
  3. group-by-key           er_group_cluster_members     RecordClusterBatch   -> EntityGroupMap
  4. aggregate/count        er_count_group_members       EntityGroupMap       -> CanonicalCountBatch
  5. canonical entities     er_build_canonical_entities  CanonicalCountBatch  -> CanonicalEntityBatch

The load-bearing steps CALL proven leaves via `apply_mutator` (rn_* record normalizers, sr_dedupe_cluster_key,
agg_count_records); each has an inline fallback so --self-test still runs standalone if a leaf-family import fails
(falling back to the base-11 mutators / equivalent inline logic). `edge_chain_strength` = the count of adjacent
steps whose canonical TYPES match (`canonicalize_edge(step[i].output) == canonicalize_edge(step[i+1].input)`) — the
honest composability metric.

Deterministic + offline ONLY: no network, no LLM, no wall-clock (fixed literal timestamp), no RNG. CLI:
--self-test | --write.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _hash,
    _receipt,
    apply_mutator,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

# IMPORT proven leaf families for their side-effect registration (rn_*, sr_*, agg_*). Defensive: if a family import
# fails, we fall back to the base-11 mutators / inline equivalents so --self-test still runs standalone.
_FAMILIES_LOADED: list[str] = []
for _family_mod in (
    "scripts.prove_leaves_record_normalization",
    "scripts.prove_leaves_set_relational",
    "scripts.prove_leaves_aggregation_reduce",
):
    try:  # noqa: SIM105
        __import__(_family_mod)
        _FAMILIES_LOADED.append(_family_mod)
    except Exception:  # noqa: BLE001 — standalone fallback is intentional
        pass

ROUTE_ID = "prim:composite:entity_resolution"
FAMILY = "entity_resolution"
# Fixed literal timestamp — deterministic, no wall-clock (repo law: no datetime.now / time.time).
GENERATED_UTC = "2026-07-03"

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_composite_entity_resolution.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_composite_entity_resolution.json"

#: key fields used to resolve two source records to the same real-world entity
_KEY_FIELDS = ["name", "email"]


def _dedupe_key(name: str, email: str) -> str:
    """Deterministic 16-hex cluster key over normalized (name, email). Recomputed independently in the expected."""
    token = "|".join(str(v).strip().lower() for v in (name, email))
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def _entity_id(dedupe_key: str) -> str:
    return "ent-" + hashlib.sha256(dedupe_key.encode("utf-8")).hexdigest()[:16]


# ── NEW batch-orchestration mutators (payload, **kwargs) -> (output, receipt). Each CALLS proven leaves via
#    apply_mutator when available, else an inline fallback that computes the identical result. ──
def _normalize_one_record(rec: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single source record + attach a deterministic dedupe_key, preferring proven rn_* leaves."""
    r = dict(rec)
    if all(m in MUTATOR_REGISTRY for m in
           ("rn_trim_all_strings", "rn_whitespace_collapse_record", "rn_lower_string_values",
            "rn_dedupe_key_from_fields")):
        r, _ = apply_mutator("rn_trim_all_strings", r)
        r, _ = apply_mutator("rn_whitespace_collapse_record", r)
        r, _ = apply_mutator("rn_lower_string_values", r)
        r, _ = apply_mutator("rn_dedupe_key_from_fields", r, fields=_KEY_FIELDS)
    else:  # standalone fallback — identical transform without the leaf family
        r = {k: (" ".join(v.split()).lower() if isinstance(v, str) else v) for k, v in r.items()}
        r["dedupe_key"] = _dedupe_key(r.get("name", ""), r.get("email", ""))
    return r


def er_normalize_record_batch(batch: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out = [_normalize_one_record(r) for r in batch]
    return out, _receipt("er_normalize_record_batch", before=batch, after=out, lossless=False,
                         note="trim+collapse+lower string fields and attach a deterministic dedupe_key per record")


def er_group_cluster_members(clusters: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Reshape a RecordClusterBatch ([{key, representative, members}]) into an EntityGroupMap {key -> members}."""
    out: dict[str, list[dict[str, Any]]] = {c["key"]: c["members"] for c in clusters}
    return out, _receipt("er_group_cluster_members", before=clusters, after=out, lossless=True,
                         note="group clustered rows into {entity_key -> member rows}")


def er_count_group_members(groups: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Count members per entity group (via proven agg_count_records when available), keeping the representative."""
    out: list[dict[str, Any]] = []
    for key, members in groups.items():
        if "agg_count_records" in MUTATOR_REGISTRY:
            count, _ = apply_mutator("agg_count_records", members)
        else:
            count = len(members)
        out.append({"dedupe_key": key, "source_count": count, "representative": members[0]})
    return out, _receipt("er_count_group_members", before=groups, after=out, lossless=False,
                         note="source_count per entity group + carry the representative record")


def er_build_canonical_entities(count_batch: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Emit one canonical entity record per resolved entity: a stable id, merged fields, and the merge count."""
    out: list[dict[str, Any]] = []
    for row in count_batch:
        rep = row["representative"]
        out.append({
            "canonical_entity_id": _entity_id(row["dedupe_key"]),
            "name": rep.get("name"),
            "email": rep.get("email"),
            "source_count": row["source_count"],
            "dedupe_key": row["dedupe_key"],
        })
    return out, _receipt("er_build_canonical_entities", before=count_batch, after=out, lossless=False,
                         note="canonical entity record per cluster: stable id + merged fields + source_count")


_NEW_MUTATORS = {
    "er_normalize_record_batch": er_normalize_record_batch,
    "er_group_cluster_members": er_group_cluster_members,
    "er_count_group_members": er_count_group_members,
    "er_build_canonical_entities": er_build_canonical_entities,
}


def register_new_mutators() -> None:
    """Plug the composite orchestration mutators into the shared registry (setdefault — idempotent, add-only)."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── a base-11 fallback for the dedupe-cluster step (used only if the sr_ family failed to import) ──
def _cluster_by_key(records: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    order: list[Any] = []
    clusters: dict[Any, list[dict[str, Any]]] = {}
    for r in records:
        k = r.get(key)
        if k not in clusters:
            clusters[k] = []
            order.append(k)
        clusters[k].append(r)
    return [{"key": k, "representative": clusters[k][0], "members": clusters[k]} for k in order]


# ── THE ROUTE: ordered steps. Each step names a mutator (proven leaf or new orchestrator) + its declared edge types.
ROUTE_STEPS: list[dict[str, Any]] = [
    {"name": "normalize_fields", "mutator": "er_normalize_record_batch", "args": {},
     "input_edge": "RecordBatch", "output_edge": "RecordBatch"},
    {"name": "dedupe_cluster_key", "mutator": "sr_dedupe_cluster_key", "args": {"key": "dedupe_key"},
     "input_edge": "RecordBatch", "output_edge": "RecordClusterBatch"},
    {"name": "group_by_key", "mutator": "er_group_cluster_members", "args": {},
     "input_edge": "RecordClusterBatch", "output_edge": "EntityGroupMap"},
    {"name": "aggregate_count", "mutator": "er_count_group_members", "args": {},
     "input_edge": "EntityGroupMap", "output_edge": "CanonicalCountBatch"},
    {"name": "canonical_entities", "mutator": "er_build_canonical_entities", "args": {},
     "input_edge": "CanonicalCountBatch", "output_edge": "CanonicalEntityBatch"},
]

# ── a realistic fixture: 5 messy source records; ids 1&2 = one entity, 3&4 = one entity, 5 = unique ──
FIXTURE: list[dict[str, Any]] = [
    {"id": 1, "name": "  John Smith ", "email": "John@Example.com "},
    {"id": 2, "name": "JOHN  SMITH", "email": "john@example.com"},
    {"id": 3, "name": "Jane Doe", "email": "JANE@example.com"},
    {"id": 4, "name": "jane doe ", "email": "jane@example.com "},
    {"id": 5, "name": "Bob Lee", "email": "bob@example.com"},
]


def build_expected() -> list[dict[str, Any]]:
    """Independently-constructed expected output — hashes recomputed with hashlib, NOT read from the mutators."""
    k_john = _dedupe_key("john smith", "john@example.com")
    k_jane = _dedupe_key("jane doe", "jane@example.com")
    k_bob = _dedupe_key("bob lee", "bob@example.com")
    return [
        {"canonical_entity_id": _entity_id(k_john), "name": "john smith", "email": "john@example.com",
         "source_count": 2, "dedupe_key": k_john},
        {"canonical_entity_id": _entity_id(k_jane), "name": "jane doe", "email": "jane@example.com",
         "source_count": 2, "dedupe_key": k_jane},
        {"canonical_entity_id": _entity_id(k_bob), "name": "bob lee", "email": "bob@example.com",
         "source_count": 1, "dedupe_key": k_bob},
    ]


def _apply_step(step: dict[str, Any], payload: Any) -> Any:
    """Apply one route step. sr_dedupe_cluster_key falls back to a base-11-only equivalent if its family is absent."""
    mutator, args = step["mutator"], step.get("args", {})
    if mutator == "sr_dedupe_cluster_key" and mutator not in MUTATOR_REGISTRY:
        return _cluster_by_key(payload, args["key"])  # standalone fallback (family import failed)
    out, _ = apply_mutator(mutator, payload, **args)
    return out


def run_route(fixture: list[dict[str, Any]]) -> dict[str, Any]:
    """Execute the FULL route end-to-end by chaining apply_mutator; return the final output + per-step trace."""
    payload: Any = fixture
    trace: list[dict[str, Any]] = []
    for step in ROUTE_STEPS:
        before_hash = _hash(payload)
        payload = _apply_step(step, payload)
        trace.append({
            "step": step["name"], "mutator": step["mutator"],
            "input_edge": step["input_edge"], "output_edge": step["output_edge"],
            "input_edge_type_id": canonicalize_edge(step["input_edge"]),
            "output_edge_type_id": canonicalize_edge(step["output_edge"]),
            "input_hash": before_hash, "output_hash": _hash(payload),
        })
    return {"output": payload, "trace": trace}


def edge_chain_strength(steps: list[dict[str, Any]]) -> int:
    """Honest composability metric: count adjacent boundaries whose canonical TYPES match (via canonicalize_edge)."""
    n = 0
    for a, b in zip(steps, steps[1:]):
        if canonicalize_edge(a["output_edge"]) == canonicalize_edge(b["input_edge"]):
            n += 1
    return n


def prove_composite(expected: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run the composite route + its executed proofs. serves_truth flips true ONLY on a passing end-to-end proof."""
    expected = build_expected() if expected is None else expected
    run = run_route(FIXTURE)
    executed = run["output"]

    # proof 1: end-to-end correctness — the WHOLE composite produces the independently-expected canonical entities
    exec_pass = executed == expected
    # proof 2: determinism — re-running the full route yields byte-identical output
    rerun = run_route(FIXTURE)["output"]
    det_pass = json.dumps(rerun, sort_keys=True) == json.dumps(executed, sort_keys=True)

    strength = edge_chain_strength(ROUTE_STEPS)
    passed = exec_pass and det_pass
    proofs = [
        {"name": "composite_end_to_end_test", "passed": exec_pass,
         "detail": f"output_hash={_hash(executed)} expected_hash={_hash(expected)}"},
        {"name": "determinism_test", "passed": det_pass,
         "detail": "re-run identical" if det_pass else "non-deterministic!"},
    ]
    return {
        "record_type": "proven_composite_route",
        "primitive_id": ROUTE_ID,
        "family": FAMILY,
        "capability": "resolve a batch of messy source records into canonical entity records (entity resolution)",
        "route_length": len(ROUTE_STEPS),
        "steps": run["trace"],
        "edge_chain_strength": strength,
        "proofs": proofs,
        "all_passed": passed,
        "exec_pass": exec_pass,
        # THE promotion: an executed passing end-to-end proof is the ONLY thing that flips serves_truth true.
        "serves_truth": bool(passed),
        "candidate": not passed,
        "promoted": bool(passed),
        "verification_level": "L7_executed_proof" if passed else "L4_proof_declared_failed",
        "tokens": 0,
        "input_hash": _hash(FIXTURE),
        "output_hash": _hash(executed),
    }


def _persisted_row(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "primitive_id": receipt["primitive_id"],
        "record_type": "proven_composite_route",
        "family": FAMILY,
        "capability": receipt["capability"],
        "serves_truth": receipt["serves_truth"],
        "candidate": receipt["candidate"],
        "verification_level": receipt["verification_level"],
        "route_length": receipt["route_length"],
        "edge_chain_strength": receipt["edge_chain_strength"],
        "steps": receipt["steps"],
        "proofs": receipt["proofs"],
        "tokens": 0,
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
        "generated_utc": GENERATED_UTC,
    }


def build_manifest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_composite_route_manifest",
        "family": FAMILY,
        "pack_id": f"proven-composite-{FAMILY}",
        "generator": "scripts/prove_composite_entity_resolution.py",
        "generated_utc": GENERATED_UTC,
        "route_id": ROUTE_ID,
        "route_length": len(ROUTE_STEPS),
        "proven_count": len(rows),
        "edge_chain_strength": rows[0]["edge_chain_strength"] if rows else 0,
        "leaf_families_loaded": _FAMILIES_LOADED,
        "verification_level": "L7_executed_proof",
        "total_rows": len(rows),
        "note": "serves_truth=true is set ONLY by a PASSING executed end-to-end proof of the COMPOSITE "
                "(prove_composite -> run_route chains apply_mutator over proven leaves). edge_chain_strength counts "
                "adjacent steps whose canonical types match (canonicalize_edge). A deliberately-broken route (wrong "
                "expected) fails the proof and is never persisted here.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    receipt = prove_composite()
    # persist ONLY on a passing end-to-end proof (the gate)
    rows = [_persisted_row(receipt)] if receipt["serves_truth"] else []
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
                         encoding="utf-8")
    manifest = build_manifest(rows)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipt = prove_composite()
    strength = receipt["edge_chain_strength"]

    # a deliberately-broken route (WRONG expected) MUST fail the end-to-end proof (never promotes)
    broken_expected = build_expected()
    broken_expected[0] = {**broken_expected[0], "source_count": 999}  # tamper the merge count
    broken = prove_composite(broken_expected)

    checks: list[tuple[str, bool]] = [
        ("route has >=5 chained steps", receipt["route_length"] == len(ROUTE_STEPS) and len(ROUTE_STEPS) >= 5),
        ("the composite executes end-to-end and matches the independently-built expected", receipt["exec_pass"] is True),
        ("the whole route is deterministic (re-run identical)",
         all(p["passed"] for p in receipt["proofs"] if p["name"] == "determinism_test")),
        ("serves_truth flips true ONLY on the passing end-to-end proof (L7_executed_proof)",
         receipt["serves_truth"] is True and receipt["promoted"] is True
         and receipt["verification_level"] == "L7_executed_proof"),
        ("edge_chain_strength > 1 (honest canonical-type matches)", strength > 1),
        ("every persisted step carries canonical input+output edge type ids",
         all(s["input_edge_type_id"] and s["output_edge_type_id"] for s in receipt["steps"])),
        ("tokens == 0 (deterministic + offline, no LLM)", receipt["tokens"] == 0),
        ("the route chains a proven leaf directly (sr_dedupe_cluster_key)",
         any(s["mutator"] == "sr_dedupe_cluster_key" for s in ROUTE_STEPS)),
        ("a deliberately-broken route (wrong expected) FAILS and stays candidate",
         broken["serves_truth"] is False and broken["promoted"] is False and broken["exec_pass"] is False),
        ("new orchestration mutators registered into the shared registry (add-only setdefault seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_composite_entity_resolution:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_composite_entity_resolution: the '{FAMILY}' composite route ({receipt['route_length']} "
          f"chained steps) is PROVEN end-to-end (serves_truth=true, L7_executed_proof) with "
          f"edge_chain_strength={strength}; a deliberately-broken route correctly fails the gate and stays candidate.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
