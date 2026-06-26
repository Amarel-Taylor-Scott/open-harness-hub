#!/usr/bin/env python3
"""scripts.check_ingestion_contracts — proof (INGESTION CONTRACTS MODE): the seven ingestion contract schemas
exist, validate via the stdlib schema validator, each ships a valid example that PASSES and an invalid example
that FAILS, and SourceArtifact — the governance boundary — REQUIRES tenant_id/source_id/source_version/
source_handle/content_hash/scope/authority/artifact_type/created_at so no raw source can become an artifact
without full provenance/scope/authority. Cross-checks: the SourceArtifact example matches the shape the existing
SourceAdapter.normalize() seam already emits (artifact_type=source_record, tenant_id/scope/source_id/source_handle/
content_hash present). Deterministic, stdlib-only.

CLI: python3 scripts/check_ingestion_contracts.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.schema_validator import validate as _validate

_REPO = Path(__file__).resolve().parents[1]
_SCHEMA_DIR = _REPO / "schemas" / "ingestion"
_EX_DIR = _SCHEMA_DIR / "examples"

#: every ingestion contract schema this lane owns (filename stem under schemas/ingestion).
_SCHEMAS = ["SourceArtifact", "IngestionReceipt", "SyncState", "SyncCursor", "SourceHandle",
            "IngestionRun", "IngestionError"]
#: the governance fields SourceArtifact MUST require (no raw source becomes an artifact without these).
_SOURCE_ARTIFACT_REQUIRED = {"tenant_id", "source_id", "source_version", "source_handle", "content_hash",
                             "scope", "authority", "artifact_type", "created_at"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    schemas: dict[str, dict] = {}
    examples: dict[str, dict] = {}
    for stem in _SCHEMAS:
        sp = _SCHEMA_DIR / f"{stem}.schema.json"
        ep = _EX_DIR / f"{stem}.example.json"
        check(f"{stem} schema file exists", sp.is_file(), str(sp))
        check(f"{stem} example file exists", ep.is_file(), str(ep))
        if sp.is_file():
            schemas[stem] = json.loads(sp.read_text())
        if ep.is_file():
            examples[stem] = json.loads(ep.read_text())

    # every schema declares $id ingestion/<Stem>, type object, additionalProperties false, required + properties
    for stem, sc in schemas.items():
        check(f"{stem} $id is ingestion/{stem}", sc.get("$id") == f"ingestion/{stem}", str(sc.get("$id")))
        check(f"{stem} is an object with additionalProperties:false",
              sc.get("type") == "object" and sc.get("additionalProperties") is False)
        check(f"{stem} declares required + properties", bool(sc.get("required")) and bool(sc.get("properties")))
        # uses only stdlib-validator keywords (type/required/properties/enum/additionalProperties/items + $id/title/description)
        allowed = {"type", "required", "properties", "enum", "additionalProperties", "items", "$id", "title", "description"}

        def _keys_ok(node) -> bool:
            if not isinstance(node, dict):
                return True
            for k, v in node.items():
                if k in ("properties",) and isinstance(v, dict):
                    if not all(_keys_ok(sub) for sub in v.values()):
                        return False
                    continue
                if k == "items" and isinstance(v, dict):
                    if not _keys_ok(v):
                        return False
                    continue
                if k not in allowed:
                    return False
            return True
        check(f"{stem} uses only stdlib-validator keywords", _keys_ok(sc))

    # valid example passes, invalid example(s) fail
    for stem, ex in examples.items():
        sc = schemas[stem]
        valid = ex.get("valid")
        check(f"{stem} has a 'valid' example", valid is not None)
        if valid is not None:
            errs = _validate(valid, sc)
            check(f"{stem} valid example validates clean", errs == [], str(errs[:4]))
        invalids = [(k, v) for k, v in ex.items() if k.startswith("invalid")]
        check(f"{stem} ships at least one invalid example", len(invalids) >= 1)
        for k, v in invalids:
            errs = _validate(v, sc)
            check(f"{stem} {k} is correctly REJECTED", errs != [])

    # SourceArtifact governance: REQUIRES the full provenance/scope/authority field set
    sa = schemas.get("SourceArtifact", {})
    req = set(sa.get("required", []))
    check("SourceArtifact requires tenant/source/source_version/handle/content_hash/scope/authority/type/created_at",
          _SOURCE_ARTIFACT_REQUIRED <= req, str(sorted(_SOURCE_ARTIFACT_REQUIRED - req)))
    # each individually missing → rejected (proves each required field is load-bearing)
    base = examples.get("SourceArtifact", {}).get("valid", {})
    if base and sa:
        for f in sorted(_SOURCE_ARTIFACT_REQUIRED):
            broken = {k: v for k, v in base.items() if k != f}
            check(f"SourceArtifact rejects an artifact missing '{f}'", _validate(broken, sa) != [])
        # scope/authority are enum-bounded — a tenant_private scope is a real value; a bogus scope is rejected
        bad_scope = dict(base); bad_scope["scope"] = "world_readable"
        check("SourceArtifact rejects an out-of-enum scope", _validate(bad_scope, sa) != [])
        bad_auth = dict(base); bad_auth["authority"] = "vibes"
        check("SourceArtifact rejects an out-of-enum authority", _validate(bad_auth, sa) != [])

    # cross-check: the valid SourceArtifact example matches the shape normalize() already emits
    if base:
        check("SourceArtifact example is artifact_type=source_record (matches the normalize() seam)",
              base.get("artifact_type") == "source_record")
        check("SourceArtifact example carries tenant_id/scope/source_id/source_handle/content_hash",
              all(base.get(k) for k in ("tenant_id", "scope", "source_id", "source_handle", "content_hash")))

    print(f"\n{'PASS — check_ingestion_contracts: 7 ingestion schemas exist + validate; each has a passing valid example and a rejected invalid example; SourceArtifact requires the full tenant/source/scope/authority/handle/content_hash governance set (each field load-bearing); example matches the normalize() seam.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ingestion contract schemas are complete + governance-enforcing.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
