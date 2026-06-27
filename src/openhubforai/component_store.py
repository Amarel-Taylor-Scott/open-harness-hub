"""src.openharnesshub.component_store — versioned, multi-tenant, GOVERNED store for Open*Hub components.

Every Open*Hub stores + serves components (context packs, tools, models, skills, reconciliation rules, ...). This is
the shared store behind ALL of them:
  * VERSIONED + LOSSLESS — every put is a new version (append-only over scripts._jsonl_store.AppendLog: SQLite-WAL +
    JSONL mirror); old versions are never overwritten. Identical content (content-hash) does not bump the version.
  * MULTI-TENANT — components live under a tenant. ``_global`` = the hub's own curated components; ``<user>`` = a
    user's OWN versioned components in that hub. Serve merges global ∪ tenant, tenant overriding by component_id.
  * GOVERNED — a version is only SERVED after a VERIFY verdict (append-only event); unverified versions are
    candidates. serves_truth=False on everything (discovery≠trust).

Open layer (dependency law): imports only stdlib + the shared_infra durability engine (lazily). No src.baltor /
src.teleon import.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
DEFAULT_PATH = _REPO / "data" / "openharnesshub" / "components.jsonl"
GLOBAL_TENANT = "_global"


def content_hash(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


class ComponentStore:
    def __init__(self, path: Path | None = None):
        from scripts._jsonl_store import AppendLog  # shared infra (lazy import keeps the open layer clean)
        p = Path(path) if path else DEFAULT_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        self._log = AppendLog(p)

    # ── write (append-only; lossless) ───────────────────────────────────────────
    def put_version(self, hub: str, tenant: str, component_id: str, body: dict, *, serves_truth: bool = False) -> dict:
        """Append a NEW version of a component (idempotent on content-hash; never overwrites). Returns the record."""
        ch = content_hash(body)
        existing = self.versions(hub, tenant, component_id)
        for r in existing:                       # identical content -> reuse the version (no churn)
            if r["content_hash"] == ch:
                return r
        version = (existing[-1]["version"] + 1) if existing else 1
        rec = {"kind": "version", "hub": hub, "tenant": tenant, "component_id": component_id, "version": version,
               "content_hash": ch, "body": body, "serves_truth": bool(serves_truth)}
        self._log.append(rec, idem_key=f"v|{hub}|{tenant}|{component_id}|{ch}")
        return rec

    def record_verdict(self, hub: str, tenant: str, component_id: str, version: int, verified: bool, reason: str = "") -> dict:
        """Append a VERIFY verdict for a specific version (append-only; the latest verdict wins at serve time)."""
        rec = {"kind": "verdict", "hub": hub, "tenant": tenant, "component_id": component_id, "version": int(version),
               "verified": bool(verified), "reason": reason, "serves_truth": False}
        self._log.append(rec)
        return rec

    # ── read ────────────────────────────────────────────────────────────────────
    def versions(self, hub: str, tenant: str, component_id: str) -> list[dict]:
        rows = self._log.all(lambda r: r.get("kind") == "version" and r.get("hub") == hub
                             and r.get("tenant") == tenant and r.get("component_id") == component_id)
        return sorted(rows, key=lambda r: r["version"])

    def latest(self, hub: str, tenant: str, component_id: str) -> dict | None:
        vs = self.versions(hub, tenant, component_id)
        return vs[-1] if vs else None

    def _verified_map(self, hub: str, tenant: str) -> dict[tuple, bool]:
        """(component_id, version) -> latest verdict.verified for this hub+tenant."""
        out: dict[tuple, bool] = {}
        for r in self._log.all(lambda r: r.get("kind") == "verdict" and r.get("hub") == hub and r.get("tenant") == tenant):
            out[(r["component_id"], r["version"])] = r["verified"]   # later append wins
        return out

    def _served_for_tenant(self, hub: str, tenant: str) -> dict[str, dict]:
        verified = self._verified_map(hub, tenant)
        byid: dict[str, dict] = {}
        for r in self._log.all(lambda r: r.get("kind") == "version" and r.get("hub") == hub and r.get("tenant") == tenant):
            if verified.get((r["component_id"], r["version"])) and r["version"] > byid.get(r["component_id"], {}).get("version", 0):
                byid[r["component_id"]] = r
        return byid

    def serve(self, hub: str, tenant: str = GLOBAL_TENANT) -> list[dict]:
        """The SERVABLE components for a tenant: latest VERIFIED version per component_id, global ∪ tenant (the
        tenant's own version overrides the global one). Unverified = withheld (governed; serves_truth=False)."""
        served = dict(self._served_for_tenant(hub, GLOBAL_TENANT))
        if tenant != GLOBAL_TENANT:
            served.update(self._served_for_tenant(hub, tenant))   # tenant overrides global by component_id
        return sorted(served.values(), key=lambda r: r["component_id"])

    # ── the funnel: governed usage signals (lead-gen + the substrate feed for Teleon/Baltor) ─────────────────────
    def record_signal(self, hub: str, tenant: str, action: str, ref: str = "", *, meta: dict | None = None) -> dict:
        """Capture a GOVERNED usage signal (store / download / search / contribute) — the lead-gen + substrate funnel.
        PII-free by contract (callers pass no personal data); tenant-scoped; consumed only in AGGREGATE globally so a
        hub becomes an information-collection endpoint that makes Teleon/Baltor stronger WITHOUT leaking tenant data."""
        rec = {"kind": "signal", "hub": hub, "tenant": tenant, "action": action, "ref": ref,
               "meta": dict(meta or {}), "serves_truth": False}
        self._log.append(rec)
        return rec

    def funnel_summary(self, hub: str | None = None) -> dict:
        """AGGREGATE (PII-free) usage for lead-gen + the substrate: counts per action / per hub + distinct tenants.
        This is what may be consumed globally — never the raw tenant rows."""
        from collections import Counter
        rows = self._log.all(lambda r: r.get("kind") == "signal" and (hub is None or r.get("hub") == hub))
        return {"signals": len(rows), "by_action": dict(Counter(r["action"] for r in rows)),
                "by_hub": dict(Counter(r["hub"] for r in rows)), "tenants": len({r["tenant"] for r in rows}),
                "serves_truth": False}

    def stats(self) -> dict:
        vers = self._log.all(lambda r: r.get("kind") == "version")
        return {"versions": len(vers), "components": len({(r["hub"], r["tenant"], r["component_id"]) for r in vers}),
                "tenants": len({r["tenant"] for r in vers}), "hubs": len({r["hub"] for r in vers})}

    def close(self) -> None:
        try:
            self._log.close()
        except Exception:  # noqa: BLE001
            pass


__all__ = ["ComponentStore", "content_hash", "GLOBAL_TENANT", "DEFAULT_PATH"]
