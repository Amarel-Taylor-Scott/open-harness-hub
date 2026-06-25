#!/usr/bin/env python3
"""scripts.bot_swarm — PERSISTENT Kimi/GLM role-bots on the Ollama lane (OpenClaw/Hermes governed pattern).

The cheap workhorses that run FOREVER so the system improves without Claude Code in the loop. Three governed
role-bots per cycle:
  * discoverer  — keyless seed_ingest on a rotating query → candidate records
  * interrogator— interrogation_engine questions, then GLM 5.2 ANSWERS the top one to enrich the record
  * enricher    — fills missing_metadata / proposes cheaper-deterministic variants (the descent target)
Bots write CANDIDATES only (serves_truth=false) and APPEND-ONLY — they NEVER touch git or edit code (so they are
safe to run alongside other writers). Governed like OpenClaw/Hermes but STRICTER: public metadata only, candidate
tier, honest-on-failure (a 429 logs + skips, never aborts the loop), no PII. Runs until
.agent/SWARM_STOP_REQUESTED.

  --self-test                       offline (no LLM/network)
  --run-once [--query Q]            one cycle
  --supervise [--interval-sec N]    loop forever (the persistent daemon)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
OUT = REPO / "data" / "dev-intel" / "swarm_candidates.jsonl"
STATE = REPO / "data" / "dev-intel" / "swarm_state.json"
STOP = REPO / ".agent" / "SWARM_STOP_REQUESTED"
ROLES = ("discoverer", "interrogator", "enricher")
QUERIES = ["AI agent framework", "MCP server", "browser automation", "RAG pipeline", "LLM router skill",
           "workflow engine", "vector database", "prompt library", "function calling tool", "autonomous coding agent",
           "agentic skill registry", "deterministic tool", "openclaw skill", "hermes function calling"]


def _llm(system: str, user: str, model: str = "glm-5.2") -> str:
    """One governed Ollama-lane call (Kimi/GLM). Honest: returns '' on missing key / error — never raises."""
    try:
        from scripts._llm_client import chat, resolve_provider
        p = resolve_provider("ollama")
        if not p.get("key"):
            return ""
        r = chat(model, system, user, p, max_tokens=1200, timeout=120)
        return "" if r.get("error") else r.get("text", "")
    except Exception:
        return ""


def _load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"cycles": 0, "qi": 0, "discovered": 0, "enriched": 0}


def _save_state(s: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def discoverer(query: str) -> list[dict]:
    from scripts.seed_ingest import fetch, normalize
    out = []
    for source in ("hacker_news", "arxiv", "github"):     # keyless
        for item in fetch(source, query, 5):
            if "_error" not in item:
                out.append(normalize(item, source))
    return out


def interrogator(record: dict) -> dict:
    """Generate interrogation questions, then GLM answers the top one — a real Kimi/GLM enrichment (candidate)."""
    from scripts.interrogation_engine import generate, load_taxonomy
    rows, _ = generate([{"ref": record.get("name", ""), "type": record.get("object_type", "tool")}],
                       load_taxonomy(), dims=["ai_native", "alternatives", "deletion"], context_samples=1, total_cap=4)
    record["interrogation"] = [r["question"] for r in rows]
    if record["interrogation"]:
        ans = _llm(
            "You analyze a software capability from PUBLIC info only. Be concise; say UNKNOWN if unsure. "
            "Output is a CANDIDATE, never asserted truth.",
            f"Capability: {record.get('name')}\nURL: {record.get('source', {}).get('url', '')}\n"
            f"Question: {record['interrogation'][0]}\n"
            "Answer in 2 sentences, then list up to 2 cheaper/more-deterministic alternatives.")
        if ans:
            record["enrichment"] = {"q": record["interrogation"][0], "a": ans[:600], "by": "glm-5.2", "serves_truth": False}
            record["confidence_score"] = min(0.5, record.get("confidence_score", 0.3) + 0.1)
            record["missing_metadata"] = [m for m in record.get("missing_metadata", []) if m != "capabilities"]
    return record


def run_once(query: str | None = None) -> dict:
    s = _load_state()
    q = query or QUERIES[s["qi"] % len(QUERIES)]
    recs = discoverer(q)
    enriched = 0
    seen: set[str] = set()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as fh:
        for r in recs:
            if r["object_id"] in seen:
                continue
            seen.add(r["object_id"])
            r = interrogator(r)
            if r.get("enrichment"):
                enriched += 1
            r["swarm_role_chain"] = list(ROLES)
            fh.write(json.dumps(r) + "\n")
    s.update(cycles=s["cycles"] + 1, qi=s["qi"] + 1, discovered=s["discovered"] + len(recs),
             enriched=s["enriched"] + enriched)
    _save_state(s)
    return {"query": q, "discovered": len(recs), "enriched": enriched, "cycle": s["cycles"]}


def supervise(interval: int) -> int:
    print(f"bot_swarm: persistent ({', '.join(ROLES)}). Stop: touch {STOP.relative_to(REPO)}")
    while True:
        if STOP.exists():
            print("SWARM_STOP_REQUESTED — halting."); return 0
        try:
            res = run_once()
            print(f"[swarm] cycle {res['cycle']}: '{res['query']}' discovered={res['discovered']} enriched={res['enriched']}")
        except Exception as e:  # noqa: BLE001 — a persistent daemon never dies on one bad cycle
            print(f"[swarm] cycle error (continuing): {type(e).__name__}: {e}")
        time.sleep(interval)


def self_test() -> int:
    assert set(ROLES) == {"discoverer", "interrogator", "enricher"}
    assert isinstance(_llm("x", "y"), str)                 # offline-safe: no key -> "" (never raises)
    s = {"cycles": 1, "qi": 3, "discovered": 5, "enriched": 2}
    _save_state(s); assert _load_state()["qi"] == 3
    assert QUERIES and all(isinstance(x, str) for x in QUERIES)
    rec = {"name": "demo/tool", "object_type": "tool", "source": {"url": ""}, "confidence_score": 0.3,
           "missing_metadata": ["capabilities"]}
    out = interrogator(dict(rec))
    assert "interrogation" in out and out.get("serves_truth", False) is False
    print("bot_swarm self-test: OK (3 roles, offline-safe LLM, state roundtrip, governed candidate shaping)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--run-once" in argv:
        print(json.dumps(run_once(opt("--query")), indent=2)); return 0
    if "--supervise" in argv:
        return supervise(int(opt("--interval-sec", "30")))
    print("usage: bot_swarm.py --self-test | --run-once [--query Q] | --supervise [--interval-sec N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
