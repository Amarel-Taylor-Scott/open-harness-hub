"""observation_store — System 20 substrate + the telemetry write-back (§10→§1).

Records LIVE economic + quality observations per computational resource (a model/provider/endpoint/backend) — from a
provider price crawl OR a measured execution — and computes the resource's CURRENT rolling economics. When the current
cost moves materially, it emits a CDC event so the router (System 22) can recompile affected pipelines. Operational tier
via the record_store port (SQLite-WAL local / Postgres cloud). serves_truth=false (it measures cost/latency/availability,
it does not assert truth).
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.teleon.storage.record_store import open_record_store

_STREAM = "economic_observations"
_CDC_STREAM = "cdc_events"
_RECENT = 8                 # rolling window: mean of the most-recent N observations per field
_REL_CHANGE_CDC = 0.10      # emit a price-change CDC when current cost moves >= 10%
_FIELDS = ("cost", "latency_ms", "quality", "success", "availability")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _open(shard: str = "000"):
    return open_record_store(_STREAM, shard=shard)


def current_economics(resource_id: str, *, shard: str = "000", store=None) -> dict:
    """Rolling current economics for a resource: the mean of the most-recent N non-null observations per field (None when
    never observed). Includes n (total observations) and observed_at (latest). success is also exposed as success_rate."""
    own = store is None
    store = store or _open(shard)
    try:
        obs = sorted((r for r in store.all() if r.get("resource_id") == resource_id),
                     key=lambda r: r.get("observed_at", ""))
        recent = obs[-_RECENT:]
        out = {"resource_id": resource_id, "n": len(obs), "observed_at": (obs[-1]["observed_at"] if obs else None)}
        for f in _FIELDS:
            vals = [float(r[f]) for r in recent if r.get(f) is not None]
            out[f] = (sum(vals) / len(vals)) if vals else None
        out["success_rate"] = out.get("success")
        return out
    finally:
        if own:
            store.close()


def record_observation(resource_id: str, *, source: str, observed_at: str | None = None, cost=None, latency_ms=None,
                       quality=None, success=None, availability=None, shard: str = "000", emit_cdc: bool = True) -> dict:
    """Append one observation; emit a price-change CDC if the current cost moved >= 10%. Idempotent on
    (resource_id, observed_at, source). Returns {recorded, cdc_emitted, prev, current}."""
    observed_at = observed_at or now_iso()
    store = _open(shard)
    try:
        prev = current_economics(resource_id, store=store)
        obs_key = f"{resource_id}|{observed_at}|{source}"
        rec = {"obs_key": obs_key, "resource_id": resource_id, "observed_at": observed_at, "source": source,
               "cost": cost, "latency_ms": latency_ms, "quality": quality,
               "success": (None if success is None else (1.0 if success else 0.0)), "availability": availability}
        store.append(rec, idem_key=obs_key)
        cur = current_economics(resource_id, store=store)
        cdc = False
        if emit_cdc and isinstance(prev.get("cost"), (int, float)) and prev["cost"] > 0 and cur.get("cost") is not None:
            if abs(cur["cost"] - prev["cost"]) / prev["cost"] >= _REL_CHANGE_CDC:
                _emit_price_cdc(resource_id, prev["cost"], cur["cost"], observed_at, shard=shard)
                cdc = True
        return {"recorded": True, "cdc_emitted": cdc, "prev": prev, "current": cur, "serves_truth": False}
    finally:
        store.close()


def _emit_price_cdc(resource_id: str, prev_cost: float, new_cost: float, observed_at: str, *, shard: str = "000") -> None:
    cdc = open_record_store(_CDC_STREAM, shard=shard)
    try:
        cdc.append({"kind": "economic_price_change", "resource_id": resource_id, "prev_cost": prev_cost,
                    "new_cost": new_cost, "observed_at": observed_at, "serves_truth": False},
                   idem_key=f"price|{resource_id}|{observed_at}")
    finally:
        cdc.close()
