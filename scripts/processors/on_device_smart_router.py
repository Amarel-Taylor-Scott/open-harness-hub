#!/usr/bin/env python3
"""Backs `processor/on-device-smart-router` (process_kind ``route.dispatch``).

Select the best available inference path for a request BEFORE committing to a
model call: on-device CPU (always available) → local GPU/Ollama (LAN) →
cloud API (only when connectivity is confirmed AND the cost ceiling allows).
Deterministic decision table over INJECTED facts (connectivity status, device
profile, budgets) — the router never probes the network itself; the
`offline-fallback-gate` processor produces the connectivity facts. Every
decision carries the reason and a content-addressed routing signature so the
same inputs always route identically (replayable).

Contract: deterministic; side_effects=read; on_error=raise.
Inputs request, connectivity_status, device_profile, cost_ceiling_usd,
latency_budget_ms → selected_path, endpoint_url, routing_reason,
estimated_cost_usd, routing_signature.

CLI / self-test: python3 scripts/processors/on_device_smart_router.py
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

PATH_ON_DEVICE = "on_device_cpu"
PATH_LOCAL_GPU = "local_gpu_http"
PATH_CLOUD = "cloud_api"
#: Priority order per the manifest: cheapest/most-available first; cloud last.
PATH_PRIORITY = (PATH_ON_DEVICE, PATH_LOCAL_GPU, PATH_CLOUD)

#: Cost model per path (USD per request, demo-scale constants with rationale:
#: on-device is sunk cost; LAN GPU is electricity-grade; cloud is metered).
PATH_COST_USD = {PATH_ON_DEVICE: 0.0, PATH_LOCAL_GPU: 0.0002, PATH_CLOUD: 0.01}

#: Latency floors per path (ms) — a path slower than the budget is ineligible.
#: On-device CPU is slow but always there; LAN GPU fast; cloud adds RTT.
PATH_MIN_LATENCY_MS = {PATH_ON_DEVICE: 1500, PATH_LOCAL_GPU: 300, PATH_CLOUD: 700}

#: Tokens-per-request size above which on-device CPU is ineligible (tiny
#: models choke on long prompts; the coherence floor).
ON_DEVICE_MAX_PROMPT_CHARS = 4000

HASH_ALGORITHM = "sha256"
SIGNATURE_PREFIX = "route:"
SIGNATURE_HEX_LEN = 16


def run(*, request: dict[str, Any], connectivity_status: dict[str, Any],
        device_profile: dict[str, Any], cost_ceiling_usd: float,
        latency_budget_ms: int) -> dict[str, Any]:
    """Pick the path. Facts are injected; the router only decides."""
    if not isinstance(request, dict) or "prompt" not in request:
        raise TypeError("request must be a dict with a prompt")
    if not isinstance(connectivity_status, dict) or "online" not in connectivity_status:
        raise ValueError("connectivity_status must carry online (from offline-fallback-gate)")
    if not isinstance(device_profile, dict):
        raise TypeError("device_profile must be a dict")
    if not isinstance(latency_budget_ms, int) or latency_budget_ms < 1:
        raise ValueError(f"latency_budget_ms must be a positive int, got {latency_budget_ms!r}")
    if not isinstance(cost_ceiling_usd, (int, float)) or cost_ceiling_usd < 0:
        raise ValueError(f"cost_ceiling_usd must be >= 0, got {cost_ceiling_usd!r}")

    prompt_chars = len(str(request["prompt"]))
    considered: list[dict[str, Any]] = []
    chosen: dict[str, Any] | None = None
    for path in PATH_PRIORITY:
        reasons: list[str] = []
        if path == PATH_ON_DEVICE:
            if not device_profile.get("on_device_model"):
                reasons.append("no on-device model installed")
            if prompt_chars > ON_DEVICE_MAX_PROMPT_CHARS:
                reasons.append(f"prompt {prompt_chars} chars > on-device cap {ON_DEVICE_MAX_PROMPT_CHARS}")
            endpoint = "local://on-device"
        elif path == PATH_LOCAL_GPU:
            endpoint = str(device_profile.get("local_gpu_url") or "")
            if not endpoint:
                reasons.append("no LAN GPU endpoint in the device profile")
        else:
            endpoint = str(device_profile.get("cloud_url") or "")
            if not endpoint:
                reasons.append("no cloud endpoint configured")
            if not connectivity_status.get("online"):
                reasons.append("connectivity not confirmed (offline gate)")
        if PATH_MIN_LATENCY_MS[path] > latency_budget_ms:
            reasons.append(f"path floor {PATH_MIN_LATENCY_MS[path]}ms > budget {latency_budget_ms}ms")
        if PATH_COST_USD[path] > float(cost_ceiling_usd):
            reasons.append(f"path cost ${PATH_COST_USD[path]} > ceiling ${cost_ceiling_usd}")
        eligible = not reasons
        considered.append({"path": path, "eligible": eligible, "blockers": reasons})
        if eligible and chosen is None:
            chosen = {"path": path, "endpoint": endpoint}
    if chosen is None:
        raise RuntimeError(f"no eligible inference path — blockers: {considered}; "
                           "an ineligible route is never silently forced")
    sig_body = json.dumps({"prompt_chars": prompt_chars, "online": bool(connectivity_status.get("online")),
                           "path": chosen["path"], "budget": latency_budget_ms,
                           "ceiling": float(cost_ceiling_usd)}, sort_keys=True)
    signature = SIGNATURE_PREFIX + hashlib.new(HASH_ALGORITHM, sig_body.encode()).hexdigest()[:SIGNATURE_HEX_LEN]
    return {"selected_path": chosen["path"],
            "endpoint_url": chosen["endpoint"],
            "routing_reason": {"considered": considered,
                               "rule": "first eligible path in priority order "
                                       f"{' -> '.join(PATH_PRIORITY)}"},
            "estimated_cost_usd": PATH_COST_USD[chosen["path"]],
            "routing_signature": signature}


def _selftest() -> None:
    device = {"on_device_model": "gemma-tiny-q4", "local_gpu_url": "http://192.168.1.20:11434",
              "cloud_url": "https://api.example/v1"}
    short = {"prompt": "Translate this alert."}
    # Generous budget → on-device wins (priority order, cheapest first).
    out = run(request=short, connectivity_status={"online": True}, device_profile=device,
              cost_ceiling_usd=0.05, latency_budget_ms=3000)
    assert out["selected_path"] == PATH_ON_DEVICE and out["estimated_cost_usd"] == 0.0
    # Tight latency knocks out the CPU; LAN GPU takes it.
    fast = run(request=short, connectivity_status={"online": True}, device_profile=device,
               cost_ceiling_usd=0.05, latency_budget_ms=500)
    assert fast["selected_path"] == PATH_LOCAL_GPU
    blockers = {c["path"]: c["blockers"] for c in fast["routing_reason"]["considered"]}
    assert any("floor" in b for b in blockers[PATH_ON_DEVICE])
    # Long prompt also knocks out the CPU (coherence floor).
    long = run(request={"prompt": "x" * 5000}, connectivity_status={"online": True},
               device_profile=device, cost_ceiling_usd=0.05, latency_budget_ms=3000)
    assert long["selected_path"] == PATH_LOCAL_GPU
    # No GPU + offline → cloud is ineligible (connectivity unconfirmed) → no path → raise.
    lean = {"on_device_model": None, "cloud_url": "https://api.example/v1"}
    raised = False
    try:
        run(request=short, connectivity_status={"online": False}, device_profile=lean,
            cost_ceiling_usd=0.05, latency_budget_ms=900)
    except RuntimeError as e:
        raised = "never silently forced" in str(e)
    assert raised
    # Online with budget → cloud only when cheaper paths are out AND ceiling allows.
    cloud = run(request=short, connectivity_status={"online": True}, device_profile=lean,
                cost_ceiling_usd=0.05, latency_budget_ms=900)
    assert cloud["selected_path"] == PATH_CLOUD and cloud["endpoint_url"].startswith("https://")
    # Cost ceiling below cloud price blocks it.
    raised = False
    try:
        run(request=short, connectivity_status={"online": True}, device_profile=lean,
            cost_ceiling_usd=0.001, latency_budget_ms=900)
    except RuntimeError:
        raised = True
    assert raised
    # Replayable: identical inputs → identical signature; different path → different.
    again = run(request=short, connectivity_status={"online": True}, device_profile=device,
                cost_ceiling_usd=0.05, latency_budget_ms=3000)
    assert again["routing_signature"] == out["routing_signature"]
    assert fast["routing_signature"] != out["routing_signature"]
    print("PASS — on_device_smart_router: priority decision table over injected facts "
          "(cpu→gpu→cloud), latency/cost/prompt-size eligibility with named blockers, "
          "no-path raises (never forced), replayable signatures verified")


if __name__ == "__main__":
    _selftest()
