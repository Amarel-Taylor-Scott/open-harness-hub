"""check_semantic_field_ontology — proof for the canonical field ontology (backs registry #20 semantic_ontology).

Verifies the catalog is well-formed + UNAMBIGUOUS (no surface name normalizes to two canonicals) and that the
resolver canonicalizes real-world surface names (Invoice Number / bill_number / NPI / E-Mail) correctly.

Deterministic, offline, stdlib only.
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

from src.teleon.resolution.field_ontology import canonicalize, normalize  # noqa: E402

_DOC = _resource("architecture") / "semantic_field_ontology.json"
_REQ = ("canonical", "domain", "type", "aliases")
# (surface name, expected canonical) — real-world spellings the resolver must collapse.
_CASES = [
    ("Invoice Number", "invoice_identifier"),
    ("bill_number", "invoice_identifier"),
    ("Amount Due", "total_amount"),
    ("NPI", "national_provider_identifier"),
    ("E-Mail", "email_address"),
    ("Zip Code", "postal_code"),
    ("company name", "organization_name"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = json.loads(_DOC.read_text())
    fields = doc.get("fields", [])
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck("serves_truth is false", doc.get("serves_truth") is False)
    ck(">=15 canonical fields", len(fields) >= 15, str(len(fields)))

    canon_ids: set[str] = set()
    surface_to_canon: dict[str, str] = {}
    for f in fields:
        cid = f.get("canonical", "?")
        for r in _REQ:
            ck(f"{cid}: has '{r}'", bool(f.get(r)))
        ck(f"{cid}: aliases is a non-empty list", isinstance(f.get("aliases"), list) and len(f.get("aliases", [])) >= 1)
        ck(f"{cid}: unique canonical", cid not in canon_ids, "duplicate")
        canon_ids.add(cid)
        # ambiguity guard: no normalized surface may map to two different canonicals
        for surface in [cid, *f.get("aliases", [])]:
            n = normalize(surface)
            if n in surface_to_canon and surface_to_canon[n] != cid:
                ck(f"alias '{surface}' is unambiguous", False, f"maps to {surface_to_canon[n]} AND {cid}")
            surface_to_canon[n] = cid

    # resolver behaviour on real-world spellings
    for surface, expected in _CASES:
        ck(f"canonicalize('{surface}') == {expected}", canonicalize(surface) == expected, str(canonicalize(surface)))
    ck("canonicalize(unknown) is None (escalate to LLM)", canonicalize("totally_novel_field_xyz") is None)

    if fails:
        print(f"\nFAIL - check_semantic_field_ontology: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_semantic_field_ontology: {len(fields)} canonical fields, {len(surface_to_canon)} surface "
          f"names, all unambiguous; resolver collapses real-world spellings; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
