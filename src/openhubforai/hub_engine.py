"""src.openhubforai.hub_engine — ONE shared engine the 22 Open*Hubs each instantiate (thin, not 22 copies).

Each Open*Hub gets its own orchestrator / models / flywheels / supervisor / agents to build out, rank, verify, improve,
version, scrape, digest, ingest, and serve what it stores — WITHOUT 22 copies of code. A single ``HubEngine`` runs the
lifecycle, parameterized per hub by a ``HubSpec`` (single-sourced from architecture/portfolio_connection_map.json):

    scrape → ingest → digest → rank → verify → version → serve   (the per-hub flywheel = run_cycle)

The model / scraper / ranker / verifier are PLUGGABLE PORTS (deterministic defaults; inject scripts._llm_client +
a real scraper in production) — flexibility, no lock-in, offline-testable.

Also the product wedge the owner named: a hub is a SHARING SURFACE + a governed LEAD-GEN / info-collection FUNNEL.
Users keep their OWN versioned components (tenant-isolated, lossless); ``contribute`` opt-in promotes a verified tenant
component to global; ``substrate_feed`` is what Teleon/Baltor CONSUME (served components + the aggregate funnel) — the
hub never imports them (dependency law: OpenHarnessHub imports neither Baltor nor Teleon; they read this feed).

Governed: candidates are serves_truth=False; only VERIFIED versions are served; tenant-private data never leaves the
tenant except via an explicit opt-in contribute (lossless-distillation law). Open layer; stdlib + shared_infra only.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.openhubforai.component_store import ComponentStore, GLOBAL_TENANT

_REPO = Path(__file__).resolve().parents[2]
_CONN = _REPO / "architecture" / "portfolio_connection_map.json"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "component"


@dataclass(frozen=True)
class HubSpec:
    hub_id: str
    component_kind: str        # what this hub stores/serves (registry 'provides')
    tier: str = "candidate"    # live | private_bench | candidate
    consumed_by: str = ""      # who downstream consumes it (baltor / teleon)


def hub_specs(path: Path | None = None) -> list[HubSpec]:
    """All 22 hub configs, SINGLE-SOURCED from portfolio_connection_map.json (never hand-listed)."""
    d = json.loads((path or _CONN).read_text(encoding="utf-8"))
    return [HubSpec(h["name"], h.get("provides", ""), h.get("tier", "candidate"), str(h.get("consumed_by", "")))
            for h in d.get("hubs", [])]


class HubEngine:
    """The shared per-hub engine. Construct one per HubSpec; ports are injectable (defaults are deterministic)."""

    def __init__(self, spec: HubSpec, store: ComponentStore, *, model: Callable[[str], str] | None = None,
                 scraper: Callable[[], list] | None = None, ranker: Callable[[list], list] | None = None,
                 verifier: Callable[[dict], tuple] | None = None):
        self.spec = spec
        self.store = store
        self.model = model            # (prompt:str)->str  e.g. scripts._llm_client.chat — agent/model port
        self.scraper = scraper        # ()->list[raw]      e.g. a real source poller — ingest port
        self.ranker = ranker or self._default_rank
        self.verifier = verifier or self._default_verify

    # ── lifecycle stages ────────────────────────────────────────────────────────
    def _normalize(self, raw) -> dict:
        if isinstance(raw, str):
            return {"component_id": _slug(raw), "name": raw}
        body = dict(raw)
        body.setdefault("name", body.get("component_id", self.spec.component_kind))
        body.setdefault("component_id", _slug(body["name"]))
        return body

    def digest(self, body: dict) -> dict:
        """Enrich a component (model-backed if a model port is injected; deterministic otherwise)."""
        body = dict(body)
        if not body.get("summary"):
            body["summary"] = (self.model(f"one-line summary of this {self.spec.component_kind}: {json.dumps(body)[:600]}")
                               if self.model else f"{self.spec.component_kind}: {body.get('name', '')}")
        body["component_kind"] = self.spec.component_kind
        return body

    def _default_rank(self, components: list[dict]) -> list[dict]:
        # deterministic: richer (more complete) + verified first, then by id
        return sorted(components, key=lambda c: (-len(json.dumps(c.get("body", c))), c.get("component_id", "")))

    def _default_verify(self, body: dict) -> tuple[bool, str]:
        ok = bool(body.get("component_id") and body.get("name") and body.get("summary"))
        return ok, ("meets the hub bar (id + name + summary)" if ok else "missing id/name/summary")

    def ingest(self, raw, *, tenant: str = GLOBAL_TENANT) -> dict:
        """Normalize + digest a raw candidate and store it as a new (unverified) version. Records a 'store' signal."""
        body = self.digest(self._normalize(raw))
        rec = self.store.put_version(self.spec.hub_id, tenant, body["component_id"], body)
        self.store.record_signal(self.spec.hub_id, tenant, "store", body["component_id"])
        return rec

    def verify(self, rec: dict) -> bool:
        ok, reason = self.verifier(rec["body"])
        self.store.record_verdict(self.spec.hub_id, rec["tenant"], rec["component_id"], rec["version"], ok, reason)
        return ok

    def improve(self, body: dict) -> str:
        return (self.model(f"suggest ONE concrete improvement to this {self.spec.component_kind}: {json.dumps(body)[:600]}")
                if self.model else f"add tests + provenance + a held-out example to {body.get('component_id')}")

    def run_cycle(self, *, tenant: str = GLOBAL_TENANT, raw_candidates: list | None = None) -> dict:
        """The per-hub FLYWHEEL: pull candidates (scraper port or passed in) → ingest → verify → (rank). Idempotent
        (content-hash dedupe), append-only, resilient (a bad candidate is skipped). Returns a governed summary."""
        raws = raw_candidates if raw_candidates is not None else (self.scraper() if self.scraper else [])
        ingested = verified = 0
        for raw in raws:
            try:
                rec = self.ingest(raw, tenant=tenant)
                ingested += 1
                if self.verify(rec):
                    verified += 1
            except Exception:  # noqa: BLE001 — one bad candidate never stops the cycle
                continue
        return {"hub": self.spec.hub_id, "tenant": tenant, "ingested": ingested, "verified": verified,
                "served": len(self.store.serve(self.spec.hub_id, tenant)), "serves_truth": False}

    # ── sharing surface + the lead-gen / substrate funnel (the product wedge) ────
    def download(self, component_id: str, *, tenant: str = GLOBAL_TENANT) -> dict | None:
        """Serve a component to a user (records a 'download' signal — the funnel)."""
        served = {r["component_id"]: r for r in self.store.serve(self.spec.hub_id, tenant)}
        rec = served.get(component_id)
        self.store.record_signal(self.spec.hub_id, tenant, "download", component_id)
        return rec

    def contribute(self, component_id: str, from_tenant: str) -> dict | None:
        """OPT-IN sharing: promote a tenant's latest VERIFIED component to global so others (and Teleon/Baltor) can use
        it. Tenant-private versions stay private; only what the user CHOOSES to contribute becomes global."""
        served = {r["component_id"]: r for r in self.store.serve(self.spec.hub_id, from_tenant)}
        rec = served.get(component_id)
        if not rec:
            return None
        g = self.store.put_version(self.spec.hub_id, GLOBAL_TENANT, component_id, {**rec["body"], "contributed": True})
        self.store.record_verdict(self.spec.hub_id, GLOBAL_TENANT, component_id, g["version"], True, "opt-in contribution from a verified tenant version")
        self.store.record_signal(self.spec.hub_id, from_tenant, "contribute", component_id)
        return g

    def substrate_feed(self) -> dict:
        """What this hub EXPOSES to Teleon/Baltor (which CONSUME it per the dependency law — the hub imports neither):
        the served global components + the AGGREGATE usage funnel (lead-gen + 'makes the core products stronger'),
        never raw tenant data."""
        return {"hub": self.spec.hub_id, "component_kind": self.spec.component_kind, "consumed_by": self.spec.consumed_by,
                "served": self.store.serve(self.spec.hub_id, GLOBAL_TENANT),
                "funnel": self.store.funnel_summary(self.spec.hub_id), "serves_truth": False}


def engines_for_all_hubs(store: ComponentStore, **ports) -> dict[str, HubEngine]:
    """One HubEngine per registry hub — proves the SINGLE engine covers all 22 (config-driven, not 22 copies)."""
    return {s.hub_id: HubEngine(s, store, **ports) for s in hub_specs()}


__all__ = ["HubSpec", "HubEngine", "hub_specs", "engines_for_all_hubs"]
