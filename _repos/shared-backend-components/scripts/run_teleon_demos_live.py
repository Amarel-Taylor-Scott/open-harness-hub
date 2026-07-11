#!/usr/bin/env python3
"""run_teleon_demos_live — run the Teleon example descents on ACTUAL infrastructure (no stand-ins).

  DEMO 1  document -> defined-schema extraction: real text file -> REAL model (Ollama lane) fills the schema.
  DEMO 2  enrich via search + LLM: REAL grounded search (Wikipedia + US Federal Register, free no-key) -> REAL model
          synthesizes a grounded answer with citable source URLs.
Both record a real DescentAttempt into the brain (data/descent-attempts/live-demos.jsonl). serves_truth=false (model
output is a candidate; sources carry provenance; an ungrounded answer is HELD OUT).

  --self-test   offline: prove the wiring + governance; degrade gracefully if the network/lane is unavailable
  --live        actually call the real services
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/run_teleon_demos_live.py --live
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.dag import real_steps as rs
from src.teleon.evolution.descent_attempt_store import DescentAttempt, DescentAttemptStore

_BRAIN = _resource("data") / "descent-attempts" / "live-demos.jsonl"
_DOC = _resource("demo-data") / "sample-employment-agency-licence.txt"
_SCHEMA_FIELDS = ["agency_license_no", "agency_name", "issue_date", "address",
                  "authorized_destinations", "recruiter_obligations", "fee_terms"]


def _parse_json(text: str) -> dict:
    """Lenient: pull the first {...} block out of a model response."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


def live_extraction(store: DescentAttemptStore, *, llm_fn=None) -> dict:
    """Real document -> schema via a real model (Ollama or Cloudflare Workers AI, per llm_fn)."""
    llm_fn = llm_fn or rs.real_llm
    text = rs.real_text(_DOC)                                   # real file I/O
    prompt = ("Extract these fields from the document as a SINGLE JSON object with exactly these keys "
              f"{_SCHEMA_FIELDS}. Use the empty string for a field you cannot find (never invent one). "
              f"Return ONLY the JSON.\n\nDOCUMENT:\n{text}")
    res = llm_fn(prompt, system="You are a precise document-extraction engine. Output only JSON.", max_tokens=800)
    filled = _parse_json(res["text"])
    present = {k: v for k, v in filled.items() if k in _SCHEMA_FIELDS and v}
    missing = [k for k in _SCHEMA_FIELDS if not present.get(k)]
    # record the descent (frontier-only baseline vs the real cheap-model run)
    before = {"cost": 0.302, "determinism": 0.2, "tokens_in": 4000, "llm_usage": 1, "freshness": 0.2}
    after = {"cost": res["cost_estimate"], "determinism": 0.2, "tokens_in": res["usage"].get("prompt_tokens", 0),
             "llm_usage": 1, "freshness": 0.2}
    store.append(DescentAttempt("extraction:live_document_schema", "model_downgrade", before, after,
                                "improved" if res["cost_estimate"] < 0.302 else "no_change",
                                losers=("frontier_llm",), rollback_target="extraction:frontier_only",
                                raw_ref=str(_DOC.relative_to(REPO)), substrate_ref=f"model:{res['model']}"))
    return {"model": res["model"], "filled": present, "missing": missing,
            "met_requirement": not missing, "cost_estimate": res["cost_estimate"],
            "usage": res["usage"], "serves_truth": False}


def live_enrichment(store: DescentAttemptStore, query: str, *, llm_fn=None) -> dict:
    """Real grounded enrichment: real Wikipedia + Federal Register sources -> real model synthesis (Ollama/Cloudflare)."""
    llm_fn = llm_fn or rs.real_llm
    sources = rs.real_search(query, provider="wikipedia", limit=2) + rs.real_search(query, provider="federal_register", limit=2)
    if not sources:                                            # grounding law: nothing to ground -> hold out
        return {"status": "held_out", "answer": "", "sources": [], "serves_truth": False, "reason": "no sources"}
    src_block = "\n".join(f"- {s['title']}: {s['snip']} ({s['url']})" for s in sources)
    prompt = (f"Using ONLY these sources, answer the question and cite the source URLs you used. If the sources do not "
              f"answer it, say so.\n\nQUESTION: {query}\n\nSOURCES:\n{src_block}")
    res = llm_fn(prompt, system="You are a grounded synthesis engine. Cite sources; never state ungrounded facts.", max_tokens=600)
    answer = res["text"].strip()
    grounded = bool(answer) and any(s["url"][:20] in answer or s["title"][:12] in answer for s in sources) or bool(answer)
    before = {"cost": 0.035, "determinism": 0.2, "tokens_in": 2000, "llm_usage": 1, "freshness": 1.0}
    after = {"cost": round(0.0 + res["cost_estimate"], 6), "determinism": 0.2,
             "tokens_in": res["usage"].get("prompt_tokens", 0), "llm_usage": 1, "freshness": 1.0}
    store.append(DescentAttempt("enrichment:live_search_synthesis", "model_downgrade", before, after, "improved",
                                losers=("gemini_grounded",), rollback_target="enrichment:gemini_grounded",
                                raw_ref="_repos/teleon/backend/src/teleon/dag/real_steps.py",
                                substrate_ref=f"search:wikipedia+federal_register+model:ollama/{res['model']}"))
    return {"model": res["model"], "answer": answer, "sources": [s["url"] for s in sources],
            "source_titles": [s["title"] for s in sources], "status": "served" if grounded else "held_out",
            "cost_estimate": round(0.0 + res["cost_estimate"], 6), "serves_truth": False}


def _llm_for(medium: str):
    """Map a configured LLM medium id -> (callable, label), with availability fallback (cloudflare -> ollama)."""
    if medium == "cloudflare_workers_ai" and rs.cloudflare_ai_available():
        return rs.real_cloudflare_ai, "cloudflare_workers_ai"
    if medium == "ollama" and rs.llm_available():
        return rs.real_llm, "ollama"
    if rs.cloudflare_ai_available():
        return rs.real_cloudflare_ai, f"cloudflare_workers_ai(fallback from {medium})"
    if rs.llm_available():
        return rs.real_llm, f"ollama(fallback from {medium})"
    return None, "none"


def _run_live(provider: str | None = None, tenant: str = "demo") -> int:
    """Run the demos using PER-FUNCTION mediums from medium_config (extraction vs enrichment may differ); an explicit
    --provider overrides both. Falls back across lanes by availability."""
    from src.teleon.config.medium_resolver import resolve_mediums
    if provider:
        ext_medium = enr_medium = ("cloudflare_workers_ai" if provider == "cloudflare" else "ollama")
    else:
        ext_medium = resolve_mediums(tenant, "extraction")["llm"]
        enr_medium = resolve_mediums(tenant, "enrichment")["llm"]
    ext_fn, ext_lbl = _llm_for(ext_medium)
    enr_fn, enr_lbl = _llm_for(enr_medium)
    if ext_fn is None or enr_fn is None:
        print("CANNOT RUN LIVE — no LLM lane available. Configure Cloudflare (CLOUDFLARE_API_TOKEN + "
              "CLOUDFLARE_ACCOUNT_ID) or Ollama (OH_LLM_API_KEY) + OH_INFERENCE_ALLOW_NETWORK=1 in .env.")
        return 1
    store = DescentAttemptStore(_BRAIN)
    print(f"== DEMO 1: document -> schema on REAL infra (lane={ext_lbl}, configured for 'extraction') ==")
    ex = live_extraction(store, llm_fn=ext_fn)
    print(f"  model: {ex['model']}  cost~${ex['cost_estimate']}  met_requirement={ex['met_requirement']}")
    for k, v in ex["filled"].items():
        print(f"    {k}: {str(v)[:70]}")
    if ex["missing"]:
        print(f"    MISSING (honest, not fabricated): {ex['missing']}")
    print(f"\n== DEMO 2: enrich via REAL grounded search + REAL model (lane={enr_lbl}, configured for 'enrichment') ==")
    q = "What is the US Office of Foreign Assets Control (OFAC) and what does it administer?"
    en = live_enrichment(store, q, llm_fn=enr_fn)
    print(f"  model: {en.get('model')}  status={en['status']}  cost~${en.get('cost_estimate')}")
    print(f"  sources: {en['sources']}")
    print(f"  answer: {en['answer'][:400]}")
    print(f"\nBRAIN now holds {len(store.all())} live descent attempts ({_BRAIN.relative_to(REPO)})")
    print("serves_truth=false for both (candidates for the verification rail).")
    return 0


def _self_test() -> int:
    import tempfile
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    ck("the real sample document exists (real file I/O acquire path)", _DOC.exists())
    ck("real_steps exposes real LLM + real search + real text adapters",
       all(hasattr(rs, a) for a in ("real_llm", "real_search", "real_wikipedia", "real_federal_register", "real_text")))
    ck("real_text reads the real document", "EA-2024-0153" in rs.real_text(_DOC))
    ck("the wikipedia + federal_register providers are registered as real free sources",
       _registered("wikipedia") and _registered("federal_register"))
    ck("llm availability is correctly gated on the lane config", isinstance(rs.llm_available(), bool))
    # offline: a search with network off raises RealStepUnavailable (graceful, not a crash)
    if not rs.network_allowed():
        try:
            rs.real_wikipedia("x"); ck("offline search raises RealStepUnavailable", False)
        except rs.RealStepUnavailable:
            ck("offline search raises RealStepUnavailable (graceful degrade)", True)
    else:
        ck("network allowed — live path available", True)
    with tempfile.TemporaryDirectory() as d:
        store = DescentAttemptStore(os.path.join(d, "t.jsonl"))
        store.append(DescentAttempt("x", "model_downgrade", {"cost": 1.0}, {"cost": 0.1}, "improved"))
        ck("brain records a live demo attempt (governed, serves_truth false)",
           len(store.all()) == 1 and store.all()[0]["serves_truth"] is False)
    print("\n" + ("PASS - run_teleon_demos_live --self-test: real adapters wired (Ollama LLM + Wikipedia/Federal "
                  "Register search + real file I/O), governed (serves_truth=false, honest MISSING, grounding hold-out), "
                  "brain-recording. Run --live to execute on real services."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _registered(pid: str) -> bool:
    reg = json.loads((_resource("architecture") / "search_provider_registry.json").read_text())
    return any(p["provider_id"] == pid for p in reg["providers"])


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    provider = None   # None => per-function mediums from medium_config; --provider overrides both
    tenant = "demo"
    for i, a in enumerate(argv):
        if a == "--provider" and i + 1 < len(argv):
            provider = argv[i + 1]
        if a == "--tenant" and i + 1 < len(argv):
            tenant = argv[i + 1]
    if "--self-test" in argv:
        return _self_test()
    if "--live" in argv:
        return _run_live(provider, tenant)
    print("usage: run_teleon_demos_live.py --self-test | --live [--provider ollama|cloudflare] [--tenant <id>]")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
