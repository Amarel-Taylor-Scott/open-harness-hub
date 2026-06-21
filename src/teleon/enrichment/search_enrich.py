"""src.teleon.enrichment.search_enrich — enrich a fact via SEARCH + LLM, descended off the expensive default.

Most teams reach for ONE expensive grounded-synthesis provider (Gemini + Grounding). But enrichment is two separable
steps: (1) SEARCH for grounded sources, (2) SYNTHESIZE from them. The descent keeps the grounding (sources/citations)
but picks the CHEAPEST provider that returns sources (architecture/search_provider_registry.json) and synthesizes with
the cheapest fresh model (model_index, via substrate_selector) — instead of paying the frontier grounded-synthesis
price. The synthesized answer is a CANDIDATE (serves_truth=false); cited facts carry source handles; an UNGROUNDED
answer is HELD OUT for review (the grounding law). Offline + deterministic (fixtures; no live calls) — the point is the
WIRING + the cost margin. Pure; Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_REGISTRY = _REPO / "architecture" / "search_provider_registry.json"
_SYNTH_TOKENS_OUT = 500          # ~tokens a cheap synthesis emits; cost = model cost_per_mtok_out * this/1e6


def load_providers() -> list[dict]:
    return json.loads(_REGISTRY.read_text(encoding="utf-8"))["providers"]


def baseline_provider() -> dict:
    """The expensive default most teams use (status=baseline) — the descent's BEFORE state."""
    return next(p for p in load_providers() if p.get("status") == "baseline")


def select_provider(*, grounding_required: bool = True, quality_floor_rank: int = 2,
                    providers: list[dict] | None = None) -> dict:
    """Cheapest provider that meets the grounding + quality floor (the search-axis descent). Excludes the baseline so
    the descent demonstrably moves OFF the expensive default when a cheaper grounded option qualifies."""
    pool = [p for p in (providers or load_providers())
            if p.get("status") != "baseline"
            and (p.get("returns_sources") or not grounding_required)
            and p.get("quality_rank", 0) >= quality_floor_rank]
    if not pool:
        return baseline_provider()                       # nothing cheaper qualifies — fall back to the default
    return min(pool, key=lambda p: (p["cost_per_query_usd"], -p.get("quality_rank", 0), p["provider_id"]))


def _synth_model() -> dict:
    """The cheapest fresh model to synthesize with + its lineage (reuses substrate_selector / model_index)."""
    try:
        from src.teleon.evolution import substrate_selector
        from src.teleon.inference import model_index
        dg = substrate_selector.model_downgrade()
        entries = model_index.load_index()
        picked = next((e for e in entries if e["model_id"] == dg.get("picked_model")), None)
        out_cost = picked["cost_per_mtok_out"] if picked else 0.0
        return {"model": dg.get("picked_model"), "cost": round(out_cost * _SYNTH_TOKENS_OUT / 1_000_000, 6),
                "substrate_ref": dg.get("substrate_ref", "")}
    except Exception:  # noqa: BLE001 — lineage is annotation; degrade to a documented cheap-synth estimate
        return {"model": None, "cost": 0.001, "substrate_ref": ""}


#: offline fixtures — synthetic, public-style sources per query (NO real PII). The point is the wiring + cost margin,
#: not a live web call; a real deployment swaps _search() for the selected provider's adapter.
_FIXTURE_SOURCES = {
    "What is the registered address and status of Acme Robotics Inc?": [
        {"url": "https://example-sos.gov/acme-robotics", "snippet": "Acme Robotics Inc, status: active, registered 12 Innovation Way, Austin TX 78701."},
        {"url": "https://example-news.test/acme-series-b", "snippet": "Acme Robotics Inc raised a Series B in 2025; HQ in Austin, Texas."},
        {"url": "https://example-registry.test/acme", "snippet": "Entity Acme Robotics Inc — incorporation state: Delaware; principal office: Austin TX."},
    ],
    "What are the disclosure requirements under Regulation E for electronic fund transfers?": [
        {"url": "https://example-ecfr.gov/12-cfr-1005", "snippet": "Regulation E (12 CFR 1005) requires institutions to give initial disclosures of EFT terms, fees, and consumer liability."},
        {"url": "https://example-federalregister.gov/reg-e-summary", "snippet": "Reg E mandates error-resolution procedures and disclosure of the consumer's liability limits for unauthorized transfers."},
    ],
    "What is the incorporation state and standing of Globex Corporation?": [
        {"url": "https://example-sos.gov/globex", "snippet": "Globex Corporation — status: active; incorporation state: Nevada; principal office: Reno NV."},
        {"url": "https://example-registry.test/globex", "snippet": "Globex Corporation has a registered agent on file and is in good standing as of 2025."},
    ],
}


def _search(query: str, provider: dict) -> list[dict]:
    """Deterministic offline stand-in for the selected provider's search adapter: returns grounded sources."""
    return list(_FIXTURE_SOURCES.get(query, []))


def _synthesize(query: str, sources: list[dict]) -> str:
    """Deterministic offline synthesis: a grounded answer that cites every source it used (a real deployment swaps in
    the cheap LLM). Grounded by construction — it only states what the sources say."""
    if not sources:
        return ""
    facts = "; ".join(s["snippet"] for s in sources)
    return f"{facts} [sources: {', '.join(s['url'] for s in sources)}]"


def enrich(query: str, *, grounding_required: bool = True, quality_floor_rank: int = 2) -> dict:
    """Enrich ``query`` via the DESCENDED path: cheapest grounded search provider + cheap-model synthesis. Returns the
    answer + source handles + cost + governance status. serves_truth=False (synthesis is a candidate); an ungrounded
    answer is HELD OUT (the grounding law), never served as truth."""
    provider = select_provider(grounding_required=grounding_required, quality_floor_rank=quality_floor_rank)
    sources = _search(query, provider)
    needs_llm = not provider.get("does_synthesis")
    synth = _synth_model() if needs_llm else {"model": provider["provider_id"], "cost": 0.0, "substrate_ref": ""}
    answer = _synthesize(query, sources)
    cost = round(provider["cost_per_query_usd"] + (synth["cost"] if needs_llm else 0.0), 6)
    grounded = bool(sources)
    status = "served" if grounded or not grounding_required else "held_out"
    return {
        "query": query, "answer": answer if status == "served" else "",
        "sources": [s["url"] for s in sources], "source_count": len(sources),
        "provider": provider["provider_id"], "synth_model": synth["model"] if needs_llm else None,
        "grounded": grounded, "status": status, "cost": cost,
        "substrate_ref": f"search:{provider['provider_id']}+model:{synth['substrate_ref']}",
        "serves_truth": False,
    }


def enrichment_savings(query: str, **kw) -> dict:
    """The headline: the expensive grounded-synthesis baseline vs the descended path, same query."""
    base = baseline_provider()["cost_per_query_usd"]
    e = enrich(query, **kw)
    saved = round(base - e["cost"], 6)
    return {"baseline_provider": baseline_provider()["provider_id"], "baseline_cost": base,
            "descended_cost": e["cost"], "descended_provider": e["provider"], "synth_model": e["synth_model"],
            "cost_saved": saved, "pct_saved": round(100 * saved / base, 1) if base else 0.0,
            "grounded": e["grounded"], "sources": e["sources"], "serves_truth": False}


def record_enrichment_descent(store, query: str, **kw) -> dict:
    """Record the enrichment as a DescentAttempt (before = expensive grounded-synthesis default; after = cheap search +
    cheap model) into the canonical brain. serves_truth stays False."""
    from src.teleon.evolution.descent_attempt_store import DescentAttempt
    s = enrichment_savings(query, **kw)
    before = {"cost": s["baseline_cost"], "determinism": 0.2, "tokens_in": 2000, "llm_usage": 1, "freshness": 1.0}
    after = {"cost": s["descended_cost"], "determinism": 0.2, "tokens_in": 1000,
             "llm_usage": 1 if s["synth_model"] else 0, "freshness": 1.0}
    e = enrich(query, **kw)
    store.append(DescentAttempt(
        unit_id="enrichment:search_plus_llm", strategy="model_downgrade",
        before=before, after=after, outcome="improved" if s["cost_saved"] > 0 else "no_change",
        losers=(s["baseline_provider"],), rollback_target=f"enrichment:{s['baseline_provider']}",
        raw_ref="src/teleon/enrichment/search_enrich.py", substrate_ref=e["substrate_ref"]))
    return s


def demonstrate() -> dict:
    q = next(iter(_FIXTURE_SOURCES))
    return enrichment_savings(q)
