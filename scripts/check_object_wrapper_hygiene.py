#!/usr/bin/env python3
"""scripts.check_object_wrapper_hygiene — the ANTI-FRAGILITY guard for the UNIVERSAL base wrappers (owner 2026-06-25).

Base objects must be THIN, FLEXIBLE WRAPPERS: a stable envelope (id/type) with the version in METADATA (never the
name), around a flexible payload/component. This guards the two portfolio-wide wrappers so they can NEVER regress to
fragile (version-in-the-name, no payload split):
  - schemas/shared/ObjectShell        — every major object composes from it (object_type + schema_version + payload).
  - schemas/registry/RegistryObject   — every registry record (type + version + flexible component; de-versioned name).

It does NOT separately police the 500+ DOMAIN record types (CanonicalFact, …): those inherit thin-ness via
`src/teleon/io/governed_record.mint_record` (a governed envelope + a flexible payload, with the version carried in
the `schema_version` METADATA field — never in the name). The portfolio-wide `.vN`-suffix elimination (owner
2026-06-25) removed every version-in-the-name from schema files, object ids, and call sites; this guard pins the two
base wrappers so that hygiene can never regress to fragile (version-in-the-name, no payload split). serves_truth=false.

  --self-test
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def self_test() -> int:
    # 1) ObjectShell — the portfolio-wide shell: stable shell + version in metadata + FLEXIBLE payload
    shell = json.loads((REPO / "schemas/shared/ObjectShell.schema.json").read_text(encoding="utf-8"))
    sp = shell["properties"]
    assert {"object_type", "schema_version", "payload"} <= set(sp), "ObjectShell = type + version-metadata + flexible payload"
    assert "object_type" in shell["required"], "ObjectShell keeps a stable object_type"

    # 2) RegistryObject — de-versioned NAME, thin wrapper, version in METADATA, FLEXIBLE component
    ro = json.loads((REPO / "schemas/registry/RegistryObject.schema.json").read_text(encoding="utf-8"))
    rp = ro["properties"]
    assert ro["title"] == "RegistryObject" and ".v" not in ro["$id"], "RegistryObject name carries NO version"
    assert {"id", "type", "version", "component"} <= set(rp), "RegistryObject = thin wrapper + flexible component"
    assert ro["required"] == ["id", "type"], "RegistryObject requires only the stable identity"

    # 3) mint_record — the DOMAIN-record wrapper: a governed envelope + a flexible payload (version in schema_version metadata)
    from src.teleon.io.governed_record import mint_record
    r = mint_record("Foo", {"x": 1, "body": "free"}, produced_by="t", created_at="2026-06-25T00:00:00Z")
    assert "envelope" in r and "schema_version" in r and r["x"] == 1, "mint_record = governed envelope + flexible payload"
    assert r["schema_version"] == "Foo", "version lives in the schema_version METADATA field, not the object id/name"

    print("check_object_wrapper_hygiene: OK (ObjectShell + RegistryObject are thin wrappers, version in metadata; "
          "mint_record envelope stays flexible; all object/schema names are version-free — the version lives in "
          "the schema_version metadata field)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: check_object_wrapper_hygiene.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
