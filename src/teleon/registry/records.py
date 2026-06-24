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

from .enrich import _EMBED_DIM, embedding, enrich_record
from .port import all_catalogs, catalog

EMBED_DIM = _EMBED_DIM
_SYNTH_DOMAINS = ("us", "eu", "global", "enterprise", "regional", "local", "federal", "open", "managed", "hosted")


def _to_record(registry: str, raw: dict, *, synthetic: bool = False) -> dict:
    e = enrich_record(raw)["_enrichment"]
    rid = raw.get("id") or raw.get("canonical") or raw.get("name") or "record"
    return {
        "id": f"{registry}:{rid}", "registry": registry,
        "name": raw.get("name") or raw.get("id") or raw.get("canonical") or str(rid),
        "description": e["description"], "long_description": e["long_description"],
        "metadata": {"keywords": e["keywords"], "labels": e["labels"], "use_cases": e["use_cases"]},
        "embedding": e["embedding"], "embedding_dim": EMBED_DIM,
        "synthetic": synthetic, "candidate": True, "serves_truth": False,
    }


def real_records(registry: str) -> list[dict]:
    """REAL records from the catalog (any curated OR auto-discovered catalog)."""
    if registry not in all_catalogs():
        return []
    return [_to_record(registry, r) for r in catalog(registry).list()]


def synthetic_records(registry: str, n: int) -> list[dict]:
    """n templated CANDIDATE records (flagged synthetic) — proves storage/search at scale, never claimed as real."""
    out = []
    for i in range(n):
        dom = _SYNTH_DOMAINS[i % len(_SYNTH_DOMAINS)]
        raw = {"id": f"{registry}_cand_{i:05d}", "name": f"{registry} {dom} candidate {i}",
               "domain": dom, "kind": registry, "note": f"synthetic {registry} record #{i} for scale-out"}
        out.append(_to_record(registry, raw, synthetic=True))
    return out


def build_records(registry: str, *, target: int = 1000) -> list[dict]:
    """Real records first, topped up with flagged synthetic candidates to reach `target` (>=1000/registry)."""
    real = real_records(registry)
    return real + synthetic_records(registry, max(0, target - len(real)))


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def record_search(query: str, records: list[dict], *, limit: int = 10) -> list[dict]:
    """VECTOR search: rank records by cosine against the query embedding (the pgvector floor; same op pgvector runs)."""
    qv = embedding({"text": query})
    scored = sorted(((_cosine(qv, r["embedding"]), r) for r in records), key=lambda s: s[0], reverse=True)
    return [{"score": round(s, 4), "name": r["name"], "registry": r["registry"], "synthetic": r["synthetic"]}
            for s, r in scored[:limit] if s > 0]
