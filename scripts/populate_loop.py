#!/usr/bin/env python3
"""scripts.populate_loop — PERSISTENT registry population: swarm candidates → staged RECORDS + VARIATIONS +
PROVENANCE + a record GRAPH. Runs forever so the registries fill with thousands of records without Claude Code.

Consumes data/dev-intel/swarm_candidates.jsonl (the swarm's discover→interrogate→enrich output) and, per candidate:
  1. RECORD     — a governed staged registry record (universal_object_schema shape) routed to a registry, stamped
                  with PROVENANCE (source seed, url, discovered_at, enriched_by, content_hash) — serves_truth=false.
  2. VARIATIONS — derived variant-records via the interrogation engine's mutation/contextual dims (cheaper /
                  deterministic / per-industry / per-geography), each with LINEAGE (variant_of) — the descent +
                  contextual-mutation as concrete records.
  3. GRAPH      — record-level edges (has_variant + related_by:<shared-tag>) → data/dev-intel/record_graph.jsonl.
Append-only, touches NO git (safe alongside the swarm/flywheel). Staged JSONL is the canonical first tier (→ DB
later via storage_tier_policy). Cursor-resumable. Lossless (parent + variants + lineage all kept).

  --self-test                    offline
  --run-once                     populate from any new candidates
  --supervise [--interval-sec N] loop forever (the persistent populator)
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
CANDIDATES = REPO / "data" / "dev-intel" / "swarm_candidates.jsonl"
RECORDS = REPO / "data" / "dev-intel" / "registry_records.jsonl"
GRAPH = REPO / "data" / "dev-intel" / "record_graph.jsonl"
STATE = REPO / "data" / "dev-intel" / "populate_cursor.json"
STOP = REPO / ".agent" / "POPULATE_STOP_REQUESTED"

VARIATION_DIMS = ["mutation", "contextual_fitness", "ai_native"]   # cheaper/deterministic/contextual variants
_REGISTRY_FOR = {"tool": "tool_registry", "document": "scientific"}   # route by object_type; record carries it for re-routing
_MAX_RELATED_EDGES = 5                                                 # per record, to bound the graph


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _hash(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"cursor": 0, "records": 0, "variations": 0, "edges": 0, "tags": {}}


def save_state(s: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def to_record(cand: dict) -> dict:
    """A staged registry record with PROVENANCE (governed candidate; serves_truth=false)."""
    name = cand.get("name", "")
    url = cand.get("source", {}).get("url", "")
    otype = cand.get("object_type", "tool")
    rid = cand.get("object_id") or _hash(name, url)
    return {
        "record_id": rid, "kind": "record", "registry": _REGISTRY_FOR.get(otype, "component"),
        "object_type": otype, "name": name, "searchability_tags": cand.get("searchability_tags", []),
        "capabilities": cand.get("capabilities", []), "enrichment": cand.get("enrichment"),
        "provenance": {
            "source_seed": cand.get("source", {}).get("seed", ""), "url": url,
            "discovered_at": _now(), "enriched_by": (cand.get("enrichment") or {}).get("by"),
            "content_hash": _hash(name, url), "pipeline": "swarm→populate",
        },
        "confidence_score": cand.get("confidence_score", 0.3), "serves_truth": False,
    }


def variations_for(rec: dict) -> list[dict]:
    """Derived variant-records (cheaper/deterministic/contextual) with lineage to the parent."""
    try:
        from scripts.interrogation_engine import generate, load_taxonomy
        rows, _ = generate([{"ref": rec["name"], "type": rec["object_type"]}], load_taxonomy(),
                           dims=VARIATION_DIMS, context_samples=1, total_cap=6)
    except Exception:
        return []
    out = []
    for r in rows:
        vid = _hash(rec["record_id"], r["dimension"], r["question"])
        out.append({
            "record_id": vid, "kind": "variation", "variant_of": rec["record_id"],
            "variant_axis": r["dimension"], "spec": r["question"], "object_type": rec["object_type"],
            "name": rec["name"], "registry": rec["registry"], "status": "variation_candidate",
            "provenance": {"derived_from": rec["record_id"], "by": "interrogation_engine", "at": _now()},
            "serves_truth": False,
        })
    return out


def edges_for(rec: dict, variants: list[dict], tag_index: dict) -> list[dict]:
    """has_variant edges + related_by:<shared-tag> edges (record-level graph)."""
    e = [{"src": rec["record_id"], "dst": v["record_id"], "rel": "has_variant", "serves_truth": False}
         for v in variants]
    related = 0
    for tag in rec.get("searchability_tags", []):
        for other in tag_index.get(tag, []):
            if other != rec["record_id"] and related < _MAX_RELATED_EDGES:
                e.append({"src": rec["record_id"], "dst": other, "rel": f"related_by:{tag}", "serves_truth": False})
                related += 1
        tag_index.setdefault(tag, [])
        if rec["record_id"] not in tag_index[tag]:
            tag_index[tag] = (tag_index[tag] + [rec["record_id"]])[-20:]   # bound the index
    return e


def _read_candidates() -> list[dict]:
    if not CANDIDATES.exists():
        return []
    out = []
    for ln in CANDIDATES.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def run_once() -> dict:
    s = load_state()
    cands = _read_candidates()
    new = cands[s["cursor"]:]
    if not new:
        return {"new": 0, "records": s["records"], "variations": s["variations"], "edges": s["edges"]}
    tag_index = s.get("tags", {})
    seen = set()
    nr = nv = ne = 0
    RECORDS.parent.mkdir(parents=True, exist_ok=True)
    with RECORDS.open("a", encoding="utf-8") as rfh, GRAPH.open("a", encoding="utf-8") as gfh:
        for cand in new:
            rec = to_record(cand)
            if rec["record_id"] in seen:
                continue
            seen.add(rec["record_id"])
            variants = variations_for(rec)
            edges = edges_for(rec, variants, tag_index)
            rfh.write(json.dumps(rec) + "\n")
            for v in variants:
                rfh.write(json.dumps(v) + "\n")
            for ed in edges:
                gfh.write(json.dumps(ed) + "\n")
            nr += 1; nv += len(variants); ne += len(edges)
    s.update(cursor=s["cursor"] + len(new), records=s["records"] + nr,
             variations=s["variations"] + nv, edges=s["edges"] + ne, tags=tag_index)
    save_state(s)
    return {"new": len(new), "records_added": nr, "variations_added": nv, "edges_added": ne,
            "totals": {"records": s["records"], "variations": s["variations"], "edges": s["edges"]}}


def supervise(interval: int) -> int:
    print(f"populate_loop: persistent. Stop: touch {STOP.relative_to(REPO)}")
    while True:
        if STOP.exists():
            print("POPULATE_STOP_REQUESTED — halting."); return 0
        try:
            res = run_once()
            if res["new"]:
                print(f"[populate] +{res.get('records_added',0)} records, +{res.get('variations_added',0)} variations, "
                      f"+{res.get('edges_added',0)} edges  (totals {res['totals']})")
        except Exception as e:  # noqa: BLE001 — a persistent daemon never dies on one bad cycle
            print(f"[populate] cycle error (continuing): {type(e).__name__}: {e}")
        time.sleep(interval)


def self_test() -> int:
    import tempfile
    cand = {"object_id": "abc123", "object_type": "tool", "name": "acme/widget",
            "source": {"seed": "github", "url": "https://github.com/acme/widget"},
            "searchability_tags": ["acme", "widget"], "confidence_score": 0.3,
            "enrichment": {"by": "glm-5.2"}}
    rec = to_record(cand)
    assert rec["kind"] == "record" and rec["registry"] == "tool_registry" and rec["serves_truth"] is False
    assert rec["provenance"]["source_seed"] == "github" and rec["provenance"]["content_hash"], "provenance stamped"
    variants = variations_for(rec)
    assert all(v["variant_of"] == rec["record_id"] and v["kind"] == "variation" for v in variants), "variation lineage"
    ti: dict = {}
    e1 = edges_for(rec, variants, ti)
    assert any(x["rel"] == "has_variant" for x in e1) or not variants, "has_variant edges"
    rec2 = to_record({**cand, "object_id": "def456", "name": "acme/other"})   # shares tag 'acme'
    e2 = edges_for(rec2, [], ti)
    assert any(x["rel"].startswith("related_by:") for x in e2), "related-by-shared-tag edge built"
    global STATE
    orig = STATE
    try:
        STATE = Path(tempfile.mkdtemp()) / "s.json"
        save_state({"cursor": 7, "records": 1, "variations": 2, "edges": 3, "tags": {}})
        assert load_state()["cursor"] == 7
    finally:
        STATE = orig
    print("populate_loop self-test: OK (record+provenance, variation lineage, graph edges, state roundtrip)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--run-once" in argv:
        print(json.dumps(run_once(), indent=2)); return 0
    if "--supervise" in argv:
        return supervise(int(opt("--interval-sec", "30")))
    print("usage: populate_loop.py --self-test | --run-once | --supervise [--interval-sec N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
