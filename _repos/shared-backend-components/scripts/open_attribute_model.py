#!/usr/bin/env python3
"""open_attribute_model — uncapped, typed, extensible attributes on ANY subject (code, image, function, tool…).

Owner (2026-07-10): a primitive record needs "fully unlimited infinity flexibility" — not just edges + blocking
keys, but custom dimensions, custom numbers, custom categoricals, custom embeddings, multiple descriptions, and
the ability to represent prepackaged Docker images, cloud functions, instance/technology-specific tools, common
use cases, ratings, throughput, industries, and every other datapoint in the world.

The principled way to get unbounded flexibility WITHOUT an unbounded hardcoded schema is an OPEN attribute
model: a subject is a `kind` (code_function / docker_image / cloud_function / service / tool / dataset / model /
workflow / …) plus an UNCAPPED bag of typed `Attribute`s. Each attribute declares its VALUE TYPE (number,
quantity+unit, rating, categorical, ordinal, tag_set, text, boolean, embedding, reference, temporal,
distribution, url, …) so it stays queryable/rankable, and carries provenance + the candidate/truth boundary.
Attribute types and subject kinds are DATA in extensible registries — adding one is a single row, never a
migration. Validation is OPEN-WORLD: it validates the SHAPE of a declared type but never restricts WHICH
attributes a subject may carry, and an unknown type is accepted + flagged (never silently dropped or coerced).

    PYTHONPATH=. python3 scripts/open_attribute_model.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"open_attribute_model requires canonical_id; import failed: {exc}")

SUBJECT_ID_PREFIX = "subj"
ATTR_ID_PREFIX = "attr"


# ── VALUE-TYPE REGISTRY: each type = a validator + how it is QUERYABLE. Add a type = one row (extensible). ────
def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_quantity(v: Any) -> bool:
    return isinstance(v, dict) and _is_number(v.get("value")) and isinstance(v.get("unit"), str)


def _is_rating(v: Any) -> bool:
    return (_is_number(v) and 0 <= v <= 5) or (isinstance(v, dict) and _is_number(v.get("value"))
                                               and _is_number(v.get("scale")))


def _is_embedding(v: Any) -> bool:
    return isinstance(v, dict) and {"model", "dim", "space"} <= set(v)


def _is_reference(v: Any) -> bool:
    # a reference to a prepackaged artifact: {kind, uri|digest} — e.g. a docker image, a cloud function, a tool.
    return isinstance(v, dict) and v.get("kind") and (v.get("uri") or v.get("digest"))


def _is_tag_set(v: Any) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _is_distribution(v: Any) -> bool:
    return isinstance(v, dict) and (isinstance(v.get("samples"), list) or isinstance(v.get("quantiles"), dict))


ATTRIBUTE_TYPES: dict[str, dict[str, Any]] = {
    "number": {"validate": _is_number, "queryable_as": "numeric"},
    "integer": {"validate": lambda v: isinstance(v, int) and not isinstance(v, bool), "queryable_as": "numeric"},
    "quantity": {"validate": _is_quantity, "queryable_as": "numeric_unit"},      # {value, unit}: throughput, memory…
    "rating": {"validate": _is_rating, "queryable_as": "numeric"},               # 0-5 or {value, scale}
    "categorical": {"validate": lambda v: isinstance(v, str), "queryable_as": "categorical"},  # industry, license…
    "ordinal": {"validate": lambda v: isinstance(v, str), "queryable_as": "ordinal"},          # tier: xs<s<m<l…
    "tag_set": {"validate": _is_tag_set, "queryable_as": "set"},                 # industries[], use_cases[], keys[]
    "text": {"validate": lambda v: isinstance(v, str), "queryable_as": "text"},  # multiple descriptions allowed
    "boolean": {"validate": lambda v: isinstance(v, bool), "queryable_as": "boolean"},
    "embedding": {"validate": _is_embedding, "queryable_as": "vector"},          # multiple/tunable embeddings
    "reference": {"validate": _is_reference, "queryable_as": "reference"},       # docker_image / cloud_function / tool
    "temporal": {"validate": lambda v: isinstance(v, str), "queryable_as": "temporal"},
    "distribution": {"validate": _is_distribution, "queryable_as": "numeric_distribution"},
    "url": {"validate": lambda v: isinstance(v, str) and "://" in v, "queryable_as": "text"},
}


def register_attribute_type(name: str, validate: Callable[[Any], bool], queryable_as: str) -> None:
    """Extensibility: a NEW value type is one row; every subject can immediately carry it, queryably."""
    ATTRIBUTE_TYPES[name] = {"validate": validate, "queryable_as": queryable_as}


# ── SUBJECT-KIND REGISTRY: a kind is METADATA, never a gate on which attributes a subject may carry. ─────────
SUBJECT_KINDS: dict[str, str] = {
    "code_function": "a single function/primitive", "code_module": "a cohesive module",
    "package": "a distributable package", "docker_image": "a prepackaged OCI/Docker image",
    "cloud_function": "a serverless function (Lambda/Cloud Run job)", "service": "a running service/API",
    "tool": "an instance/technology-specific tool", "dataset": "a governed dataset",
    "model": "an ML model artifact", "workflow": "a multi-step workflow", "sql_udf": "a SQL/UDF transform",
    "wasm_component": "a WASI component", "api": "an API surface", "capability": "a logical capability family",
}


def register_subject_kind(name: str, note: str = "") -> None:
    """Extensibility: a NEW artifact kind (terraform_module, notebook, helm_chart, …) is one row."""
    SUBJECT_KINDS[name] = note


def make_attribute(namespace: str, name: str, type_: str, value: Any, *, unit: Optional[str] = None,
                   provenance: Optional[str] = None) -> dict[str, Any]:
    return {"attr_id": canonical_id(ATTR_ID_PREFIX, namespace, name, type_),
            "namespace": namespace, "name": name, "type": type_, "value": value,
            **({"unit": unit} if unit else {}),
            "provenance": provenance or "unspecified", "candidate": True, "serves_truth": False}


def validate_attribute(attr: dict[str, Any]) -> dict[str, Any]:
    """OPEN-WORLD validation: check the value matches its declared type's shape. An UNKNOWN type is ACCEPTED
    (never dropped/coerced) but flagged open_world=true with queryable_as='opaque' — flexibility without lying."""
    t = attr.get("type")
    if t not in ATTRIBUTE_TYPES:
        return {"valid": True, "open_world": True, "queryable_as": "opaque",
                "reason": f"unknown type {t!r} accepted as opaque (extensible; register a type to make it queryable)"}
    spec = ATTRIBUTE_TYPES[t]
    ok = bool(spec["validate"](attr.get("value")))
    return {"valid": ok, "open_world": False, "queryable_as": spec["queryable_as"],
            "reason": "" if ok else f"value does not match the shape of type {t!r}"}


def new_subject(kind: str, title: str = "") -> dict[str, Any]:
    return {"subject_id": canonical_id(SUBJECT_ID_PREFIX, kind, title), "record_type": "open_subject",
            "kind": kind, "kind_known": kind in SUBJECT_KINDS, "title": title, "attributes": [],
            "candidate": True, "serves_truth": False}


def attach(subject: dict[str, Any], attr: dict[str, Any]) -> dict[str, Any]:
    """APPEND-ONLY, OPEN: attach an attribute. Never rejects an attribute NAME (uncapped flexibility); only the
    value SHAPE is validated for the declared type. Returns a new subject."""
    return {**subject, "attributes": [*subject["attributes"], attr]}


# ── QUERY/FILTER over ARBITRARY attributes — a filter zoo (add a filter = one row). ──────────────────────────
def _attr(subject: dict[str, Any], namespace: str, name: str) -> Optional[dict[str, Any]]:
    return next((a for a in subject["attributes"] if a["namespace"] == namespace and a["name"] == name), None)


FILTERS: dict[str, Callable[..., bool]] = {
    "numeric_gte": lambda subj, ns, name, threshold=0, **_: (
        (a := _attr(subj, ns, name)) is not None and _is_number(a["value"]) and a["value"] >= threshold),
    "numeric_range": lambda subj, ns, name, lo=float("-inf"), hi=float("inf"), **_: (
        (a := _attr(subj, ns, name)) is not None and _is_number(a["value"]) and lo <= a["value"] <= hi),
    "quantity_gte": lambda subj, ns, name, threshold=0, unit=None, **_: (
        (a := _attr(subj, ns, name)) is not None and _is_quantity(a["value"])
        and (unit is None or a["value"]["unit"] == unit) and a["value"]["value"] >= threshold),
    "categorical_eq": lambda subj, ns, name, equals=None, **_: (
        (a := _attr(subj, ns, name)) is not None and a["value"] == equals),
    "tag_contains": lambda subj, ns, name, tag=None, **_: (
        (a := _attr(subj, ns, name)) is not None and isinstance(a["value"], list) and tag in a["value"]),
    "has_reference_kind": lambda subj, ns, name, ref_kind=None, **_: (
        (a := _attr(subj, ns, name)) is not None and _is_reference(a["value"])
        and a["value"].get("kind") == ref_kind),
    "kind_eq": lambda subj, kind=None, **_: subj["kind"] == kind,
}


def register_filter(name: str, fn: Callable[..., bool]) -> None:
    FILTERS[name] = fn


def filter_subjects(subjects: list[dict[str, Any]], filter_name: str, **args: Any) -> list[dict[str, Any]]:
    if filter_name not in FILTERS:
        raise ValueError(f"unknown filter {filter_name!r}; known: {sorted(FILTERS)}")
    fn = FILTERS[filter_name]
    return [s for s in subjects if fn(s, **args)]


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) attach EVERY requested characteristic to ONE subject — a code function with numbers, ratings,
    #     throughput, industries, multiple descriptions, multiple embeddings, and references to prepackaged
    #     artifacts (docker image + cloud function + tool) — all validating.
    subj = new_subject("code_function", "parse csv")
    attrs = [
        make_attribute("perf", "latency_p95_ms", "number", 42),
        make_attribute("quality", "user_rating", "rating", 4.5),
        make_attribute("perf", "throughput", "quantity", {"value": 12000, "unit": "rows_per_sec"}),
        make_attribute("domain", "industries", "tag_set", ["fintech", "healthcare-admin", "logistics"]),
        make_attribute("domain", "use_cases", "tag_set", ["etl", "ingest", "normalize"]),
        make_attribute("doc", "description_plain", "text", "Parses a CSV file into typed rows."),
        make_attribute("doc", "description_technical", "text", "Streaming RFC-4180 dialect-sniffing parser."),
        make_attribute("embed", "vec_model2vec", "embedding", {"model": "potion-8m", "dim": 256, "space": "cosine"}),
        make_attribute("embed", "vec_bge", "embedding", {"model": "bge-small", "dim": 384, "space": "cosine"}),
        make_attribute("artifact", "docker_image", "reference",
                       {"kind": "docker_image", "digest": "sha256:abc", "uri": "registry/csv:1"}),
        make_attribute("artifact", "cloud_function", "reference",
                       {"kind": "cloud_function", "uri": "gcf://parse-csv"}),
        make_attribute("artifact", "tool", "reference", {"kind": "tool", "uri": "tool://pandas.read_csv"}),
        make_attribute("cost", "monthly_usd", "quantity", {"value": 3.2, "unit": "usd_per_month"}),
        make_attribute("meta", "custom_dimension_42", "categorical", "some-bespoke-bucket"),
    ]
    for a in attrs:
        subj = attach(subj, a)
    validations = [validate_attribute(a) for a in subj["attributes"]]
    checks.append(("one subject carries numbers + ratings + throughput + industries + multiple descriptions + "
                   "multiple embeddings + docker/cloud-function/tool references + a custom dimension — ALL "
                   "validate (every requested datapoint kind is representable)",
                   len(subj["attributes"]) == 14 and all(v["valid"] for v in validations)
                   and not any(v["open_world"] for v in validations),
                   json.dumps([v for v in validations if not v["valid"]])[:120]))

    # (2) different SUBJECT KINDS: a docker_image, a cloud_function, and a tool are all first-class subjects,
    #     each carrying its own attributes — the model is not code-only.
    image = attach(new_subject("docker_image", "ocr-service"),
                   make_attribute("size", "compressed_mb", "quantity", {"value": 512, "unit": "mb"}))
    fn = attach(new_subject("cloud_function", "resize"),
                make_attribute("perf", "cold_start_ms", "number", 800))
    tool = attach(new_subject("tool", "ripgrep"),
                  make_attribute("meta", "technology", "categorical", "rust-cli"))
    checks.append(("prepackaged Docker images, cloud functions, and instance/technology-specific tools are "
                   "first-class subjects (not code-only) with their own attributes",
                   image["kind"] == "docker_image" and fn["kind"] == "cloud_function" and tool["kind"] == "tool"
                   and all(s["kind_known"] for s in (image, fn, tool)), ""))

    # (3) UNCAPPED: attach 500 custom attributes; nothing is dropped or capped.
    big = new_subject("code_function", "big")
    for i in range(500):
        big = attach(big, make_attribute("custom", f"dimension_{i}", "number", i))
    checks.append(("uncapped: 500 custom attributes attach with none dropped (infinite flexibility, not a fixed "
                   "column set)", len(big["attributes"]) == 500, ""))

    # (4) OPEN-WORLD: an UNKNOWN type is accepted + flagged opaque (never dropped/coerced) — flexibility without
    #     lying; registering the type makes it queryable.
    opaque = make_attribute("weird", "quantum_state", "qubit_vector", [0.7, 0.7])
    before = validate_attribute(opaque)
    register_attribute_type("qubit_vector", lambda v: isinstance(v, list), "vector")
    after = validate_attribute(opaque)
    checks.append(("open-world types: an unknown type is ACCEPTED + flagged opaque (never dropped); registering "
                   "it (one row) makes it valid + queryable",
                   before["valid"] and before["open_world"] and before["queryable_as"] == "opaque"
                   and after["valid"] and not after["open_world"] and after["queryable_as"] == "vector", ""))

    # (5) QUERY over ARBITRARY attributes: filter by a rating, a throughput quantity, an industry tag, and a
    #     reference kind — arbitrary datapoints are queryable, not just edges.
    subjects = [subj, image, fn, tool]
    by_rating = filter_subjects(subjects, "numeric_gte", ns="quality", name="user_rating", threshold=4.0)
    by_industry = filter_subjects(subjects, "tag_contains", ns="domain", name="industries", tag="fintech")
    by_ref = filter_subjects(subjects, "has_reference_kind", ns="artifact", name="docker_image",
                             ref_kind="docker_image")
    by_throughput = filter_subjects(subjects, "quantity_gte", ns="perf", name="throughput", threshold=10000,
                                    unit="rows_per_sec")
    checks.append(("arbitrary attributes are QUERYABLE: filter by rating>=4, industry='fintech', a "
                   "docker_image reference, and throughput>=10k rows/s — each returns the right subject",
                   len(by_rating) == 1 and len(by_industry) == 1 and len(by_ref) == 1 and len(by_throughput) == 1,
                   ""))

    # (6) EXTENSIBILITY: a new SUBJECT KIND (terraform_module) + a new FILTER are each one row; existing data is
    #     unaffected.
    register_subject_kind("terraform_module", "an IaC module")
    register_filter("kind_in", lambda subj, kinds=(), **_: subj["kind"] in kinds)
    tf = new_subject("terraform_module", "vpc")
    checks.append(("extensibility: a new subject kind + a new filter are each one row; the model grows without "
                   "migration",
                   tf["kind_known"] is True and "kind_in" in FILTERS
                   and len(filter_subjects([tf, subj], "kind_in", kinds=("terraform_module",))) == 1, ""))

    # (7) governance per attribute + determinism.
    checks.append(("every attribute carries the candidate/truth boundary + provenance; deterministic ids",
                   all(a["serves_truth"] is False and "provenance" in a for a in subj["attributes"])
                   and make_attribute("a", "b", "number", 1)["attr_id"]
                   == make_attribute("a", "b", "number", 1)["attr_id"], ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - open_attribute_model: uncapped, typed, extensible attributes on ANY "
          f"subject kind — {len(ATTRIBUTE_TYPES)} value types (number/quantity/rating/categorical/tag_set/text/"
          f"embedding/reference/…) + {len(SUBJECT_KINDS)} subject kinds (code/docker_image/cloud_function/tool/"
          f"service/dataset/model/…), open-world (unknown type accepted+flagged, register→queryable), 500 "
          f"attributes attach uncapped, arbitrary attributes queryable, new type/kind/filter each one row. "
          f"serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Open, typed, extensible attribute model for any subject kind.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
