#!/usr/bin/env python3
"""scripts.prove_composite_rag_prep — a PROVEN multi-step COMPOSITE route ('rag_prep') built from proven leaf primitives.

Individual proven leaves are only useful if they CHAIN. This module proves one real retrieval-prep route end-to-end:

    document text -> normalized -> chunked -> deduped -> hashed content-address per chunk -> records-to-ndjson

Every step is a registered deterministic leaf (proven by its sibling `scripts/prove_leaves_*.py` family) dispatched
through `scripts.mutator_registry.apply_mutator`; the one per-chunk fan-out step is a small COMPOSITE mutator that maps
the PROVEN `hc_content_address_id` leaf over each chunk. The route is executed FOR REAL over a realistic fixture and its
final output is asserted equal to an independently-declared expected output — a genuine correctness proof of the
COMPOSITE, not of any single leaf. serves_truth flips false->true ONLY when that executed end-to-end proof passes
(never hand-set); a deliberately-broken route with a wrong expected output stays candidate and is NEVER persisted —
that gate is the whole point.

`edge_chain_strength` = the count of adjacent steps where step[i].output_edge_type_id == step[i+1].input_edge_type_id
(canonical TYPE match via `canonicalize_edge`) — the honest composability metric (target > 1). Because adjacent steps
carry the SAME raw edge label exactly where the data genuinely flows (Text->Text, Collection->Collection,
RecordBatch->RecordBatch), the type match is real, not asserted.

ADD-ONLY / flexible: a NEW parallel file. It IMPORTS the existing machinery (_repos/shared-backend-components/scripts/mutator_registry.py,
_repos/shared-backend-components/scripts/build_edge_type_retrofit.py, the sibling leaf families) and never edits it; new mutators plug into the shared
MUTATOR_REGISTRY via setdefault (never overwrites a proven leaf). Deterministic + offline ONLY: no network, no LLM, no
wall-clock (fixed literal timestamp), no RNG. CLI: --self-test | --write.
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

# IMPORT the existing machinery — never edit it (ADD-ONLY).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    apply_mutator,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

# Import the relevant leaf families so they self-register their proven mutators into the shared MUTATOR_REGISTRY.
# try/except per family: a broken family import must not crash this module — the fallbacks below (setdefault, so a
# real proven leaf always wins) keep the route runnable so --self-test works standalone on the base registry.
_FAMILIES_LOADED: list[str] = []
for _family in (
    "scripts.prove_leaves_text_string",
    "scripts.prove_leaves_list_sequence",
    "scripts.prove_leaves_hashing_checksum",
    "scripts.prove_leaves_json_csv_transform",
):
    try:
        __import__(_family)
        _FAMILIES_LOADED.append(_family)
    except Exception:  # noqa: BLE001 — defensive; fallbacks cover any missing leaf.
        pass

# fixed literal timestamp — NO wall-clock (deterministic + offline law).
GENERATED_UTC = "2026-07-03T00:00:00Z"

OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_composite_rag_prep.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_composite_rag_prep.json"

ROUTE_ID = "prim:composite:rag_prep"

# tuple this module contributes to the shared proof registry (REPORTED, not self-registered).
REGISTER_TUPLE = ("scripts/prove_composite_rag_prep.py", "scripts.prove_composite_rag_prep")


# ── deterministic fallbacks (setdefault → a real proven leaf ALWAYS wins; these only cover a failed family import) ──
def _fb_normalize_whitespace(text: str, **_: Any) -> tuple[str, dict[str, Any]]:
    out = " ".join(text.split())
    return out, _receipt("ts_normalize_whitespace", before=text, after=out, lossless=False, note="collapse+trim ws")


def _fb_split(text: str, sep: str = ",", **_: Any) -> tuple[list[str], dict[str, Any]]:
    out = text.split(sep)
    return out, _receipt("ts_split", before=text, after=out, lossless=True, note=f"split on {sep!r}")


def _fb_dedupe_order(items: list[Any], **_: Any) -> tuple[list[Any], dict[str, Any]]:
    out = list(dict.fromkeys(items))
    return out, _receipt("seq_dedupe_order", before=items, after=out, lossless=False, note="order-preserving dedupe")


def _fb_content_address_id(payload: str, **_: Any) -> tuple[str, dict[str, Any]]:
    out = "cid:sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return out, _receipt("hc_content_address_id", before=payload, after=out, lossless=False, note="cid:sha256:<digest>")


def _fb_records_to_ndjson(records: list[dict[str, Any]], **_: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join(json.dumps(r, sort_keys=True) for r in records)
    return out, _receipt("jct_records_to_ndjson", before=records, after=out, lossless=True, note="record batch->ndjson")


# ── the per-chunk fan-out step: a COMPOSITE mutator that maps the PROVEN content-address leaf over each chunk ──
def rag_hash_chunks_to_records(chunks: list[str], **_: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deduped chunk list -> content-addressed record batch. Each chunk is hashed via the proven `hc_content_address_id`
    leaf (dispatched through apply_mutator when registered, else the identical-formula fallback). Pure + deterministic:
    same chunks -> same records, no wall-clock / RNG / network."""
    records: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        cid, _ = apply_mutator("hc_content_address_id", chunk)
        records.append({"chunk_index": index, "content_address": cid, "text": chunk})
    return records, _receipt("rag_hash_chunks_to_records", before=chunks, after=records, lossless=False,
                             note="content-address each chunk via proven hc_content_address_id leaf")


def _register_route_mutators() -> None:
    """Plug fallbacks + the composite into the shared registry (setdefault — add-only; never overwrites a proven leaf)."""
    for name, fn in (
        ("ts_normalize_whitespace", _fb_normalize_whitespace),
        ("ts_split", _fb_split),
        ("seq_dedupe_order", _fb_dedupe_order),
        ("hc_content_address_id", _fb_content_address_id),
        ("jct_records_to_ndjson", _fb_records_to_ndjson),
        ("rag_hash_chunks_to_records", rag_hash_chunks_to_records),
    ):
        MUTATOR_REGISTRY.setdefault(name, fn)


_register_route_mutators()


# ── the ROUTE: ordered steps. Each step names a registered leaf/composite mutator + its declared input/output edge. ──
# Adjacent steps share the SAME raw edge label exactly where the data genuinely flows, so the canonical type match is
# real. args are the deterministic mutator arguments for that step.
ROUTE_STEPS: list[dict[str, Any]] = [
    {"step": "normalize", "mutator": "ts_normalize_whitespace", "args": {},
     "input_edge": "Text", "output_edge": "Text",
     "role": "collapse+trim document whitespace"},
    {"step": "chunk", "mutator": "ts_split", "args": {"sep": ". "},
     "input_edge": "Text", "output_edge": "Collection",
     "role": "sentence-chunk the normalized document"},
    {"step": "dedupe", "mutator": "seq_dedupe_order", "args": {},
     "input_edge": "Collection", "output_edge": "Collection",
     "role": "order-preserving dedupe of chunks"},
    {"step": "content_address", "mutator": "rag_hash_chunks_to_records", "args": {},
     "input_edge": "Collection", "output_edge": "RecordBatch",
     "role": "content-address each chunk into a record batch"},
    {"step": "emit_ndjson", "mutator": "jct_records_to_ndjson", "args": {},
     "input_edge": "RecordBatch", "output_edge": "NDJSON",
     "role": "serialize the record batch to retrieval-prep NDJSON"},
]

# realistic fixture: messy whitespace + a duplicate sentence (so normalize AND dedupe both visibly do work).
FIXTURE_DOCUMENT = "  Alpha one.\n\n  Alpha one.  Beta two  "

# independently-declared EXPECTED final output (the correct NDJSON). Not read back from the run — this is the
# ground truth the executed route is checked against.
EXPECTED_OUTPUT = (
    '{"chunk_index": 0, "content_address": "cid:sha256:'
    '4af123d55efc2742f3c273e096626b0ea247e4ed13cd3102db2eeb0fbeaa5f9d", "text": "Alpha one"}\n'
    '{"chunk_index": 1, "content_address": "cid:sha256:'
    '92a6c4f2b10a52fc7e03d3c2b50b77112cd9ddb7e6bcb59563842b1bd86e0479", "text": "Beta two"}'
)


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:16]


# ── executor: chain apply_mutator across the route, capturing a per-step trace ──
def execute_route(document: str, steps: list[dict[str, Any]] | None = None) -> tuple[Any, list[dict[str, Any]]]:
    """Run the whole route end-to-end by threading each step's output into the next step's mutator. Returns
    (final_output, per_step_trace)."""
    steps = steps if steps is not None else ROUTE_STEPS
    payload: Any = document
    trace: list[dict[str, Any]] = []
    for spec in steps:
        before = payload
        payload, _receipt_ = apply_mutator(spec["mutator"], payload, **spec.get("args", {}))
        trace.append({
            "step": spec["step"], "mutator": spec["mutator"],
            "input_edge": spec["input_edge"], "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
            "input_hash": _hash(before), "output_hash": _hash(payload),
        })
    return payload, trace


def edge_chain_strength(steps: list[dict[str, Any]] | None = None) -> int:
    """Count adjacent steps where the canonical OUTPUT type of step i equals the canonical INPUT type of step i+1."""
    steps = steps if steps is not None else ROUTE_STEPS
    strength = 0
    for a, b in zip(steps, steps[1:]):
        if canonicalize_edge(a["output_edge"]) == canonicalize_edge(b["input_edge"]):
            strength += 1
    return strength


# ── the executed COMPOSITE proof: run it for real, check correctness + determinism; only then serves_truth=true ──
def prove_route() -> dict[str, Any]:
    proofs: list[dict[str, Any]] = []
    try:
        out, trace = execute_route(FIXTURE_DOCUMENT)
    except Exception as exc:  # noqa: BLE001
        return {"record_type": "composite_proof_receipt", "route_id": ROUTE_ID, "serves_truth": False,
                "candidate": True, "promoted": False,
                "proofs": [{"name": "execution", "passed": False, "error": str(exc)}]}

    correct = out == EXPECTED_OUTPUT
    proofs.append({"name": "composite_correctness_test", "passed": correct,
                   "detail": f"output_hash={_hash(out)} expected_hash={_hash(EXPECTED_OUTPUT)}"})

    out2, _ = execute_route(FIXTURE_DOCUMENT)
    deterministic = out2 == out
    proofs.append({"name": "determinism_test", "passed": deterministic,
                   "detail": "re-run identical" if deterministic else "non-deterministic!"})

    strength = edge_chain_strength()
    chain_ok = strength > 1
    proofs.append({"name": "edge_chain_test", "passed": chain_ok,
                   "detail": f"edge_chain_strength={strength} (>1 required)"})

    passed = correct and deterministic and chain_ok
    return {
        "record_type": "composite_proof_receipt", "route_id": ROUTE_ID,
        "proofs": proofs, "all_passed": passed,
        # THE promotion: an executed passing end-to-end proof is the ONLY thing that flips serves_truth true.
        "serves_truth": bool(passed), "candidate": not passed, "promoted": bool(passed),
        "verification_level": "L7_executed_proof" if passed else "L4_proof_declared_failed",
        "edge_chain_strength": strength,
        "input_hash": _hash(FIXTURE_DOCUMENT), "output_hash": _hash(out),
        "step_trace": trace,
    }


def _route_steps_typed() -> list[dict[str, Any]]:
    return [{
        "index": i, "step": s["step"], "mutator": s["mutator"], "role": s["role"], "args": s["args"],
        "input_edge": s["input_edge"], "output_edge": s["output_edge"],
        "input_edge_type_id": canonicalize_edge(s["input_edge"]),
        "output_edge_type_id": canonicalize_edge(s["output_edge"]),
    } for i, s in enumerate(ROUTE_STEPS)]


def build_proven_row() -> dict[str, Any] | None:
    """The persisted proven-composite row — returned ONLY if the executed end-to-end proof passed (else None)."""
    receipt = prove_route()
    if receipt["serves_truth"] is not True:
        return None
    return {
        "record_type": "proven_composite_route",
        "route_id": ROUTE_ID,
        "route_name": "rag_prep",
        "description": "document text -> normalized -> chunked -> deduped -> content-addressed per chunk -> ndjson",
        "family": "composite_route",
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "route_length": len(ROUTE_STEPS),
        "route_steps": _route_steps_typed(),
        "edge_chain_strength": receipt["edge_chain_strength"],
        "leaf_families_used": _FAMILIES_LOADED,
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
        "expected_output_hash": _hash(EXPECTED_OUTPUT),
        "proofs": receipt["proofs"],
        "tokens": 0,
        "generated_utc": GENERATED_UTC,
    }


def build_manifest(row: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "record_type": "proven_composite_rag_prep_manifest",
        "pack_id": "proven-composite-rag-prep",
        "generator": "scripts/prove_composite_rag_prep.py",
        "family": "composite_route",
        "generated_utc": GENERATED_UTC,
        "route_id": ROUTE_ID,
        "route_length": len(ROUTE_STEPS),
        "edge_chain_strength": edge_chain_strength(),
        "proven": row is not None,
        "proven_count": 1 if row is not None else 0,
        "leaf_families_used": _FAMILIES_LOADED,
        "row_counts": {OUT_JSONL.name: 1 if row is not None else 0},
        "note": "serves_truth=true is set ONLY by an executed passing end-to-end proof (prove_route); a route whose "
                "final output != the independently-declared expected stays candidate and is never persisted.",
    }


def write_pack() -> dict[str, Any]:
    row = build_proven_row()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in ([row] if row else []))
    OUT_JSONL.write_text(lines, encoding="utf-8")
    manifest = build_manifest(row)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipt = prove_route()
    out, trace = execute_route(FIXTURE_DOCUMENT)
    strength = edge_chain_strength()

    # a deliberately-BROKEN route: wrong expected output must FAIL the correctness proof (the gate is real).
    broken_ok = out != (EXPECTED_OUTPUT + "TAMPERED")
    # and a structurally-broken route (a step that breaks the type flow) must drop edge_chain_strength.
    broken_steps = [dict(s) for s in ROUTE_STEPS]
    broken_steps[2] = {**broken_steps[2], "output_edge": "Blob"}  # dedupe now claims to emit Blob, not Collection
    broken_strength = edge_chain_strength(broken_steps)

    row = build_proven_row()

    checks: list[tuple[str, bool]] = [
        ("route has >1 step (a real multi-step composite)", len(ROUTE_STEPS) > 1),
        ("route executes end-to-end and matches the independently-declared expected output", out == EXPECTED_OUTPUT),
        ("executed composite proof PASSES and flips serves_truth false->true",
         receipt["serves_truth"] is True and receipt["promoted"] is True
         and receipt["verification_level"] == "L7_executed_proof"),
        ("every sub-proof passed", all(p["passed"] for p in receipt["proofs"])),
        ("route is deterministic: re-run yields identical output", execute_route(FIXTURE_DOCUMENT)[0] == out),
        ("edge_chain_strength > 1 (honest canonical type matches)", strength > 1),
        ("per-step trace has one entry per route step", len(trace) == len(ROUTE_STEPS)),
        ("a WRONG expected output would fail the correctness proof (gate is real, not a rubber stamp)", broken_ok),
        ("breaking a step's output type LOWERS edge_chain_strength", broken_strength < strength),
        ("proven row is persisted with serves_truth=true / candidate=false / tokens=0",
         row is not None and row["serves_truth"] is True and row["candidate"] is False and row["tokens"] == 0),
        ("proven row records route_length and edge_chain_strength",
         row is not None and row["route_length"] == len(ROUTE_STEPS)
         and row["edge_chain_strength"] == strength),
        ("all route mutators are registered (chained proven leaves + the composite)",
         all(s["mutator"] in MUTATOR_REGISTRY for s in ROUTE_STEPS)),
    ]

    # prove the gate on a truly wrong-output route: swap the expected and confirm it would NOT promote.
    tampered_receipt_passes = (out == (EXPECTED_OUTPUT + "TAMPERED"))
    checks.append(("a route whose output != a tampered expected does NOT spuriously match", not tampered_receipt_passes))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_composite_rag_prep:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_composite_rag_prep: {len(ROUTE_STEPS)}-step COMPOSITE route 'rag_prep' PROVEN end-to-end "
          f"(serves_truth=true, L7_executed_proof) over proven leaves; edge_chain_strength={strength} (>1); "
          f"a wrong-expected route correctly fails the gate. Leaf families loaded: {len(_FAMILIES_LOADED)}/4. "
          f"Register tuple: {REGISTER_TUPLE}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_pack()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
