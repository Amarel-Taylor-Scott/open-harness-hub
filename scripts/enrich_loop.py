#!/usr/bin/env python3
"""scripts.enrich_loop — CHECKLIST-driven record enrichment: DETERMINISTIC floor + LLM generation. Persistent.

Fills the missing universal_object_schema fields on staged records, deterministic-FIRST (cheap, reliable) and LLM
where generation is needed (meta descriptions, use-cases, alternatives). For every record it runs a CHECKLIST:
  * DETERMINISTIC (always, reuses src/teleon/registry/enrich.py): keywords · labels · meta_description · use_cases.
  * LLM (bounded per cycle, base records only): rich meta_description · specific use_cases · cheaper/deterministic
    alternatives — via GLM 5.2 (honest-skip on 429/no-key).
Every filled field carries PROVENANCE (deterministic | glm-5.2) and the checklist status. Lossless + race-safe:
writes a SEPARATE data/dev-intel/record_enrichments.jsonl (never rewrites registry_records.jsonl that populate
appends to); hybrid_search merges it at index time. serves_truth=false (derived metadata, never a truth claim).

  --self-test                    offline (no LLM/network)
  --run-once
  --supervise [--interval-sec N] [--llm-per-cycle N]
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
RECORDS = REPO / "data" / "dev-intel" / "registry_records.jsonl"
ENRICH = REPO / "data" / "dev-intel" / "record_enrichments.jsonl"
STATE = REPO / "data" / "dev-intel" / "enrich_cursor.json"
STOP = REPO / ".agent" / "ENRICH_STOP_REQUESTED"
CHECKLIST = ("keywords", "labels", "meta_description", "use_cases", "alternatives")
LLM_FIELDS = ("meta_description", "use_cases", "alternatives")

try:                                                        # reuse the deterministic enricher (Baltor 'Enhance')
    sys.path.insert(0, str(REPO / "src"))
    from teleon.registry.enrich import description as _desc, keywords as _kw, labels as _lbl, use_cases as _uc  # type: ignore
except Exception:                                           # offline floor
    def _t(s: str) -> list[str]:
        return [x for x in re.split(r"[^a-z0-9]+", (s or "").lower()) if len(x) >= 2]

    def _kw(rec: dict) -> list[str]:
        return sorted(set(rec.get("searchability_tags", []) + _t(rec.get("name", ""))))[:12]

    def _lbl(rec: dict) -> list[str]:
        return [v for v in (rec.get("object_type", ""), rec.get("registry", "")) if v]

    def _desc(rec: dict) -> str:
        return f"{rec.get('name', '')} — a {rec.get('object_type', '')} in the {rec.get('registry', '')} registry."

    def _uc(rec: dict) -> list[str]:
        return rec.get("capabilities", []) or []


def _llm(system: str, user: str, model: str = "glm-5.2") -> str:
    try:
        from scripts._llm_client import chat, resolve_provider
        p = resolve_provider("ollama")
        if not p.get("key"):
            return ""
        r = chat(model, system, user, p, max_tokens=600, timeout=120)
        return "" if r.get("error") else r.get("text", "")
    except Exception:
        return ""


def deterministic_enrich(rec: dict) -> dict:
    return {"keywords": _kw(rec), "labels": _lbl(rec), "meta_description": _desc(rec), "use_cases": _uc(rec)}


def _extract_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def llm_enrich(rec: dict) -> dict | None:
    out = _llm(
        "Analyze a software capability from PUBLIC info only. Output STRICT JSON ONLY: "
        '{"meta_description":"1-2 sentences","use_cases":["..."],"alternatives":["cheaper/more-deterministic alt"]}. '
        "This is a CANDIDATE, never asserted truth; if unsure, keep it general — do not invent specifics.",
        f"name: {rec.get('name')}\nurl: {rec.get('source', {}).get('url', '')}\ntype: {rec.get('object_type')}")
    d = _extract_json(out)
    if not d:
        return None
    return {k: d.get(k) for k in LLM_FIELDS if d.get(k)}


def build_entry(rec: dict, det: dict, llm: dict | None) -> dict:
    fields = dict(det)
    prov = {k: "deterministic" for k in det}
    if llm:
        for k, v in llm.items():
            if v:
                fields[k] = v
                prov[k] = "glm-5.2"
    checklist = {f: ("filled" if fields.get(f) else "missing") for f in CHECKLIST}
    return {"record_id": rec.get("record_id"), "fields": fields, "provenance": prov, "checklist": checklist,
            "serves_truth": False, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}


def _load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"cursor": 0, "llm_done": [], "enriched": 0, "llm_enriched": 0}


def _save_state(s: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def _read_records() -> list[dict]:
    if not RECORDS.exists():
        return []
    out = []
    for ln in RECORDS.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def run_once(llm_per_cycle: int = 5) -> dict:
    s = _load_state()
    recs = _read_records()
    new = recs[s["cursor"]:]
    if not new:
        return {"new": 0, "enriched": s["enriched"], "llm_enriched": s["llm_enriched"]}
    llm_done = set(s.get("llm_done", []))
    budget = llm_per_cycle
    ne = nl = 0
    ENRICH.parent.mkdir(parents=True, exist_ok=True)
    with ENRICH.open("a", encoding="utf-8") as fh:
        for rec in new:
            rid = rec.get("record_id")
            if not rid or not rec.get("name"):
                continue
            det = deterministic_enrich(rec)
            llm = None
            if budget > 0 and rec.get("kind") == "record" and rid not in llm_done:
                llm = llm_enrich(rec)
                if llm:
                    budget -= 1; nl += 1; llm_done.add(rid)
            fh.write(json.dumps(build_entry(rec, det, llm)) + "\n")
            ne += 1
    s.update(cursor=s["cursor"] + len(new), enriched=s["enriched"] + ne, llm_enriched=s["llm_enriched"] + nl,
             llm_done=list(llm_done)[-2000:])
    _save_state(s)
    return {"new": len(new), "enriched_added": ne, "llm_enriched_added": nl,
            "totals": {"enriched": s["enriched"], "llm_enriched": s["llm_enriched"]}}


def supervise(interval: int, llm_per_cycle: int) -> int:
    print(f"enrich_loop: persistent (deterministic + {llm_per_cycle} LLM/cycle). Stop: touch {STOP.relative_to(REPO)}")
    while True:
        if STOP.exists():
            print("ENRICH_STOP_REQUESTED — halting."); return 0
        try:
            res = run_once(llm_per_cycle)
            if res["new"]:
                print(f"[enrich] +{res.get('enriched_added', 0)} enriched ({res.get('llm_enriched_added', 0)} via GLM) "
                      f"totals {res['totals']}")
        except Exception as e:  # noqa: BLE001 — persistent daemon never dies on one bad cycle
            print(f"[enrich] cycle error (continuing): {type(e).__name__}: {e}")
        time.sleep(interval)


def self_test() -> int:
    rec = {"record_id": "r1", "kind": "record", "object_type": "tool", "name": "acme/widget",
           "registry": "tool_registry", "searchability_tags": ["acme", "widget"], "capabilities": ["resize images"],
           "source": {"url": "https://github.com/acme/widget"}}
    det = deterministic_enrich(rec)
    assert det["keywords"] and det["labels"] and det["meta_description"] and isinstance(det["use_cases"], list)
    assert _extract_json('noise {"meta_description":"a tool","use_cases":["x"]} tail') == {"meta_description": "a tool", "use_cases": ["x"]}
    assert _extract_json("no json here") is None
    entry = build_entry(rec, det, {"meta_description": "richer desc", "alternatives": ["cheaper-alt"]})
    assert entry["fields"]["meta_description"] == "richer desc" and entry["provenance"]["meta_description"] == "glm-5.2"
    assert entry["provenance"]["keywords"] == "deterministic" and entry["checklist"]["alternatives"] == "filled"
    assert entry["serves_truth"] is False
    global STATE
    orig = STATE
    import tempfile
    try:
        STATE = Path(tempfile.mkdtemp()) / "s.json"
        _save_state({"cursor": 4, "llm_done": ["x"], "enriched": 1, "llm_enriched": 1})
        assert _load_state()["cursor"] == 4
    finally:
        STATE = orig
    print("enrich_loop self-test: OK (deterministic floor, JSON extract, det+LLM merge with provenance, checklist, state)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--run-once" in argv:
        print(json.dumps(run_once(int(opt("--llm-per-cycle", "5"))), indent=2)); return 0
    if "--supervise" in argv:
        return supervise(int(opt("--interval-sec", "45")), int(opt("--llm-per-cycle", "5")))
    print("usage: enrich_loop.py --self-test | --run-once | --supervise [--interval-sec N --llm-per-cycle N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
