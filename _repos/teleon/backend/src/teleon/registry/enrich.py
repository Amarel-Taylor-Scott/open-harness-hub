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

from .port import py_function_src_teleon_registry_port__available, py_function_src_teleon_registry_port__catalog

py_var_src_teleon_registry_enrich___EMBED_DIM = 64                       # enrichment embedding dim (deterministic floor; a learned embedder swaps in)
py_var_src_teleon_registry_enrich___TOP_KEYWORDS = 8
py_var_src_teleon_registry_enrich___MIN_TOKEN_LEN = 3
py_var_src_teleon_registry_enrich___TOKEN_RE = re.compile(r"[a-z0-9]+")
py_var_src_teleon_registry_enrich___STOP = {"the", "and", "for", "with", "via", "per", "you", "your", "its", "not", "are", "that", "this", "from"}
# fields that read as categorical labels / as the human-readable 'what'
py_var_src_teleon_registry_enrich___LABEL_FIELDS = ("domain", "scope", "access", "cost_tier", "signal", "engagement", "kind", "status", "invasiveness")
py_var_src_teleon_registry_enrich___WHAT_FIELDS = ("returns", "holds", "action", "skills", "yields")
py_var_src_teleon_registry_enrich___DETAIL_FIELDS = ("domain", "scope", "access", "cost_tier", "jurisdiction", "authority", "governance", "when", "license", "ref")


def py_function_src_teleon_registry_enrich___text(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__text__record: dict) -> str:
    return " ".join(str(v) for v in py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__text__record.values() if isinstance(v, (str, int, float)))


def py_function_src_teleon_registry_enrich___tokens(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__tokens__text: str) -> list[str]:
    return [t for t in py_var_src_teleon_registry_enrich___TOKEN_RE.findall(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__tokens__text.lower()) if t not in py_var_src_teleon_registry_enrich___STOP and len(t) >= py_var_src_teleon_registry_enrich___MIN_TOKEN_LEN]


def py_function_src_teleon_registry_enrich__keywords(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__keywords__record: dict) -> list[str]:
    return [w for w, _ in Counter(py_function_src_teleon_registry_enrich___tokens(py_function_src_teleon_registry_enrich___text(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__keywords__record))).most_common(py_var_src_teleon_registry_enrich___TOP_KEYWORDS)]


def py_function_src_teleon_registry_enrich__embedding(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__embedding__record: dict) -> list[float]:
    """Deterministic lexical hash embedding (L2-normalized); a learned embedder drops in behind this signature."""
    py_local_src_teleon_registry_enrich__embedding__vec = [0.0] * py_var_src_teleon_registry_enrich___EMBED_DIM
    for py_local_src_teleon_registry_enrich__embedding__t in py_function_src_teleon_registry_enrich___tokens(py_function_src_teleon_registry_enrich___text(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__embedding__record)):
        py_local_src_teleon_registry_enrich__embedding__bucket = int(hashlib.sha256(py_local_src_teleon_registry_enrich__embedding__t.encode()).hexdigest(), 16) % py_var_src_teleon_registry_enrich___EMBED_DIM
        py_local_src_teleon_registry_enrich__embedding__vec[py_local_src_teleon_registry_enrich__embedding__bucket] += 1.0
    py_local_src_teleon_registry_enrich__embedding__norm = sum(x * x for x in py_local_src_teleon_registry_enrich__embedding__vec) ** 0.5
    return [round(x / py_local_src_teleon_registry_enrich__embedding__norm, 6) for x in py_local_src_teleon_registry_enrich__embedding__vec] if py_local_src_teleon_registry_enrich__embedding__norm > 0 else py_local_src_teleon_registry_enrich__embedding__vec


def py_function_src_teleon_registry_enrich__labels(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__labels__record: dict) -> list[str]:
    return [f"{k}:{py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__labels__record[k]}" for k in py_var_src_teleon_registry_enrich___LABEL_FIELDS if isinstance(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__labels__record.get(k), str) and py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__labels__record.get(k)]


def py_function_src_teleon_registry_enrich__description(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__description__record: dict) -> str:
    py_local_src_teleon_registry_enrich__description__name = py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__description__record.get("name") or py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__description__record.get("id") or py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__description__record.get("canonical") or "record"
    py_local_src_teleon_registry_enrich__description__what = next((py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__description__record[k] for k in py_var_src_teleon_registry_enrich___WHAT_FIELDS if isinstance(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__description__record.get(k), str) and py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__description__record.get(k)), "")
    return f"{py_local_src_teleon_registry_enrich__description__name}: {py_local_src_teleon_registry_enrich__description__what}".strip().strip(":").strip()


def py_function_src_teleon_registry_enrich__long_description(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__long_description__record: dict) -> str:
    py_local_src_teleon_registry_enrich__long_description__parts = [py_function_src_teleon_registry_enrich__description(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__long_description__record)]
    py_local_src_teleon_registry_enrich__long_description__parts += [f"{k}={py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__long_description__record[k]}" for k in py_var_src_teleon_registry_enrich___DETAIL_FIELDS if isinstance(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__long_description__record.get(k), str) and py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__long_description__record.get(k)]
    return " | ".join(py_local_src_teleon_registry_enrich__long_description__parts)


def py_function_src_teleon_registry_enrich__use_cases(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__use_cases__record: dict) -> list[str]:
    py_local_src_teleon_registry_enrich__use_cases__dom = py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__use_cases__record.get("domain") or py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__use_cases__record.get("scope") or py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__use_cases__record.get("signal") or "this"
    py_local_src_teleon_registry_enrich__use_cases__name = py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__use_cases__record.get("name") or py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__use_cases__record.get("id") or "it"
    return [f"use {py_local_src_teleon_registry_enrich__use_cases__name} to source {py_local_src_teleon_registry_enrich__use_cases__dom} information", f"compose {py_local_src_teleon_registry_enrich__use_cases__name} as a DAG step for a {py_local_src_teleon_registry_enrich__use_cases__dom} task"]


def py_function_src_teleon_registry_enrich__enrich_record(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_record__record: dict) -> dict:
    """Return the record with a derived `_enrichment` block (embedding/description/use_cases/labels/keywords)."""
    return {**py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_record__record, "_enrichment": {
        "embedding": py_function_src_teleon_registry_enrich__embedding(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_record__record),
        "embedding_dim": py_var_src_teleon_registry_enrich___EMBED_DIM,
        "description": py_function_src_teleon_registry_enrich__description(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_record__record),
        "long_description": py_function_src_teleon_registry_enrich__long_description(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_record__record),
        "keywords": py_function_src_teleon_registry_enrich__keywords(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_record__record),
        "labels": py_function_src_teleon_registry_enrich__labels(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_record__record),
        "use_cases": py_function_src_teleon_registry_enrich__use_cases(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_record__record),
    }}


def py_function_src_teleon_registry_enrich__enrich_catalog(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_catalog__name: str) -> list[dict]:
    """Enrich every record in a registered catalog (via the RegistryPort menu)."""
    return [py_function_src_teleon_registry_enrich__enrich_record(r) for r in py_function_src_teleon_registry_port__catalog(py_arg_src_teleon_registry_enrich__py_function_src_teleon_registry_enrich__enrich_catalog__name).list()]


def py_function_src_teleon_registry_enrich__enrich_all() -> dict[str, list[dict]]:
    return {name: py_function_src_teleon_registry_enrich__enrich_catalog(name) for name in py_function_src_teleon_registry_port__available()}
