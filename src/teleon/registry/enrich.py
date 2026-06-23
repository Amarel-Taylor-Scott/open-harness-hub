"""registry.enrich — the registry maintenance / ENRICHMENT worker (Baltor 'Enhance' on the registries).

For each registry record, GENERATE the derived metadata that makes the buffet rich + searchable: a deterministic
embedding, a short + long description, use cases, labels, and keywords. Reads catalogs through the RegistryPort
(dogfoods the menu). Deterministic FLOOR (lexical); a learned/LLM enricher swaps behind the same functions
(the agnostic-adapter pattern). serves_truth=false — enrichment is DERIVED metadata, never a truth claim. This
is the reconcile/improve/enrich worker that keeps registries current + discoverable.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter

from .port import available, catalog

_EMBED_DIM = 64                       # enrichment embedding dim (deterministic floor; a learned embedder swaps in)
_TOP_KEYWORDS = 8
_MIN_TOKEN_LEN = 3
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {"the", "and", "for", "with", "via", "per", "you", "your", "its", "not", "are", "that", "this", "from"}
# fields that read as categorical labels / as the human-readable 'what'
_LABEL_FIELDS = ("domain", "scope", "access", "cost_tier", "signal", "engagement", "kind", "status", "invasiveness")
_WHAT_FIELDS = ("returns", "holds", "action", "skills", "yields")
_DETAIL_FIELDS = ("domain", "scope", "access", "cost_tier", "jurisdiction", "authority", "governance", "when", "license", "ref")


def _text(record: dict) -> str:
    return " ".join(str(v) for v in record.values() if isinstance(v, (str, int, float)))


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOP and len(t) >= _MIN_TOKEN_LEN]


def keywords(record: dict) -> list[str]:
    return [w for w, _ in Counter(_tokens(_text(record))).most_common(_TOP_KEYWORDS)]


def embedding(record: dict) -> list[float]:
    """Deterministic lexical hash embedding (L2-normalized); a learned embedder drops in behind this signature."""
    vec = [0.0] * _EMBED_DIM
    for t in _tokens(_text(record)):
        bucket = int(hashlib.sha256(t.encode()).hexdigest(), 16) % _EMBED_DIM
        vec[bucket] += 1.0
    norm = sum(x * x for x in vec) ** 0.5
    return [round(x / norm, 6) for x in vec] if norm > 0 else vec


def labels(record: dict) -> list[str]:
    return [f"{k}:{record[k]}" for k in _LABEL_FIELDS if isinstance(record.get(k), str) and record.get(k)]


def description(record: dict) -> str:
    name = record.get("name") or record.get("id") or record.get("canonical") or "record"
    what = next((record[k] for k in _WHAT_FIELDS if isinstance(record.get(k), str) and record.get(k)), "")
    return f"{name}: {what}".strip().strip(":").strip()


def long_description(record: dict) -> str:
    parts = [description(record)]
    parts += [f"{k}={record[k]}" for k in _DETAIL_FIELDS if isinstance(record.get(k), str) and record.get(k)]
    return " | ".join(parts)


def use_cases(record: dict) -> list[str]:
    dom = record.get("domain") or record.get("scope") or record.get("signal") or "this"
    name = record.get("name") or record.get("id") or "it"
    return [f"use {name} to source {dom} information", f"compose {name} as a DAG step for a {dom} task"]


def enrich_record(record: dict) -> dict:
    """Return the record with a derived `_enrichment` block (embedding/description/use_cases/labels/keywords)."""
    return {**record, "_enrichment": {
        "embedding": embedding(record),
        "embedding_dim": _EMBED_DIM,
        "description": description(record),
        "long_description": long_description(record),
        "keywords": keywords(record),
        "labels": labels(record),
        "use_cases": use_cases(record),
    }}


def enrich_catalog(name: str) -> list[dict]:
    """Enrich every record in a registered catalog (via the RegistryPort menu)."""
    return [enrich_record(r) for r in catalog(name).list()]


def enrich_all() -> dict[str, list[dict]]:
    return {name: enrich_catalog(name) for name in available()}
