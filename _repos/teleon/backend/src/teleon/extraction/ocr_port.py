"""src.teleon.extraction.ocr_port — the OCR / document-parse ABSTRACTION LAYER: any OCR engine behind ONE port.

Why (the agnostic-adapter principle, _repos/shared-backend-components/docs/architecture/agnostic-adapters.md): more OCR engines keep arriving, so the
document-extraction cascade depends on an engine-AGNOSTIC port, never a specific engine. Selectable engines are
POPULATED FROM _repos/shared-backend-components/architecture/ocr_provider_registry.json, cheapest-first: a PDF text layer (no OCR) → local deterministic
OCR (Tesseract/PaddleOCR) → cloud OCR (key-gated) → a vision-LLM last resort. A FUTURE engine drops in by a registry
row or `register_ocr_adapter`, zero caller change. Honest: an engine whose binary/package/key is absent reports
unavailable (never fabricates text). serves_truth=false. Open-import-safe (stdlib only; real engines wired by adapters).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

_REGISTRY = _resource("architecture") / "ocr_provider_registry.json"


@runtime_checkable
class OCRPort(Protocol):
    name: str
    def available(self) -> bool: ...
    def extract(self, source: str) -> str: ...   # source = a path/handle; returns text ("" if unavailable)


class CallableOCR:
    """Wrap any (source)->str extractor (tests / a real engine binding)."""
    def __init__(self, fn: Callable[[str], str], *, name: str = "callable", available: bool = True):
        self._fn, self.name, self._av = fn, name, available
    def available(self) -> bool:
        return self._av
    def extract(self, source: str) -> str:
        try:
            return self._fn(source) or ""
        except Exception:  # noqa: BLE001
            return ""


class UnavailableOCR:
    """Honest no-engine port — reports unavailable + never fabricates text (the caller falls back / reports MISSING)."""
    def __init__(self, name: str = "unavailable", reason: str = "engine not installed/configured"):
        self.name, self.reason = name, reason
    def available(self) -> bool:
        return False
    def extract(self, source: str) -> str:
        return ""


def _provider(pid: str) -> dict:
    for p in load_registry().get("providers", []):
        if p["id"] == pid:
            return p
    return {}


def _needs_met(needs: list) -> bool:
    """A provider is available iff its needs are satisfied: a binary on PATH, an importable package, or an env key."""
    import os
    import shutil
    for n in needs or []:
        if n.endswith("_KEY"):
            if not os.environ.get(n):
                return False
        elif n.endswith("_bin"):
            if not shutil.which(n[:-4]):
                return False
        elif n.endswith("_pkg"):
            try:
                __import__(n[:-4])
            except Exception:  # noqa: BLE001
                return False
    return True


#: registered adapter factories — a FUTURE engine drops in here (or as a registry row), zero caller change.
_ADAPTERS: dict[str, Callable[[], OCRPort]] = {}


def register_ocr_adapter(name: str, factory: Callable[[], OCRPort]) -> None:
    _ADAPTERS[str(name)] = factory


def load_registry(path: Path | None = None) -> dict:
    try:
        return json.loads((path or _REGISTRY).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"providers": [], "tiers": {}}


def available_ocr() -> dict:
    """Selectable OCR engines POPULATED FROM the registry + registered adapters, with which are reachable now."""
    reg = load_registry()
    provs = reg.get("providers", [])
    return {"providers": [p["id"] for p in provs], "adapters": sorted(_ADAPTERS),
            "reachable": [p["id"] for p in provs if _needs_met(p.get("needs", []))], "serves_truth": False}


def select_ocr(name: str = "auto", *, require_reachable: bool = True) -> OCRPort:
    """Resolve a name to an OCRPort. 'auto' → the CHEAPEST reachable engine from the registry (text-layer → local →
    cloud → vision-llm). A specific id → its adapter if registered, else a registry-backed stub (available iff its
    needs are met). Unknown/none-reachable → UnavailableOCR (honest). Never raises."""
    if name in _ADAPTERS:
        return _ADAPTERS[name]()
    reg = load_registry()
    tiers = reg.get("tiers", {})
    provs = reg.get("providers", [])
    if name == "auto":
        elig = sorted([p for p in provs if (not require_reachable or _needs_met(p.get("needs", [])))],
                      key=lambda p: (tiers.get(p.get("tier"), 9), p.get("cost", 9), p["id"]))
        if not elig:
            return UnavailableOCR(reason="no OCR engine reachable (no text layer / local bin / cloud key)")
        chosen = elig[0]
    else:
        chosen = _provider(name)
        if not chosen:
            return UnavailableOCR(name=name, reason="unknown OCR provider")
    if _ADAPTERS.get(chosen["id"]):
        return _ADAPTERS[chosen["id"]]()
    # no concrete binding registered → an honest stub that is 'available' only if its needs are met (real adapter
    # bindings are injected by the operator layer; this keeps the port usable + honest offline).
    reachable = _needs_met(chosen.get("needs", []))
    return CallableOCR(lambda src: "", name=chosen["id"], available=reachable) if reachable else \
        UnavailableOCR(name=chosen["id"], reason=f"needs {chosen.get('needs')}")


def descent_order(**kw) -> list[str]:
    """The cheapest-first OCR escalation order among reachable engines (the acquire-stage descent)."""
    reg = load_registry()
    tiers = reg.get("tiers", {})
    elig = [p for p in reg.get("providers", []) if _needs_met(p.get("needs", []))]
    return [p["id"] for p in sorted(elig, key=lambda p: (tiers.get(p.get("tier"), 9), p.get("cost", 9), p["id"]))]


__all__ = ["OCRPort", "CallableOCR", "UnavailableOCR", "register_ocr_adapter", "load_registry",
           "available_ocr", "select_ocr", "descent_order"]
