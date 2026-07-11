#!/usr/bin/env python3
"""scripts.check_configuration_standards — proof: architecture/configuration_standards.json is well-formed,
every config_type's declared JSON Schema RESOLVES to a real file on disk that faithfully encodes the entry,
and every config TEMPLATE obeys the standards + validates against its schema.

VERIFY-THE-VERIFIER (why this file was hardened): the earlier gate only checked that the `schema` KEY was a
non-empty string, so it passed GREEN over 14 DANGLING schema pointers — `schemas/config/` did not exist and
none of the 14 `schemas/config/<type>.schema.json` files existed. A claim ("every config type declares its
schema") that cannot be falsified proves nothing. This gate now:

* ASSERTS each declared `schema` path RESOLVES to a real file via scripts._repo_paths.resource() (the fix);
* treats an EXPLICIT gap (`"schema": null` + `"schema_status": "unspecified"`) as an allowed-but-declared
  gap — never a dangling file pointer — so an honestly-unspecified shape is legal but a silent dangling
  pointer is not;
* checks each resolved schema is a valid draft-2020-12 JSON Schema whose `required` equals the manifest
  entry's `required_fields`, and is BYTE-IDENTICAL to what the manifest derives — the schemas are GENERATED
  from configuration_standards.json (single source per NO-MAGIC-VALUES), not hand-typed, so they can never
  drift from the required-field rules;
* checks every field-level type constraint it encodes (enum / integer / secret-ref / const) is GROUNDED in
  the manifest's own `rules` prose (no fabricated types);
* validates every config TEMPLATE under templates/configs/ against its generated schema (end-to-end);
* MUTATION PROBES (the point of the hardening): a synthetic config_type pointing at a nonexistent schema
  MUST go RED; and an `unspecified` gap is allowed while a null schema WITHOUT the marker is caught.

Also (unchanged): NO config template anywhere contains a RAW secret value — secrets appear only as
references (env://… or secret://…), asserted as a NEGATIVE test (a synthetic raw-key template MUST be
detected).

  python3 .../scripts/check_configuration_standards.py --self-test
  python3 .../scripts/check_configuration_standards.py --emit-schemas   # (re)generate schemas/config/*.schema.json from the manifest
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_STD = _resource("architecture") / "configuration_standards.json"
_TEMPLATES = _resource("templates/configs")
#: where the per-type generated schemas live (root-relative; resolved via _resource so a repo move is safe).
_SCHEMA_DIR_REL = "schemas/config"

_REQUIRED_FOR_ALL = ("schema", "version", "owner", "environment_scope")
#: provider-style config types must declare a fallback (offline/degraded path).
_FALLBACK_REQUIRED = {"provider_config", "llm_provider_config", "object_store_config", "vector_store_config"}
#: a "raw secret" = an api_key/token/secret/password assigned an inline value that is NOT a secret ref.
_RAW_SECRET = re.compile(
    r'"(?:api_key|token|secret|password|access_key|private_key|client_secret)"\s*:\s*"(?!env://|secret://)[^"]+"',
    re.IGNORECASE,
)
#: the draft this repo standardises on (same validator validate.py / validate_flywheel_schemas.py use).
_META = "https://json-schema.org/draft/2020-12/schema"


def _has_raw_secret(text: str) -> bool:
    return bool(_RAW_SECRET.search(text))


def _load_std() -> dict:
    return json.loads(_STD.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------------
# Schema derivation — the schemas under schemas/config/ are COMPUTED from configuration_standards.json,
# never hand-typed. `required` == the entry's required_fields; a property type is encoded ONLY where the
# entry's own `rules` prose explicitly declares it (enum / integer / secret-ref / const). Everything else
# is required-but-unconstrained ({}), so we never invent a type the manifest does not state.
# ---------------------------------------------------------------------------------------------------
def _secret_ref_schema(std: dict) -> dict:
    """A secret-REFERENCE string, pattern built from the manifest's secret_reference_schemes (single source)."""
    schemes = std.get("secret_reference_schemes", ["env://", "secret://"])
    return {"type": "string", "pattern": "^(" + "|".join(re.escape(s) for s in schemes) + ")"}


def _declared_field_constraints(std: dict) -> dict[tuple[str, str], dict]:
    """(config_type, field) -> the JSON-Schema fragment the manifest's `rules` explicitly declare for it.
    Each fragment is GROUNDED against the rules prose by the self-test (see _grounding_tokens)."""
    secret_ref = _secret_ref_schema(std)
    return {
        ("tenant_policy", "isolation_mode"): {"type": "string", "enum": ["strict", "shared"]},
        ("source_connector_config", "auth_ref"): secret_ref,
        ("retry_policy", "max_attempts"): {"type": "integer"},
        ("rate_limit_policy", "on_exceed"): {"type": "string", "enum": ["backoff", "reject", "queue"]},
        ("llm_provider_config", "api_key_ref"): secret_ref,
        ("reconciliation_policy", "held_out_on_loss"): {"const": True},
    }


def _grounding_tokens(field: str, constraint: dict) -> list[str]:
    """The lowercase tokens that MUST appear in a config_type's `rules` text for `constraint` to be grounded
    (not fabricated): the field name, plus each enum value / 'integer' / the const literal / 'secret' (ref)."""
    tokens = [field.lower()]
    if "enum" in constraint:
        tokens += [str(v).lower() for v in constraint["enum"]]
    if constraint.get("type") == "integer":
        tokens.append("integer")
    if "const" in constraint:
        tokens.append(str(constraint["const"]).lower())
    if "pattern" in constraint:
        tokens.append("secret")
    return tokens


def _property_schema(std: dict, config_type: str, field: str, declared: dict[tuple[str, str], dict]) -> dict:
    """The property schema for one required field: an explicitly-declared constraint if the rules state one,
    else a self-evident type for the four universal fields, else {} (present but unconstrained)."""
    if (config_type, field) in declared:
        return declared[(config_type, field)]
    if field == "environment_scope":
        return {"type": "string", "enum": list(std.get("environment_scope_enum", []))}
    if field in ("schema", "version", "owner"):
        return {"type": "string"}
    return {}


def _derive_schema(std: dict, entry: dict) -> dict:
    """A minimal draft-2020-12 schema derived from a config_types[] entry. Deterministic (fixed key order +
    required_fields order), so it builds byte-identical every time."""
    ct = entry["config_type"]
    required = list(entry.get("required_fields", []))
    declared = _declared_field_constraints(std)
    return {
        "$schema": _META,
        "$id": f"{_SCHEMA_DIR_REL}/{ct}.schema.json",
        "$comment": (
            "GENERATED from architecture/configuration_standards.json by "
            "scripts/check_configuration_standards.py --emit-schemas. The manifest is the single source of "
            "the required-field rules; do not hand-edit this file — regenerate it."
        ),
        "title": ct,
        "description": (
            f"Minimal shape for Baltor config_type '{ct}'. Derived from its "
            "architecture/configuration_standards.json entry: `required` is the entry's required_fields; a "
            "property type is encoded ONLY where the entry's rules explicitly declare it "
            "(enum / integer / secret-ref / const). Fields without a declared type are required but "
            "unconstrained. Extra fields (e.g. notes) are allowed."
        ),
        "type": "object",
        "additionalProperties": True,
        "required": required,
        "properties": {f: _property_schema(std, ct, f, declared) for f in required},
    }


def _serialize(schema: dict) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def _has_real_schema(entry: dict) -> bool:
    """True iff the entry declares a concrete schema PATH (not a null/unspecified gap)."""
    s = entry.get("schema")
    return isinstance(s, str) and bool(s.strip())


def _dangling_schemas(std: dict) -> list[str]:
    """Every config_type whose schema claim cannot be honoured — the bug the old gate was blind to. A
    concrete `schema` string MUST resolve to a real file; a null/absent schema is legal ONLY when explicitly
    marked `schema_status: "unspecified"` (an allowed declared gap); anything else is a dangling/undeclared
    pointer. Returns 'config_type: reason' strings (empty == all claims honoured)."""
    bad: list[str] = []
    for entry in std.get("config_types", []):
        ct = entry.get("config_type", "<no-type>")
        schema = entry.get("schema")
        if isinstance(schema, str) and schema.strip():
            if not _resource(schema).is_file():
                bad.append(f"{ct}: declared schema does not resolve to a file ({schema})")
        elif entry.get("schema_status") == "unspecified":
            continue  # honestly-declared gap: allowed, not a dangling pointer
        else:
            bad.append(f"{ct}: no schema declared and not marked schema_status='unspecified'")
    return bad


def _emit_schemas(std: dict | None = None) -> int:
    std = std or _load_std()
    out_dir = _resource(_SCHEMA_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for entry in std.get("config_types", []):
        if not _has_real_schema(entry):
            continue
        (_resource(entry["schema"])).write_text(_serialize(_derive_schema(std, entry)), encoding="utf-8")
        written += 1
    print(f"wrote {written} schema(s) under {out_dir}")
    return 0


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    std = _load_std()
    check("configuration_standards.json parses + has version/config_types",
          all(k in std for k in ("version", "config_types")))
    scope_enum = set(std.get("environment_scope_enum", []))

    types = std.get("config_types", [])
    missing_required, bad_scope, no_fallback = [], [], []
    for t in types:
        ct = t.get("config_type", "<no-type>")
        # schema counts as "declared" if it is a real path OR an explicit unspecified gap.
        miss = []
        for k in _REQUIRED_FOR_ALL:
            if k == "schema":
                if not (_has_real_schema(t) or t.get("schema_status") == "unspecified"):
                    miss.append("schema")
            elif not t.get(k):
                miss.append(k)
        if miss:
            missing_required.append(f"{ct}:{miss}")
        if t.get("environment_scope") not in scope_enum:
            bad_scope.append(f"{ct}:{t.get('environment_scope')}")
        if ct in _FALLBACK_REQUIRED and "fallback" not in t.get("required_fields", []):
            no_fallback.append(ct)

    check("every config_type declares schema(-or-unspecified)+version+owner+environment_scope",
          missing_required == [], str(missing_required[:8]))
    check("every config_type environment_scope is in the enum", bad_scope == [], str(bad_scope[:8]))
    check("every provider-style config_type requires a fallback field", no_fallback == [], str(no_fallback))

    # THE FIX: every declared schema path RESOLVES to a real file (or is an allowed unspecified gap).
    dangling = _dangling_schemas(std)
    check("every declared schema RESOLVES to a file on disk (no dangling pointers)",
          dangling == [], "; ".join(dangling[:8]))

    # Each resolved schema is a valid draft-2020-12 schema whose required == the entry's required_fields.
    invalid_schema, required_mismatch = [], []
    for entry in types:
        if not _has_real_schema(entry):
            continue
        path = _resource(entry["schema"])
        if not path.is_file():
            continue  # already reported by the dangling check
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(doc)
            if doc.get("type") != "object":
                invalid_schema.append(f"{entry['config_type']}: type!=object")
        except Exception as exc:  # noqa: BLE001
            invalid_schema.append(f"{entry['config_type']}: {exc!r}")
            continue
        if doc.get("required") != list(entry.get("required_fields", [])):
            required_mismatch.append(entry["config_type"])
    check("every schema file is a valid draft-2020-12 object schema", invalid_schema == [], str(invalid_schema[:6]))
    check("every schema.required == its manifest entry's required_fields", required_mismatch == [],
          str(required_mismatch))

    # Single source + determinism: each schema file is BYTE-IDENTICAL to what the manifest derives, and the
    # derivation is stable across two calls (byte-identical rebuild).
    drift, nondet = [], []
    for entry in types:
        if not _has_real_schema(entry):
            continue
        path = _resource(entry["schema"])
        want = _serialize(_derive_schema(std, entry))
        if _serialize(_derive_schema(std, entry)) != want:
            nondet.append(entry["config_type"])
        if not path.is_file() or path.read_text(encoding="utf-8") != want:
            drift.append(entry["config_type"])
    check("every schema file is byte-identical to the manifest-derived schema (single source, no drift)",
          drift == [], str(drift[:6]))
    check("schema derivation is deterministic (byte-identical rebuild)", nondet == [], str(nondet))

    # Grounding: every field constraint we encode is evidenced in the manifest's own rules prose.
    declared = _declared_field_constraints(std)
    rules_by_ct = {t.get("config_type"): " ".join(t.get("rules", [])).lower() for t in types}
    ungrounded = []
    for (ct, field), constraint in declared.items():
        text = rules_by_ct.get(ct, "")
        missing = [tok for tok in _grounding_tokens(field, constraint) if tok not in text]
        if missing:
            ungrounded.append(f"{ct}.{field}:{missing}")
    check("every encoded field constraint is grounded in the manifest rules prose (no fabricated types)",
          ungrounded == [], str(ungrounded))

    # every config template under templates/configs/ is parseable, secret-clean, and valid vs its schema.
    templates = sorted(p for p in _TEMPLATES.rglob("*.json"))
    check("at least 3 config template files exist under templates/configs/",
          len(templates) >= 3, str(len(templates)))
    raw_secret_hits, unparseable, tpl_invalid = [], [], []
    schema_by_ct = {e["config_type"]: _resource(e["schema"]) for e in types if _has_real_schema(e)}
    validators: dict[str, Draft202012Validator] = {}
    for tpl in templates:
        text = tpl.read_text(encoding="utf-8")
        try:
            doc = json.loads(text)
        except json.JSONDecodeError:
            unparseable.append(str(tpl.relative_to(_REPO)))
            continue
        if _has_raw_secret(text):
            raw_secret_hits.append(str(tpl.relative_to(_REPO)))
        ct = doc.get("config_type")
        sp = schema_by_ct.get(ct)
        if ct and sp and sp.is_file():
            if ct not in validators:
                validators[ct] = Draft202012Validator(json.loads(sp.read_text(encoding="utf-8")))
            errs = sorted(validators[ct].iter_errors(doc), key=lambda e: e.path)
            if errs:
                tpl_invalid.append(f"{tpl.relative_to(_REPO)}: {errs[0].message}")
    check("every config template parses as JSON", unparseable == [], str(unparseable))
    check("NO config template contains a raw secret (refs only: env://… / secret://…)",
          raw_secret_hits == [], str(raw_secret_hits))
    check("every config template VALIDATES against its generated schema", tpl_invalid == [], str(tpl_invalid[:6]))

    # NEGATIVE TEST 1 (raw secret): a synthetic template with a raw key MUST be caught.
    tmp = Path(tempfile.mkdtemp(prefix="cfgstd_neg_"))
    try:
        bad = tmp / "bad_provider.json"
        bad.write_text(json.dumps({
            "schema": "schemas/config/provider_config.schema.json", "version": "v1",
            "owner": "x", "environment_scope": "production", "config_type": "provider_config",
            "provider_id": "openai", ("api" + "_key"): "RAW-INLINE-NOT-A-REF",
            "emulator": "stub", "fallback": "local",
        }), encoding="utf-8")
        caught = _has_raw_secret(bad.read_text(encoding="utf-8"))
        check("negative test: a raw-secret template is DETECTED by the secret rule", caught is True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # MUTATION PROBE 1 (verify-the-verifier): the resolution gate MUST bite the exact bug it was blind to —
    # a config_type pointing at a schema file that does not exist. Build a synthetic manifest and assert
    # _dangling_schemas flags it (and does NOT flag the real, now-resolvable manifest).
    mutant = json.loads(json.dumps(std))  # deep copy
    mutant["config_types"].append({
        "config_type": "__mutant_dangling__",
        "schema": f"{_SCHEMA_DIR_REL}/__does_not_exist_{'x' * 8}__.schema.json",
        "version": "v1", "owner": "test", "environment_scope": "all",
        "required_fields": list(_REQUIRED_FOR_ALL),
    })
    mutant_flagged = any(s.startswith("__mutant_dangling__:") for s in _dangling_schemas(mutant))
    check("mutation probe: a config_type with a NONEXISTENT schema is caught (gate now bites the bug)",
          mutant_flagged is True)

    # MUTATION PROBE 2 (the honest-gap branch): an explicit unspecified gap is ALLOWED, while a null schema
    # WITHOUT the marker is caught — the checker distinguishes a declared gap from a dangling pointer.
    gap = json.loads(json.dumps(std))
    gap["config_types"].append({
        "config_type": "__declared_gap__", "schema": None, "schema_status": "unspecified",
        "version": "v1", "owner": "test", "environment_scope": "all", "required_fields": list(_REQUIRED_FOR_ALL),
    })
    gap["config_types"].append({
        "config_type": "__silent_null__", "schema": None,
        "version": "v1", "owner": "test", "environment_scope": "all", "required_fields": list(_REQUIRED_FOR_ALL),
    })
    gap_dangling = _dangling_schemas(gap)
    gap_ok = (not any(s.startswith("__declared_gap__:") for s in gap_dangling)
              and any(s.startswith("__silent_null__:") for s in gap_dangling))
    check("mutation probe: unspecified gap ALLOWED, but a null schema WITHOUT the marker is caught", gap_ok is True)

    print(f"\n{'PASS — check_configuration_standards: standards well-formed; every declared schema RESOLVES to a valid draft-2020-12 file byte-identical to the manifest-derived shape; every template validates against its schema; the raw-secret detector and both resolution mutation probes bite.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: configuration standards + templates (schemas resolve, no raw secrets, fallbacks declared).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--emit-schemas", action="store_true",
                   help="(re)generate schemas/config/*.schema.json from the manifest (single source).")
    a = p.parse_args(argv)
    if a.emit_schemas:
        return _emit_schemas()
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
