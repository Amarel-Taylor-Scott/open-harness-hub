"""registry.records — the SCALE record pipeline: every registry -> enriched, embedded, pgvector-ready records.

Builds a uniform RECORD for every registry (id, registry, name, description, metadata, embedding):
  - REAL records from the catalog where available (the menu registries);
  - SYNTHETIC CANDIDATE records (clearly flagged synthetic=true) to demonstrate the storage / embedding /
    vector-search at scale (>=1000/registry) WITHOUT fabricating data as real.

Governed (repo law): candidate-only, synthetic flagged, serves_truth=false; the promotion boundary separates
these STAGED candidates from committed/active rows. High-volume rows belong in Postgres+pgvector (the operational
tier of storage_tier_policy), NOT in git — so the materialization is a load plan + DDL, run when the DB is
provisioned. Vector search runs deterministic cosine here (the pgvector floor); pgvector serves it at scale.
"""
from __future__ import annotations

import math

from .enrich import py_var_src_teleon_registry_enrich___EMBED_DIM, py_function_src_teleon_registry_enrich__embedding, py_function_src_teleon_registry_enrich__enrich_record
from .port import py_function_src_teleon_registry_port__all_catalogs, py_function_src_teleon_registry_port__catalog

py_const_src_teleon_registry_records__EMBED_DIM = py_var_src_teleon_registry_enrich___EMBED_DIM
py_var_src_teleon_registry_records___SYNTH_DOMAINS = ("us", "eu", "global", "enterprise", "regional", "local", "federal", "open", "managed", "hosted")


def py_function_src_teleon_registry_records___to_record(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__registry: str, py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__raw: dict, *, synthetic: bool = False) -> dict:
    py_local_src_teleon_registry_records__to_record__e = py_function_src_teleon_registry_enrich__enrich_record(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__raw)["_enrichment"]
    py_local_src_teleon_registry_records__to_record__rid = py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__raw.get("id") or py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__raw.get("canonical") or py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__raw.get("name") or "record"
    return {
        "id": f"{py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__registry}:{py_local_src_teleon_registry_records__to_record__rid}", "registry": py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__registry,
        "name": py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__raw.get("name") or py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__raw.get("id") or py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__to_record__raw.get("canonical") or str(py_local_src_teleon_registry_records__to_record__rid),
        "description": py_local_src_teleon_registry_records__to_record__e["description"], "long_description": py_local_src_teleon_registry_records__to_record__e["long_description"],
        "metadata": {"keywords": py_local_src_teleon_registry_records__to_record__e["keywords"], "labels": py_local_src_teleon_registry_records__to_record__e["labels"], "use_cases": py_local_src_teleon_registry_records__to_record__e["use_cases"]},
        "embedding": py_local_src_teleon_registry_records__to_record__e["embedding"], "embedding_dim": py_const_src_teleon_registry_records__EMBED_DIM,
        "synthetic": synthetic, "candidate": True, "serves_truth": False,
    }


def py_function_src_teleon_registry_records__real_records(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__real_records__registry: str) -> list[dict]:
    """REAL records from the catalog (any curated OR auto-discovered catalog)."""
    if py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__real_records__registry not in py_function_src_teleon_registry_port__all_catalogs():
        return []
    return [py_function_src_teleon_registry_records___to_record(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__real_records__registry, r) for r in py_function_src_teleon_registry_port__catalog(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__real_records__registry).list()]


def py_function_src_teleon_registry_records__synthetic_records(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__synthetic_records__registry: str, py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__synthetic_records__n: int) -> list[dict]:
    """n templated CANDIDATE records (flagged synthetic) — proves storage/search at scale, never claimed as real."""
    py_local_src_teleon_registry_records__synthetic_records__out = []
    for py_local_src_teleon_registry_records__synthetic_records__i in range(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__synthetic_records__n):
        py_local_src_teleon_registry_records__synthetic_records__dom = py_var_src_teleon_registry_records___SYNTH_DOMAINS[py_local_src_teleon_registry_records__synthetic_records__i % len(py_var_src_teleon_registry_records___SYNTH_DOMAINS)]
        py_local_src_teleon_registry_records__synthetic_records__raw = {"id": f"{py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__synthetic_records__registry}_cand_{py_local_src_teleon_registry_records__synthetic_records__i:05d}", "name": f"{py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__synthetic_records__registry} {py_local_src_teleon_registry_records__synthetic_records__dom} candidate {py_local_src_teleon_registry_records__synthetic_records__i}",
               "domain": py_local_src_teleon_registry_records__synthetic_records__dom, "kind": py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__synthetic_records__registry, "note": f"synthetic {py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__synthetic_records__registry} record #{py_local_src_teleon_registry_records__synthetic_records__i} for scale-out"}
        py_local_src_teleon_registry_records__synthetic_records__out.append(py_function_src_teleon_registry_records___to_record(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__synthetic_records__registry, py_local_src_teleon_registry_records__synthetic_records__raw, synthetic=True))
    return py_local_src_teleon_registry_records__synthetic_records__out


def py_function_src_teleon_registry_records__build_records(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__build_records__registry: str, *, target: int = 1000) -> list[dict]:
    """Real records first, topped up with flagged synthetic candidates to reach `target` (>=1000/registry)."""
    py_local_src_teleon_registry_records__build_records__real = py_function_src_teleon_registry_records__real_records(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__build_records__registry)
    return py_local_src_teleon_registry_records__build_records__real + py_function_src_teleon_registry_records__synthetic_records(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__build_records__registry, max(0, target - len(py_local_src_teleon_registry_records__build_records__real)))


def py_function_src_teleon_registry_records___cosine(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__cosine__a: list[float], py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__cosine__b: list[float]) -> float:
    py_local_src_teleon_registry_records__cosine__dot = sum(x * y for x, y in zip(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__cosine__a, py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__cosine__b))
    py_local_src_teleon_registry_records__cosine__na = math.sqrt(sum(x * x for x in py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__cosine__a))
    py_local_src_teleon_registry_records__cosine__nb = math.sqrt(sum(y * y for y in py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__cosine__b))
    return py_local_src_teleon_registry_records__cosine__dot / (py_local_src_teleon_registry_records__cosine__na * py_local_src_teleon_registry_records__cosine__nb) if py_local_src_teleon_registry_records__cosine__na and py_local_src_teleon_registry_records__cosine__nb else 0.0


def py_function_src_teleon_registry_records__record_search(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__record_search__query: str, py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__record_search__records: list[dict], *, limit: int = 10) -> list[dict]:
    """VECTOR search: rank records by cosine against the query embedding (the pgvector floor; same op pgvector runs)."""
    py_local_src_teleon_registry_records__record_search__qv = py_function_src_teleon_registry_enrich__embedding({"text": py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__record_search__query})
    py_local_src_teleon_registry_records__record_search__scored = sorted(((py_function_src_teleon_registry_records___cosine(py_local_src_teleon_registry_records__record_search__qv, r["embedding"]), r) for r in py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__record_search__records), key=lambda py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__record_search__s: py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__record_search__s[0], reverse=True)
    return [{"score": round(py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__record_search__s, 4), "name": r["name"], "registry": r["registry"], "synthetic": r["synthetic"]}
            for py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__record_search__s, r in py_local_src_teleon_registry_records__record_search__scored[:limit] if py_arg_src_teleon_registry_records__py_function_src_teleon_registry_records__record_search__s > 0]
