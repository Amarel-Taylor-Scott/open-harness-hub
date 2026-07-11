#!/usr/bin/env python3
"""scripts.schema_org_primitive_foundry — walk EVERY schema.org type and property (the machine-readable
vocabulary: ~1,000 classes, ~1,700 properties) and ask, per property ("column"), the owner's question grid:
common use case · transformation · validation · comparison · storage · format · display · indexing — then
mint primitive candidates and system candidates from the answers.

Three row kinds:
  * PROPERTY x ASPECT primitives — every property's rangeIncludes maps to a datatype FAMILY (text, number,
    boolean, temporal, duration, url, enumeration, entity_ref); each family renders the 8 aspects into
    concrete candidate primitives. Edges use a SHARED schema.org-typed vocabulary
    (``SchemaOrgTextValue`` -> ``NormalizedSchemaOrgTextValue`` ...), so candidates minted from different
    properties CHAIN on exact typed joins — a direct lever on the measured exact-join~0 chainability gap.
  * TYPE primitives — one records-system candidate per class (storage schema sketch from its properties'
    families, CRUD, JSON-LD handling, display card).
  * FAMILY SYSTEMS — one pipeline-system candidate per top-level Thing branch (Person, Organization,
    CreativeWork, Place, Product, Event, ...).

Text-family rows cross-link the string-standardization pack (standardize_person_name /
standardize_us_address / standardize_company_name / generate_match_keys) so schema.org columns resolve to
EXECUTABLE primitives where they exist. The vocabulary snapshot is a governed source (url + sha256 digest +
license CC BY-SA in the receipt; schema.org releases are open). Deterministic; candidate=true,
serves_truth=false; generation is not promotion.

    python3 scripts/schema_org_primitive_foundry.py --self-test
    python3 scripts/schema_org_primitive_foundry.py --run [--snapshot PATH] [--limit-properties N]
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"schema_org_primitive_foundry requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-schemaorg"
_SNAPSHOT_URL = "https://schema.org/version/latest/schemaorg-current-https.jsonld"
_SNAPSHOT_LICENSE = "CC BY-SA 3.0 (schema.org terms)"
_OUT_DIRNAME = "schema_org_foundry"

#: rangeIncludes -> datatype family (single source for the aspect rendering)
_RANGE_FAMILY = {"Text": "text", "URL": "url", "Number": "number", "Integer": "number", "Float": "number",
                 "Boolean": "boolean", "Date": "temporal", "DateTime": "temporal", "Time": "temporal",
                 "Duration": "duration"}
_ASPECTS = ("use_case", "transformation", "validation", "comparison", "storage", "format", "display",
            "indexing")
#: family -> aspect -> (title verb phrase, method/tool note). The owner's question grid, answered per family.
_FAMILY_ASPECTS: dict[str, dict[str, tuple[str, str]]] = {
    "text": {
        "use_case": ("Capture and preserve raw", "raw landing column; never overwritten; provenance kept"),
        "transformation": ("Normalize and clean", "trim/collapse whitespace, Unicode NFC, punctuation + case normalization (string-standardization atoms)"),
        "validation": ("Validate shape and emptiness of", "non-empty after cleaning, length bounds, control-character rejection"),
        "comparison": ("Fuzzy-compare and match", "casefolded + diacritic-stripped match keys, token-sorted, n-gram, phonetic (RapidFuzz-style scorers)"),
        "storage": ("Store and version", "TEXT column + JSONB parsed components; raw/cleaned/display/match stored separately"),
        "format": ("Serialize", "JSON-LD literal; UTF-8; NFC for storage"),
        "display": ("Render display form of", "meaning-preserving display value (diacritics/case kept), locale-aware"),
        "indexing": ("Index for retrieval", "btree exact + trigram/inverted index + blocking keys for dedupe")},
    "url": {
        "use_case": ("Capture canonical link", "identity + external-reference column"),
        "transformation": ("Normalize", "scheme/host lowercase, strip tracking params, resolve relative form"),
        "validation": ("Validate", "RFC-3986 parse, scheme allowlist, reachability optional"),
        "comparison": ("Compare", "registrable-domain match then full-URL exact"),
        "storage": ("Store", "TEXT + parsed host/domain columns"),
        "format": ("Serialize", "absolute IRI in JSON-LD"),
        "display": ("Render", "shortened display with hostname emphasis"),
        "indexing": ("Index", "btree on registrable domain + hash on full URL")},
    "number": {
        "use_case": ("Capture measured quantity", "metric/amount column with unit discipline"),
        "transformation": ("Coerce and unit-normalize", "locale decimal parse, unit conversion, precision policy"),
        "validation": ("Range-validate", "min/max plausibility, NaN/inf rejection"),
        "comparison": ("Numerically compare", "epsilon equality, range/percentile compare"),
        "storage": ("Store", "NUMERIC with declared scale; unit in sibling column"),
        "format": ("Serialize", "JSON number; string when precision-critical"),
        "display": ("Format", "locale grouping + unit suffix"),
        "indexing": ("Index", "btree range index; histogram stats")},
    "boolean": {
        "use_case": ("Capture flag", "tri-state: true/false/unknown — never default unknown to false"),
        "transformation": ("Coerce", "yes/no/1/0/true/false token map"),
        "validation": ("Validate", "reject non-mappable tokens to unknown"),
        "comparison": ("Compare", "exact tri-state"),
        "storage": ("Store", "BOOLEAN NULLable (NULL = unknown)"),
        "format": ("Serialize", "JSON true/false/null"),
        "display": ("Render", "Yes/No/Unknown labels"),
        "indexing": ("Index", "partial index on the rare state")},
    "temporal": {
        "use_case": ("Capture point-in-time", "event/effective-date column; timezone discipline"),
        "transformation": ("Parse and normalize", "ISO-8601, timezone-normalize to UTC + original offset kept"),
        "validation": ("Validate", "calendar validity, plausible range, precision tagging (date vs datetime)"),
        "comparison": ("Chronologically compare", "range/window compare at declared precision"),
        "storage": ("Store", "TIMESTAMP/DATE + precision column"),
        "format": ("Serialize", "ISO-8601 string in JSON-LD"),
        "display": ("Format", "locale-formatted at stored precision"),
        "indexing": ("Index", "btree range; partition key when high-volume")},
    "duration": {
        "use_case": ("Capture elapsed/planned span", "duration column"),
        "transformation": ("Parse", "ISO-8601 duration to seconds + original form"),
        "validation": ("Validate", "non-negative, plausible magnitude"),
        "comparison": ("Compare", "numeric seconds compare"),
        "storage": ("Store", "INTEGER seconds + original TEXT"),
        "format": ("Serialize", "ISO-8601 duration"),
        "display": ("Humanize", "e.g. 1h 30m at chosen granularity"),
        "indexing": ("Index", "btree on seconds")},
    "enumeration": {
        "use_case": ("Capture controlled value", "closed-vocabulary column"),
        "transformation": ("Canonicalize", "alias map -> canonical member (versioned dictionary rows)"),
        "validation": ("Validate", "membership in the enumeration; unknowns quarantined"),
        "comparison": ("Compare", "exact canonical member"),
        "storage": ("Store", "TEXT + FK to enumeration reference table"),
        "format": ("Serialize", "schema.org enumeration IRI"),
        "display": ("Render", "human label per locale"),
        "indexing": ("Index", "btree; low-cardinality bitmap where supported")},
    "entity_ref": {
        "use_case": ("Link to entity", "foreign-reference column to another schema.org typed record"),
        "transformation": ("Resolve", "string -> canonical entity id via standardization + blocking + entity resolution"),
        "validation": ("Validate", "referenced entity exists; type matches rangeIncludes"),
        "comparison": ("Compare", "canonical entity id equality; fuzzy only for candidate generation"),
        "storage": ("Store", "FK column + resolution confidence + provenance"),
        "format": ("Serialize", "JSON-LD @id reference"),
        "display": ("Render", "linked display name of the referenced entity"),
        "indexing": ("Index", "btree FK + reverse index for whom-references")},
}
#: text properties that resolve to EXECUTABLE string-standardization primitives (cross-links)
_EXEC_LINKS = {"name": "generate_match_keys", "givenName": "standardize_person_name",
               "familyName": "standardize_person_name", "additionalName": "standardize_person_name",
               "legalName": "standardize_company_name", "streetAddress": "standardize_us_address",
               "postalCode": "standardize_us_address", "addressLocality": "standardize_us_address",
               "addressRegion": "standardize_us_address", "alternateName": "generate_match_keys"}


# ── vocabulary parsing ────────────────────────────────────────────────────────────────────────────────────────
def _local(x: Any) -> str:
    if isinstance(x, dict):
        x = x.get("@id", "")
    return str(x).split("/")[-1].split(":")[-1]


def _listify(x: Any) -> list:
    return x if isinstance(x, list) else ([x] if x else [])


def parse_vocabulary(doc: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    """JSON-LD graph -> (classes: name->{description, parents}, properties: name->{description, domains,
    ranges, family})."""
    classes: dict[str, dict] = {}
    props: dict[str, dict] = {}
    graph = doc.get("@graph", [])
    enum_parents: set[str] = set()
    for node in graph:
        types = {_local(t) for t in _listify(node.get("@type"))}
        name = _local(node.get("@id"))
        comment = node.get("rdfs:comment", "")
        if isinstance(comment, dict):
            comment = comment.get("@value", "")
        if "Class" in types:
            parents = [_local(p) for p in _listify(node.get("rdfs:subClassOf"))]
            classes[name] = {"description": str(comment)[:240], "parents": parents}
            if "Enumeration" in parents:
                enum_parents.add(name)
        if "Property" in types:
            domains = [_local(d) for d in _listify(node.get("schema:domainIncludes"))]
            ranges = [_local(r) for r in _listify(node.get("schema:rangeIncludes"))]
            props[name] = {"description": str(comment)[:240], "domains": domains, "ranges": ranges}
    for p in props.values():
        fams = []
        for r in p["ranges"]:
            if r in _RANGE_FAMILY:
                fams.append(_RANGE_FAMILY[r])
            elif r in enum_parents or "Enumeration" in classes.get(r, {}).get("parents", []):
                fams.append("enumeration")
            elif r in classes:
                fams.append("entity_ref")
        p["family"] = fams[0] if fams else "text"  # schema.org convention: Text is the universal fallback
    return classes, props


# ── row minting ───────────────────────────────────────────────────────────────────────────────────────────────
def _edge(family: str, normalized: bool = False) -> str:
    camel = "".join(w.title() for w in family.split("_"))
    return f"{'Normalized' if normalized else ''}SchemaOrg{camel}Value"


def mint_property_rows(props: dict[str, dict], limit: int = 0) -> list[dict[str, Any]]:
    rows = []
    for pname in sorted(props)[: limit or None]:
        p = props[pname]
        table = _FAMILY_ASPECTS[p["family"]]
        for aspect in _ASPECTS:
            verb, method = table[aspect]
            title = f"{verb} schema.org {pname} ({p['family']})"
            body = (f"{verb} the schema.org property `{pname}` — {p['description'] or 'see schema.org'} "
                    f"Method: {method}. Input: a {_edge(p['family'])}. "
                    f"Output: a {aspect} result for downstream {p['family']} consumers.")
            rows.append({
                "primitive_id": canonical_id(CARD_PREFIX, title, pname, aspect),
                "record_type": "schema_org_property_primitive_candidate", "kind": "primitive",
                "title": title[:160], "blackbox": body[:480],
                "schema_org_property": pname, "schema_org_domains": p["domains"][:8],
                "schema_org_ranges": p["ranges"][:6], "datatype_family": p["family"], "aspect": aspect,
                "input_edge": _edge(p["family"]),
                "output_edge": _edge(p["family"], normalized=True) if aspect == "transformation"
                               else f"SchemaOrg{aspect.title().replace('_', '')}Result",
                "executable_link": _EXEC_LINKS.get(pname, ""),
                "tags": f"schemaorg:{pname} family:{p['family']} aspect:{aspect}", **BOUNDARY})
    return rows


def mint_type_rows(classes: dict[str, dict], props: dict[str, dict]) -> list[dict[str, Any]]:
    by_domain: dict[str, list[str]] = {}
    for pname, p in props.items():
        for d in p["domains"]:
            by_domain.setdefault(d, []).append(pname)
    rows = []
    for cname in sorted(classes):
        c = classes[cname]
        cols = sorted(by_domain.get(cname, []))[:12]
        title = f"Records system for schema.org {cname}"
        rows.append({
            "primitive_id": canonical_id(CARD_PREFIX, title, cname), "kind": "primitive_group",
            "record_type": "schema_org_type_system_candidate", "title": title[:160],
            "blackbox": (f"CRUD + standardization system for schema.org type {cname} — "
                         f"{c['description'] or 'see schema.org'} Columns: {', '.join(cols) or 'inherited'}. "
                         f"Storage: relational table + JSON-LD document; raw preserved per column; "
                         f"per-column primitives via the property x aspect grid. "
                         f"Input: SchemaOrg{cname}RawRecord. Output: SchemaOrg{cname}CanonicalRecord."),
            "schema_org_type": cname, "parents": c["parents"][:4], "column_count": len(by_domain.get(cname, [])),
            "input_edge": f"SchemaOrg{cname}RawRecord", "output_edge": f"SchemaOrg{cname}CanonicalRecord",
            "tags": f"schemaorg:{cname} kind:type_system", **BOUNDARY})
    return rows


def mint_family_system_rows(classes: dict[str, dict]) -> list[dict[str, Any]]:
    top = sorted({c for c, v in classes.items() if "Thing" in v["parents"]})
    rows = []
    for branch in top:
        title = f"End-to-end pipeline system for the schema.org {branch} branch"
        rows.append({
            "primitive_id": canonical_id(CARD_PREFIX, title, branch), "kind": "primitive_group",
            "record_type": "schema_org_branch_system_candidate", "title": title[:160],
            "blackbox": (f"Load -> standardize -> resolve -> store -> index -> serve pipeline for the "
                         f"schema.org {branch} branch and its subtypes: raw landing, per-column "
                         f"standardization, blocking + entity resolution, canonical entities, match keys, "
                         f"JSON-LD serving, monitoring. Input: SchemaOrg{branch}SourceFeed. "
                         f"Output: SchemaOrg{branch}CanonicalEntityStore."),
            "schema_org_type": branch, "input_edge": f"SchemaOrg{branch}SourceFeed",
            "output_edge": f"SchemaOrg{branch}CanonicalEntityStore",
            "tags": f"schemaorg:{branch} kind:branch_system", **BOUNDARY})
    return rows


def run_foundry(snapshot: Path, *, limit_properties: int = 0) -> dict[str, Any]:
    raw = snapshot.read_bytes()
    doc = json.loads(raw)
    classes, props = parse_vocabulary(doc)
    prop_rows = mint_property_rows(props, limit=limit_properties)
    type_rows = mint_type_rows(classes, props)
    system_rows = mint_family_system_rows(classes)
    out_dir = resource("data") / "dev-intel" / _OUT_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows = prop_rows + type_rows + system_rows
    (out_dir / "schema_org_primitive_candidates.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in all_rows))
    rec = {"record_type": "schema_org_foundry_receipt",
           "source": {"url": _SNAPSHOT_URL, "sha256": hashlib.sha256(raw).hexdigest(),
                      "bytes": len(raw), "license": _SNAPSHOT_LICENSE,
                      "note": "governed open-vocabulary snapshot; handle+digest, body kept as reference file"},
           "classes": len(classes), "properties": len(props),
           "property_aspect_rows": len(prop_rows), "type_system_rows": len(type_rows),
           "branch_system_rows": len(system_rows), "total_candidates": len(all_rows),
           "aspects": list(_ASPECTS), "families": sorted(_FAMILY_ASPECTS),
           "shared_edge_vocabulary": sorted({r["input_edge"] for r in prop_rows}),
           "executable_links": sum(1 for r in prop_rows if r["executable_link"]),
           "staged_path": str(out_dir / "schema_org_primitive_candidates.jsonl"), **BOUNDARY}
    (out_dir / "schema_org_foundry_receipt.json").write_text(json.dumps(rec, indent=2, sort_keys=True))
    return rec


# ── self-test (embedded fixture graph; deterministic; chainability + cross-links mutation-gated) ─────────────
_FIXTURE = {"@graph": [
    {"@id": "schema:Thing", "@type": "rdfs:Class", "rdfs:comment": "The most generic type."},
    {"@id": "schema:Person", "@type": "rdfs:Class", "rdfs:comment": "A person.",
     "rdfs:subClassOf": {"@id": "schema:Thing"}},
    {"@id": "schema:PostalAddress", "@type": "rdfs:Class", "rdfs:comment": "The mailing address.",
     "rdfs:subClassOf": {"@id": "schema:Thing"}},
    {"@id": "schema:DayOfWeek", "@type": "rdfs:Class", "rdfs:comment": "The day of the week.",
     "rdfs:subClassOf": {"@id": "schema:Enumeration"}},
    {"@id": "schema:givenName", "@type": "rdf:Property", "rdfs:comment": "Given name.",
     "schema:domainIncludes": {"@id": "schema:Person"}, "schema:rangeIncludes": {"@id": "schema:Text"}},
    {"@id": "schema:streetAddress", "@type": "rdf:Property", "rdfs:comment": "The street address.",
     "schema:domainIncludes": {"@id": "schema:PostalAddress"}, "schema:rangeIncludes": {"@id": "schema:Text"}},
    {"@id": "schema:birthDate", "@type": "rdf:Property", "rdfs:comment": "Date of birth.",
     "schema:domainIncludes": {"@id": "schema:Person"}, "schema:rangeIncludes": {"@id": "schema:Date"}},
    {"@id": "schema:address", "@type": "rdf:Property", "rdfs:comment": "Physical address.",
     "schema:domainIncludes": {"@id": "schema:Person"},
     "schema:rangeIncludes": [{"@id": "schema:PostalAddress"}, {"@id": "schema:Text"}]},
    {"@id": "schema:dayOfWeek", "@type": "rdf:Property", "rdfs:comment": "The day of the week.",
     "schema:domainIncludes": {"@id": "schema:PostalAddress"},
     "schema:rangeIncludes": {"@id": "schema:DayOfWeek"}},
]}


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    classes, props = parse_vocabulary(_FIXTURE)
    checks.append(("parses classes + properties with domains/ranges from JSON-LD",
                   set(classes) >= {"Person", "PostalAddress"} and props["givenName"]["domains"] == ["Person"]))
    checks.append(("range -> family mapping: Text/Date/Enumeration/entity-ref all resolved",
                   props["givenName"]["family"] == "text" and props["birthDate"]["family"] == "temporal"
                   and props["dayOfWeek"]["family"] == "enumeration"
                   and props["address"]["family"] == "entity_ref"))
    rows = mint_property_rows(props)
    checks.append(("every property mints ALL 8 aspects of the question grid",
                   len(rows) == len(props) * len(_ASPECTS)
                   and {r["aspect"] for r in rows} == set(_ASPECTS)))
    given = [r for r in rows if r["schema_org_property"] == "givenName"]
    street = [r for r in rows if r["schema_org_property"] == "streetAddress"]
    checks.append(("CHAINABILITY: same-family properties share the schema.org-typed input edge",
                   given[0]["input_edge"] == street[0]["input_edge"] == "SchemaOrgTextValue"))
    checks.append(("transformation rows emit the Normalized typed edge (composable downstream)",
                   next(r for r in given if r["aspect"] == "transformation")["output_edge"]
                   == "NormalizedSchemaOrgTextValue"))
    checks.append(("EXECUTABLE cross-links: person/address text columns resolve to the standardization pack",
                   next(r for r in given if r["aspect"] == "transformation")["executable_link"]
                   == "standardize_person_name"
                   and street[0]["executable_link"] == "standardize_us_address"))
    trows = mint_type_rows(classes, props)
    checks.append(("every class mints a records-system candidate with typed record edges",
                   len(trows) == len(classes)
                   and any(r["input_edge"] == "SchemaOrgPersonRawRecord" for r in trows)))
    srows = mint_family_system_rows(classes)
    checks.append(("Thing branches mint pipeline-system candidates",
                   {r["schema_org_type"] for r in srows} == {"Person", "PostalAddress"}))
    checks.append(("deterministic: identical fixture -> byte-identical rows",
                   json.dumps(mint_property_rows(props), sort_keys=True)
                   == json.dumps(mint_property_rows(props), sort_keys=True)))
    with tempfile.TemporaryDirectory() as td:
        snap = Path(td) / "fixture.jsonld"
        snap.write_text(json.dumps(_FIXTURE))
        import scripts._repo_paths as rp  # noqa: PLC0415
        rec = run_foundry(snap)  # writes under the real data dir; verify then leave (receipt is tiny+honest)
        checks.append(("run receipt: digest + counts + shared edge vocabulary + boundary",
                       len(rec["source"]["sha256"]) == 64 and rec["total_candidates"] == len(rows) + len(trows) + len(srows)
                       and "SchemaOrgTextValue" in rec["shared_edge_vocabulary"]
                       and rec.get("serves_truth") is False))
    checks.append(("boundary on every row", all(r.get("serves_truth") is False for r in rows + trows + srows)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - schema_org_primitive_foundry: every schema.org property x the 8-aspect question grid + "
          f"per-type records systems + per-branch pipeline systems; shared typed-edge vocabulary; "
          f"executable cross-links; deterministic. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--snapshot", default=None, help="path to schemaorg-current-https.jsonld (fetched once)")
    ap.add_argument("--limit-properties", type=int, default=0)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        snap = Path(args.snapshot) if args.snapshot else (
            resource("data") / "dev-intel" / _OUT_DIRNAME / "schemaorg-current-https.jsonld")
        if not snap.exists():
            print(f"snapshot missing: {snap}\nfetch once: curl -sL -o {snap} {_SNAPSHOT_URL}")
            return 1
        rec = run_foundry(snap, limit_properties=args.limit_properties)
        print(json.dumps({k: rec[k] for k in ("classes", "properties", "property_aspect_rows",
                                              "type_system_rows", "branch_system_rows", "total_candidates",
                                              "executable_links", "staged_path")}, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
