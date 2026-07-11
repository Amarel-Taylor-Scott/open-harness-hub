#!/usr/bin/env python3
"""Backs `processor/disable-thinking-mode-latency` (process_kind ``policy.identity``).

Latency policy for low-power / on-device serving: inject a prompt prefix
that suppresses extended chain-of-thought on models that support a thinking
mode, and pin the inference parameters for sub-second response (temperature,
max_tokens, beams). PURE request transform — the original request is never
mutated; the output carries the modified copy plus an exact diff of what was
injected/overridden so the change is auditable.

Suppression applies when ``force_disable_thinking`` is set OR the latency
target is below ``THINKING_LATENCY_FLOOR_MS`` — thinking modes cost seconds,
so a sub-second target implies suppression.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs inference_request, target_latency_ms, force_disable_thinking →
modified_request, thinking_mode_disabled, injected_prefix, param_overrides.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/disable_thinking_mode_latency.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Below this latency target, thinking mode cannot fit — suppress it.
THINKING_LATENCY_FLOOR_MS = 1000

#: The suppression prefix (works across Gemma/Gemini/Claude-style modes:
#: an explicit no-deliberation instruction).
NO_THINKING_PREFIX = ("Answer directly and concisely. Do not show reasoning steps, "
                      "deliberation, or thinking tags.")

#: Low-latency parameter pins, with rationale: greedy-ish decode, tight
#: output budget, single beam.
LOW_LATENCY_PARAMS = {"temperature": 0.2, "max_tokens": 256, "num_beams": 1}

#: Model-API flags that toggle thinking modes off when present.
THINKING_FLAGS_OFF = {"thinking": False, "enable_thinking": False}


def run(*, inference_request: dict[str, Any], target_latency_ms: int,
        force_disable_thinking: bool = False) -> dict[str, Any]:
    """Apply the latency policy to a copy of ``inference_request``."""
    if not isinstance(inference_request, dict) or "prompt" not in inference_request:
        raise TypeError("inference_request must be a dict with a prompt")
    if not isinstance(target_latency_ms, int) or target_latency_ms < 1:
        raise ValueError(f"target_latency_ms must be a positive int, got {target_latency_ms!r}")
    disable = bool(force_disable_thinking) or target_latency_ms < THINKING_LATENCY_FLOOR_MS
    modified = json.loads(json.dumps(inference_request))  # deep copy — original untouched
    injected_prefix = None
    overrides: dict[str, Any] = {}
    if disable:
        injected_prefix = NO_THINKING_PREFIX
        modified["prompt"] = f"{NO_THINKING_PREFIX}\n\n{modified['prompt']}"
        for key, value in {**LOW_LATENCY_PARAMS, **THINKING_FLAGS_OFF}.items():
            if modified.get(key) != value:
                overrides[key] = {"was": modified.get(key), "now": value}
                modified[key] = value
    return {"modified_request": modified,
            "thinking_mode_disabled": disable,
            "injected_prefix": injected_prefix,
            "param_overrides": overrides,
            "policy": {"latency_floor_ms": THINKING_LATENCY_FLOOR_MS,
                       "target_latency_ms": target_latency_ms}}


def _selftest() -> None:
    request = {"prompt": "Summarize the alert.", "temperature": 0.9, "max_tokens": 2048}
    snap = json.dumps(request, sort_keys=True)
    # Sub-second target → suppression + pinned params, with an exact diff.
    out = run(inference_request=request, target_latency_ms=800)
    assert out["thinking_mode_disabled"] is True
    assert out["modified_request"]["prompt"].startswith(NO_THINKING_PREFIX)
    assert out["modified_request"]["temperature"] == LOW_LATENCY_PARAMS["temperature"]
    assert out["param_overrides"]["temperature"] == {"was": 0.9, "now": 0.2}
    assert out["param_overrides"]["max_tokens"]["was"] == 2048
    assert out["modified_request"]["thinking"] is False
    # The ORIGINAL request is never mutated (pure transform).
    assert json.dumps(request, sort_keys=True) == snap
    # Relaxed target → identity (no prefix, no overrides).
    calm = run(inference_request=request, target_latency_ms=5000)
    assert calm["thinking_mode_disabled"] is False and calm["injected_prefix"] is None
    assert calm["param_overrides"] == {} and calm["modified_request"]["prompt"] == request["prompt"]
    # Force flag wins regardless of target.
    forced = run(inference_request=request, target_latency_ms=5000, force_disable_thinking=True)
    assert forced["thinking_mode_disabled"] is True
    # Boundary: exactly the floor does NOT suppress (floor means "below").
    edge = run(inference_request=request, target_latency_ms=THINKING_LATENCY_FLOOR_MS)
    assert edge["thinking_mode_disabled"] is False
    # Deterministic; on_error=raise.
    assert json.dumps(run(inference_request=request, target_latency_ms=800), sort_keys=True) == \
           json.dumps(run(inference_request=request, target_latency_ms=800), sort_keys=True)
    for bad in (lambda: run(inference_request={}, target_latency_ms=800),
                lambda: run(inference_request=request, target_latency_ms=0)):
        raised = False
        try:
            bad()
        except (TypeError, ValueError):
            raised = True
        assert raised
    print("PASS — disable_thinking_mode_latency: sub-second targets suppress thinking "
          "(prefix + pinned params + thinking flags off) with an auditable diff, "
          "originals never mutated, floor boundary exact, force flag verified")


if __name__ == "__main__":
    _selftest()
