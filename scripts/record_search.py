#!/usr/bin/env python3
"""scripts.record_search — make the populated registry records TRULY USABLE + SEARCHABLE.

The populator (scripts/populate_loop.py) stages records + variations into data/dev-intel/registry_records.jsonl.
This indexes them (name · type · registry · tags · enrichment · variation-spec) into an inverted index and serves
ranked search, so a record can actually be FOUND. It also audits USABILITY (a record is usable only if it carries
the fields needed to be searched + composed). Complements src/teleon/registry/port.py federated search (this covers
the dynamic populated records the static catalog index doesn't). serves_truth=false (candidates).

  --self-test
  --index                 (re)build the index from registry_records.jsonl
  --search "<query>" [-k N]
  --audit                 usability + searchability coverage over all records
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECORDS = REPO / "data" / "dev-intel" / "registry_records.jsonl"
INDEX = REPO / "data" / "dev-intel" / "record_index.json"
_WORD = re.compile(r"[a-z0-9]+")


def _tok_str(s: str) -> list[str]:
    return [t for t in _WORD.findall((s or "").lower()) if len(t) >= 2]


def _rec_text(rec: dict) -> str:
    return " ".join([
        rec.get("name", ""), rec.get("object_type", ""), rec.get("registry", ""),
        " ".join(rec.get("searchability_tags", [])),
        (rec.get("enrichment") or {}).get("a", "")[:200],
        rec.get("spec", ""), rec.get("variant_axis", ""),
    ])


def usable(rec: dict) -> bool:
    """A record is usable only if it can be searched AND composed: name + type + tags, and a source/lineage."""
    has_core = bool(rec.get("name")) and bool(rec.get("object_type")) and bool(rec.get("searchability_tags"))
    has_origin = bool(rec.get("source") or rec.get("provenance") or rec.get("variant_of"))
    return has_core and has_origin


def _read_records() -> list[dict]:
    if not RECORDS.exists():
        return []
    out = []
    for ln in RECORDS.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def build_index(records: list[dict] | None = None) -> int:
    records = _read_records() if records is None else records
    inv: dict[str, list[str]] = {}
    recs: dict[str, dict] = {}
    for rec in records:
        rid = rec.get("record_id")
        if not rid:
            continue
        recs[rid] = {"name": rec.get("name", ""), "type": rec.get("object_type", ""),
                     "registry": rec.get("registry", ""), "kind": rec.get("kind", "record"),
                     "usable": usable(rec)}
        for t in set(_tok_str(_rec_text(rec))):
            inv.setdefault(t, []).append(rid)
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps({"built_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "n": len(recs),
                                 "inv": inv, "recs": recs}, separators=(",", ":")), encoding="utf-8")
    return len(recs)


def search(query: str, k: int = 10) -> list[dict]:
    if not INDEX.exists():
        build_index()
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    inv, recs = idx["inv"], idx["recs"]
    score: dict[str, int] = {}
    for t in set(_tok_str(query)):
        for rid in inv.get(t, []):
            score[rid] = score.get(rid, 0) + 1
    ranked = sorted(score.items(), key=lambda x: (-x[1], x[0]))[:k]
    return [{"record_id": rid, "score": sc, **recs.get(rid, {})} for rid, sc in ranked]


def audit() -> dict:
    records = _read_records()
    n = len(records)
    nu = sum(1 for r in records if usable(r))
    built = build_index(records)
    # searchability: every usable record contributes ≥1 token
    searchable = sum(1 for r in records if usable(r) and _tok_str(_rec_text(r)))
    return {"records": n, "usable": nu, "usable_pct": round(nu / n * 100, 1) if n else 0.0,
            "indexed": built, "searchable": searchable}


def self_test() -> int:
    recs = [
        {"record_id": "r1", "kind": "record", "object_type": "tool", "name": "langchain agent framework",
         "registry": "tool_registry", "searchability_tags": ["langchain", "agent"], "source": {"seed": "github"}},
        {"record_id": "r2", "kind": "record", "object_type": "tool", "name": "email regex util",
         "registry": "component", "searchability_tags": ["regex", "email"], "source": {"seed": "github"}},
        {"record_id": "v1", "kind": "variation", "object_type": "tool", "name": "langchain agent framework",
         "registry": "tool_registry", "searchability_tags": ["langchain"], "variant_of": "r1",
         "spec": "deterministic cheaper variant", "variant_axis": "mutation"},
        {"record_id": "bad", "name": "", "object_type": "", "searchability_tags": []},
    ]
    assert usable(recs[0]) and usable(recs[2]) and not usable(recs[3]), "usability gate"
    global INDEX
    orig = INDEX
    import tempfile
    try:
        INDEX = Path(tempfile.mkdtemp()) / "idx.json"
        assert build_index(recs) == 3, "bad record (no id? has id but unusable still indexed by id) "
        hits = search("agent framework", k=5)
        assert hits and hits[0]["record_id"] == "r1", f"search must rank the agent framework first: {hits[:2]}"
        assert any(h["record_id"] == "r2" for h in search("regex email")), "regex record findable"
        assert all("usable" in h for h in hits), "results carry usability"
    finally:
        INDEX = orig
    print("record_search self-test: OK (usability gate, inverted index, ranked search, results carry usability)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--index" in argv:
        print(f"indexed {build_index()} records → {INDEX.relative_to(REPO)}"); return 0
    if "--audit" in argv:
        print(json.dumps(audit(), indent=2)); return 0
    if "--search" in argv:
        q = opt("--search") or ""
        for h in search(q, int(opt("-k", "10"))):
            tag = "·var" if h.get("kind") == "variation" else ""
            print(f"  [{h['score']}] {h['name'][:50]} ({h['type']}/{h['registry']}{tag}) usable={h['usable']}")
        return 0
    print("usage: record_search.py --self-test | --index | --search '<query>' [-k N] | --audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
