"""provider_intel — System 20 (Provider Intelligence): keep the economics LIVE.

Two paths, both real:
- INGEST (always works, deterministic): feed observations from measured executions (the telemetry write-back) or from a
  price feed into the observation store. This is the fully-working core.
- CRAWL (network-gated, registry-driven): fetch current prices from the wired pricing sources (official + secondary
  providers, listed in _repos/shared-backend-components/architecture/pricing_sources.json) and ingest them. HONESTLY unavailable offline or when no source
  is wired — it never fabricates a price (same doctrine as every other live adapter here: honest-unavailable, not faked).

serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

from src.teleon.economics import observation_store as OBS

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
_SOURCES = _resource("architecture") / "pricing_sources.json"


def ingest(observations: list, *, default_source: str = "ingest", shard: str = "000") -> dict:
    """Record a batch of observations. Each item: {resource_id, [observed_at], [source], cost?, latency_ms?, quality?,
    success?, availability?}. Returns {recorded, cdc_emitted}."""
    recorded = cdc = 0
    for o in observations:
        rid = o.get("resource_id")
        if not rid:
            continue
        res = OBS.record_observation(rid, source=o.get("source", default_source), observed_at=o.get("observed_at"),
                                     cost=o.get("cost"), latency_ms=o.get("latency_ms"), quality=o.get("quality"),
                                     success=o.get("success"), availability=o.get("availability"), shard=shard)
        recorded += 1
        cdc += 1 if res["cdc_emitted"] else 0
    return {"recorded": recorded, "cdc_emitted": cdc, "serves_truth": False}


def record_measured_run(resource_id: str, *, cost=None, latency_ms=None, quality=None, success=None, shard: str = "000") -> dict:
    """The telemetry write-back (§10→§1): a real execution's measured economics become an observation (source=measured)."""
    return OBS.record_observation(resource_id, source="measured", cost=cost, latency_ms=latency_ms,
                                  quality=quality, success=success, shard=shard)


def pricing_sources() -> list:
    if not _SOURCES.exists():
        return []
    return json.loads(_SOURCES.read_text()).get("sources", [])


def crawl(*, network_allowed=None, timeout: int = 20) -> dict:
    """Fetch + ingest current prices from the wired sources (official + secondary providers). Network-gated and
    registry-driven: honest-unavailable offline / when no source is wired — never a fabricated price."""
    if network_allowed is None:
        from src.teleon.dag.real_steps import network_allowed as _net
        network_allowed = _net()
    sources = pricing_sources()
    if not network_allowed:
        return {"available": False, "reason": "needs network (honest offline) — no fabricated prices",
                "sources": len(sources), "ingested": 0, "serves_truth": False}
    if not sources:
        return {"available": False, "reason": "no pricing source wired yet (add one to architecture/pricing_sources.json)",
                "sources": 0, "ingested": 0, "serves_truth": False}
    import urllib.request
    obs, fetched, errors = [], 0, 0
    for src in sources:
        try:
            with urllib.request.urlopen(src["url"], timeout=timeout) as r:
                data = json.loads(r.read().decode())
            rows = data.get(src.get("records_key", "records"), []) if isinstance(data, dict) else data
            for row in rows:
                rid = row.get(src.get("resource_field", "resource_id"))
                if rid:
                    obs.append({"resource_id": rid, "cost": row.get(src.get("cost_field", "cost")),
                                "latency_ms": row.get(src.get("latency_field", "latency_ms")),
                                "availability": row.get(src.get("availability_field", "availability")),
                                "source": src.get("name", "crawl")})
            fetched += 1
        except Exception:  # noqa: BLE001
            errors += 1
    res = ingest(obs)
    return {"available": True, "sources": len(sources), "fetched": fetched, "errors": errors,
            "ingested": res["recorded"], "cdc_emitted": res["cdc_emitted"], "serves_truth": False}
