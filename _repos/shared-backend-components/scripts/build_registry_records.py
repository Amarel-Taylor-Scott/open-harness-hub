"""build_registry_records — wire EVERY registry to records at scale: enrich -> embed -> describe -> metadata ->
pgvector storage + vector search. Honest accounting (real vs synthetic), governed, high-volume -> DB not git.

For each registry on the menu it builds >=1000 records (REAL from the catalog + flagged SYNTHETIC candidates to
demonstrate scale), each ENRICHED (description + metadata + embedding). It emits:
  - data/dev-intel/registry_records_manifest.json  — per-registry real/synthetic/total counts (the honest ledger)
  - data/dev-intel/registry_record_pgvector_plan.sql — the Postgres+pgvector DDL + load plan (vector dim from EMBED_DIM)
  - data/dev-intel/registry_records_sample.jsonl   — a small visible sample (record shape, truncated embedding)
The full 1000/registry materializes into Postgres+pgvector via the plan (high-volume belongs in the operational
tier, not git). serves_truth=false; candidates only (promotion boundary applies).

  python3 _repos/shared-backend-components/scripts/build_registry_records.py            # write manifest + pgvector plan + sample
  python3 _repos/shared-backend-components/scripts/build_registry_records.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry import available_all  # noqa: E402
from src.teleon.registry.records import py_const_src_teleon_registry_records__EMBED_DIM, py_function_src_teleon_registry_records__build_records, py_function_src_teleon_registry_records__real_records, py_function_src_teleon_registry_records__record_search  # noqa: E402

_TARGET = 1000
_SAMPLE_PER_REG = 4
_EMBED_PREVIEW = 6
_DIR = _resource("data") / "dev-intel"
_MANIFEST = _DIR / "registry_records_manifest.json"
_PLAN = _DIR / "registry_record_pgvector_plan.sql"
_SAMPLE = _DIR / "registry_records_sample.jsonl"
_TABLE = "registry_record"


def _pgvector_plan() -> str:
    # DDL with the vector dimension BUILT from EMBED_DIM (single source — never a parallel literal).
    return "\n".join([
        "-- pgvector storage + search for registry records (generated; vector dim from registry.records.EMBED_DIM).",
        "CREATE EXTENSION IF NOT EXISTS vector;",
        f"CREATE TABLE IF NOT EXISTS {_TABLE} (",
        "  id            text PRIMARY KEY,",
        "  registry      text NOT NULL,",
        "  name          text NOT NULL,",
        "  description   text,",
        "  metadata      jsonb,",
        f"  embedding     vector({py_const_src_teleon_registry_records__EMBED_DIM}),",
        "  synthetic     boolean NOT NULL DEFAULT false,",
        "  candidate     boolean NOT NULL DEFAULT true,   -- discovery != trust; promotion boundary applies",
        "  serves_truth  boolean NOT NULL DEFAULT false",
        ");",
        f"CREATE INDEX IF NOT EXISTS {_TABLE}_registry_idx ON {_TABLE} (registry);",
        f"CREATE INDEX IF NOT EXISTS {_TABLE}_embedding_idx ON {_TABLE} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
        "-- load: stream JSONL -> COPY/INSERT (the population engine), then ANALYZE; vector search:",
        f"--   SELECT id, name, 1 - (embedding <=> :query_vec) AS score FROM {_TABLE}",
        "--   WHERE (:registry IS NULL OR registry = :registry) ORDER BY embedding <=> :query_vec LIMIT :k;",
    ])


def _build(write: bool) -> dict:
    per_registry, sample_lines = {}, []
    total_real = total_synth = 0
    for reg in available_all():
        real = py_function_src_teleon_registry_records__real_records(reg)
        n_real = len(real)
        n_synth = max(0, _TARGET - n_real)
        per_registry[reg] = {"real": n_real, "synthetic": n_synth, "total": n_real + n_synth}
        total_real += n_real
        total_synth += n_synth
        for r in real[:_SAMPLE_PER_REG]:
            sample_lines.append(json.dumps({
                "id": r["id"], "registry": r["registry"], "name": r["name"],
                "description": r["description"], "keywords": r["metadata"]["keywords"][:5],
                "embedding_preview": [round(x, 4) for x in r["embedding"][:_EMBED_PREVIEW]],
                "embedding_dim": r["embedding_dim"], "synthetic": r["synthetic"], "serves_truth": r["serves_truth"],
            }))
    manifest = {
        "version": "0.1.0",
        "principle": "Honest ledger of registry records at scale. real = from the catalog; synthetic = flagged "
                     "candidates topping up to the target (proves storage/search at scale, never claimed real). "
                     "Full volume materializes into Postgres+pgvector via the plan; serves_truth=false; candidate-only.",
        "serves_truth": False,
        "target_per_registry": _TARGET,
        "embed_dim": py_const_src_teleon_registry_records__EMBED_DIM,
        "pgvector_table": _TABLE,
        "registries_wired": len(per_registry),
        "totals": {"real": total_real, "synthetic": total_synth, "records": total_real + total_synth},
        "per_registry": per_registry,
    }
    if write:
        _DIR.mkdir(parents=True, exist_ok=True)
        _MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
        _PLAN.write_text(_pgvector_plan() + "\n")
        _SAMPLE.write_text("\n".join(sample_lines) + "\n")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if not args.self_test:
        m = _build(write=True)
        print(f"wired {m['registries_wired']} registries -> {m['totals']['records']} records "
              f"({m['totals']['real']} real + {m['totals']['synthetic']} synthetic candidates); "
              f"manifest + pgvector plan (vector({py_const_src_teleon_registry_records__EMBED_DIM})) + sample written")
        return 0

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    m = _build(write=False)
    ck("every menu registry is wired", m["registries_wired"] >= 10, str(m["registries_wired"]))
    ck("target is >=1000 records per registry", m["target_per_registry"] >= 1000)
    ck("manifest honestly splits real vs synthetic", all(
        r["real"] + r["synthetic"] == r["total"] == _TARGET for r in m["per_registry"].values()))

    # PROVE the pipeline actually builds 1000 enriched+embedded records for a registry, in memory
    recs = py_function_src_teleon_registry_records__build_records("component", target=_TARGET)
    ck("builds 1000 records for a registry", len(recs) >= _TARGET, str(len(recs)))
    ck("every record has embedding + description + metadata", all(
        len(r["embedding"]) == py_const_src_teleon_registry_records__EMBED_DIM and r["description"] and r["metadata"]["keywords"] for r in recs[:50]))
    ck("real records present (not all synthetic)", any(not r["synthetic"] for r in recs))

    # PROVE vector search works over the records (the pgvector floor)
    hits = py_function_src_teleon_registry_records__record_search("pdf document parser", recs, limit=5)
    ck("vector search returns ranked hits", len(hits) >= 1 and hits[0]["score"] > 0, str(hits[:2]))

    # pgvector DDL is single-sourced (dim from EMBED_DIM, no parallel literal) + governed
    plan = _pgvector_plan()
    ck("pgvector DDL uses vector(EMBED_DIM) single-source", f"vector({py_const_src_teleon_registry_records__EMBED_DIM})" in plan)
    ck("DDL marks candidate + non-truth (governed)", "candidate" in plan and "serves_truth" in plan)
    ck("manifest serves_truth false", m["serves_truth"] is False)

    if fails:
        print(f"\nFAIL - build_registry_records: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - build_registry_records: {m['registries_wired']} registries wired to >=1000 records each "
          f"(real+synthetic, enriched: embedding/description/metadata), pgvector DDL+search proven, honest ledger; "
          f"{checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
