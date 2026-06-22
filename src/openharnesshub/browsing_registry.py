"""src.openharnesshub.browsing_registry — load + compose + cover the web-browsing stack registry.

Web browsing is a COMPOSED stack (browser + driving logic + model). This loads architecture/web_browsing_stack_registry
.json, derives license_class/vendorable (single-source classifier), composes a governed stack for a need, and computes
COVERAGE vs the targets (>=20 browsers, >=100 driving components) — surfacing the gap honestly rather than padding with
filler. Governance: 'evasion_restricted' browsers (stealth/anti-bot) are excluded unless explicitly authorized; the
guardrail POLICY logic components (robots/rate/captcha-refuse/pii) are always kept. serves_truth=false. Open layer:
stdlib + src.openharnesshub.licenses only (no teleon/baltor import).
"""
from __future__ import annotations

import json
from pathlib import Path

from src.openharnesshub.licenses import classify_license

_REGISTRY = Path(__file__).resolve().parents[2] / "architecture" / "web_browsing_stack_registry.json"
_STATUS_RANK = {"live": 0, "candidate": 1, "service": 2}


def load_registry(path: Path | None = None) -> dict:
    return json.loads((path or _REGISTRY).read_text(encoding="utf-8"))


def browser_view(b: dict) -> dict:
    """A browser entry with license_class + vendorable derived, and a restricted flag (stealth/anti-bot evasion)."""
    lclass, vendorable = classify_license(b.get("license"))
    restricted = b.get("governance") == "evasion_restricted"
    return {**b, "license_class": lclass, "vendorable": vendorable and not restricted, "restricted": restricted}


def model_view(m: dict) -> dict:
    lclass, vendorable = classify_license(m.get("license"))
    return {**m, "license_class": lclass, "vendorable": vendorable}


def coverage(reg: dict | None = None) -> dict:
    """Compute coverage vs the targets (honest gap; no filler). Counts are derived, never hand-typed."""
    reg = reg or load_registry()
    tb, tdc = reg.get("targets", {}).get("browsers", 0), reg.get("targets", {}).get("driving_components", 0)
    hb, hdc = len(reg.get("browsers", [])), len(reg.get("driving_components", []))
    models = sum(1 for d in reg["driving_components"] if d.get("category") == "model")
    logic = sum(1 for d in reg["driving_components"] if d.get("category") == "logic")
    return {"browsers": {"have": hb, "target": tb, "met": hb >= tb, "gap": max(0, tb - hb)},
            "driving_components": {"have": hdc, "target": tdc, "met": hdc >= tdc, "gap": max(0, tdc - hdc),
                                   "models": models, "logic": logic},
            "fill_via": "scripts/repo_intake_strategize.py + the discovery channel", "serves_truth": False}


def select_stack(needs, *, vendorable_only: bool = True, allow_restricted: bool = False, reg: dict | None = None) -> dict:
    """Compose the cheapest GOVERNED browsing stack for `needs` (a set of capabilities): a browser + the driving logic
    components that provide the needed caps + a model when vision/deep_detail is needed. Excludes evasion-restricted
    browsers (unless authorized) and, when vendorable_only, copyleft/proprietary/unstated browsers + models."""
    reg = reg or load_registry()
    needs = set(needs)
    browser_caps = {"js_render", "interaction", "dom", "network_intercept", "crawl", "stealth"}
    need_browser = needs & browser_caps or {"js_render"}

    cands = [browser_view(b) for b in reg["browsers"]]
    elig = [b for b in cands
            if need_browser.issubset(set(b["caps"]))
            and (allow_restricted or not b["restricted"])
            and (not vendorable_only or b["vendorable"])]
    if not elig:
        return {"needs": sorted(needs), "browser": None, "logic": [], "model": None,
                "reason": "no eligible browser (vendorable/governance/caps)", "serves_truth": False}
    # cheapest = vendorable first, then live>candidate>service, then fewest extra caps, then id
    browser = sorted(elig, key=lambda b: (not b["vendorable"], _STATUS_RANK.get(b["status"], 9),
                                          len(set(b["caps"]) - needs), b["id"]))[0]

    logic = [d["id"] for d in reg["driving_components"]
             if d.get("category") == "logic" and (set(d.get("drives", [])) & needs
                                                   or d.get("subtype") == "governance")]  # keep guardrail policies
    model = None
    if needs & {"vision", "deep_detail"}:
        # deep_detail is COMPOSED by the logic (extraction + planning); the model contributes vision/dom understanding.
        model_caps = {"vision", "dom"}
        models = [model_view(m) for m in reg["driving_components"] if m.get("category") == "model"
                  and set(m.get("drives", [])) & model_caps and (not vendorable_only or model_view(m)["vendorable"])]
        models.sort(key=lambda m: (not m["vendorable"], m["id"]))
        model = models[0]["id"] if models else None
    return {"needs": sorted(needs), "browser": browser["id"], "logic": logic, "model": model,
            "vendorable_only": vendorable_only, "serves_truth": False}


__all__ = ["load_registry", "browser_view", "model_view", "coverage", "select_stack"]
