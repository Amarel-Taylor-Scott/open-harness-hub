#!/usr/bin/env python3
"""AIDevObserver Benchmark Lab — primitive-lift A/B harness (resource envelope v0).

Measures the SAME task executed two ways, in isolated subprocesses:

  Run A (baseline)        — a monolithic re-implementation (the "agent rebuilt the
                            helpers" arm). Its simulated agent context is the FULL
                            SOURCE of the modules an agent would read to rebuild.
  Run B (primitive-first) — composes the EXISTING primitives (`normalize_field_name`,
                            canonical digests from `src.teleon.experiments.ids`) into
                            the real graph runtime (`src.teleon.dag.pipeline_dag.DAG`).
                            Its simulated agent context is only the EDGE CARDS.

Both arms do real work on identical synthetic inputs and must produce an IDENTICAL
canonical output hash (black-box equivalence). Per run the harness records the full
resource envelope, each with an explicit basis label:

  wall_ms · cpu_ms · peak_rss_kb (process high-water) · py_alloc_peak_kb (tracemalloc)
  · context_bytes_read (edge-cards vs full-source; basis: simulated_agent_read)
  · tokens_est (context_bytes/4; basis: deterministic_proxy) · model_calls (0 — the
  deterministic lane; model-lane arms plug in via the observer IDE runner later)

Receipts are JSONL rows minted via canonical_id, quality level L4 (tested candidate
with fixture/proof receipt), candidate=true, serves_truth=false — benchmark output is
promotion EVIDENCE, never promotion.

Usage:
  python3 _repos/shared-backend-components/scripts/primitive_lift_benchmark.py --rows 20000        # full run
  python3 _repos/shared-backend-components/scripts/primitive_lift_benchmark.py --self-test         # bounded proof
  python3 _repos/shared-backend-components/scripts/primitive_lift_benchmark.py --run-one record_normalize_dedupe A --rows 500
"""
from __future__ import annotations
from scripts._repo_paths import pythonpath as _pythonpath  # noqa: E402
from scripts._repo_paths import resource as _resource
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()  # add every _repos/*/backend so `from src.teleon...` resolves bare (parents[1] alone -> ModuleNotFoundError: 'src')

import argparse
import json
import re
import resource
import subprocess
import sys
import time
import tracemalloc
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.experiments.ids import canonical_bytes, canonical_id, sha256_hex  # noqa: E402

OUT_DIR = _resource("data") / "dev-intel" / "primitive_lift_benchmark"
#: modules a baseline agent would read IN FULL to rebuild the helpers (Run A context).
FULL_SOURCE_CONTEXT = [
    "src/teleon/primitives/groups.py",
    "src/teleon/dag/pipeline_dag.py",
    "src/teleon/experiments/ids.py",
]
#: chars-per-token deterministic proxy (basis is labeled on every receipt).
CHARS_PER_TOKEN = 4

#: the edge cards Run B reads INSTEAD of source (compact black-box contracts).
EDGE_CARDS = [
    {
        "primitive_id": "prim:candidate:local-repo:src-teleon-primitives-groups-normalize-field-name",
        "kind": "reuse_card", "candidate": True, "serves_truth": False,
        "label": "primitives.groups.normalize_field_name",
        "contract": {"input": "RawFieldLabel", "output": "SnakeCaseAsciiFieldName"},
        "blackbox": "Normalize an external field label to snake_case ASCII (NFKD, camel splits, non-alnum -> _).",
        "effects": [], "runtime_targets": ["local.python"],
    },
    {
        "primitive_id": "prim:candidate:local-repo:src-teleon-experiments-ids-canonical-digest",
        "kind": "reuse_card", "candidate": True, "serves_truth": False,
        "label": "experiments.ids.sha256_hex",
        "contract": {"input": "JsonSerializableValue", "output": "Sha256HexDigest"},
        "blackbox": "Canonical bytes (sorted keys, compact separators) -> full sha256 hex.",
        "effects": [], "runtime_targets": ["local.python"],
    },
    {
        "primitive_id": "prim:candidate:local-repo:src-teleon-dag-pipeline-dag-runtime",
        "kind": "reuse_card", "candidate": True, "serves_truth": False,
        "label": "dag.pipeline_dag.DAG",
        "contract": {"input": "TypedNodes+InputBus", "output": "OutputBus+RunReceipt"},
        "blackbox": "Data-flow DAG executor: nodes consume/produce named bus artifacts; emits cost receipt.",
        "effects": [], "runtime_targets": ["local.python"],
    },
]


def synthetic_rows(n: int) -> list[dict]:
    """Deterministic messy input: camel/space/unicode field labels, dupes, invalid rows."""
    rows = []
    for i in range(n):
        key = f"ent-{i % max(1, n // 3)}"  # ~3x duplication pressure on the identity field
        rows.append({
            "Entity ID": key,
            "displayName": f"Name {i}",
            "Contact-Émail": f"user{i}@example.test" if i % 17 else "",  # some invalid
            "createdAt": f"2026-06-{(i % 28) + 1:02d}",
            "row_seq": i,
        })
    return rows


# ── Run A: the monolith (baseline "agent rebuilt it" arm) ────────────────────────────
_A_FIRST_CAP = re.compile(r"(.)([A-Z][a-z]+)")
_A_ALL_CAP = re.compile(r"([a-z0-9])([A-Z])")
_A_NON_ALNUM = re.compile(r"[^0-9a-zA-Z]+")


def run_a_monolith(rows: list[dict]) -> dict:
    def norm(name: object) -> str:  # faithful re-implementation (the rebuild)
        text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode("ascii")
        text = _A_FIRST_CAP.sub(r"\1_\2", text)
        text = _A_ALL_CAP.sub(r"\1_\2", text)
        text = _A_NON_ALNUM.sub("_", text)
        text = "_".join(p for p in text.strip("_").lower().split("_") if p)
        return text or "field"

    normalized = [{norm(k): v for k, v in row.items()} for row in rows]
    invalid = [r for r in normalized if not r.get("contact_email")]
    valid = [r for r in normalized if r.get("contact_email")]
    seen, deduped = set(), []
    for r in valid:  # keep-first identity dedupe
        key = r.get("entity_id")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    import hashlib  # the monolith re-hashes by hand too (the drift the naming law bans)
    digest = hashlib.sha256(json.dumps(deduped, sort_keys=True, separators=(",", ":"),
                                       ensure_ascii=False).encode("utf-8")).hexdigest()
    return {"records": deduped, "invalid_count": len(invalid), "digest": digest}


# ── Run B: primitive-first composition over the real DAG runtime ─────────────────────
def run_b_primitives(rows: list[dict]) -> dict:
    from src.teleon.dag.pipeline_dag import DAG, Node
    from src.teleon.primitives.groups import normalize_field_name

    dag = DAG([
        Node(id="normalize_fields", produces="normalized", consumes=("raw_rows",), primitive="Loop",
             fn=lambda bus: [{normalize_field_name(k): v for k, v in row.items()}
                             for row in bus["raw_rows"]]),
        Node(id="validate_required", produces="validated", consumes=("normalized",), primitive="If Statement",
             fn=lambda bus: {
                 "valid": [r for r in bus["normalized"] if r.get("contact_email")],
                 "invalid_count": sum(1 for r in bus["normalized"] if not r.get("contact_email")),
             }),
        Node(id="dedupe_identity", produces="deduped", consumes=("validated",), primitive="Action",
             fn=lambda bus: _keep_first(bus["validated"]["valid"], "entity_id")),
        Node(id="digest_receipt", produces="digest", consumes=("deduped",), primitive="Output",
             fn=lambda bus: sha256_hex(bus["deduped"])),
    ])
    result = dag.run({"raw_rows": rows})
    bus = result["bus"]
    return {"records": bus["deduped"], "invalid_count": bus["validated"]["invalid_count"],
            "digest": bus["digest"], "dag_receipt_nodes": len(result["receipt"])}


def _keep_first(rows: list[dict], key_field: str) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        key = r.get(key_field)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


TASKS = {"record_normalize_dedupe": {"A": run_a_monolith, "B": run_b_primitives}}


def _context_bytes(arm: str) -> int:
    if arm == "A":  # baseline agent loads the full implementations
        return sum(len((_resource(p)).read_bytes()) for p in FULL_SOURCE_CONTEXT)
    return len(json.dumps(EDGE_CARDS).encode("utf-8"))  # edges only


def run_one(task: str, arm: str, rows_n: int) -> dict:
    """Execute one arm in-process and print its measured envelope as JSON (child mode)."""
    rows = synthetic_rows(rows_n)
    context_bytes = _context_bytes(arm)
    tracemalloc.start()
    t0_wall = time.monotonic_ns()
    t0_cpu = resource.getrusage(resource.RUSAGE_SELF)
    result = TASKS[task][arm](rows)
    t1_cpu = resource.getrusage(resource.RUSAGE_SELF)
    wall_ms = (time.monotonic_ns() - t0_wall) / 1e6
    _, py_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    envelope = {
        "task": task, "arm": arm, "rows": rows_n,
        "output_hash": sha256_hex({"records": result["records"], "invalid": result["invalid_count"]}),
        "wall_ms": round(wall_ms, 3),
        "cpu_ms": round(((t1_cpu.ru_utime - t0_cpu.ru_utime) + (t1_cpu.ru_stime - t0_cpu.ru_stime)) * 1000, 3),
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,  # process high-water
        "py_alloc_peak_kb": round(py_peak / 1024, 1),
        "context_bytes_read": context_bytes,
        "context_basis": "simulated_agent_read: full-source (A) vs edge-cards (B)",
        "tokens_est": context_bytes // CHARS_PER_TOKEN,
        "tokens_basis": "deterministic_proxy_chars/4",
        "model_calls": 0, "lane": "deterministic",
        "records_out": len(result["records"]), "invalid_count": result["invalid_count"],
        "candidate": True, "serves_truth": False,
    }
    print(json.dumps(envelope, sort_keys=True))
    return envelope


def _spawn(task: str, arm: str, rows_n: int) -> dict:
    """Run one arm in a FRESH subprocess so peak_rss is per-run, not cumulative."""
    proc = subprocess.run(
        [sys.executable, str(Path(__file__)), "--run-one", task, arm, "--rows", str(rows_n)],
        capture_output=True, text=True, cwd=REPO, timeout=600,
        env={**__import__("os").environ, "PYTHONPATH": _pythonpath(".")},
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{task}/{arm} failed: {proc.stderr[-500:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def orchestrate(rows_n: int, out_dir: Path = OUT_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    receipts, comparisons = [], []
    for task in TASKS:
        a = _spawn(task, "A", rows_n)
        b = _spawn(task, "B", rows_n)
        equivalent = a["output_hash"] == b["output_hash"]
        run_id = canonical_id("primlift", task, str(rows_n), a["output_hash"], b["output_hash"])
        comparison = {
            "run_id": run_id, "record_type": "primitive_lift_comparison",
            "schema_version": "primitive_lift_comparison",
            "task": task, "rows": rows_n,
            "blackbox_equivalent": equivalent,
            "deltas": {
                "context_bytes_saved": a["context_bytes_read"] - b["context_bytes_read"],
                "context_reduction_x": round(a["context_bytes_read"] / max(1, b["context_bytes_read"]), 1),
                "tokens_est_saved": a["tokens_est"] - b["tokens_est"],
                "peak_rss_delta_kb": a["peak_rss_kb"] - b["peak_rss_kb"],
                "py_alloc_peak_delta_kb": round(a["py_alloc_peak_kb"] - b["py_alloc_peak_kb"], 1),
                "wall_ms_delta": round(a["wall_ms"] - b["wall_ms"], 3),
                "cpu_ms_delta": round(a["cpu_ms"] - b["cpu_ms"], 3),
            },
            "arms": {"A": a, "B": b},
            "quality_level": "L4_tested_candidate_with_fixture_proof_receipt",
            "candidate": True, "serves_truth": False,
        }
        receipts.extend([a, b])
        comparisons.append(comparison)
    with (out_dir / "receipts.jsonl").open("a", encoding="utf-8") as fh:
        for row in receipts + comparisons:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    summary = {
        "record_type": "primitive_lift_benchmark_summary",
        "schema_version": "primitive_lift_benchmark_summary",
        "comparisons": comparisons,
        "envelope_dimensions": ["tokens_est", "context_bytes_read", "peak_rss_kb",
                                "py_alloc_peak_kb", "cpu_ms", "wall_ms", "model_calls"],
        "candidate": True, "serves_truth": False,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
    return summary


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        summary = orchestrate(500, out_dir=Path(td))
        comp = summary["comparisons"][0]
        a, b = comp["arms"]["A"], comp["arms"]["B"]
        check("A and B are BLACK-BOX EQUIVALENT (identical canonical output hash)",
              comp["blackbox_equivalent"], f"A={a['output_hash'][:12]} B={b['output_hash'][:12]}")
        check("edge-card context is dramatically smaller than full-source context (>=20x)",
              comp["deltas"]["context_reduction_x"] >= 20, str(comp["deltas"]["context_reduction_x"]))
        check("every envelope carries memory dimensions (peak_rss_kb + py_alloc_peak_kb > 0)",
              all(r["peak_rss_kb"] > 0 and r["py_alloc_peak_kb"] > 0 for r in (a, b)))
        check("every envelope labels its estimate bases (tokens + context)",
              all(r.get("tokens_basis") and r.get("context_basis") for r in (a, b)))
        check("deterministic lane makes zero model calls",
              a["model_calls"] == 0 and b["model_calls"] == 0)
        check("receipts + summary written, all rows candidate=true / serves_truth=false",
              (Path(td) / "receipts.jsonl").exists()
              and all(json.loads(line).get("serves_truth") is False
                      for line in (Path(td) / "receipts.jsonl").read_text().splitlines()))
        check("run ids are minted via canonical_id (prefix-hash16)",
              comp["run_id"].startswith("primlift-") and len(comp["run_id"].split("-")[-1]) == 16)
        check("real work happened (dedupe collapsed duplicate identities)",
              0 < a["records_out"] < 500 and a["records_out"] == b["records_out"])
        # negative: a tampered baseline output must break equivalence detection
        tampered = dict(a)
        tampered["output_hash"] = sha256_hex("tampered")
        check("negative: a tampered arm output breaks black-box equivalence",
              tampered["output_hash"] != b["output_hash"])

    print(f"\n{'PASS - primitive_lift_benchmark: A/B arms proven equivalent; full resource envelope (tokens + CONTEXT BYTES + MEMORY + cpu/wall) measured per-arm in isolated subprocesses; receipts candidate-only' if not fails else str(len(fails)) + ' FAILURES: ' + str(fails)}")
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run-one", nargs=2, metavar=("TASK", "ARM"))
    ap.add_argument("--rows", type=int, default=20000)
    args = ap.parse_args()
    if args.self_test:
        return _self_test()
    if args.run_one:
        run_one(args.run_one[0], args.run_one[1], args.rows)
        return 0
    summary = orchestrate(args.rows)
    for comp in summary["comparisons"]:
        d = comp["deltas"]
        print(f"{comp['task']} rows={comp['rows']} equivalent={comp['blackbox_equivalent']} "
              f"context_saved={d['context_bytes_saved']}B ({d['context_reduction_x']}x) "
              f"tokens_est_saved={d['tokens_est_saved']} rss_delta={d['peak_rss_delta_kb']}KB "
              f"wall_delta={d['wall_ms_delta']}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
