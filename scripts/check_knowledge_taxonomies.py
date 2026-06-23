"""check_knowledge_taxonomies — proof for architecture/knowledge_taxonomies.json (backs registry #81).

POINTER-ONLY catalog of standard knowledge/subject/news classification systems (Dewey/LCC/Wikidata/MeSH/ACM/
JEL/EuroVoc/IPTC/O*NET/Schema.org). Enforces required fields; scope in the legend; machine_readable is a bool;
pointer-only (short ref, no bulk data); coverage (>=10 taxonomies across >=6 scopes incl. news_media);
serves_truth=false. Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOC = _REPO / "architecture" / "knowledge_taxonomies.json"
_REQ = ("id", "name", "scope", "authority", "machine_readable", "access", "ref")
_ACCESS = {"free", "key", "paid"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = json.loads(_DOC.read_text())
    taxos = doc.get("taxonomies", [])
    legend = set(doc.get("scope_legend", {}))
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
    ck(">=10 taxonomies", len(taxos) >= 10, str(len(taxos)))
    ck("scope_legend defined", len(legend) >= 6, str(sorted(legend)))

    ids: set[str] = set()
    scopes: set[str] = set()
    for t in taxos:
        tid = t.get("id", "?")
        for f in _REQ:
            ck(f"{tid}: has '{f}'", f in t and t.get(f) is not None and t.get(f) != "")
        ck(f"{tid}: unique id", tid not in ids, "duplicate")
        ids.add(tid)
        scopes.add(t.get("scope", ""))
        ck(f"{tid}: scope in legend", t.get("scope") in legend, str(t.get("scope")))
        ck(f"{tid}: access in {_ACCESS}", t.get("access") in _ACCESS, str(t.get("access")))
        ck(f"{tid}: machine_readable is bool", isinstance(t.get("machine_readable"), bool))
        ck(f"{tid}: ref is a short pointer string", isinstance(t.get("ref"), str) and len(t.get("ref", "")) < 80)
        ck(f"{tid}: stores no bulk data (pointer-only)", not any(isinstance(v, list) and len(v) > 3 for v in t.values()))

    ck(">=6 scopes", len(scopes) >= 6, str(sorted(scopes)))
    ck("covers news_media", "news_media" in scopes)

    if fails:
        print(f"\nFAIL - check_knowledge_taxonomies: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_knowledge_taxonomies: {len(taxos)} pointer-only knowledge/subject/news taxonomies across "
          f"{len(scopes)} scopes ({sorted(scopes)}); {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
