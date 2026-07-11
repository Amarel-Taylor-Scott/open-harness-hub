#!/usr/bin/env python3
"""src.baltor.runtime.registry.capability_registry — the single in-code reader of the External Capability
Catalog (_repos/shared-backend-components/architecture/external_capability_catalog.json), the repo health policy, and the replacement matrix.

Baltor domain code depends on a CAPABILITY SLOT, never on a vendor. This registry is how the runtime answers:
"which adapter is wired for slot X?", "what are its fallbacks/stub?", "is this 3rd-party import cataloged?",
"is the catalog itself well-formed?". The governed runtime is STDLIB-ONLY today — every adoptable slot ships a
working stub so the FIRST real dependency cannot land without a card + I/O contract + fallback in the catalog.

Single sources of truth (no magic values): the 13 backend-tool capability keys and the flagged/do-not-adopt
names are READ from data/backend-tools.yaml (regex, no PyYAML — this host has no pip); the catalog mirrors them
and any drift is a FAILING proof. This module imports stdlib only (runtime layer; see import_boundaries.json).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import re
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[4])
_CATALOG_PATH = _resource("architecture") / "external_capability_catalog.json"
_HEALTH_PATH = _resource("architecture") / "repo_health_policy.json"
_MATRIX_PATH = _resource("architecture") / "repo_replacement_matrix.json"
_BACKEND_TOOLS_PATH = _resource("data") / "backend-tools.yaml"

#: adapter-slot adoption maturity. foil/reference slots are NOT adoptable as a runtime.
VALID_STATUS = {"active", "candidate", "experimental", "deprecated", "quarantined", "replaced", "foil", "reference"}
#: a slot whose status is one of these is a comparison/safety record, not something we wire.
NON_ADOPTABLE_STATUS = {"foil", "reference"}
#: adapter roles inside a slot.
VALID_ROLES = {"primary", "fallback", "stub", "foil", "reference"}
#: roles that count as "we would actually run this provider" — flagged tools must never appear here.
ADOPTED_ROLES = {"primary", "fallback", "stub"}


class UncatalogedRepoError(RuntimeError):
    """Raised when code reaches for a 3rd-party provider that has no card in the capability catalog."""


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def backend_tool_keys() -> list[str]:
    """The 13 capability keys, read from data/backend-tools.yaml (the verified seed — single source)."""
    text = _BACKEND_TOOLS_PATH.read_text(encoding="utf-8")
    return re.findall(r"^  - key:\s*(\w+)", text, re.M)


def flagged_tool_names() -> list[str]:
    """The do-not-reintroduce names, read from the `flagged:` block of data/backend-tools.yaml (single source)."""
    text = _BACKEND_TOOLS_PATH.read_text(encoding="utf-8")
    tail = text.split("\nflagged:", 1)
    if len(tail) != 2:
        return []
    return re.findall(r'name:\s*"([^"]+)"', tail[1])


def load_catalog() -> dict:
    """The External Capability Catalog manifest (_repos/shared-backend-components/architecture/external_capability_catalog.json)."""
    return _read(_CATALOG_PATH)


def load_health_policy() -> dict:
    return _read(_HEALTH_PATH)


def load_matrix() -> dict:
    return _read(_MATRIX_PATH)


class CapabilityRegistry:
    """In-code view over the capability catalog: resolve adapters per slot, gate uncataloged imports, validate."""

    def __init__(self, catalog: dict | None = None, health: dict | None = None) -> None:
        self._catalog = catalog if catalog is not None else load_catalog()
        self._health = health if health is not None else load_health_policy()
        self._slots = {s["capability_slot"]: s for s in self._catalog.get("capability_slots", [])}

    # ---- reads -----------------------------------------------------------------
    def slots(self) -> list[dict]:
        return list(self._slots.values())

    def slot_names(self) -> list[str]:
        return list(self._slots)

    def get_by_capability_slot(self, slot: str) -> dict:
        if slot not in self._slots:
            raise KeyError(f"no capability slot named {slot!r} in the catalog")
        return self._slots[slot]

    def adapters_for(self, slot: str) -> list[dict]:
        return self.get_by_capability_slot(slot).get("adapters", [])

    def get_adapter(self, adapter_id: str) -> dict:
        for s in self._slots.values():
            for a in s.get("adapters", []):
                if a.get("adapter_id") == adapter_id:
                    return a
        raise KeyError(f"no adapter with id {adapter_id!r} in any slot")

    def wired_adapter(self, slot: str) -> dict | None:
        """The adapter currently wired into the stdlib runtime for this slot (its working stub/active), if any."""
        s = self.get_by_capability_slot(slot)
        aid = s.get("adapter_id")
        return self.get_adapter(aid) if aid else None

    def replacement_candidates(self, slot: str) -> list[dict]:
        """Adapters that could replace the wired one if a repo decays: fallbacks + stub (not the wired primary)."""
        s = self.get_by_capability_slot(slot)
        wired = s.get("adapter_id")
        return [a for a in s.get("adapters", []) if a.get("adapter_id") != wired and a.get("role") in ("fallback", "stub", "primary")]

    # ---- NUMERIC preference graph (non-fragile selection; see preference_graph.py) ----------------------
    def preference_order(self, slot: str, *, health: dict | None = None, available: set | None = None,
                         runnable_only: bool = False) -> list[dict]:
        """Adapters for `slot` ordered by NUMERIC priority (desc), not by brittle role strings. Adding or
        relabeling an adapter, or enriching a provider name, never reorders this — only the numbers do."""
        from .preference_graph import resolve_order
        return resolve_order(self.adapters_for(slot), health=health, available=available, runnable_only=runnable_only)

    def preference_graph(self, slot: str) -> dict:
        """Numeric graph view of `slot`'s adapters: nodes + falls_back_to/alternative_of edges by priority."""
        from .preference_graph import preference_graph as _pg
        return _pg(self.adapters_for(slot))

    def import_modules(self) -> dict[str, dict]:
        """Map every declared python import-module → its adapter card. This IS the allowlist for 3rd-party imports."""
        out: dict[str, dict] = {}
        for s in self._slots.values():
            for a in s.get("adapters", []):
                mod = a.get("import_module")
                if mod:
                    out[mod] = a
        return out

    def approved_adapter_paths(self) -> list[str]:
        return list(self._catalog.get("approved_adapter_paths", []))

    def require_cataloged_repo(self, import_module: str) -> dict:
        """Gate: a 3rd-party provider package may only be used if it has a card. Raises otherwise."""
        card = self.import_modules().get(import_module)
        if card is None:
            raise UncatalogedRepoError(
                f"import {import_module!r} has no adapter card in {_CATALOG_PATH.name}; add a card "
                f"(capability_slot + I/O contract + fallback + license + health) before importing it")
        return card

    # ---- validation (used by the proofs) --------------------------------------
    def validate_catalog(self) -> list[str]:
        """Return a list of problems with the catalog; empty == valid. Pure-structural, deterministic, offline."""
        problems: list[str] = []
        required_entry = ("capability_slot", "adapter_id", "input_schema", "output_schema",
                          "contract_proofs", "fallback_adapters", "status", "license", "health_status", "adapters")
        health_enum = set(self._health.get("health_status_enum", []))

        for s in self._catalog.get("capability_slots", []):
            slot = s.get("capability_slot", "<unnamed>")
            for f in required_entry:
                if f not in s:
                    problems.append(f"{slot}: missing field {f!r}")
            if s.get("status") not in VALID_STATUS:
                problems.append(f"{slot}: bad status {s.get('status')!r}")
            if health_enum and s.get("health_status") not in health_enum:
                problems.append(f"{slot}: health_status {s.get('health_status')!r} not in policy enum")
            adopt = s.get("status") not in NON_ADOPTABLE_STATUS
            # adoptable slots MUST have a wired adapter_id that actually exists among their adapters
            adapter_ids = {a.get("adapter_id") for a in s.get("adapters", [])}
            if adopt and s.get("adapter_id") not in adapter_ids:
                problems.append(f"{slot}: wired adapter_id {s.get('adapter_id')!r} not among its adapters")
            for a in s.get("adapters", []):
                if a.get("role") not in VALID_ROLES:
                    problems.append(f"{slot}/{a.get('adapter_id')}: bad role {a.get('role')!r}")
                if health_enum and a.get("health_status") not in health_enum:
                    problems.append(f"{slot}/{a.get('adapter_id')}: health {a.get('health_status')!r} not in policy enum")
                # foil/reference adapters must carry the do-not-adopt note so no one wires them by accident
                if a.get("role") in ("foil", "reference") and not a.get("do_not_adopt_as_runtime"):
                    problems.append(f"{slot}/{a.get('adapter_id')}: foil/reference card missing do_not_adopt_as_runtime")
            # active/candidate slots can't be wired to a decayed/archived adapter
            if s.get("status") in ("active", "candidate"):
                wired = next((a for a in s.get("adapters", []) if a.get("adapter_id") == s.get("adapter_id")), None)
                if wired and wired.get("health_status") in ("decayed", "archived"):
                    problems.append(f"{slot}: active/candidate slot wired to {wired.get('health_status')} adapter")
        return problems

    def covers_backend_tool_keys(self) -> list[str]:
        """Backend-tool capability keys NOT represented as a slot (catalog must build ON backend-tools.yaml)."""
        slots = set(self._slots)
        return [k for k in backend_tool_keys() if k not in slots]

    def adopted_flagged_tools(self) -> list[str]:
        """Flagged (do-not-reintroduce) names that appear as an ADOPTED adapter provider — must be empty."""
        flagged = {n.lower() for n in flagged_tool_names()}
        hits: list[str] = []
        for s in self._slots.values():
            if s.get("status") in NON_ADOPTABLE_STATUS:
                continue
            for a in s.get("adapters", []):
                if a.get("role") not in ADOPTED_ROLES:
                    continue
                prov = str(a.get("provider", "")).lower()
                for fn in flagged:
                    # match a flagged provider name as a whole word in the provider string
                    base = fn.split("(")[0].strip()
                    if base and re.search(rf"\b{re.escape(base)}\b", prov):
                        hits.append(f"{s['capability_slot']}/{a.get('adapter_id')}={a.get('provider')}")
        return hits


def _main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Inspect/validate the External Capability Catalog.")
    p.add_argument("--validate", action="store_true", help="print catalog problems (empty == valid)")
    a = p.parse_args(argv)
    reg = CapabilityRegistry()
    if a.validate:
        probs = reg.validate_catalog()
        print("\n".join(probs) if probs else f"OK — {len(reg.slot_names())} slots, catalog valid")
        return 1 if probs else 0
    print(f"capability slots ({len(reg.slot_names())}): {', '.join(reg.slot_names())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
